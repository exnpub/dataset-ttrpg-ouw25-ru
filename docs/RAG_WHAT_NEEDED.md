# 🤖 RAG для Укрытого моря — Полная информация

## Что нужно для создания RAG

RAG (Retrieval-Augmented Generation) требует **четырёх ключевых компонентов**:

### 1️⃣ **Подготовленный корпус** ✅ (уже готов!)

Вы уже имеете:
- ✅ `content/chunks/chunks.jsonl` — 1378 чанков для RAG
- ✅ Все чанки содержат метаданные и связи с документами
- ✅ Структурирован по смыслу (размер ~400–1000 токенов)
- ✅ Лицензирован как Public Domain

### 2️⃣ **Модель эмбеддингов** (embeddings)

Конвертирует текст в векторы для семантического поиска.

**Рекомендуемые модели для русского:**
```python
# Лучшее качество
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('intfloat/multilingual-e5-small')

# Альтернативы:
# 'cointegrated/rubert-large' — очень хорошее качество
# 'cointegrated/rubert-tiny2' — быстро
```

**Что делает:**
- Текст на входе → Вектор (384-768 чисел) на выходе
- Похожие тексты имеют похожие векторы
- Используется для поиска релевантных фрагментов

### 3️⃣ **Векторная БД** (vector store)

Хранит эмбеддинги и позволяет быстро найти похожие.

**Вариант 1: FAISS (локально, бесплатно)**
```python
import faiss
import numpy as np

# Построить индекс
embeddings = np.array(...).astype('float32')
index = faiss.IndexFlatL2(embeddings.shape[1])
index.add(embeddings)

# Найти похожие
distances, indices = index.search(query_embedding, k=5)
```

**Вариант 2: Облачные решения**
| Сервис | Стоимость | Простота | Масштабируемость |
|--------|----------|---------|-----------------|
| **FAISS** | Бесплатно | ⭐⭐ | Ограничена ПК |
| **Qdrant** | Бесплатно/💰 | ⭐⭐⭐ | Высокая |
| **Pinecone** | 💰💰 | ⭐ | Очень высокая |
| **Weaviate** | Бесплатно | ⭐⭐⭐⭐ | Высокая |

### 4️⃣ **Языковая модель** (LLM)

Генерирует ответ на основе контекста.

**Вариант A: Локальная (Ollama)**
```bash
# Установить Ollama: https://ollama.ai
ollama pull mistral

# Использовать в коде
import requests
response = requests.post(
    "http://localhost:11434/api/generate",
    json={"model": "mistral", "prompt": prompt}
)
```

**Вариант B: Cloud API (OpenAI, Anthropic)**
```python
import openai
openai.api_key = "sk-your-key"

response = openai.ChatCompletion.create(
    model="gpt-4",
    messages=[{"role": "user", "content": prompt}]
)
```

---

## 🚀 Минимальный RAG за 30 минут

### Шаг 1: Установка (5 минут)

```bash
cd /путь/к/ouw25_lm

# Установить основные зависимости
pip install numpy sentence-transformers faiss-cpu

# Опционально: для LLM
pip install openai  # или requests если используете Ollama
```

### Шаг 2: Построить индекс (10-15 минут на первый раз)

```python
import json
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss

# Загрузить чанки
chunks = []
with open("content/chunks/chunks.jsonl") as f:
    for line in f:
        chunks.append(json.loads(line))

# Загрузить модель эмбеддингов
model = SentenceTransformer('intfloat/multilingual-e5-small')

# Сгенерировать эмбеддинги
texts = [c["text"] for c in chunks]
embeddings = model.encode(texts, batch_size=32, show_progress_bar=True)
embeddings = np.array(embeddings).astype("float32")

# Построить FAISS-индекс
index = faiss.IndexFlatL2(embeddings.shape[1])
index.add(embeddings)
faiss.write_index(index, "rag_index.faiss")

print(f"✓ Индекс построен: {len(chunks)} чанков")
```

### Шаг 3: Поиск (готово к использованию)

```python
# Загрузить сохранённый индекс
index = faiss.read_index("rag_index.faiss")

# Поиск
query = "Как работает Collision Engine?"
query_embedding = model.encode([query])[0].astype("float32")
distances, indices = index.search(np.array([query_embedding]), k=3)

# Результаты
for idx in indices[0]:
    print(chunks[idx]["text"][:300])
```

### Шаг 4: Интегрировать с LLM

**Вариант A: OpenAI (одна строка!)**
```python
import openai
openai.api_key = "sk-your-key"

# Получить контекст из RAG (из шага 3)
context = "\n".join([chunks[i]["text"] for i in indices[0]])

# Отправить в GPT-4
response = openai.ChatCompletion.create(
    model="gpt-4",
    messages=[{
        "role": "user",
        "content": f"Контекст:\n{context}\n\nВопрос: {query}"
    }]
)
print(response.choices[0].message.content)
```

**Вариант B: Ollama (локально, бесплатно)**
```python
import requests

context = "\n".join([chunks[i]["text"] for i in indices[0]])

response = requests.post(
    "http://localhost:11434/api/generate",
    json={
        "model": "mistral",
        "prompt": f"Контекст:\n{context}\n\nВопрос: {query}"
    }
)
print(response.json()["response"])
```

---

## 🎯 Готовые примеры в репозитории

Все примеры уже в папке `examples/`:

### 1. `rag_quick_demo.py` — основной пример

```bash
python3 examples/rag_quick_demo.py --mode demo
python3 examples/rag_quick_demo.py --mode interactive
```

