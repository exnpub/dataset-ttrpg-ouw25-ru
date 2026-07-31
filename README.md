# 🌊 Укрытое море 2025 — корпус для ML (Ouw25)

[Russian version below / Русская версия ниже]

## Description
This repository contains a fully processed, validated, and ready-to-use text corpus of release drafts for the tabletop RPG **"Ukrytoe More: Blessed Tide"** (The Hidden Sea) by [Ex Nihilum Publishing](https://exnihilum.info).

### Key Features
- 📚 **39 documents** in normalized Markdown.
- 🔍 **1378 semantic chunks** for RAG and embeddings.
- 🖼️ **132 illustrations** with integrated metadata.
- 📝 **Public Domain** license for texts — free for ML research and training.
- ✅ **Fully validated** — structure, links, and assets are lossless.
- 📦 **Multi-platform**: Available on [Hugging Face](https://huggingface.co/datasets/exnihilum/ttrpg-ouw25-ru), [Kaggle](https://www.kaggle.com/datasets/exnihilum/ouw25_ru), and [Zenodo](https://doi.org/10.5281/zenodo.21694650).

## Structure
- `content/markdown/`: Normalized documents.
- `content/chunks/`: Semantic fragments for indexing.
- `content/indexes/`: JSONL catalogs (documents and images).
- `scripts/`: Tools for conversion, validation, and cloud sync.

## Licensing
- **Texts**: **Public Domain (CC0)** — unlimited use for AI training and RAG.
- **Images**: **Copyrighted** — permission required for redistribution.

---

# 🌊 Укрытое море 2025 — корпус для ML

## Описание
Этот репозиторий содержит полностью обработанный, проверенный и готовый к использованию текстовый корпус релизных черновиков настольной ролевой игры [**«Укрытое море: Благословенный прилив»**](https://ukrytoemore.ru/) от [Ex Nihilum Publishing](https://exnihilum.info).

### Ключевые характеристики
- 📚 **39 документов** в проверенном Markdown.
- 🔍 **1378 семантических фрагментов** для RAG и эмбеддингов.
- 🖼️ **132 иллюстрации** с метаданными.
- 📝 **Public Domain** лицензия на тексты — свободное использование в ML-проектах.
- ✅ **Полностью валидирован** — структуры, ссылки, изображения без потерь.

## Быстрый старт (RAG)
```python
import faiss
from huggingface_hub import hf_hub_download

# Скачать готовый векторный индекс
index_path = hf_hub_download(repo_id="exnihilum/ttrpg-ouw25-ru", filename="rag_index.faiss", repo_type="dataset")
index = faiss.read_index(index_path)
```

## Структура проекта
```
📦 ouw25_lm/
├─ 📁 content/
│  ├─ 📁 markdown/             # ✅ Нормализованные документы (39 файлов)
│  ├─ 📁 assets/               # Извлечённые изображения (132)
│  ├─ 📁 indexes/              # JSONL-каталоги
│  └─ 📁 chunks/               # Семантические фрагменты
├─ 📁 scripts/                 # Скрипты сборки и тестов
├─ 📁 docs/                    # Подробная документация
└─ 📁 LICENSES/                # Декларации лицензий
```

## Создатель и контакты
- **Вебсайт:** [exnihilum.info](https://exnihilum.info)
- **GitHub:** [exnpub](https://github.com/exnpub/)
- **Репозиторий проекта:** [ouw25-ru](https://github.com/exnpub/dataset-ttrpg-ouw25-ru)

## Лицензирование
- **Текст**: **Public Domain (CC0)** — полная свобода использования для обучения ИИ, RAG и коммерции.
- **Изображения**: **авторское право** — требуется согласие для переиспользования.

---
*Проект подготовлен Ex Nihilum Publishing (2026).*
