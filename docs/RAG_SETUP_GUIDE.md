# 🤖 Руководство по созданию RAG-системы на базе корпуса

Полный пошаговый гайд по созданию Retrieval-Augmented Generation (RAG) системы
для настольной ролевой игры «Укрытое море».

---

## 📋 Что такое RAG?

RAG — это архитектура, которая:
1. **Извлекает** релевантные фрагменты из базы знаний
2. **Передаёт** их языковой модели как контекст
3. **Генерирует** ответ на основе контекста

**Преимущества для игровой системы:**
- ✅ Точные ответы без галлюцинаций (только из корпуса)
- ✅ Цитирование источников
- ✅ Актуальная информация о правилах
- ✅ Поддержка всех игровых механик

---

## 🏗️ Компоненты RAG-системы

```
┌─────────────────────────────────────────┐
│      Подготовленный корпус              │
│  (content/chunks/chunks.jsonl)          │
└────────────────┬────────────────────────┘
                 │
         ┌───────▼────────┐
         │ 1. ЭМБЕДДИНГИ  │  ← Конвертируем текст в векторы
         │   (embeddings) │
         └───────┬────────┘
                 │
         ┌───────▼─────────────┐
         │ 2. ВЕКТОРНАЯ БД     │  ← Сохраняем векторы + метаданные
         │  (vector store)     │   • FAISS, Weaviate, Milvus, Pinecone
         └───────┬─────────────┘
                 │
         ┌───────▼────────────┐
         │ 3. ПОИСК           │  ← Находим похожие чанки
         │ (retriever)        │   по семантическому сходству
         └───────┬────────────┘
                 │
         ┌───────▼──────────────────┐
         │ 4. ГЕНЕРАЦИЯ             │  ← LLM формирует ответ
         │ (LLM generator)          │   на основе контекста
         └────────────────────────────┘
```

---

## 🚀 Быстрый старт (30 минут)

### Вариант 1: Локальная RAG с Python (самый простой)

#### Шаг 1: Установить зависимости

```bash
# Основные пакеты
pip install numpy sentence-transformers faiss-cpu

# Опционально (для работы с LLM)
pip install ollama  # локальная модель
# или
pip install openai  # OpenAI API
```

#### Шаг 2: Загрузить данные и построить индекс

```python
import json
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss

# 1. Загрузить чанки из корпуса
chunks = []
with open("content/chunks/chunks.jsonl") as f:
    for line in f:
        chunks.append(json.loads(line))

print(f"Загружено {len(chunks)} чанков")

# 2. Загрузить модель эмбеддингов (русский текст)
model = SentenceTransformer('intfloat/multilingual-e5-small')
# или для более точного результата:
# model = SentenceTransformer('cointegrated/rubert-tiny2')

# 3. Сгенерировать эмбеддинги для всех чанков
print("Генерирую эмбеддинги...")
texts = [chunk["text"] for chunk in chunks]
embeddings = model.encode(texts, batch_size=32, show_progress_bar=True)
embeddings = np.array(embeddings).astype("float32")

print(f"Размер эмбеддингов: {embeddings.shape}")

# 4. Построить FAISS-индекс
dimension = embeddings.shape[1]
index = faiss.IndexFlatL2(dimension)
index.add(embeddings)

# 5. Сохранить индекс
faiss.write_index(index, "rag_index.faiss")
print("Индекс сохранён в rag_index.faiss")
```

#### Шаг 3: Создать простой RAG-поиск

```python
import json
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss

# Загрузить сохранённый индекс и чанки
model = SentenceTransformer('intfloat/multilingual-e5-small')
index = faiss.read_index("rag_index.faiss")

chunks = []
with open("content/chunks/chunks.jsonl") as f:
    for line in f:
        chunks.append(json.loads(line))

def search_rag(query: str, top_k: int = 3) -> list:
    """Поиск релевантных чанков по запросу."""
    # Конвертировать запрос в эмбеддинг
    query_embedding = model.encode([query])[0].astype("float32")
    
    # Найти K ближайших соседей
    distances, indices = index.search(np.array([query_embedding]), top_k)
    
    # Вернуть результаты с метаданными
    results = []
    for idx in indices[0]:
        if idx != -1:  # -1 означает пустой результат
            results.append({
                "chunk_id": chunks[idx]["chunk_id"],
                "document_id": chunks[idx]["document_id"],
                "heading_path": " → ".join(chunks[idx]["heading_path"]),
                "text": chunks[idx]["text"][:500],  # первые 500 символов
                "full_text": chunks[idx]["text"]
            })
    return results

# Тестирование
query = "Как рассчитать риск в Укрытом море?"
results = search_rag(query)

print(f"Найдено результатов: {len(results)}\n")
for i, result in enumerate(results, 1):
    print(f"--- Результат {i} ---")
    print(f"Документ: {result['heading_path']}")
    print(f"ID: {result['chunk_id']}")
    print(f"Текст: {result['text']}...\n")
```

