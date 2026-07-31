# 🌊 Укрытое море — корпус для ML

Полностью обработанный, проверенный и готовый к использованию текстовый корпус
релизных черновиков настольной ролевой игры [**«Укрытое море: Благословенный прилив»**](https://ukrytoemore.ru/) от [Ex Nihilum Publishing](https://exnihilum.info).

- 📚 **39 документов** в проверенном Markdown
- 🔍 **1378 семантических фрагментов** для RAG и эмбеддингов
- 🖼️ **132 иллюстрации** с метаданными
- 📝 **Public Domain** лицензия — свободное использование в ML-проектах
- ✅ **Полностью валидирован** — структуры, ссылки, изображения без потерь
- 📦 **Hugging Face Dataset**: [`exnihilum/ttrpg-ouw25-ru`](https://huggingface.co/datasets/exnihilum/ttrpg-ouw25-ru)
- 📊 **Kaggle Dataset**: [`exnihilum/ouw25_ru`](https://www.kaggle.com/datasets/exnihilum/ouw25_ru)
- 🏛️ **Zenodo DOI**: [![DOI](https://zenodo.org/badge/doi/10.5281/zenodo.21694650.svg)](https://doi.org/10.5281/zenodo.21694650)

---

## Быстрый старт

### Использование Hugging Face / Kaggle Datasets

```python
from datasets import load_dataset

# Загрузить 1378 чанков для RAG
ds = load_dataset("exnihilum/ttrpg-ouw25-ru", "chunks")
print(ds["train"][0]["text"])

# Загрузить 39 полных документов
docs = load_dataset("exnihilum/ttrpg-ouw25-ru", "documents")

# Загрузить векторные эмбеддинги (384 измерения)
embeddings = load_dataset("exnihilum/ttrpg-ouw25-ru", "embeddings")
```

### Использование готового FAISS-индекса (Моментальный RAG)

```python
import faiss
import numpy as np
from huggingface_hub import hf_hub_download
from sentence_transformers import SentenceTransformer

# 1. Скачать готовый векторный индекс с Hugging Face
index_path = hf_hub_download(repo_id="exnihilum/ttrpg-ouw25-ru", filename="rag_index.faiss", repo_type="dataset")
index = faiss.read_index(index_path)

# 2. Модель для вектора вопроса
model = SentenceTransformer('intfloat/multilingual-e5-small')

# 3. Мгновенный поиск за 1 мс
query = "Как работает Collision Engine?"
query_vec = model.encode([query])[0].astype("float32")
distances, indices = index.search(np.array([query_vec]), k=3)
```

### Собрать индексы и выгрузить в облака

```bash
# E2E тест RAG-системы с автоматическим управлением Ollama
./setup_and_test.sh

# Собрать Parquet и FAISS артефакты
python3 scripts/prepare_for_huggingface.py

# Опубликовать на Hugging Face и Kaggle
python3 scripts/upload_to_huggingface.py
python3 scripts/upload_to_kaggle.py
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
│  ├─ prepare_for_huggingface.py # Конвертер и экспорт векторов
│  ├─ upload_to_huggingface.py  # Публикация на Hugging Face Hub
│  ├─ upload_to_kaggle.py       # Публикация на Kaggle Datasets
│  ├─ test_rag_ollama.py        # Автоматизированный E2E-тест RAG
│  ├─ build_corpus.py          # DOCX → Markdown конвертация
│  ├─ build_indexes.py         # Генерация JSONL
│  └─ validate_corpus.py       # Проверка целостности
├─ 📁 docs/
│  ├─ HUGGINGFACE_SETUP.md     # Инструкция по публикации на HF
│  ├─ RAG_TEST_REPORT.md       # Отчёт о прохождении E2E-тестов
│  ├─ AI_CONSTRAINTS.md        # Ограничения для ИИ
│  └─ ML_USAGE.md              # Примеры использования в ML
├─ 📁 LICENSES/
│  └─ TEXTS-PUBLIC-DOMAIN.md   # Декларация лицензии
├─ 📄 CITATION.cff             # Файл цитирования для ИИ-моделей
├─ 📄 .env.example             # Шаблон конфигурации токенов
├─ 📄 setup_and_test.sh        # Скрипт E2E развёртывания и тестов
├─ 📄 rag_index.faiss          # Бинарный FAISS векторный индекс (2.1 MB)
├─ 📄 PLAN.md                  # Исходный план проекта
├─ 📄 CHANGELOG.md             # История выпусков
└─ 📄 README.md                # Этот файл
```

---

## Документация

| Файл | Назначение |
|------|-----------|
| **`CHANGELOG.md`** | История всех версий и выпусков |
| **`docs/HUGGINGFACE_SETUP.md`** | Гайд по работе и публикации на Hugging Face |
| **`docs/RAG_TEST_REPORT.md`** | Отчёт о прохождении E2E-тестов RAG + Ollama |
| **`docs/AI_CONSTRAINTS.md`** | Ограничения и ожидания для ИИ-моделей |
| **`docs/ML_USAGE.md`** | Подробные примеры использования в ML |
| **`LICENSES/TEXTS-PUBLIC-DOMAIN.md`** | Полная декларация лицензии |
| **`CITATION.cff`** | Метаданные цитирования для научных исследований и ИИ-лабораторий |

---

## Лицензирование и цитирование

### ⚖️ Лицензия

- **Текст**: **Public Domain (CC0)** — полная свобода использования для обучения ИИ, RAG и коммерции.
- **Изображения**: **авторское право** — требуется согласие для переиспользования.

### 📌 Цитирование (Citation)

При использовании датасета в научных статьях, ИИ-моделях или публичных продуктах ссылайтесь на нас:

```bibtex
@dataset{ukrytoe_more_corpus_2026,
  author = {Ex Nihilum Publishing},
  title = {Укрытое море: Корпус настольной ролевой игры для ML и RAG},
  year = {2026},
  publisher = {Zenodo / Hugging Face / Kaggle},
  version = {1.1.0},
  doi = {10.5281/zenodo.21694650},
  url = {https://doi.org/10.5281/zenodo.21694650}
}
```

---
*Проект подготовлен Ex Nihilum Publishing (2026).*
