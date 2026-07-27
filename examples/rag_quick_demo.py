#!/usr/bin/env python3
"""
Полностью рабочий RAG для Укрытого моря.

Установка зависимостей:
    pip install numpy sentence-transformers faiss-cpu

Запуск:
    python3 examples/rag_quick_demo.py

Для использования с OpenAI/Ollama см. комментарии в коде.
"""

import json
import numpy as np
import sys
from pathlib import Path
from typing import List, Dict, Tuple
import time

def load_dependencies():
    """Загрузить зависимости с обработкой ошибок."""
    try:
        from sentence_transformers import SentenceTransformer
        import faiss
        return SentenceTransformer, faiss
    except ImportError as e:
        print(f"❌ Ошибка импорта: {e}")
        print("\nУстановите зависимости:")
        print("  pip install numpy sentence-transformers faiss-cpu")
        sys.exit(1)

class UkrytoeMoreRAG:
    """RAG-система для игры «Укрытое море»."""
    
    def __init__(self, corpus_path: str = "content/chunks/chunks.jsonl",
                 index_path: str = "rag_index.faiss",
                 embedding_model: str = "intfloat/multilingual-e5-small"):
        """
        Инициализация RAG.
        
        Args:
            corpus_path: путь к chunks.jsonl
            index_path: путь к сохранённому индексу FAISS
            embedding_model: модель для эмбеддингов
        """
        self.corpus_path = corpus_path
        self.index_path = index_path
        self.embedding_model_name = embedding_model
        self.chunks = []
        self.model = None
        self.index = None
        
        # Загрузить компоненты
        self._load_components()
    
    def _load_components(self):
        """Загрузить модель, индекс и чанки."""
        SentenceTransformer, faiss = load_dependencies()
        
        # 1. Загрузить чанки
        print("[1/3] 📚 Загружаю чанки из корпуса...")
        if not Path(self.corpus_path).exists():
            raise FileNotFoundError(f"Файл не найден: {self.corpus_path}")
        
        with open(self.corpus_path) as f:
            self.chunks = [json.loads(line) for line in f]
        print(f"      ✓ Загружено {len(self.chunks)} чанков")
        
        # 2. Загрузить модель эмбеддингов
        print(f"[2/3] 🧠 Загружаю модель: {self.embedding_model_name}...")
        self.model = SentenceTransformer(self.embedding_model_name)
        print("      ✓ Модель загружена")
        
        # 3. Загрузить или построить индекс
        print("[3/3] 🔍 Загружаю FAISS-индекс...")
        try:
            self.index = faiss.read_index(self.index_path)
            print(f"      ✓ Индекс загружен из {self.index_path}")
        except FileNotFoundError:
            print(f"      ℹ️  Индекс не найден. Строю новый...")
            self._build_index(faiss)
    
    def _build_index(self, faiss_module):
        """Построить FAISS-индекс для всех чанков."""
        print("      ⏳ Генерирую эмбеддинги (это может занять 1-5 минут)...")
        
        texts = [chunk["text"] for chunk in self.chunks]
        start = time.time()
        
        # Генерировать эмбеддинги батчами
        embeddings = self.model.encode(
            texts,
            batch_size=32,
            show_progress_bar=True,
            convert_to_numpy=True
        )
        embeddings = np.array(embeddings).astype("float32")
        
        elapsed = time.time() - start
        print(f"      ✓ Эмбеддинги генерированы ({elapsed:.1f}с)")
        
        # Построить индекс
        print("      ⏳ Строю FAISS-индекс...")
        dimension = embeddings.shape[1]
        self.index = faiss_module.IndexFlatL2(dimension)
        self.index.add(embeddings)
        
        # Сохранить индекс
        faiss_module.write_index(self.index, self.index_path)
        print(f"      ✓ Индекс сохранён в {self.index_path}")
    
    def search(self, query: str, top_k: int = 3) -> List[Dict]:
        """
        Найти релевантные чанки по запросу.
        
        Args:
            query: текст запроса
            top_k: число результатов
        
        Returns:
            Список релевантных чанков с метаданными
        """
        # Конвертировать запрос в эмбеддинг
        query_embedding = self.model.encode(
            [query],
            convert_to_numpy=True
        )[0].astype("float32")
        
        # Найти K ближайших соседей
        distances, indices = self.index.search(
            np.array([query_embedding]),
            top_k
        )
        
        # Собрать результаты
        results = []
        for i, idx in enumerate(indices[0]):
            if idx == -1:  # -1 означает пустой результат
                continue
            
            chunk = self.chunks[idx]
            distance = distances[0][i]
            
            # Конвертировать расстояние L2 в схожесть (0-1)
            similarity = 1.0 / (1.0 + distance)
            
            results.append({
                "rank": len(results) + 1,
                "chunk_id": chunk["chunk_id"],
                "document_id": chunk["document_id"],
                "heading_path": chunk["heading_path"],
                "heading_str": " → ".join(chunk["heading_path"]),
                "text": chunk["text"],
                "similarity": similarity,
                "distance": distance
            })
        
        return results
    
    def format_results(self, results: List[Dict], max_chars: int = 500) -> str:
        """Форматировать результаты для вывода."""
        if not results:
            return "❌ Результаты не найдены"
        
        output = []
        for result in results:
            output.append(f"🏷️  {result['heading_str']}")
            output.append(f"📍 {result['chunk_id']} (схожесть: {result['similarity']:.1%})")
            
            text_preview = result["text"]
            if len(text_preview) > max_chars:
                text_preview = text_preview[:max_chars] + "..."
            output.append(f"📝 {text_preview}")
            output.append("")
        
        return "\n".join(output)
    
    def format_context(self, results: List[Dict]) -> str:
        """Форматировать результаты для LLM контекста."""
        if not results:
            return ""
        
        parts = []
        for result in results:
            heading = " → ".join(result["heading_path"])
            parts.append(f"**{heading}** `{result['chunk_id']}`\n\n{result['text']}")
        
        return "\n\n---\n\n".join(parts)
    
    def interactive_search(self):
        """Интерактивный режим поиска."""
        print("\n" + "="*70)
        print("🌊 Укрытое море RAG - Интерактивный поиск")
        print("="*70)
        print(f"📚 Индекс: {len(self.chunks)} чанков загружено")
        print("   Введите вопрос (или 'quit' для выхода)\n")
        
        while True:
            try:
                query = input("❓ Вопрос: ").strip()
            except KeyboardInterrupt:
                print("\n\n⚓ До свидания!")
                break
            except EOFError:
                break
            
            if query.lower() in ['quit', 'выход', 'exit', 'q']:
                print("⚓ До свидания!")
                break
            
            if not query:
                continue
            
            # Поиск
            print("🔍 Ищу...")
            start = time.time()
            results = self.search(query, top_k=3)
            elapsed = time.time() - start
            
            print(f"✅ Найдено {len(results)} результатов за {elapsed*1000:.0f}мс\n")
            
            if results:
                print(self.format_results(results))
                
                # Опционально: вывести контекст для LLM
                context = self.format_context(results)
                print(f"💡 Контекст для LLM ({len(context)} символов):")
                print("-" * 70)
                print(context[:1000])
                if len(context) > 1000:
                    print("...")
                print("-" * 70)
            
            print()