#### Шаг 4: Интегрировать с LLM

**Вариант A: Локальная модель (Ollama)**

```bash
# 1. Установить Ollama: https://ollama.ai
# 2. Загрузить русскую модель
ollama pull mistral:latest
ollama pull neural-chat:latest

# 3. Запустить сервер (автоматически при установке)
```

```python
import ollama
import json
from sentence_transformers import SentenceTransformer
import faiss

# Загрузить RAG-компоненты (из предыдущего шага)
model = SentenceTransformer('intfloat/multilingual-e5-small')
index = faiss.read_index("rag_index.faiss")
chunks = [json.loads(line) for line in open("content/chunks/chunks.jsonl")]

def rag_query(question: str) -> str:
    """RAG-запрос с использованием локальной модели Ollama."""
    
    # 1. Найти релевантные чанки
    query_embedding = model.encode([question])[0].astype("float32")
    distances, indices = index.search(np.array([query_embedding]), 3)
    
    # 2. Собрать контекст
    context_parts = []
    for idx in indices[0]:
        if idx != -1:
            chunk = chunks[idx]
            heading = " → ".join(chunk["heading_path"])
            context_parts.append(f"**{heading}**\n\n{chunk['text']}")
    
    context = "\n\n---\n\n".join(context_parts)
    
    # 3. Подготовить промпт
    system_prompt = """Вы — ИИ-навигатор, эксперт по настольной ролевой игре «Укрытое море». 
Ваша задача — помогать ведущему и игрокам находить правила и описания на основе предоставленного контекста.

ПРАВИЛА:
1. Строго следуйте предоставленному контексту. 
2. Если в контексте нет ответа, честно ответьте: «В бортовом журнале (базе знаний) нет таких сведений».
3. Сохраняйте оригинальную терминологию игры.
4. Используйте иронично-морской тон."""
    
    user_prompt = f"""Контекст из правил:
{context}

Вопрос: {question}

Ответьте, используя только информацию из контекста выше."""
    
    # 4. Получить ответ от LLM
    response = ollama.generate(
        model="mistral",
        prompt=user_prompt,
        system=system_prompt,
        stream=False
    )
    
    return response['response']

# Тестирование
question = "Как работает Collision Engine?"
answer = rag_query(question)
print(f"Вопрос: {question}\n")
print(f"Ответ:\n{answer}")
```

**Вариант B: OpenAI API**

```python
import openai
import json
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np

# Настроить API ключ
openai.api_key = "sk-your-api-key-here"

# Загрузить RAG-компоненты
model = SentenceTransformer('intfloat/multilingual-e5-small')
index = faiss.read_index("rag_index.faiss")
chunks = [json.loads(line) for line in open("content/chunks/chunks.jsonl")]

def rag_query_openai(question: str, model_name: str = "gpt-4") -> str:
    """RAG-запрос с использованием OpenAI."""
    
    # 1. Найти релевантные чанки
    query_embedding = model.encode([question])[0].astype("float32")
    distances, indices = index.search(np.array([query_embedding]), 5)
    
    # 2. Собрать контекст
    context_parts = []
    citations = []
    for idx in indices[0]:
        if idx != -1:
            chunk = chunks[idx]
            heading = " → ".join(chunk["heading_path"])
            context_parts.append(f"**{heading}**\n\n{chunk['text']}")
            citations.append(chunk["chunk_id"])
    
    context = "\n\n---\n\n".join(context_parts)
    
    # 3. Вызвать OpenAI API
    response = openai.ChatCompletion.create(
        model=model_name,
        messages=[
            {
                "role": "system",
                "content": """Вы — ИИ-навигатор, эксперт по настольной ролевой игре «Укрытое море». 
Помогайте ведущему и игрокам находить правила и описания на основе предоставленного контекста.
Если контекста недостаточно, честно скажите об этом."""
            },
            {
                "role": "user",
                "content": f"""Контекст из правил:
{context}

Вопрос: {question}

Ответьте, используя только информацию из контекста."""
            }
        ],
        temperature=0.7,
        max_tokens=500
    )
    
    answer = response.choices[0].message.content
    citations_str = ", ".join(citations)
    
    return f"{answer}\n\n**Источники:** {citations_str}"

# Тестирование
answer = rag_query_openai("Как правильно считать Благословенный прилив?")
print(answer)
```

