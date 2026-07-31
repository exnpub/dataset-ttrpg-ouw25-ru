#!/usr/bin/env python3
"""
Автоматизированное тестирование RAG-системы с Ollama.
Проверяет точность ответов на основе 'Золотых вопросов'.

Использование:
    export KMP_DUPLICATE_LIB_OK=TRUE
    python3 scripts/test_rag_ollama.py --model mistral
"""

import os
import sys
import time
import json
import subprocess
import requests
from typing import List, Dict

# Добавляем корневую директорию в путь для импорта
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from examples.rag_with_ollama import OllamaRAG
except ImportError:
    print("❌ Ошибка: Не удалось импортировать OllamaRAG.")
    print("Убедитесь, что вы запускаете скрипт из корня проекта.")
    sys.exit(1)

# Набор тестовых случаев (Золотые вопросы с учётом морфологии русского языка)
TEST_CASES = [
    {
        "id": "TC-001",
        "question": "Что такое Collision Engine?",
        "expected_keywords": ["конфликт", "движок", "подсистем"],
        "min_keywords": 1
    },
    {
        "id": "TC-002",
        "question": "Кто такой Кррмп Лэм?",
        "expected_keywords": ["станок", "печат", "технические"],
        "min_keywords": 1
    },
    {
        "id": "TC-003",
        "question": "Как рассчитывается базовая ставка (БС) при перевозках?",
        "expected_keywords": ["кают", "ог", "сектор"],
        "min_keywords": 1
    },
    {
        "id": "TC-004",
        "question": "Что официально означает 'Благословенный прилив' по мнению Олъмсовета?",
        "expected_keywords": ["мир", "стабильност", "состояние"],
        "min_keywords": 2
    }
]

class RAGTester:
    def __init__(self, model_name: str = "mistral"):
        self.ollama_url = "http://localhost:11434"
        self._ensure_ollama()
        print(f"🛠️  Инициализация тестера RAG (модель: {model_name})...")
        try:
            self.rag = OllamaRAG(llm_model=model_name)
            print("✅ Система инициализирована\n")
        except Exception as e:
            print(f"❌ Ошибка инициализации: {e}")
            sys.exit(1)

    def _ensure_ollama(self):
        """Гарантирует запуск Ollama."""
        try:
            requests.get(f"{self.ollama_url}/api/tags", timeout=5)
            return True
        except Exception:
            print("🚀 Сервер Ollama не запущен. Попытка запуска...")
            try:
                subprocess.Popen(["open", "-a", "Ollama"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                for i in range(30):
                    try:
                        requests.get(f"{self.ollama_url}/api/tags", timeout=2)
                        print("✅ Сервер Ollama успешно запущен!")
                        time.sleep(2)
                        return True
                    except:
                        time.sleep(1)
                print("❌ Не удалось дождаться запуска Ollama.")
                sys.exit(1)
            except Exception as e:
                print(f"❌ Ошибка при попытке запуска Ollama: {e}")
                sys.exit(1)

    def run_tests(self) -> List[Dict]:
        results = []
        total_start = time.time()
        
        print(f"🚀 Запуск {len(TEST_CASES)} тестов...\n")
        print(f"{'ID':<8} | {'Статус':<10} | {'Поиск':<6} | {'Ген.':<6} | {'Совпадения'}")
        print("-" * 65)

        for case in TEST_CASES:
            test_id = case["id"]
            question = case["question"]
            min_kw = case.get("min_keywords", 1)
            
            # 1. Выполняем запрос
            start = time.time()
            res = self.rag.query_with_llm(question, top_k=3)
            
            # 2. Проверяем наличие ключевых слов
            answer = res["answer"].lower()
            found_keywords = [k for k in case["expected_keywords"] if k.lower() in answer]
            
            # 3. Определяем статус
            passed = len(found_keywords) >= min_kw and len(answer) > 20
            status = "✅ PASSED" if passed else "❌ FAILED"
            
            # 4. Логируем
            match_str = f"{len(found_keywords)}/{len(case['expected_keywords'])}"
            print(f"{test_id:<8} | {status:<10} | {res['search_time']:>5.1f}s | {res['generation_time']:>5.1f}s | {match_str}")
            
            results.append({
                "id": test_id,
                "passed": passed,
                "question": question,
                "answer": res["answer"],
                "keywords_found": found_keywords,
                "search_time": res["search_time"],
                "gen_time": res["generation_time"]
            })

        duration = time.time() - total_start
        passed_count = sum(1 for r in results if r["passed"])
        
        print("\n" + "="*65)
        print(f"📊 ИТОГО: {passed_count}/{len(TEST_CASES)} тестов пройдено")
        print(f"⏱️  Общее время: {duration:.1f}с")
        print("="*65)
        
        return results

    def save_report(self, results: List[Dict], path: str = "docs/RAG_TEST_REPORT.md"):
        """Сохранить детальный отчет в Markdown."""
        with open(path, "w", encoding="utf-8") as f:
            f.write("# 📊 Отчет о тестировании RAG + Ollama\n\n")
            f.write(f"**Дата:** {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"**Модель:** {self.rag.llm_model}\n\n")
            
            f.write("## Сводка\n\n")
            passed = sum(1 for r in results if r["passed"])
            f.write(f"- Всего тестов: {len(results)}\n")
            f.write(f"- Пройдено: {passed}\n")
            f.write(f"- Провалено: {len(results) - passed}\n\n")
            
            f.write("## Детали тестов\n\n")
            for r in results:
                status = "✅ PASSED" if r["passed"] else "❌ FAILED"
                f.write(f"### {r['id']}: {r['question']}\n\n")
                f.write(f"**Статус:** {status}\n\n")
                f.write(f"**Ответ LLM:**\n> {r['answer']}\n\n")
                f.write(f"**Ключевые слова найдено:** {', '.join(r['keywords_found']) if r['keywords_found'] else 'нет'}\n\n")
                f.write(f"**Время:** поиск {r['search_time']:.1f}с, генерация {r['gen_time']:.1f}с\n\n")
                f.write("---\n\n")
        
        print(f"\n📝 Детальный отчет сохранен в: {path}")

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Авто-тест RAG + Ollama")
    parser.add_argument("--model", default="mistral", help="Модель Ollama")
    args = parser.parse_args()

    tester = RAGTester(model_name=args.model)
    results = tester.run_tests()
    tester.save_report(results)

if __name__ == "__main__":
    main()
