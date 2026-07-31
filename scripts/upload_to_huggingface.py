#!/usr/bin/env python3
"""
Скрипт загрузки подготовленного корпуса и RAG-артефактов на Hugging Face Hub.

Использует переменные окружения из .env:
    HF_TOKEN - ваш API токен с правами записи
    HF_REPO_ID - ID репозитория (например, exnihilum/ukrytoe-more-corpus)
    HF_DATASET_VISIBILITY - 'public' или 'private'

Использование:
    python3 scripts/upload_to_huggingface.py
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from huggingface_hub import HfApi, create_repo

# Настройки
BASE_DIR = Path(__file__).parent.parent
EXPORT_DIR = BASE_DIR / "hf_dataset_export"
DOTENV_PATH = BASE_DIR / ".env"

def main():
    print("🚢 Подготовка к загрузке на Hugging Face Hub...")

    # 1. Загрузка конфигурации
    if not DOTENV_PATH.exists():
        print(f"❌ Файл .env не найден в {BASE_DIR}")
        print("Скопируйте .env.example в .env и заполните HF_TOKEN.")
        sys.exit(1)

    load_dotenv(DOTENV_PATH)
    
    token = os.getenv("HF_TOKEN")
    repo_id = os.getenv("HF_REPO_ID")
    visibility = os.getenv("HF_DATASET_VISIBILITY", "private").lower()
    
    if not token or token == "hf_your_token_here":
        print("❌ HF_TOKEN не задан в .env файле.")
        sys.exit(1)
    
    if not repo_id:
        print("❌ HF_REPO_ID не задан в .env файле.")
        sys.exit(1)

    # 2. Авторизация
    print(f"🔑 Авторизация...")
    try:
        api = HfApi(token=token)
        user = api.whoami()
        print(f"   ✓ Авторизован как: {user['name']}")
    except Exception as e:
        print(f"❌ Ошибка авторизации: {e}")
        sys.exit(1)

    # 3. Создание репозитория (если не существует)
    print(f"📂 Проверка репозитория {repo_id}...")
    try:
        create_repo(
            repo_id=repo_id,
            token=token,
            repo_type="dataset",
            private=(visibility == "private"),
            exist_ok=True
        )
        print(f"   ✓ Репозиторий готов")
    except Exception as e:
        print(f"❌ Не удалось создать репозиторий: {e}")
        sys.exit(1)

    # 4. Загрузка файлов
    print(f"📤 Загрузка файлов из {EXPORT_DIR}...")
    
    files_to_upload = list(EXPORT_DIR.glob("*.parquet"))
    files_to_upload.extend(list(EXPORT_DIR.glob("*.faiss")))
    files_to_upload.extend(list(EXPORT_DIR.glob("dataset_summary.json")))
    files_to_upload.extend(list(EXPORT_DIR.glob("global_knowledge_map.json")))
    files_to_upload.extend(list(EXPORT_DIR.glob("GAME_CONCEPT.md")))
    files_to_upload.extend(list(EXPORT_DIR.glob("dataset_info.yaml")))
    files_to_upload.extend(list(EXPORT_DIR.glob("README.md")))
    
    if not files_to_upload:
        print(f"⚠️  Файлы для загрузки не найдены в {EXPORT_DIR}")
        print("Сначала запустите scripts/prepare_for_huggingface.py")
        sys.exit(1)

    for file_path in files_to_upload:
        print(f"   ⬆️  Загрузка {file_path.name}...")
        try:
            api.upload_file(
                path_or_fileobj=str(file_path),
                path_in_repo=file_path.name,
                repo_id=repo_id,
                repo_type="dataset",
                token=token
            )
        except Exception as e:
            print(f"      ✕ Ошибка при загрузке {file_path.name}: {e}")

    # Загружаем hf_dataset_README.md как README.md в репозиторий HF
    hf_readme = BASE_DIR / "hf_dataset_README.md"
    if hf_readme.exists():
        print(f"   ⬆️  Загрузка Dataset Card (README.md)...")
        api.upload_file(
            path_or_fileobj=str(hf_readme),
            path_in_repo="README.md",
            repo_id=repo_id,
            repo_type="dataset",
            token=token
        )

    print(f"\n🎉 Все файлы и RAG-артефакты успешно загружены в https://huggingface.co/datasets/{repo_id}")

if __name__ == "__main__":
    main()
