# Руководство по использованию корпуса в ML-проектах

Этот документ описывает как использовать корпус «Укрытое море» в задачах машинного обучения,
генеративного поиска (RAG), дообучения (fine-tuning) и создания игровых ИИ-помощников.

## Быстрый старт

### 1. Получение индексов

После клонирования репозитория индексы уже готовы:

```bash
# Документный слой (полный текст каждого документа)
cat content/indexes/documents.jsonl | head -1 | python3 -m json.tool

# Чанк-слой (семантические фрагменты для RAG)
cat content/chunks/chunks.jsonl | head -1 | python3 -m json.tool

# Изображения (метаданные и пути)
cat content/indexes/images.jsonl | head -1 | python3 -m json.tool
```

### 2. Загрузка в Python

```python
import json
from pathlib import Path

# Загрузить документы
documents = []
with open("content/indexes/documents.jsonl") as f:
    for line in f:
        documents.append(json.loads(line))

# Загрузить чанки для RAG
chunks = []
with open("content/chunks/chunks.jsonl") as f:
    for line in f:
        chunks.append(json.loads(line))

print(f"Всего документов: {len(documents)}")
print(f"Всего чанков: {len(chunks)}")
```

### 3. Базовый полнотекстовый поиск

```python
import re

def search_chunks(query: str, chunks: list, top_k: int = 5) -> list:
    """Простой полнотекстовый поиск по чанкам."""
    query_lower = query.lower()
    results = []
    for chunk in chunks:
        if query_lower in chunk["text"].lower():
            results.append(chunk)
    return results[:top_k]

# Пример
results = search_chunks("Благословенный прилив", chunks)
for result in results:
    print(f"[{result['chunk_id']}] {' > '.join(result['heading_path'])}")
    print(f"{result['text'][:200]}...\n")
```

## Структура данных

### documents.jsonl

Каждая строка — JSON-объект с полной информацией о документе:

```json
{
  "document_id": "ouw25-0-vvodnaya-chast",
  "title": "Вводная часть",
  "source_path": "docx_sources/0. Вводная часть.docx",
  "markdown_path": "content/markdown/0-vvodnaya-chast.md",
  "document_type": "chapter",
  "section": "0",
  "language": "ru",
  "license": "Public Domain",
  "license_scope": "text",
  "asset_license": "UNSPECIFIED",
  "status": "reviewed",
  "text": "# Вводная часть\n\n...",
  "text_sha256": "abc123..."
}
```

**Ключевые поля:**

- `document_id` — стабильный идентификатор (никогда не меняется)
- `document_type` — тип: `chapter`, `sidebar`, `template`, `table`, `index`
- `status` — статус документа: всегда `reviewed` в этом выпуске
- `license` / `license_scope` — всегда `Public Domain` для текстового слоя
- `text` — полный очищенный текст документа (без комментариев и служебных полей)
- `text_sha256` — хеш текста для проверки целостности

### chunks.jsonl

Каждая строка — семантический фрагмент для RAG/эмбеддингов:

```json
{
  "chunk_id": "ouw25-0-vvodnaya-chast--0001",
  "document_id": "ouw25-0-vvodnaya-chast",
  "chunk_number": 1,
  "heading_path": ["Вводная часть"],
  "document_type": "chapter",
  "section": "0",
  "language": "ru",
  "license": "Public Domain",
  "license_scope": "text",
  "status": "reviewed",
  "text": "# Вводная часть\n\nМир Укрытого моря...",
  "text_sha256": "def456..."
}
```

**Ключевые поля:**

- `chunk_id` — уникальный ID фрагмента (документ--XXXX)
- `heading_path` — путь заголовков для контекста (`["Глава", "Раздел", "Подраздел"]`)
- `text` — текст фрагмента (~400–800 токенов)
- Все поля `document_id` и выше — из исходного документа

### images.jsonl

Метаданные извлечённых изображений:

```json
{
  "image_id": "ouw25-3-1-narody-morya--001",
  "document_id": "ouw25-3-1-narody-morya",
  "filename": "ouw25-3-1-narody-morya--001.png",
  "path": "content/assets/ouw25-3-1-narody-morya/ouw25-3-1-narody-morya--001.png",
  "alt_text": "Народы Укрытого моря: рисунок из книги",
  "caption": "...",
  "width": 800,
  "height": 600
}
```

## Типичные сценарии использования

### Сценарий 1: RAG-чатбот для помощи ведущему

```python
from typing import Any

class UkrytoeMoreRAG:
    def __init__(self, chunks_path: str):
        self.chunks = []
        with open(chunks_path) as f:
            for line in f:
                self.chunks.append(json.loads(line))
    
    def search(self, query: str, top_k: int = 3) -> list[dict[str, Any]]:
        """Полнотекстовый поиск (можно заменить на семантический через эмбеддинги)."""
        query_lower = query.lower()
        scored = []
        for chunk in self.chunks:
            # Простая оценка: количество совпадений слов
            score = sum(1 for word in query.split() 
                       if word.lower() in chunk["text"].lower())
            if score > 0:
                scored.append((score, chunk))
        scored.sort(reverse=True)
        return [chunk for _, chunk in scored[:top_k]]
    
    def format_context(self, chunks: list[dict]) -> str:
        """Форматировать результаты в промпт для LLM."""
        context_parts = []
        for chunk in chunks:
            heading = " > ".join(chunk["heading_path"])
            context_parts.append(f"**{heading}**\n\n{chunk['text']}")
        return "\n\n---\n\n".join(context_parts)

# Использование
rag = UkrytoeMoreRAG("content/chunks/chunks.jsonl")

# Пример запроса
user_query = "Как рассчитать риск кораблекрушения?"
results = rag.search(user_query)
context = rag.format_context(results)

# Отправить в LLM с системным промптом из docs/AI_CONSTRAINTS.md
print(f"Контекст для LLM ({len(results)} результатов):")
print(context)
```

