# 🌊 Укрытое море — корпус для ML

Полностью обработанный, проверенный и готовый к использованию текстовый корпус
настольной ролевой игры **«Укрытое море»** (Укрытые воды).

- 📚 **39 документов** в проверенном Markdown
- 🔍 **1378 семантических фрагментов** для RAG и эмбеддингов
- 🖼️ **132 иллюстрации** с метаданными
- 📝 **Public Domain** лицензия — свободное использование в ML-проектах
- ✅ **Полностью валидирован** — структуры, ссылки, изображения без потерь

---

## Быстрый старт

### Использование готовых индексов

Индексы уже вычислены и готовы к использованию:

```bash
# Посмотреть статистику
wc -l content/indexes/documents.jsonl content/chunks/chunks.jsonl

# Загрузить в Python
python3 -c "
import json
with open('content/chunks/chunks.jsonl') as f:
    chunk = json.loads(f.readline())
    print(json.dumps(chunk, indent=2, ensure_ascii=False)[:500])
"
```

### Собрать индексы с нуля

Если вы редактировали Markdown:

```bash
python3 scripts/validate_corpus.py  # Проверить структуру
python3 scripts/build_indexes.py     # Пересчитать JSONL
python3 scripts/audit_conversion.py  # QA-аудит
```

### Первый RAG-запрос

```python
import json

# Загрузить чанки
chunks = [json.loads(line) for line in open("content/chunks/chunks.jsonl")]

# Поиск
query = "Благословенный прилив"
results = [c for c in chunks if query.lower() in c["text"].lower()][:3]

for r in results:
    print(f"[{r['chunk_id']}] {' > '.join(r['heading_path'])}")
    print(r['text'][:300] + "...\n")
```

---

## Структура проекта

```
📦 ouw25_lm/
├─ 📁 docx_sources/           # Неизменяемые исходники (39 DOCX)
├─ 📁 content/
│  ├─ 📁 markdown/             # ✅ Нормализованные документы (39 файлов)
│  ├─ 📁 imported/             # Прямой экспорт Pandoc (для справки)
│  ├─ 📁 assets/               # Извлечённые изображения (132)
│  ├─ 📁 indexes/
│  │  ├─ documents.jsonl       # 39 документов с полным текстом
│  │  └─ images.jsonl          # 132 изображения с метаданными
│  ├─ 📁 chunks/
│  │  └─ chunks.jsonl          # 1378 семантических фрагментов
│  ├─ 📁 manifests/            # Реестры и открытые вопросы
│  └─ 📄 README.md             # О слоях данных
├─ 📁 scripts/
│  ├─ build_corpus.py          # DOCX → Markdown конвертация
│  ├─ build_indexes.py         # Генерация JSONL
│  ├─ validate_corpus.py       # Проверка целостности
│  ├─ audit_conversion.py      # QA-аудит
│  └─ index_images.py          # Индексация изображений
├─ 📁 docs/
│  ├─ AI_CONSTRAINTS.md        # Ограничения для ИИ
│  ├─ ML_USAGE.md              # Примеры использования в ML
│  └─ CONTRIBUTING.md          # Правила редактирования
├─ 📁 LICENSES/
│  └─ TEXTS-PUBLIC-DOMAIN.md   # Декларация лицензии
├─ 📄 PLAN.md                  # Исходный план проекта
├─ 📄 CHANGELOG.md             # История выпусков
└─ 📄 README.md                # Этот файл
```

---

## Использование корпуса

### 📖 Для RAG-ассистентов

```python
from typing import Any

class OkhotnoeMoreRAG:
    def __init__(self):
        self.chunks = [
            json.loads(line) 
            for line in open("content/chunks/chunks.jsonl")
        ]
    
    def search(self, query: str) -> list[dict[str, Any]]:
        """Найти релевантные чанки."""
        results = []
        for chunk in self.chunks:
            if query.lower() in chunk["text"].lower():
                results.append(chunk)
        return results[:5]
    
    def format_for_llm(self, chunks: list) -> str:
        """Форматировать контекст для LLM."""
        parts = []
        for chunk in chunks:
            path = " → ".join(chunk["heading_path"])
            parts.append(f"**{path}**\n\n{chunk['text']}")
        return "\n\n---\n\n".join(parts)

# Использование
rag = OkhotnoeMoreRAG()
results = rag.search("Как рассчитать риск?")
context = rag.format_for_llm(results)
# → отправить в LLM вместе с системным промптом из docs/AI_CONSTRAINTS.md
```

### 🤖 Для дообучения моделей

```bash
# Подготовить датасет (текст)
python3 scripts/build_indexes.py

# Экспортировать в HuggingFace format
python3 -c "
import json
docs = [json.loads(line) for line in open('content/indexes/documents.jsonl')]
for doc in docs:
    print(json.dumps({'text': doc['text'], 'metadata': {
        'document_id': doc['document_id'],
        'type': doc['document_type']
    }}, ensure_ascii=False))
" > finetune_dataset.jsonl
```