---

## 🛠️ Вариант 2: Полнофункциональная RAG (production)

### Архитектура

```
User
  ↓
[API Backend] ← FastAPI, Flask
  ↓
[RAG Pipeline]
  ├─ Query Embedding (SentenceTransformers)
  ├─ Vector Search (FAISS/Weaviate/Pinecone)
  ├─ Context Retrieval (chunks.jsonl)
  └─ LLM Generation (OpenAI/Local/Hugging Face)
  ↓
[Response with Citations]
```

### Минимальный production-код

```python
# rag_service.py
import json
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss
import openai
from typing import List, Dict
from dataclasses import dataclass

@dataclass
class RAGResult:
    answer: str
    sources: List[str]
    confidence: float

class RAGService:
    def __init__(self, 
                 chunks_path: str = "content/chunks/chunks.jsonl",
                 index_path: str = "rag_index.faiss",
                 embedding_model: str = "intfloat/multilingual-e5-small"):
        
        # Загрузить эмбеддинг-модель
        self.encoder = SentenceTransformer(embedding_model)
        
        # Загрузить FAISS-индекс
        self.index = faiss.read_index(index_path)
        
        # Загрузить чанки
        self.chunks = []
        with open(chunks_path) as f:
            for line in f:
                self.chunks.append(json.loads(line))
        
        print(f"RAG Service инициализирован: {len(self.chunks)} чанков")
    
    def retrieve(self, query: str, top_k: int = 5) -> List[Dict]:
        """Найти релевантные чанки."""
        query_embedding = self.encoder.encode([query])[0].astype("float32")
        distances, indices = self.index.search(np.array([query_embedding]), top_k)
        
        results = []
        for i, idx in enumerate(indices[0]):
            if idx != -1:
                chunk = self.chunks[idx]
                results.append({
                    "rank": i + 1,
                    "distance": float(distances[0][i]),
                    "chunk_id": chunk["chunk_id"],
                    "heading": " → ".join(chunk["heading_path"]),
                    "text": chunk["text"],
                    "document_id": chunk["document_id"]
                })
        
        return results
    
    def generate(self, query: str, context: str) -> str:
        """Генерировать ответ с помощью LLM."""
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": "Вы — эксперт по игре «Укрытое море». Отвечайте точно на основе контекста."
                },
                {
                    "role": "user",
                    "content": f"Контекст:\n{context}\n\nВопрос: {query}"
                }
            ],
            temperature=0.3,
            max_tokens=500
        )
        return response.choices[0].message.content
    
    def query(self, question: str, top_k: int = 5) -> RAGResult:
        """Полный RAG-запрос."""
        # 1. Найти релевантные чанки
        retrieved = self.retrieve(question, top_k=top_k)
        
        if not retrieved:
            return RAGResult(
                answer="Не найдено релевантной информации в базе знаний.",
                sources=[],
                confidence=0.0
            )
        
        # 2. Собрать контекст
        context_parts = []
        for r in retrieved:
            context_parts.append(f"**{r['heading']}**\n\n{r['text']}")
        
        context = "\n\n---\n\n".join(context_parts)
        
        # 3. Генерировать ответ
        answer = self.generate(question, context)
        
        # 4. Собрать источники
        sources = [r["chunk_id"] for r in retrieved[:3]]
        confidence = 1.0 - (retrieved[0]["distance"] / 100.0)  # условная оценка
        
        return RAGResult(answer=answer, sources=sources, confidence=confidence)

# FastAPI интеграция
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Укрытое море RAG API")
rag_service = RAGService()

class QueryRequest(BaseModel):
    question: str
    top_k: int = 5

class QueryResponse(BaseModel):
    answer: str
    sources: List[str]
    confidence: float

@app.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    """RAG-запрос."""
    try:
        result = rag_service.query(request.question, top_k=request.top_k)
        return QueryResponse(
            answer=result.answer,
            sources=result.sources,
            confidence=result.confidence
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Запуск: uvicorn rag_service:app --reload
```

---

## 📦 Вариант 3: Используемые инструменты и платформы

### A. Векторные БД (Vector Stores)

