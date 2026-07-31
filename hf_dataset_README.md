---
language:
- ru
license: cc0-1.0
task_categories:
- text-generation
- question-answering
- text-retrieval
tags:
- rpg
- ttrpg
- tabletop
- worldbuilding
- creative-writing
- russian
configs:
- config_name: chunks
  data_files: "chunks.parquet"
- config_name: documents
  data_files: "documents.parquet"
- config_name: images
  data_files: "images.parquet"
- config_name: embeddings
  data_files: "embeddings.parquet"
dataset_info:
- config_name: chunks
  features:
  - name: chunk_id
    dtype: string
  - name: document_id
    dtype: string
  - name: chunk_number
    dtype: int64
  - name: heading_path
    sequence: string
  - name: document_type
    dtype: string
  - name: language
    dtype: string
  - name: license
    dtype: string
  - name: text
    dtype: string
- config_name: documents
  features:
  - name: document_id
    dtype: string
  - name: title
    dtype: string
  - name: document_type
    dtype: string
  - name: language
    dtype: string
  - name: license
    dtype: string
  - name: text
    dtype: string
- config_name: images
  features:
  - name: image_id
    dtype: string
  - name: alt_text
    dtype: string
  - name: source_document
    dtype: string
  - name: file_path
    dtype: string
  - name: license
    dtype: string
- config_name: embeddings
  features:
  - name: chunk_id
    dtype: string
  - name: embedding
    sequence: float32
---

# 🌊 Укрытое море: Корпус для ML и RAG (v1.1.0)

Полностью обработанный, проверенный и готовый к использованию текстовый корпус релизных черновиков настольной ролевой игры [**«Укрытое море: Благословенный прилив»**](https://ukrytoemore.ru/) от [Ex Nihilum Publishing](https://exnihilum.info).

## 📋 Описание

Этот датасет содержит структурированные тексты игровой системы, оптимизированные для обучения языковых моделей, создания RAG-систем (Retrieval-Augmented Generation) и семантического поиска.

### Основные характеристики:
- **Документов**: 39 (все проверены вручную)
- **Фрагментов (chunks)**: 1378 семантически законченных блоков
- **Иллюстраций**: метаданные для 132 изображений
- **Готовые векторы (embeddings)**: 1378 векторов (384 измерения, модель `intfloat/multilingual-e5-small`)
- **Бинарный FAISS-индекс**: `rag_index.faiss` (для моментального поиска за 1мс)
- **Язык**: Русский
- **Лицензия**: Public Domain (CC0) для текстовой части

## 🏗️ Структура датасета

Датасет поставляется в следующих конфигурациях и артефактах:

### 1. `chunks` (основная)
Семантические фрагменты размером 400-1000 токенов, идеально подходящие для векторных индексов и RAG.
- `chunk_id`: уникальный идентификатор фрагмента
- `heading_path`: иерархия заголовков (путь к фрагменту в книге)
- `text`: содержание фрагмента

### 2. `documents`
Полные тексты всех 39 документов репозитория.
- `document_id`: идентификатор файла
- `title`: название главы или документа
- `text`: полный текст в формате Markdown (очищенный)

### 3. `embeddings`
Предобработанные векторные эмбеддинги (384-dim, `multilingual-e5-small`) для загрузки в ChromaDB, Qdrant, Pinecone, PGVector или Weaviate.

### 4. `rag_index.faiss` (Бинарный индекс)
Готовый FAISS-индекс для моментального поиска без генерации эмбеддингов корпуса.

### 5. `global_knowledge_map.json` (Карта знаний)
Структурированный словарь всех сущностей проекта (Personas, Media, Lore, Mechanics, Concepts). Идеально для NER (Named Entity Recognition) и обогащения промптов.

## 🚀 Быстрый старт

### Вариант 1: Загрузка текста чанков

```python
from datasets import load_dataset

# Загрузить чанки для RAG
dataset = load_dataset("exnihilum/ttrpg-ouw25-ru", "chunks")
print(dataset["train"][0]["text"])
```

### Вариант 2: Использование готового FAISS-индекса (Моментальный RAG)

```python
import faiss
import numpy as np
from huggingface_hub import hf_hub_download
from sentence_transformers import SentenceTransformer

# 1. Скачать готовый индекс из Hugging Face
index_path = hf_hub_download(repo_id="exnihilum/ttrpg-ouw25-ru", repo_type="dataset", filename="rag_index.faiss")
index = faiss.read_index(index_path)

# 2. Модель для эмбеддинга вопросов
model = SentenceTransformer('intfloat/multilingual-e5-small')

# 3. Поиск
query = "Как работает Collision Engine?"
query_vec = model.encode([query])[0].astype("float32")
distances, indices = index.search(np.array([query_vec]), k=3)
```

## ⚖️ Лицензирование

- **Тексты**: [Public Domain (CC0)](https://creativecommons.org/publicdomain/zero/1.0/deed.ru). Вы можете использовать, изменять и распространять тексты без ограничений.
- **Иллюстрации**: Авторское право принадлежит Ex Nihilum Publishing. Разрешено некоммерческое использование в рамках проектов по игре.

## 🔗 Ссылки и Цитирование

- **Сайт игры**: [ukrytoemore.ru](https://ukrytoemore.ru/)
- **Издательство**: [exnihilum.info](https://exnihilum.info)
- **GitHub проекта**: [github.com/exnihilum/ouw25_lm](https://github.com/exnihilum/ouw25_lm)
- **Zenodo DOI**: [![DOI](https://zenodo.org/badge/doi/10.5281/zenodo.21694650.svg)](https://doi.org/10.5281/zenodo.21694650)

### 📌 Цитирование (Citation)
```bibtex
@dataset{ukrytoe_more_corpus_2026,
  author = {Ex Nihilum Publishing},
  title = {Укрытое море: Корпус настольной ролевой игры для ML и RAG},
  year = {2026},
  publisher = {Zenodo / Hugging Face},
  version = {1.1.0},
  doi = {10.5281/zenodo.21694650},
  url = {https://doi.org/10.5281/zenodo.21694650}
}
```

---
*Датасет и RAG-инструменты подготовлены для проекта «Укрытое море».*