### 🔍 Для полнотекстового поиска

```sql
-- Примерный запрос для Elasticsearch/OpenSearch
POST /ukrytoe-more-chunks/_search
{
  "query": {
    "multi_match": {
      "query": "Благословенный прилив",
      "fields": ["text", "heading_path"]
    }
  },
  "size": 10
}
```

### 🖼️ Для визуального поиска (multimodal)

```python
# Загрузить метаданные изображений
images = [
    json.loads(line) 
    for line in open("content/indexes/images.jsonl")
]

# Пример: найти все изображения в конкретном документе
doc_images = [img for img in images if img["document_id"] == "ouw25-3-1-narody-morya"]
for img in doc_images:
    print(f"![{img['alt_text']}]({img['path']})")
```

---

## Документация

| Файл | Назначение |
|------|-----------|
| **`CHANGELOG.md`** | История всех версий и выпусков |
| **`docs/AI_CONSTRAINTS.md`** | Ограничения и ожидания для ИИ-моделей |
| **`docs/ML_USAGE.md`** | Подробные примеры использования в ML |
| **`docs/CONTRIBUTING.md`** | Правила редактирования и внесения изменений |
| **`LICENSES/TEXTS-PUBLIC-DOMAIN.md`** | Полная декларация лицензии |
| **`content/README.md`** | О структуре слоёв данных |
| **`PLAN.md`** | Исходный план проекта (история) |

---

## Качество и валидация

### ✅ Что проверено

- Все 39 документов конвертированы без ошибок
- Структура заголовков корректна (H1 → H2–H4)
- Все внутренние и внешние ссылки рабочие
- 132 изображения извлечены и переиндексированы
- Таблицы и сноски сохранены или явно отмечены
- Все документы имеют валидные YAML-метаданные
- JSONL-индексы детерминированны (одинаковые при пересборке)

### 📊 Статистика

- **Исходники**: 39 DOCX (~61 МБ)
- **Markdown текст**: ~18 000 строк (~1.2 МБ)
- **Документный индекс**: 39 записей (~2.5 МБ JSON)
- **Чанк-индекс**: 1378 фрагментов (~3.2 МБ JSON)
- **Изображения**: 132 файла (~450 МБ PNG/JPEG)
- **Общий размер**: ~470 МБ с ассетами

---

## Лицензирование

### ✅ Что можно делать

- Использовать в коммерческих и некоммерческих проектах
- Дообучивать модели на текстовом корпусе
- Создавать RAG-ассистентов и чатботов
- Генерировать новые материалы в сеттинге
- Распространять производные работы

### ⚠️ Ограничения

- Текст: **Public Domain (CC0)** — полная свобода
- Изображения: **авторское право** — требуется отдельное согласие для переиспользования
- При публикации — указать источник:
  ```
  Корпус основан на настольной ролевой игре «Укрытое море» (2025),
  выпущено под Public Domain.
  ```

Полный текст — см. `LICENSES/TEXTS-PUBLIC-DOMAIN.md`

---

## Разработка и внесение вклада

### Редактирование корпуса

Если вы хотите исправить опечатку, добавить описание к изображению или уточнить содержание:

1. Отредактируйте файл в `content/markdown/`
2. Запустите валидацию: `python3 scripts/validate_corpus.py`
3. Пересчитайте индексы: `python3 scripts/build_indexes.py`
4. Коммитьте: `git commit -m "docs: описание изменений"`

Подробнее — в `docs/CONTRIBUTING.md`

### Выявление ошибок

Если вы нашли опечатку, неработающую ссылку или другую проблему:

1. Откройте **Issue** с описанием
2. Укажите документ (`document_id`) и строку
3. Предложите исправление

### Расширение корпуса

Для добавления новых материалов нужно согласие правообладателя.

---

## Примеры проектов

Этот корпус готов для использования в:

- 🤖 **RAG-ассистентов**: поиск правил, помощь ведущему
- 📚 **Дообучения LLM**: специализированные модели для игровых миров
- 🔍 **Семантического поиска**: эмбеддинги и векторные индексы
- 📊 **Анализа данных**: статистика используемых терминов, правила, жанр
- 🎮 **Генераторов контента**: создание приключений и NPC
- 🗂️ **Каталогизации материалов**: интеграция с wiki/базами знаний

---

## Поддержка и вопросы

- 📖 **Документация**: см. папку `docs/`
- 🐛 **Ошибки**: откройте Issue
- 💬 **Обсуждение**: см. Discussions (если включены)
- 📧 **Контакт**: через репозиторий

---

## Версия

```
Укрытое море — корпус для ML v1.0.0 (2026-07-27)
Все 39 документов проверены и готовы к использованию
```

[📖 Полная история изменений](CHANGELOG.md) | [📄 Исходный план](PLAN.md)

---

**Спасибо за использование корпуса!** ⚓

Помните: Укрытое море — это мир абсурда, иронии и меланхолии.
Ваши модели тоже должны это понимать. 🌊