| Инструмент | Использование | Стоимость | Сложность |
|-----------|--------------|---------|----------|
| **FAISS** | Локальный, быстрый | Бесплатно | ⭐⭐ |
| **Weaviate** | Self-hosted, Docker | Бесплатно | ⭐⭐⭐ |
| **Milvus** | Self-hosted, cloud | Бесплатно | ⭐⭐⭐⭐ |
| **Pinecone** | Managed cloud | 💰💰 | ⭐ |
| **Supabase** | PostgreSQL + pgvector | Дешевая | ⭐⭐ |
| **Qdrant** | Специализированная, быстрая | Бесплатно (cloud) | ⭐⭐ |

### B. Модели эмбеддингов (русский текст)

```python
# Рекомендуемые модели
from sentence_transformers import SentenceTransformer

# Лучшее качество, медленнее
model = SentenceTransformer('cointegrated/rubert-large')

# Хороший баланс качества и скорости
model = SentenceTransformer('intfloat/multilingual-e5-small')

# Очень быстро, хорошо для демо
model = SentenceTransformer('cointegrated/rubert-tiny2')

# Специализированные модели
model = SentenceTransformer('sentence-transformers/distiluse-base-multilingual-cased-v2')
```

### C. Языковые модели (LLM)

| Источник | Модель | Язык | Стоимость | Скорость |
|---------|--------|------|---------|---------|
| **OpenAI** | GPT-4, GPT-3.5 | Отличный | 💰💰 | Быстро |
| **Ollama** | Mistral, Neural Chat | Хороший | Бесплатно | Зависит от ПК |
| **HuggingFace** | YandexGPT, Saiga | Хороший | Разная | Медленно |
| **Together.ai** | Открытые модели | Хороший | 💰 | Быстро |
| **LocalAI** | Локально | Зависит | Бесплатно | Медленно |

---

## 🎯 Пошаговый план создания RAG

### Неделя 1: MVP (Minimum Viable Product)

```
День 1-2: Подготовка
├─ Установить Python 3.9+
├─ Установить зависимости (numpy, sentence-transformers, faiss)
└─ Загрузить корпус (chunks.jsonl)

День 3-4: Построение индекса
├─ Загрузить модель эмбеддингов
├─ Сгенерировать эмбеддинги для всех чанков
└─ Построить FAISS-индекс (~5 минут)

День 5: Поиск
├─ Реализовать функцию поиска по сходству
└─ Протестировать на 10-20 запросах

День 6-7: Интеграция с LLM
├─ Выбрать LLM (OpenAI или локальная)
├─ Написать функцию генерации ответа
└─ Тестировать end-to-end
```

### Неделя 2-3: Production

```
├─ Упаковать в FastAPI/Flask
├─ Добавить логирование и мониторинг
├─ Оптимизировать производительность
├─ Написать документацию API
└─ Развернуть на сервере (AWS, DigitalOcean, Heroku)
```

---

## 💻 Полный рабочий пример

Создайте файл `rag_main.py`:

