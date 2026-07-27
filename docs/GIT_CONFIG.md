# .gitignore и .gitattributes для проекта

## Обзор

Проект содержит два файла конфигурации Git:

1. **`.gitignore`** — какие файлы НЕ коммитить
2. **`.gitattributes`** — как обрабатывать разные типы файлов

---

## `.gitignore` — что исключается

### 📊 Основные разделы

#### 1. Системные файлы
- macOS: `.DS_Store`, `*.swp`, `*.swo`
- Windows: `Thumbs.db`, `$RECYCLE.BIN`
- Linux: `.directory`, `.Trash-*`

#### 2. Python артефакты
- `__pycache__/` — скомпилированный Python код
- `*.pyc`, `*.pyo` — байт-код
- `venv/`, `.env/` — виртуальные окружения
- `*.egg-info/` — установочная информация

#### 3. RAG и ML файлы
```
rag_index.faiss        # FAISS индекс (может быть большим)
embeddings.npy         # Эмбеддинги (могут занимать ГБ)
sentence_transformers/ # Кэшированные модели
transformers/          # Кэш HuggingFace
```

#### 4. Разработка
- `logs/` — логи
- `tmp/`, `temp/` — временные файлы
- `.vscode/`, `.idea/` — IDE конфиги
- `test_output/` — результаты тестов

#### 5. Большие файлы
```
*.zip, *.tar.gz        # Архивы
*.mp4, *.avi           # Видео
*.bin, *.pt, *.pth     # Модели ML
models/, checkpoints/  # Каталоги моделей
```

#### 6. Конфиденциальная информация
```
.env                   # API ключи
secrets/               # Пароли
credentials/           # Учетные данные
```

### 🔒 Защита критических файлов

Все эти файлы **ВСЕГДА коммитятся** (даже если они в .gitignore):
```
✓ README.md
✓ PLAN.md
✓ CHANGELOG.md
✓ VERSION
✓ LICENSE*
✓ content/markdown/
✓ content/indexes/
✓ content/chunks/
✓ content/assets/
✓ scripts/
✓ docs/
✓ examples/
```

---

## `.gitattributes` — как обрабатывать файлы

### 📝 Текстовые файлы (eol=lf)

```
*.md        → LF (Unix)
*.py        → LF (Unix)
*.json      → LF (Unix)
*.yaml      → LF (Unix)
```

Все текстовые файлы используют **LF** (Unix-style) для консистентности.

### 🖼️ Двоичные файлы

```
*.png       → binary (не менять)
*.faiss     → binary (не менять)
*.pt        → binary (не менять)
```

### 🔄 Специальные случаи

**Windows скрипты — CRLF:**
```
*.bat       → CRLF
*.cmd       → CRLF
*.ps1       → CRLF
```

---

## 📈 Размеры файлов (что исключается)

### Большие файлы которые исключаются

```
FAISS индекс (rag_index.faiss)    ~100 MB – 1 GB
Embeddings (embeddings.npy)        ~500 MB – 2 GB
Модели (*.pt, *.bin)              ~500 MB – 13 GB
Кэш трансформеров                 ~2-5 GB
```

### Файлы которые ВКЛЮЧАЮТСЯ (несмотря на размер)

```
content/assets/ (изображения)     ~450 MB  ← ВКЛЮЧАЕМ!
content/chunks/chunks.jsonl        ~3 MB
content/indexes/documents.jsonl    ~2.5 MB
```

---

## ⚙️ Как использовать

### Проверить что исключается

```bash
# Показать все игнорируемые файлы
git status --ignored

# Показать что будет добавлено при commit
git status

# Показать отслеживаемые файлы
git ls-files
```

### Добавить временный файл (несмотря на .gitignore)

```bash
# Принудительно добавить исключённый файл
git add -f big_file.faiss

# Удалить из отслеживания но оставить локально
git rm --cached large_model.pt
```

### Проверить конкретный файл

```bash
# Проверяет ли .gitignore этот файл
git check-ignore -v my_file.txt

# Если вывод есть — файл исключён
# Если пусто — файл будет включён
```

---

## 🚨 Важные замечания

### ⚠️ Не исключайте случайно важное

Проверьте перед commit:
```bash
git status

# Все ли нужные файлы в списке?
# Нет ли ошибочно исключённых файлов?
```

### 💾 Если нужны большие файлы в репозитории

Используйте **Git LFS** (Large File Storage):
```bash
# Установить
git lfs install

# Отслеживать большие файлы
git lfs track "*.faiss"
git lfs track "*.pt"

# Добавить .gitattributes
git add .gitattributes
git commit -m "Add Git LFS tracking"
```

### 🔐 Если случайно закоммитили секрет

```bash
# Удалить из истории (сложно, лучше создать новый ключ)
git filter-branch --tree-filter 'rm -f .env' HEAD

# Или использовать инструмент
git-secret  # специальный инструмент для управления секретами
```

---

## 📋 Быстрый чек-лист

Перед первым push:

- [ ] `.gitignore` и `.gitattributes` скопированы
- [ ] `git status` не показывает временные файлы
- [ ] `git ls-files` содержит все нужные документы и коды
- [ ] Нет `.env` или другие секреты в `git status`
- [ ] Большие файлы исключены (`rag_index.faiss`, модели)
- [ ] Размер репозитория разумный (`< 1 GB` идеально)

---

## 📂 Структура проекта (что коммитится)

```
✓ README.md, PLAN.md, CHANGELOG.md     ← документация
✓ VERSION, LICENSE*                     ← мета-файлы
✓ .gitignore, .gitattributes           ← конфиги git
✓ content/markdown/                    ← основной корпус
✓ content/indexes/                     ← JSONL индексы
✓ content/chunks/                      ← чанки для RAG
✓ content/assets/                      ← изображения
✓ scripts/                             ← скрипты обработки
✓ docs/                                ← документация
✓ examples/                            ← примеры кода

✗ rag_index.faiss                      ← исключён (большой)
✗ venv/, __pycache__/                  ← исключены
✗ .env, secrets/                       ← исключены (конфиденциально)
✗ *.log, tmp/, logs/                   ← исключены (временно)
```

---

## 🎯 Рекомендуемые команды

```bash
# Проверить статус
git status

# Показать все файлы которые будут добавлены
git add . --dry-run

# Добавить все кроме исключённых
git add .

# Или выборочно
git add content/markdown/ scripts/ docs/

# Commit
git commit -m "Update corpus and RAG"

# Push
git push origin main
```

---

## 🔗 Дополнительные ресурсы

- [GitHub — создание .gitignore](https://docs.github.com/en/get-started/getting-started-with-git/ignoring-files)
- [gitignore.io](https://www.toptal.com/developers/gitignore) — генератор .gitignore
- [Git LFS](https://git-lfs.github.com/) — для больших файлов
- [Git атрибуты](https://git-scm.com/book/en/v2/Customizing-Git-Git-Attributes)

---

## ✨ Итого

- ✅ `.gitignore` исключает временные, системные и ML артефакты
- ✅ `.gitattributes` гарантирует правильную обработку файлов
- ✅ Корпус (markdown, индексы, ассеты) всегда коммитится
- ✅ Секреты и большие модели исключены
- ✅ Размер репозитория оптимален

Проект готов к git!
