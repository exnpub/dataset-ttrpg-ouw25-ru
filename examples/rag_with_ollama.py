#!/usr/bin/env python3
"""
RAG с локальной LLM через Ollama.

Установка:
1. Ollama: https://ollama.ai
2. Загрузить модель: ollama pull mistral
3. Запустить: python3 examples/rag_with_ollama.py

Ollama скачает модель автоматически (~4-7 ГБ).
Требуется хороший интернет и место на диске.
"""

import json
import numpy as np
import sys
from pathlib import Path
from typing import List, Dict
import requests
import time

# Импортируем основной класс RAG
from examples.rag_quick_demo import UkrytoeMoreRAG, load_dependencies

class OllamaRAG(UkrytoeMoreRAG):
    """RAG с локальной LLM (Ollama)."""
    
    def __init__(self, 
                 corpus_path: str = "content/chunks/chunks.jsonl",
                 index_path: str = "rag_index.faiss",
                 embedding_model: str = "intfloat/multilingual-e5-small",
                 llm_model: str = "mistral",
                 ollama_base_url: str = "http://localhost:11434"):
        """
        Инициализация RAG с Ollama.
        
        Args:
            corpus_path: путь к chunks.jsonl
            index_path: путь к FAISS-индексу
            embedding_model: модель для эмбеддингов
            llm_model: имя модели Ollama (mistral, neural-chat, dolphin-mixtral)
            ollama_base_url: URL сервера Ollama
        """
        super().__init__(corpus_path, index_path, embedding_model)
        
        self.llm_model = llm_model
        self.ollama_url = ollama_base_url
        self.system_prompt = """Вы — ИИ-навигатор, эксперт по настольной ролевой игре «Укрытое море». 
Ваша задача — помогать ведущему и игрокам находить правила и описания мира на основе предоставленного контекста.

ПРАВИЛА:
1. Строго следуйте предоставленному контексту. Если в контексте нет ответа, честно ответьте: «В бортовом журнале нет такой информации».
2. Никогда не смешивайте правила «Укрытого моря» с другими игровыми системами или реальным миром.
3. Сохраняйте оригинальную игровую терминологию и иронично-абсурдистский тон.
4. Отвечайте кратко и по делу."""
        
        # Проверить доступность Ollama
        self._check_ollama()
    
    def _check_ollama(self):
        """Проверить, доступен ли Ollama."""
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get("models", [])
                model_names = [m["name"] for m in models]
                print(f"✓ Ollama доступен")
                print(f"  Доступные модели: {', '.join(model_names[:3])}")
                
                if not any(self.llm_model in m for m in model_names):
                    print(f"\n⚠️  Модель '{self.llm_model}' не установлена!")
                    print(f"  Установите её командой:")
                    print(f"    ollama pull {self.llm_model}")
                    sys.exit(1)
        except requests.exceptions.ConnectionError:
            print("❌ Ошибка: Ollama недоступен!")
            print("\nУбедитесь, что Ollama запущена:")
            print("  ollama serve")
            print("\nИли установите Ollama: https://ollama.ai")
            sys.exit(1)
        except Exception as e:
            print(f"❌ Ошибка при подключении к Ollama: {e}")
            sys.exit(1)
    
    def generate_with_ollama(self, prompt: str) -> str:
        """
        Генерировать ответ с помощью Ollama.
        
        Args:
            prompt: текст запроса
        
        Returns:
            Сгенерированный ответ
        """
        url = f"{self.ollama_url}/api/generate"
        
        # Подготовить полный промпт с системным контекстом
        full_prompt = f"{self.system_prompt}\n\n{prompt}"
        
        try:
            # Отправить запрос потоком
            response = requests.post(
                url,
                json={
                    "model": self.llm_model,
                    "prompt": full_prompt,
                    "stream": False,
                    "temperature": 0.7
                },
                timeout=300  # 5 минут максимум
            )
            
            if response.status_code != 200:
                print(f"⚠️  Ollama вернула статус {response.status_code}")
                return ""
            
            result = response.json()
            return result.get("response", "").strip()
        
        except requests.exceptions.Timeout:
            return "⏳ Timeout: генерация ответа заняла слишком долго"
        except Exception as e:
            print(f"⚠️  Ошибка при работе с Ollama: {e}")
            return ""
    
    def query_with_llm(self, question: str, top_k: int = 5) -> Dict:
        """
        Полный RAG-запрос с LLM.
        
        Args:
            question: вопрос пользователя
            top_k: число фрагментов контекста
        
        Returns:
            Словарь с вопросом, контекстом и ответом
        """
        print("🔍 Поиск релевантных фрагментов...")
        start = time.time()
        
        # 1. Найти релевантные чанки
        results = self.search(question, top_k=top_k)
        
        search_time = time.time() - start
        print(f"✓ Найдено {len(results)} результатов за {search_time:.1f}с")
        
        if not results:
            return {
                "question": question,
                "context": "",
                "answer": "❌ Не найдено релевантной информации в базе знаний.",
                "sources": []
            }
        
        # 2. Собрать контекст
        context_parts = []
        for result in results:
            heading = " → ".join(result["heading_path"])
            context_parts.append(
                f"**{heading}** ({result['chunk_id']})\n\n{result['text']}"
            )
        
        context = "\n\n---\n\n".join(context_parts)
        
        # 3. Подготовить промпт для LLM
        llm_prompt = f"""Контекст из правил игры:
{context}

Вопрос: {question}

Ответьте на основе только информации из контекста выше."""
        
        # 4. Получить ответ от LLM
        print("🧠 Генерирую ответ...")
        gen_start = time.time()
        answer = self.generate_with_ollama(llm_prompt)
        gen_time = time.time() - gen_start
        print(f"✓ Ответ сгенерирован за {gen_time:.1f}с")
        
        # 5. Собрать результат
        return {
            "question": question,
            "answer": answer,
            "sources": [r["chunk_id"] for r in results[:3]],
            "context_chunks": len(results),
            "search_time": search_time,
            "generation_time": gen_time
        }
    
    def interactive_with_llm(self):
        """Интерактивный режим с LLM."""
        print("\n" + "="*70)
        print("🌊 Укрытое море RAG + Ollama LLM")
        print("="*70)
        print(f"📚 Индекс: {len(self.chunks)} чанков")
        print(f"🧠 LLM: {self.llm_model}")
        print("   Введите вопрос (или 'quit' для выхода)\n")
        
        while True:
            try:
                question = input("❓ Вопрос: ").strip()
            except KeyboardInterrupt:
                print("\n\n⚓ До свидания!")
                break
            
            if question.lower() in ['quit', 'выход', 'exit', 'q']:
                print("⚓ До свидания!")
                break
            
            if not question:
                continue
            
            # Полный RAG-запрос
            print()
            result = self.query_with_llm(question, top_k=3)
            
            print(f"\n📝 Ответ:\n{result['answer']}")
            print(f"\n🏷️  Источники: {', '.join(result['sources'])}")
            print(f"⏱️  Время: поиск {result['search_time']:.1f}s, генерация {result['generation_time']:.1f}s")
            print()

