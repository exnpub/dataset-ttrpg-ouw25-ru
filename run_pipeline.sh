#!/bin/bash

# Скрипт полного цикла сборки и публикации Ouw25
set -e

# Цвета
BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Значения по умолчанию
BUILD_FULL=false
HF_PREPARE=false
DO_PUBLISH=false
USE_TUI=false

usage() {
    echo -e "${BLUE}Скрипт управления корпусом Укрытое море 2025${NC}"
    echo "Использование: ./run_pipeline.sh [OPTIONS]"
    echo ""
    echo "Опции:"
    echo -e "  ${YELLOW}--tui${NC}              Запустить интерактивное меню"
    echo -e "  ${YELLOW}--full-build${NC}       Полная пересборка всех Markdown и индексов"
    echo -e "  ${YELLOW}--hf-prepare${NC}       Подготовка артефактов для Hugging Face"
    echo -e "  ${YELLOW}--publish${NC}          Автоматическая публикация на HF/Kaggle"
    echo -e "  ${YELLOW}-h, --help${NC}         Показать эту справку"
}

# Парсинг аргументов
while [[ $# -gt 0 ]]; do
    case $1 in
        --tui) USE_TUI=true; shift ;;
        --full-build) BUILD_FULL=true; shift ;;
        --hf-prepare) HF_PREPARE=true; shift ;;
        --publish) DO_PUBLISH=true; shift ;;
        -h|--help) usage; exit 0 ;;
        *) echo "Неизвестный параметр: $1"; usage; exit 1 ;;
    esac
done

# 1. Проверка окружения
if [ -f .env ]; then
    echo -e "${GREEN}[OK]${NC} Файл .env найден. Загружаем переменные..."
    export $(grep -v '^#' .env | xargs)
else
    echo -e "${YELLOW}[WARN]${NC} Файл .env не найден! Используются значения по умолчанию."
fi

# 2. Установка зависимостей
echo -e "\n${BLUE}--- Подготовка окружения ---${NC}"
make setup

# 3. Если выбран TUI, запускаем его
if [ "$USE_TUI" = true ]; then
    python3 scripts/tui_launcher.py
    if [ -f .tui_config ]; then
        source .tui_config
        rm .tui_config
    else
        echo -e "${RED}TUI прерван.${NC}"
        exit 1
    fi
fi

echo -e "\n${BLUE}=== Конфигурация запуска ===${NC}"
echo -e "Режим сборки: $( [ "$BUILD_FULL" = true ] && echo -e "${YELLOW}FULL${NC}" || echo -e "${GREEN}INCREMENTAL${NC}" )"
echo -e "Подготовка HF: $( [ "$HF_PREPARE" = true ] && echo -e "${YELLOW}YES${NC}" || echo -e "${GREEN}NO${NC}" )"
echo -e "Публикация:    $( [ "$DO_PUBLISH" = true ] && echo -e "${YELLOW}YES${NC}" || echo -e "${GREEN}NO${NC}" )"
echo "----------------------------"

# Запуск этапов
echo -e "\n${BLUE}1. Сборка корпуса (DOCX -> Markdown)...${NC}"
make build

echo -e "\n${BLUE}2. Генерация индексов и чанков...${NC}"
make index

echo -e "\n${BLUE}3. Валидация целостности...${NC}"
make validate

if [ "$HF_PREPARE" = true ]; then
    echo -e "\n${BLUE}4. Подготовка артефактов Hugging Face...${NC}"
    make hf-prepare
fi

echo -e "\n${BLUE}5. Проверка безопасности (Gitleaks)...${NC}"
make security-check

if [ "$DO_PUBLISH" = true ]; then
    echo -e "\n${BLUE}6. Публикация...${NC}"
    make publish
fi

echo -e "\n${GREEN}=== Выполнение завершено! ===${NC}"
