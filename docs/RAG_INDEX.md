# 🤖 RAG для Укрытого моря — Полный индекс материалов

## Где начать

### 🚀 Для нетерпеливых (5 минут)
1. Прочитайте: `examples/QUICKSTART.md`
2. Запустите: `python3 examples/rag_quick_demo.py --mode demo`
3. Готово! 🎉

### 📖 Для изучающих (30 минут)
1. Прочитайте: `docs/RAG_WHAT_NEEDED.md`
2. Выберите подход (FAISS vs облако)
3. Следуйте инструкциям в `examples/QUICKSTART.md`

### 🎓 Для специалистов (несколько часов)
1. Прочитайте: `docs/RAG_SETUP_GUIDE.md` (полное руководство)
2. Изучите примеры: `examples/rag_*.py`
3. Создавайте свои RAG-приложения!

---

## 📚 Структура документации RAG

### Основные документы

```
docs/
├─ RAG_WHAT_NEEDED.md ............. ТО ЧТО НУЖНО для RAG
│                                  (начните отсюда)
│
├─ RAG_SETUP_GUIDE.md ............. ПОЛНОЕ РУКОВОДСТВО
│                                  (30+ страниц, все примеры)
│
├─ ML_USAGE.md .................... Примеры использования
│                                  (5 сценариев с кодом)
│
├─ AI_CONSTRAINTS.md .............. Ограничения для ИИ
│                                  (важно для качества ответов)
│
└─ CONTRIBUTING.md ................ Редактирование корпуса
                                   (если хотите улучшать содержимое)

examples/
├─ QUICKSTART.md .................. БЫСТРЫЙ СТАРТ (5 мин)
│                                  ← НАЧНИТЕ ЗДЕСЬ
│
├─ rag_quick_demo.py .............. Минимальный RAG
│                                  (чистый Python, без LLM)
│
├─ rag_with_ollama.py ............. RAG + локальная LLM
│                                  (полный цикл RAG)
│
└─ requirements_rag.txt ............ Все зависимости
                                   (pip install -r)
```

### Вспомогательные документы

```
README.md ......................... Главная документация проекта
CHANGELOG.md ....................... История всех версий
RELEASE_NOTES.md .................. Заметки о выпуске v1.0.0
PLAN.md ........................... Исходный план проекта
VERSION ........................... Текущая версия (1.0.0)
```

---

## 🎯 Практический путь

### Этап 1: Быстрая демонстрация (5 минут)

```bash
cd /путь/к/ouw25_lm
python3 examples/rag_quick_demo.py --mode demo
```

**Что вы увидите:**
- Примеры работы поиска
- Как ищутся чанки
- Как форматируется контекст для LLM

### Этап 2: Интерактивный режим (10 минут)

```bash
python3 examples/rag_quick_demo.py --mode interactive
```

**Что вы делаете:**
- Задаёте свои вопросы
- Видите релевантные результаты
- Изучаете, как работает поиск

### Этап 3: Интеграция с LLM (30 минут)

Выберите один:

**A) С локальной LLM (Ollama)**
```bash
# 1. Установить Ollama: https://ollama.ai
# 2. Загрузить модель: ollama pull mistral
# 3. Запустить:
python3 examples/rag_with_ollama.py --mode interactive
```

**B) С OpenAI (облако)**
```bash
# 1. Установить: pip install openai
# 2. Установить ключ: export OPENAI_API_KEY="sk-..."
# 3. Модифицировать пример и запустить
```

### Этап 4: Собственное приложение (1-2 дня)

Используйте классы из примеров как основу:

```python
from examples.rag_quick_demo import UkrytoeMoreRAG

# Создайте свой RAG
rag = UkrytoeMoreRAG()

# Используйте в своём коде
results = rag.search("ваш вопрос")
context = rag.format_context(results)
```

---

## 📋 Что есть в коробке

### Корпус (всё необходимое уже подготовлено)

- ✅ **39 документов** — полная игра
- ✅ **1378 чанков** — оптимально структурировано для RAG
- ✅ **132 изображения** — с метаданными
- ✅ **Public Domain** — свободно используй везде
- ✅ **JSONL-индексы** — готовы к загрузке

### Примеры RAG

- ✅ **`rag_quick_demo.py`** — полностью рабочий пример (220 строк)
- ✅ **`rag_with_ollama.py`** — RAG + локальная LLM (300 строк)
- ✅ **Классы готовы** — используй как основу

### Документация

- ✅ **RAG_SETUP_GUIDE.md** — 27 KB, полное руководство
- ✅ **RAG_WHAT_NEEDED.md** — 12 KB, что нужно
- ✅ **QUICKSTART.md** — 5 KB, быстрый старт
- ✅ **Примеры кода** — 30+ готовых сниппетов

---

## 🚀 Типичные сценарии

### Сценарий 1: Я хочу просто попробовать

```bash
pip install numpy sentence-transformers faiss-cpu
python3 examples/rag_quick_demo.py
```
**Время:** 15 минут | **Стоимость:** Бесплатно | **Результат:** Работающая демо

