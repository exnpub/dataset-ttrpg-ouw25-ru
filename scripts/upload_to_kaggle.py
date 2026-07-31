#!/usr/bin/env python3
"""
Скрипт загрузки корпуса и RAG-артефактов на Kaggle Datasets.
Исключает тяжёлые бинарные файлы (.faiss) и адаптирует README для Kaggle.

Использует переменные окружения из .env:
    KAGGLE_TOKEN - ваш API токен Kaggle
    KAGGLE_REPO  - ID датасета на Kaggle (например, exnihilum/ttrpg-ouw25-ru)

Использование:
    python3 scripts/upload_to_kaggle.py
"""

import json
import os
import re
import sys
import shutil
from pathlib import Path
from dotenv import load_dotenv

# Настройки путей
BASE_DIR = Path(__file__).parent.parent
EXPORT_DIR = BASE_DIR / "hf_dataset_export"
KAGGLE_STAGING_DIR = BASE_DIR / "kaggle_export"
DOTENV_PATH = BASE_DIR / ".env"

def main():
    print("🚢 Подготовка к загрузке на Kaggle Datasets (без FAISS и с адаптированным README)...")

    # 1. Загрузка конфигурации
    if not DOTENV_PATH.exists():
        print(f"❌ Файл .env не найден в {BASE_DIR}")
        print("Скопируйте .env.example в .env и заполните KAGGLE_TOKEN и KAGGLE_REPO.")
        sys.exit(1)

    load_dotenv(DOTENV_PATH)

    token = os.getenv("KAGGLE_TOKEN") or os.getenv("KAGGLE_API_TOKEN") or os.getenv("KAGGLE_KEY")
    repo_id = os.getenv("KAGGLE_REPO") or os.getenv("KAGGLE_DATASET_ID")

    if not token:
        print("❌ KAGGLE_TOKEN не задан в .env файле.")
        sys.exit(1)

    if not repo_id:
        print("❌ KAGGLE_REPO не задан в .env файле.")
        sys.exit(1)

    username = repo_id.split("/")[0] if "/" in repo_id else "exnihilum"

    os.environ["KAGGLE_API_TOKEN"] = token
    os.environ["KAGGLE_KEY"] = token
    os.environ["KAGGLE_USERNAME"] = username

    # 2. Инициализация Kaggle API
    try:
        from kaggle.api.kaggle_api_extended import KaggleApi
        api = KaggleApi()
        api.authenticate()
        print(f"🔑 Успешная авторизация в Kaggle API (пользователь: {username})")
    except Exception as e:
        print(f"❌ Ошибка авторизации в Kaggle API: {e}")
        sys.exit(1)

    # 3. Подготовка папки для Kaggle (исключаем .faiss файлы)
    if not EXPORT_DIR.exists() or not list(EXPORT_DIR.glob("*.parquet")):
        print(f"❌ Файлы датасета не найдены в {EXPORT_DIR}.")
        print("Сначала запустите: python3 scripts/prepare_for_huggingface.py")
        sys.exit(1)

    KAGGLE_STAGING_DIR.mkdir(exist_ok=True)

    # Очищаем старые файлы в staging
    for old_f in KAGGLE_STAGING_DIR.glob("*"):
        if old_f.is_file():
            old_f.unlink()

    # Копируем всё, кроме *.faiss
    for item in EXPORT_DIR.iterdir():
        if item.is_file() and not item.name.endswith(".faiss"):
            shutil.copy2(item, KAGGLE_STAGING_DIR / item.name)

    # Обрабатываем README для Kaggle: убираем упоминания FAISS индекса
    hf_readme = BASE_DIR / "hf_dataset_README.md"
    if hf_readme.exists():
        readme_text = hf_readme.read_text(encoding="utf-8")

        # Удаляем Вариант 2 с FAISS
        pattern = r"### Вариант 2: Использование готового FAISS-индекса.*?## ⚖️ Лицензирование"
        readme_text = re.sub(pattern, "## ⚖️ Лицензирование", readme_text, flags=re.DOTALL | re.IGNORECASE)

        # Удаляем упоминание FAISS из списка артефактов
        faiss_item_pattern = r"### 4\. `rag_index\.faiss`.*?контекста\.\n\n"
        readme_text = re.sub(faiss_item_pattern, "", readme_text, flags=re.DOTALL)

        # Перенумеровываем пункт 5 в 4
        readme_text = readme_text.replace("### 5. `global_knowledge_map.json`", "### 4. `global_knowledge_map.json`")

        (KAGGLE_STAGING_DIR / "README.md").write_text(readme_text, encoding="utf-8")

    print(f"📦 Подготовлены файлы для Kaggle:")
    for f in sorted(KAGGLE_STAGING_DIR.iterdir()):
        if f.is_file():
            print(f"   - {f.name} ({f.stat().st_size / 1024:.1f} KB)")

    # 4. Создание метаданных Kaggle dataset-metadata.json
    metadata = {
        "title": "«Укрытое море: Благословенный прилив» ML DS",
        "id": repo_id,
        "subtitle": "Corpus, semantic chunks & embeddings for On Ulerior Waves (Ru) TTRPG.",
        "description": "The official machine-learning and RAG dataset for the tabletop role-playing game **On Ulerior Waves** (Укрытое море) by Ex Nihilum Publishing. Featuring a unique decopunk, seacrawl, and weird fiction setting in Veah Toaoroah.\n\n### Contents:\n- **Chunks**: 1378 semantic chunks optimized for RAG and vector retrieval.\n- **Documents**: 39 fully normalized markdown chapters, supplements, and SRD.\n- **Embeddings**: Precomputed 384-dimensional multilingual embeddings (multilingual-e5-small).\n- **Images & Knowledge Map**: Metadata for 132 illustrations and the global knowledge map.\n\n**License**: Text contents are released under Public Domain (CC0).",
        "keywords": [
            "ttrpg",
            "seacrawl",
            "hexcrawl",
            "decopunk",
            "weird-fiction",
            "tabletop-rpg",
            "rag",
            "worldbuilding",
            "rulebook",
            "russian-nlp"
        ],
        "licenses": [
            {
                "name": "CC0-1.0"
            }
        ]
    }

    metadata_path = KAGGLE_STAGING_DIR / "dataset-metadata.json"
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    # 5. Создание или обновление датасета на Kaggle
    print(f"📂 Загрузка датасета {repo_id} на Kaggle...")
    try:
        existing_datasets = [d.ref for d in api.dataset_list(user=username)]
        if repo_id in existing_datasets:
            print(f"   🔄 Обновление существующего датасета {repo_id}...")
            api.dataset_create_version(
                folder=str(KAGGLE_STAGING_DIR),
                version_notes="v1.1.0 update: clean README for Kaggle without FAISS instructions",
                dir_mode="zip"
            )
        else:
            print(f"   ✨ Создание нового публичного датасета {repo_id}...")
            api.dataset_create_new(
                folder=str(KAGGLE_STAGING_DIR),
                dir_mode="zip",
                public=True
            )

        print(f"\n🎉 Датасет успешно обновлен на Kaggle с чистым README!")
        print(f"🌐 Ссылка: https://www.kaggle.com/datasets/{repo_id}")

    except Exception as e:
        print(f"❌ Ошибка при загрузке на Kaggle: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