### Сценарий 2: Подготовка датасета для дообучения

```python
def prepare_finetune_dataset(documents_path: str, output_path: str):
    """Подготовить данные для dpo/sft дообучения."""
    dataset = []
    
    with open(documents_path) as f:
        for line in f:
            doc = json.loads(line)
            
            # Пропустить служебные документы
            if doc["document_type"] == "index":
                continue
            
            # Структурировать как пары (вопрос, ответ)
            # Это очень упрощённый пример; в реальности нужна разметка
            dataset.append({
                "document_id": doc["document_id"],
                "title": doc["title"],
                "content": doc["text"],
                "document_type": doc["document_type"],
                "license": doc["license"]
            })
    
    # Сохранить в формате HuggingFace datasets
    with open(output_path, "w") as f:
        for item in dataset:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
    
    print(f"Подготовлено {len(dataset)} документов для дообучения")

prepare_finetune_dataset(
    "content/indexes/documents.jsonl",
    "finetune_dataset.jsonl"
)
```

### Сценарий 3: Векторный индекс для семантического поиска

```python
# Пример с использованием faiss (потребуется установить)

def build_semantic_index(
    chunks_path: str,
    embedder_fn: callable  # функция, которая возвращает эмбеддинги
) -> tuple[list, dict]:
    """
    Построить FAISS-индекс для семантического поиска.
    
    embedder_fn должна быть функцией вроде:
        lambda text: model.encode(text, normalize_embeddings=True)
    """
    import numpy as np
    
    chunks = []
    embeddings = []
    
    with open(chunks_path) as f:
        for line in f:
            chunk = json.loads(line)
            chunks.append(chunk)
            
            # Получить эмбеддинг (например, используя SentenceTransformers)
            emb = embedder_fn(chunk["text"])
            embeddings.append(emb)
    
    embeddings = np.array(embeddings).astype("float32")
    
    # Примечание: нужно установить faiss-cpu или faiss-gpu
    # import faiss
    # index = faiss.IndexFlatL2(embeddings.shape[1])
    # index.add(embeddings)
    
    return chunks, {
        "embeddings": embeddings,
        "chunk_count": len(chunks)
    }
```

## Обслуживание и валидация

### Проверка целостности

Корпус включает встроенную валидацию:

```bash
# Проверить структуру Markdown и синтаксис
python3 scripts/validate_corpus.py

# Выполнить детальный QA-аудит (сверка с DOCX)
python3 scripts/audit_conversion.py

# Пересчитать индексы (должны быть идентичными)
python3 scripts/build_indexes.py
```

### Проверка лицензирования

Убедитесь, что используемые материалы лицензированы корректно:

```python
def verify_license_compliance(documents_path: str):
    """Проверить, что все документы имеют правильную лицензию."""
    with open(documents_path) as f:
        for line in f:
            doc = json.loads(line)
            assert doc["license"] == "Public Domain", \
                f"Неожиданная лицензия: {doc['document_id']}"
            assert doc["license_scope"] == "text", \
                f"Неожиданная область лицензии: {doc['document_id']}"
    print("✅ Все документы имеют Public Domain лицензию")

verify_license_compliance("content/indexes/documents.jsonl")
```

## Ограничения и рекомендации

1. **Тон и стиль**: Модели, дообученные на корпусе, должны сохранять иронично-меланхоличный
   декопанк-абсурдистский тон оригинала.

2. **Строгая точность в правилах**: При ответах на вопросы о правилах (Collision Engine, драматический
   размен и т. д.) модель **не должна** додумывать детали из других RPG-систем.

3. **Физика вымышленного мира**: Игровой мир работает по собственным законам. RAG не должна
   пытаться «исправить» реалистичность морских перевозок или экономику через реальные данные.

4. **Изображения**: Хотя изображения включены в корпус, их использование для обучения
   генеративных моделей (Stable Diffusion, DALL-E) требует отдельного согласия художников.

5. **Версионирование**: Используйте хеши (`text_sha256`) для проверки того, что вы работаете
   с ожидаемой версией текстов.

## Размещение и распространение

Корпус находится под лицензией Public Domain (CC0). Вы можете:

- ✅ Использовать в коммерческих и некоммерческих проектах
- ✅ Модифицировать и дистрибьютить производные работы
- ✅ Использовать в обучении моделей и создании эмбеддингов
- ✅ Включать в публичные датасеты ML

Требуется указание источника (атрибуция):

```
Корпус основан на настольной ролевой игре «Укрытое море»,
издание 2025, выпущено под Public Domain.
```

## Дополнительные ресурсы

- **AI_CONSTRAINTS.md** — детальные ограничения для ИИ-ассистентов
- **LICENSES/TEXTS-PUBLIC-DOMAIN.md** — полная декларация лицензии
- **content/manifests/issues.json** — журнал вопросов QA (пусто в v1.0.0)
- **scripts/** — исходники скриптов конвертации и валидации