### Сценарий 2: Я хочу RAG без интернета

```bash
# Установить Ollama
# Загрузить модель: ollama pull mistral
python3 examples/rag_with_ollama.py
```
**Время:** 30 минут | **Стоимость:** Бесплатно (но ~7 ГБ) | **Результат:** Локальный RAG

### Сценарий 3: Я хочу лучшее качество

```bash
pip install openai
export OPENAI_API_KEY="sk-your-key"
# Модифицировать rag_quick_demo.py для OpenAI
```
**Время:** 15 минут | **Стоимость:** $1-5 | **Результат:** Профессиональное качество

### Сценарий 4: Я хочу свой API

```bash
pip install fastapi uvicorn
# Обернуть RAG в FastAPI endpoints
# Запустить: uvicorn app:app --reload
```
**Время:** 1-2 часа | **Стоимость:** Зависит | **Результат:** REST API

### Сценарий 5: Я хочу Telegram-бота

```bash
pip install python-telegram-bot
# Обернуть RAG в Telegram handlers
```
**Время:** 2-3 часа | **Стоимость:** ~$1/месяц | **Результат:** Бот в Telegram

---

## 💡 Рекомендации по выбору

### Если у вас есть GPU
→ Используйте FAISS локально
```bash
pip install faiss-gpu
```

### Если у вас 16+ ГБ RAM
→ Используйте Ollama с большой моделью
```bash
ollama pull neural-chat  # 7.4 ГБ, отличное качество
```

### Если хотите простоты
→ Используйте OpenAI
```bash
pip install openai
export OPENAI_API_KEY="sk-..."
```

### Если нужна масштабируемость
→ Используйте облачные решения
```python
# Qdrant, Weaviate, Milvus и т.д.
```

---

## 🔗 Связи между документами

```
БЫСТРЫЙ СТАРТ (5 мин)
    ↓
examples/QUICKSTART.md
    ↓
[Выбираете подход]
    ├─→ FAISS локально
    │   ├─→ examples/rag_quick_demo.py
    │   └─→ docs/RAG_SETUP_GUIDE.md (раздел 1)
    │
    ├─→ Ollama (локальная LLM)
    │   ├─→ examples/rag_with_ollama.py
    │   └─→ docs/RAG_SETUP_GUIDE.md (раздел 3)
    │
    └─→ OpenAI (облако)
        └─→ docs/RAG_SETUP_GUIDE.md (раздел 2)
```

---

## 📦 Что устанавливать

### Минимум (только поиск)
```bash
pip install numpy sentence-transformers faiss-cpu
```

### Рекомендуемое (поиск + генерация)
```bash
pip install -r examples/requirements_rag.txt
```

### Полное (всё включено)
```bash
pip install -r examples/requirements_rag.txt
# плюс Ollama: https://ollama.ai
```

---

## ✅ Чек-лист для начала

- [ ] Я прочитал `examples/QUICKSTART.md` (5 мин)
- [ ] Я установил зависимости (5 мин)
- [ ] Я запустил `rag_quick_demo.py --mode demo` (5 мин)
- [ ] Я понял, как работает поиск (10 мин)
- [ ] Я решил, какой подход использовать (5 мин)
- [ ] Я установил LLM (если нужна) (15 мин)
- [ ] Я запустил интерактивный режим (5 мин)
- [ ] Я готов создавать свой RAG! 🎉

**Общее время:** 50 минут

---

## 🆘 Если что-то не работает

### "ModuleNotFoundError"
```bash
pip install numpy sentence-transformers faiss-cpu
```

### "connection refused" (Ollama)
```bash
# Убедитесь, что Ollama запущена
ollama serve

# В другом терминале:
python3 examples/rag_with_ollama.py
```

### "OPENAI_API_KEY not set"
```bash
export OPENAI_API_KEY="sk-your-key"
python3 your_script.py
```

### "Slow performance"
→ Используйте более лёгкую модель эмбеддингов:
```python
embedding_model="cointegrated/rubert-tiny2"
```

---

## 📞 Дополнительная помощь

- 📖 **Полное руководство:** `docs/RAG_SETUP_GUIDE.md`
- 💬 **Примеры кода:** `examples/rag_*.py`
- 📚 **Что нужно:** `docs/RAG_WHAT_NEEDED.md`
- 🎯 **Быстрый старт:** `examples/QUICKSTART.md`

---

## 🎓 Следующие шаги после RAG

1. **Продвинутая индексация** — гибридный поиск, re-ranking
2. **Оптимизация** — кэширование, батчинг
3. **Мониторинг** — логи, метрики качества
4. **Интеграции** — API, UI, чат-боты
5. **Масштабирование** — облачные БД, распределённые системы

---

## 🚀 Вы готовы!

Выберите подходящий для вас уровень:

- **Новичок?** → `examples/QUICKSTART.md`
- **Опытный?** → `examples/rag_quick_demo.py`
- **Специалист?** → `docs/RAG_SETUP_GUIDE.md`

И начните создавать RAG для Укрытого моря! ⚓

**Удачи!** 🌊
