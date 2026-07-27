# 🚀 Быстрый старт RAG для «Укрытого моря»

## За 5 минут от нуля до RAG

### Шаг 1: Установить зависимости (2 минуты)

```bash
cd /путь/к/ouw25_lm

# Вариант A: Минимальное (только семантический поиск)
pip install numpy sentence-transformers faiss-cpu

# Вариант B: Полное (с поддержкой LLM)
pip install -r examples/requirements_rag.txt
```

### Шаг 2: Запустить демо (1 минута)

```bash
python3 examples/rag_quick_demo.py --mode demo
```

**Вывод:**
```
🌊 Укрытое море RAG - Демонстрация
======================================================================

❓ Вопрос: Как работает Collision Engine?
----------------------------------------------------------------------
📖 4 > Разные разборки > Драматический размен
   Схожесть: 89%
   Collision Engine — это система разрешения конфликтов в Укрытом...
...
```

### Шаг 3: Интерактивный режим (оставшееся время)

```bash
python3 examples/rag_quick_demo.py --mode interactive
```

Теперь вы можете вводить вопросы и видеть релевантные ответы!

```
🌊 Укрытое море RAG - Интерактивный поиск
======================================================================

❓ Вопрос: Что такое Благословенный прилив?
🔍 Ищу...
✅ Найдено 3 результатов за 123мс

🏷️  3 > Минимальный контекст > География и климат
📍 ouw25-2-1-minimalnyy-kontekst--0002 (схожесть: 92%)
📝 Благословенный прилив — это циклическое явление в мире Укрытого...

...
```

---

## Что дальше?

### Для локальной RAG (без интернета):

```bash
# 1. Установить Ollama
# https://ollama.ai

# 2. Загрузить модель
ollama pull mistral:latest

# 3. Запустить RAG с локальной LLM
python3 examples/rag_with_ollama.py
```

### Для облачной RAG (OpenAI):

```bash
# 1. Установить openai
pip install openai

# 2. Установить API ключ
export OPENAI_API_KEY="sk-your-key-here"

# 3. Запустить RAG с GPT-4
python3 examples/rag_with_openai.py
```

### Для веб-приложения:

```bash
# 1. Установить FastAPI
pip install fastapi uvicorn

# 2. Запустить API сервер
uvicorn examples.rag_api:app --reload

# 3. Открыть в браузере
# http://localhost:8000/docs
```

---

## 📊 Сравнение подходов

| Подход | Установка | Стоимость | Скорость | Качество |
|--------|-----------|----------|---------|---------|
| **FAISS-локально** | 5 мин | Бесплатно | ⚡⚡ | ⭐⭐⭐ |
| **Ollama** | 15 мин | Бесплатно | ⚡ | ⭐⭐⭐⭐ |
| **OpenAI** | 5 мин | 💰 | ⚡⚡⚡ | ⭐⭐⭐⭐⭐ |
| **Qdrant** | 20 мин | Бесплатно | ⚡⚡ | ⭐⭐⭐ |
| **Weaviate** | 30 мин | Бесплатно | ⚡⚡ | ⭐⭐⭐ |

---

## 🆘 Решение проблем

### "ModuleNotFoundError: No module named 'sentence_transformers'"

```bash
pip install sentence-transformers
```

### "FAISS error: index_type=6, ret=-1, index destroyed?"

Это нормально при первом запуске. RAG построит индекс автоматически.

### Поиск медленный

Используйте более простую модель:
```python
embedding_model="cointegrated/rubert-tiny2"  # быстро
# вместо
embedding_model="intfloat/multilingual-e5-small"  # медленнее
```

### "Результаты не релевантны"

- Попробуйте другую модель эмбеддингов
- Увеличьте `top_k` (количество результатов)
- Измените размер чанков в `content/chunks/chunks.jsonl`

---

## 🎓 Дополнительные примеры

См. полное руководство: [`docs/RAG_SETUP_GUIDE.md`](../docs/RAG_SETUP_GUIDE.md)

Рабочие примеры в [`examples/`](./):
- `rag_quick_demo.py` — основной пример
- `rag_with_ollama.py` — локальная LLM
- `rag_with_openai.py` — OpenAI API
- `rag_api.py` — веб-сервис

---

**Готово! Теперь у вас есть рабочая RAG-система.** ⚓