```python
#!/usr/bin/env python3
"""
Полностью рабочий RAG для Укрытого моря.
Запуск: python3 rag_main.py
"""

import json
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss
import sys

class UkrytoeMoreRAG:
    def __init__(self):
        print("[1/3] Загружаю модель эмбеддингов...")
        self.model = SentenceTransformer('intfloat/multilingual-e5-small')
        
        print("[2/3] Загружаю чанки...")
        self.chunks = []
        with open("content/chunks/chunks.jsonl") as f:
            self.chunks = [json.loads(line) for line in f]
        
        print(f"[3/3] Загружаю индекс ({len(self.chunks)} чанков)...")
        
        # Если индекс ещё не существует, создать его
        try:
            self.index = faiss.read_index("rag_index.faiss")
        except:
            print("Индекс не найден, создаю новый...")
            self._build_index()
    
    def _build_index(self):
        """Построить FAISS-индекс."""
        texts = [chunk["text"] for chunk in self.chunks]
        embeddings = self.model.encode(texts, batch_size=32, show_progress_bar=True)
        embeddings = np.array(embeddings).astype("float32")
        
        dimension = embeddings.shape[1]
        self.index = faiss.IndexFlatL2(dimension)
        self.index.add(embeddings)
        faiss.write_index(self.index, "rag_index.faiss")
    
    def search(self, query: str, top_k: int = 5) -> list:
        """Поиск релевантных чанков."""
        query_embedding = self.model.encode([query])[0].astype("float32")
        distances, indices = self.index.search(np.array([query_embedding]), top_k)
        
        results = []
        for idx in indices[0]:
            if idx != -1:
                chunk = self.chunks[idx]
                results.append({
                    "chunk_id": chunk["chunk_id"],
                    "heading": " → ".join(chunk["heading_path"]),
                    "text": chunk["text"][:300],
                    "full_text": chunk["text"]
                })
        return results
    
    def format_context(self, results: list) -> str:
        """Форматировать результаты для LLM."""
        parts = []
        for r in results:
            parts.append(f"**{r['heading']}** [{r['chunk_id']}]\n\n{r['full_text']}")
        return "\n\n---\n\n".join(parts)
    
    def interactive_mode(self):
        """Интерактивный режим поиска."""
        print("\n" + "="*70)
        print("🌊 Укрытое море RAG - Интерактивный режим")
        print("="*70)
        print("Введите вопрос (или 'quit' для выхода):\n")
        
        while True:
            query = input("❓ Вопрос: ").strip()
            
            if query.lower() in ['quit', 'выход', 'exit']:
                print("До свидания! ⚓")
                break
            
            if not query:
                continue
            
            print("\n🔍 Поиск...")
            results = self.search(query, top_k=3)
            
            if not results:
                print("❌ Результаты не найдены.\n")
                continue
            
            print(f"\n📚 Найдено результатов: {len(results)}\n")
            for i, result in enumerate(results, 1):
                print(f"--- Результат {i} ---")
                print(f"📖 Раздел: {result['heading']}")
                print(f"🏷️  ID: {result['chunk_id']}")
                print(f"📝 Текст:\n{result['text']}...\n")
            
            # Собрать контекст для LLM
            context = self.format_context(results)
            print(f"✅ Контекст готов для LLM ({len(context)} символов)")
            print("=" * 70 + "\n")

if __name__ == "__main__":
    try:
        rag = UkrytoeMoreRAG()
        rag.interactive_mode()
    except KeyboardInterrupt:
        print("\n\nПрограмма прервана.")
    except Exception as e:
        print(f"❌ Ошибка: {e}", file=sys.stderr)
        sys.exit(1)
```

Запуск:
```bash
python3 rag_main.py
```

---

## 📋 Чек-лист создания RAG

- [ ] Установлены зависимости (numpy, sentence-transformers, faiss-cpu)
- [ ] Загружен корпус (content/chunks/chunks.jsonl)
- [ ] Выбрана модель эмбеддингов (интфлоат или Saiga)
- [ ] Построен FAISS-индекс
- [ ] Реализована функция поиска
- [ ] Выбрана LLM (OpenAI, Ollama или локальная)
- [ ] Написана функция генерации ответа
- [ ] Протестированы 10-20 запросов
- [ ] Упаковано в API (FastAPI/Flask)
- [ ] Документация написана
- [ ] Развернуто на сервере (опционально)

---

## 🎓 Полезные ресурсы

### Документация
- [Sentence-Transformers](https://www.sbert.net/)
- [FAISS](https://github.com/facebookresearch/faiss/wiki)
- [LangChain RAG](https://python.langchain.com/docs/use_cases/question_answering)
- [Ollama](https://ollama.ai)

### Примеры
- [RAG с LangChain](https://github.com/langchain-ai/langchain/tree/master/docs/docs/use_cases/question_answering)
- [FAISS + SentenceTransformers](https://huggingface.co/spaces/mteb/leaderboard)
- [OpenAI RAG](https://openai.com/research/retrieval-plugin)

### Статьи
- [Что такое RAG](https://arxiv.org/abs/2005.11401)
- [Semantic Search with BERT](https://www.sbert.net/examples/applications/semantic-search/README.html)
- [Vector Database Comparison](https://www.pinecone.io/learn/vector-database/)

---

## 🚀 Следующие шаги

1. **Выберите подход:**
   - Локальный (FAISS + Ollama) — для личных проектов
   - Cloud (OpenAI + Pinecone) — для production
   - Гибридный — лучшее из обоих

2. **Следуйте пошаговому плану** из раздела выше

3. **Тестируйте с реальными вопросами** из игры

4. **Оптимизируйте** размер чанков, модель эмбеддингов и параметры LLM

5. **Развернуйте** как веб-приложение или Telegram-бота

---

**Удачи в создании RAG!** ⚓

Если у вас есть вопросы, создайте issue или обратитесь в документацию проекта.
