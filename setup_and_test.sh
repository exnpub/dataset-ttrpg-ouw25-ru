#!/bin/bash

# ==============================================================================
# 🌊 Укрытое море: E2E Тест (Auto-Lifecycle Ollama)
# ==============================================================================

set -e 

# Цвета для вывода
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}======================================================================"
echo -e "🌊 Укрытое море — E2E RAG Test (Ollama Lifecycle Management)"
echo -e "======================================================================${NC}"

# Добавляем стандартные пути Homebrew в PATH для macOS
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"

OLLAMA_PID=""
STARTED_BY_SCRIPT=false

# Функция для завершения Ollama
cleanup() {
    if [ "$STARTED_BY_SCRIPT" = true ] && [ -n "$OLLAMA_PID" ]; then
        echo -e "\n${YELLOW}⚓ Завершение фонового процесса Ollama (PID: $OLLAMA_PID)...${NC}"
        kill $OLLAMA_PID 2>/dev/null || true
        echo -e "${GREEN}✓ Ollama выгружена${NC}"
    fi
}

# Устанавливаем ловушку для очистки при выходе или ошибке
trap cleanup EXIT

# 1. Проверка системных зависимостей (macOS)
if [[ "$OSTYPE" == "darwin"* ]]; then
    if ! brew list libomp &> /dev/null; then
        echo -e "${BLUE}📦 Установка libomp...${NC}"
        brew install libomp
    else
        echo -e "${GREEN}✓ libomp установлен${NC}"
    fi
fi

# 2. Настройка Python
echo -e "\n${YELLOW}🐍 Настройка Python окружения...${NC}"
if [[ ! -d "venv" ]]; then
    echo -e "${BLUE}📦 Создание виртуального окружения venv...${NC}"
    python3 -m venv venv || { echo -e "${RED}❌ Не удалось создать venv${NC}"; exit 1; }
fi

source venv/bin/activate || { echo -e "${RED}❌ Не удалось активировать venv${NC}"; exit 1; }

echo -e "${BLUE}📦 Проверка/установка Python-пакетов...${NC}"
python3 -m pip install -q --upgrade pip setuptools wheel
python3 -m pip install -q -r examples/requirements_rag.txt python-dotenv datasets huggingface-hub pandas pyarrow || { echo -e "${RED}❌ Ошибка при установке пакетов${NC}"; exit 1; }
echo -e "${GREEN}✓ Окружение Python готово${NC}"

# 3. Управление Ollama
echo -e "\n${YELLOW}🧠 Проверка статуса Ollama...${NC}"
if ! curl -s http://localhost:11434/api/tags &> /dev/null; then
    echo -e "${BLUE}🚀 Ollama не запущена. Запуск 'ollama serve' в фоне...${NC}"
    ollama serve > /dev/null 2>&1 &
    OLLAMA_PID=$!
    STARTED_BY_SCRIPT=true
    
    echo -ne "${YELLOW}⏳ Ожидание готовности Ollama...${NC}"
    MAX_RETRIES=30
    COUNT=0
    while ! curl -s http://localhost:11434/api/tags &> /dev/null; do
        sleep 1
        echo -ne "."
        COUNT=$((COUNT+1))
        if [ $COUNT -ge $MAX_RETRIES ]; then
            echo -e "${RED}\n❌ Ошибка: Ollama не запустилась за 30 секунд.${NC}"
            exit 1
        fi
    done
    echo -e "${GREEN} Готова!${NC}"
else
    echo -e "${GREEN}✓ Ollama уже запущена пользователем (не будет выгружена автоматически)${NC}"
fi

MODEL_NAME="mistral"
echo -e "${BLUE}📥 Проверка модели ${MODEL_NAME}...${NC}"
if ! ollama list | grep -q "$MODEL_NAME"; then
    echo -e "${YELLOW}⏳ Загрузка модели ${MODEL_NAME}...${NC}"
    ollama pull $MODEL_NAME
else
    echo -e "${GREEN}✓ Модель готова${NC}"
fi

# 4. Подготовка индексов
export KMP_DUPLICATE_LIB_OK=TRUE
if [[ ! -f "rag_index.faiss" ]]; then
    echo -e "${BLUE}⏳ Сборка FAISS-индекса...${NC}"
    python3 examples/rag_quick_demo.py --mode demo > /dev/null
fi

# 5. Запуск e2e автотеста
echo -e "\n${YELLOW}🧪 Запуск E2E автотеста (RAG + LLM)...${NC}"
python3 scripts/test_rag_ollama.py --model $MODEL_NAME

echo -e "\n${GREEN}======================================================================"
echo -e "✅ E2E ТЕСТИРОВАНИЕ ЗАВЕРШЕНО УСПЕШНО"
echo -e "======================================================================${NC}"