def demo_with_llm():
    """Демонстрация RAG + LLM."""
    print("\n" + "="*70)
    print("🌊 Укрытое море RAG + Ollama - Демонстрация")
    print("="*70 + "\n")
    
    rag = OllamaRAG()
    
    # Предопределённые вопросы
    demo_questions = [
        "Как работает Collision Engine?",
        "Что такое Благословенный прилив?",
    ]
    
    for question in demo_questions[:1]:  # Только первый для быстрой демо
        print(f"❓ Вопрос: {question}\n")
        result = rag.query_with_llm(question)
        
        print(f"📝 Ответ:\n{result['answer']}")
        print(f"\n🏷️  Источники: {', '.join(result['sources'])}")
        print("\n" + "="*70 + "\n")

def main():
    """Главная функция."""
    import argparse
    
    parser = argparse.ArgumentParser(description="RAG с Ollama для Укрытого моря")
    parser.add_argument("--mode", choices=["demo", "interactive"], 
                       default="interactive", help="Режим работы")
    parser.add_argument("--model", default="mistral", 
                       help="Модель Ollama (mistral, neural-chat)")
    
    args = parser.parse_args()
    
    try:
        if args.mode == "demo":
            demo_with_llm()
        else:
            rag = OllamaRAG(llm_model=args.model)
            rag.interactive_with_llm()
    except Exception as e:
        print(f"❌ Ошибка: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