def demo_mode():
    """Демонстрационный режим с предопределёнными вопросами."""
    print("\n" + "="*70)
    print("🌊 Укрытое море RAG - Демонстрация")
    print("="*70 + "\n")
    
    rag = UkrytoeMoreRAG()
    
    # Предопределённые вопросы для демонстрации
    demo_queries = [
        "Как работает Collision Engine?",
        "Что такое Благословенный прилив?",
        "Какие есть порты в Укрытом море?",
        "Как считать риск при взаимодействии?",
    ]
    
    for query in demo_queries:
        print(f"❓ Вопрос: {query}")
        print("-" * 70)
        
        results = rag.search(query, top_k=2)
        
        if results:
            for result in results:
                print(f"📖 {result['heading_str']}")
                print(f"   Схожесть: {result['similarity']:.1%}")
                text_preview = result["text"][:200]
                print(f"   {text_preview}...")
                print()
        else:
            print("Результаты не найдены\n")
        
        print()

def main():
    """Главная функция."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="RAG для игры «Укрытое море»"
    )
    parser.add_argument(
        "--mode",
        choices=["interactive", "demo"],
        default="demo",
        help="Режим работы"
    )
    parser.add_argument(
        "--corpus",
        default="content/chunks/chunks.jsonl",
        help="Путь к файлу чанков"
    )
    parser.add_argument(
        "--index",
        default="rag_index.faiss",
        help="Путь к индексу FAISS"
    )
    
    args = parser.parse_args()
    
    try:
        if args.mode == "demo":
            demo_mode()
        else:
            rag = UkrytoeMoreRAG(
                corpus_path=args.corpus,
                index_path=args.index
            )
            rag.interactive_search()
    
    except FileNotFoundError as e:
        print(f"❌ Файл не найден: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Ошибка: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
