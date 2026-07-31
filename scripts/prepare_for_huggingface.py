#!/usr/bin/env python3
"""
Скрипт подготовки корпуса «Укрытое море» для публикации на Hugging Face.
Конвертирует JSONL индексы в формат Parquet, экспортирует эмбеддинги и FAISS-индекс.

Зависимости:
    pip install pandas pyarrow faiss-cpu datasets python-dotenv

Использование:
    python3 scripts/prepare_for_huggingface.py
"""

import json
import os
import shutil
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime

# Настройки путей
BASE_DIR = Path(__file__).parent.parent
INPUT_DIR = BASE_DIR / "content"
OUTPUT_DIR = BASE_DIR / "hf_dataset_export"
FAISS_INDEX_PATH = BASE_DIR / "rag_index.faiss"

INDEXES = {
    "chunks": INPUT_DIR / "chunks" / "chunks.jsonl",
    "documents": INPUT_DIR / "indexes" / "documents.jsonl",
    "images": INPUT_DIR / "indexes" / "images.jsonl"
}

def check_dependencies():
    """Проверка наличия необходимых библиотек."""
    missing = []
    try:
        import pandas
    except ImportError:
        missing.append("pandas")
    try:
        import pyarrow
    except ImportError:
        missing.append("pyarrow")
    try:
        import faiss
    except ImportError:
        missing.append("faiss-cpu")
    
    if missing:
        print(f"❌ Отсутствуют необходимые библиотеки: {', '.join(missing)}")
        print("Установите их командой:")
        print(f"  pip install {' '.join(missing)}")
        return False
    return True

def load_jsonl(path: Path):
    """Загрузка данных из JSONL файла."""
    if not path.exists():
        print(f"⚠️  Файл не найден: {path}")
        return []
    
    data = []
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                data.append(json.loads(line))
    return data

def prepare_chunks(data):
    """Подготовка конфига чанков."""
    df = pd.DataFrame(data)
    cols = [
        "chunk_id", "document_id", "chunk_number", 
        "heading_path", "document_type", "language", 
        "license", "text"
    ]
    return df[cols] if not df.empty else df

def prepare_documents(data):
    """Подготовка конфига полных документов."""
    df = pd.DataFrame(data)
    cols = [
        "document_id", "title", "document_type", 
        "language", "license", "text"
    ]
    return df[cols] if not df.empty else df

def prepare_images(data):
    """Подготовка конфига метаданных изображений."""
    df = pd.DataFrame(data)
    
    mapping = {
        "alt": "alt_text",
        "path": "file_path",
        "document_id": "source_document"
    }
    df = df.rename(columns=mapping)
    df = df.loc[:, ~df.columns.duplicated()]
    
    if "image_id" not in df.columns:
        df["image_id"] = df.index.map(lambda i: f"img_{i+1:04d}")
        
    df["license"] = "Copyright (Ex Nihilum Publishing)"
    df = df.loc[:, ~df.columns.duplicated()]
    
    cols = [
        "image_id", "alt_text", "source_document", 
        "file_path", "license"
    ]
    existing_cols = [c for c in cols if c in df.columns]
    return df[existing_cols]

def prepare_embeddings(chunks_data):
    """Экспорт векторных эмбеддингов из FAISS индекса в Parquet."""
    import faiss
    if not FAISS_INDEX_PATH.exists():
        print(f"⚠️  FAISS индекс не найден в {FAISS_INDEX_PATH}. Пропускаем export embeddings.parquet.")
        return None
        
    print(f"🧠 Извлечение векторов из {FAISS_INDEX_PATH.name}...")
    index = faiss.read_index(str(FAISS_INDEX_PATH))
    vectors = index.reconstruct_n(0, index.ntotal)
    
    chunk_ids = [c["chunk_id"] for c in chunks_data]
    if len(chunk_ids) != len(vectors):
        print(f"⚠️  Несоответствие количества чанков ({len(chunk_ids)}) и векторов ({len(vectors)})!")
        return None
        
    df = pd.DataFrame({
        "chunk_id": chunk_ids,
        "embedding": vectors.tolist()
    })
    return df

def main():
    print("🚀 Начинаю подготовку датасета и RAG-артефактов для Hugging Face...")
    
    if not check_dependencies():
        return

    OUTPUT_DIR.mkdir(exist_ok=True)
    stats = {}

    # 1. Основные таблицы данных
    chunks_raw = []
    for name, path in INDEXES.items():
        print(f"📦 Обработка конфигурации: {name}...")
        raw_data = load_jsonl(path)
        
        if not raw_data:
            print(f"      ✕ Данные не найдены")
            continue
            
        if name == "chunks":
            chunks_raw = raw_data
            df = prepare_chunks(raw_data)
        elif name == "documents":
            df = prepare_documents(raw_data)
        elif name == "images":
            df = prepare_images(raw_data)
        else:
            df = pd.DataFrame(raw_data)
            
        output_file = OUTPUT_DIR / f"{name}.parquet"
        df.to_parquet(output_file, index=False)
        stats[name] = len(df)
        print(f"      ✓ Сохранено {len(df)} записей в {output_file.name}")

    # 2. Векторные эмбеддинги
    if chunks_raw:
        df_emb = prepare_embeddings(chunks_raw)
        if df_emb is not None:
            emb_file = OUTPUT_DIR / "embeddings.parquet"
            df_emb.to_parquet(emb_file, index=False)
            stats["embeddings"] = len(df_emb)
            print(f"      ✓ Сохранено {len(df_emb)} векторов в {emb_file.name}")

    # 3. Копирование бинарного FAISS индекса
    if FAISS_INDEX_PATH.exists():
        dest_faiss = OUTPUT_DIR / "rag_index.faiss"
        shutil.copy2(FAISS_INDEX_PATH, dest_faiss)
        print(f"      ✓ Бинарный FAISS-индекс скопирован в {dest_faiss.name}")
        stats["faiss_index"] = f"{dest_faiss.stat().st_size / (1024*1024):.2f} MB"

    # 4. Копирование Глобальной Карты Знаний и Манифеста Концепции
    global_map_src = INPUT_DIR / "manifests" / "global_knowledge_map.json"
    if global_map_src.exists():
        dest_map = OUTPUT_DIR / "global_knowledge_map.json"
        shutil.copy2(global_map_src, dest_map)
        print(f"      ✓ Глобальная карта знаний скопирована в {dest_map.name}")
        stats["knowledge_map"] = "included"

    concept_src = BASE_DIR / "GAME_CONCEPT.md"
    if concept_src.exists():
        dest_concept = OUTPUT_DIR / "GAME_CONCEPT.md"
        shutil.copy2(concept_src, dest_concept)
        print(f"      ✓ Манифест концепции скопирован в {dest_concept.name}")
        stats["game_concept"] = "included"

    # 5. Генерация сводной информации
    summary = {
        "dataset_name": "ukrytoe-more-corpus",
        "version": "1.1.0",
        "generated_at": datetime.now().isoformat(),
        "stats": stats,
        "embedding_model": "intfloat/multilingual-e5-small",
        "vector_dimension": 384,
        "license": "CC0 (text), Copyright (images)"
    }
    
    with open(OUTPUT_DIR / "dataset_summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
        
    print("\n✨ Подготовка всех датасетов и RAG-артефактов завершена успешно!")
    print(f"📂 Файлы подготовлены в папке: {OUTPUT_DIR}")
    print(f"📊 Статистика: {stats}")

if __name__ == "__main__":
    main()