Возможности:
- ✅ Поиск по семантическому сходству
- ✅ Рейтинг результатов
- ✅ Форматирование для LLM

### 2. `rag_with_ollama.py` — локальная LLM

```bash
# 1. Установить Ollama: https://ollama.ai
# 2. Загрузить модель: ollama pull mistral
# 3. Запустить:
python3 examples/rag_with_ollama.py --mode interactive
```

Возможности:
- ✅ Полный RAG цикл
- ✅ Генерация ответов локально
- ✅ Без облачных сервисов

### 3. `QUICKSTART.md` — быстрый старт

См. файл `examples/QUICKSTART.md` для пошагового руководства.

---

## 📊 Сравнение подходов

### По сложности и времени

| Подход | Время установки | Время инициализации | Сложность | Стоимость |
|--------|-----------------|-------------------|----------|----------|
| **FAISS локально** | 5 мин | 15-30 мин | ⭐⭐ | Бесплатно |
| **Ollama** | 30 мин | 15-30 мин | ⭐⭐ | Бесплатно |
| **OpenAI** | 5 мин | 1 сек | ⭐ | 💰-💰💰 |
| **LangChain** | 10 мин | Зависит | ⭐⭐⭐ | Зависит |

### По производительности

| Фактор | FAISS | Ollama | OpenAI | Облачная БД |
|--------|-------|--------|--------|-----------|
| Скорость поиска | ⚡⚡⚡ | ⚡⚡ | ⚡⚡⚡ | ⚡⚡⚡ |
| Скорость генерации | — | ⚡ | ⚡⚡⚡ | ⚡⚡⚡ |
| Качество ответов | Зависит от LLM | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | Зависит |
| Масштабируемость | Ограничена ПК | Ограничена ПК | ∞ | ∞ |

---

## 💡 Рекомендуемые конфигурации

### Для личного использования
```
FAISS (локально) + Ollama (локально)
= Бесплатно, полная приватность, работает без интернета
```

### Для демонстрации
```
FAISS (локально) + OpenAI API
= Минимальная установка, отличное качество, ~$1-5 за использование
```

### Для production
```
Qdrant (облако) + OpenAI / Open Source модель
= Масштабируемо, быстро, надёжно, $50-1000/месяц
```

### Для образования/экспериментов
```
FAISS (локально) + Ollama (локально)
= Полная контроль, понимание каждого шага, бесплатно
```

---

## 📚 Документация

| Файл | Содержание |
|------|-----------|
| **`docs/RAG_SETUP_GUIDE.md`** | Полное руководство по RAG (30 страниц) |
| **`examples/QUICKSTART.md`** | Быстрый старт (5 минут) |
| **`examples/rag_quick_demo.py`** | Минимальный рабочий пример |
| **`examples/rag_with_ollama.py`** | RAG с локальной LLM |
| **`examples/requirements_rag.txt`** | Все зависимости |

---

## ✅ Чек-лист создания RAG

- [ ] **Выбрать подход** (FAISS vs облака)
- [ ] **Установить зависимости** (`pip install ...`)
- [ ] **Загрузить модель эмбеддингов** (первый запуск автоматический)
- [ ] **Построить индекс** (15-30 минут один раз)
- [ ] **Протестировать поиск** (5 запросов)
- [ ] **Выбрать LLM** (OpenAI vs Ollama)
- [ ] **Написать промпт** (см. примеры)
- [ ] **Интегрировать в приложение** (API/UI)

---

## 🎓 Что дальше?

### Продвинутые техники

1. **Гибридный поиск** — комбинировать семантический + BM25
2. **Re-ranking** — переранжировать результаты второй моделью
3. **Query expansion** — расширять запрос синонимами
4. **Few-shot prompting** — добавлять примеры в промпт
5. **Chain-of-thought** — разбивать сложные вопросы

### Масштабирование

1. Перейти с FAISS на Qdrant/Weaviate
2. Добавить кэширование часто задаваемых вопросов
3. Распределить поиск на несколько машин
4. Добавить аналитику и логирование

### Интеграции

- 🤖 Telegram-бот
- 💬 Discord-бот
- 🌐 Веб-приложение (FastAPI)
- 📱 Мобильное приложение
- 🎮 Встроить в VTT (Roll20, Foundry)

---

## 🆘 Часто задаваемые вопросы

**Q: С чего начать?**
A: Установите `sentence-transformers` и `faiss-cpu`, запустите `examples/rag_quick_demo.py`.

**Q: Нужно ли платить?**
A: Нет! FAISS + Ollama полностью бесплатны. OpenAI стоит дешево (~$0.001 за запрос).

**Q: Будет ли это работать без интернета?**
A: Да! FAISS + Ollama работают локально. Нужен интернет только для первой загрузки моделей.

**Q: Насколько быстро работает?**
A: Поиск: 50-200мс, генерация (Ollama): 1-10 сек, генерация (GPT-4): 1-3 сек.

**Q: Можно ли использовать другие ПК игры?**
A: Абсолютно! Корпус структурирован так, чтобы легко добавлять новые материалы.

---

## 🎯 Итоговые шаги

1. **Читайте `examples/QUICKSTART.md`** — самый быстрый путь
2. **Запустите `rag_quick_demo.py`** — увидите, как это работает
3. **Прочитайте `docs/RAG_SETUP_GUIDE.md`** — полное понимание
4. **Выберите свою конфигурацию** — локальную или облачную
5. **Начните экспериментировать** — создавайте свои RAG-приложения!

---

**Вы готовы создавать RAG-системы!** ⚓

Вопросы? Откройте issue или обратитесь к документации.
