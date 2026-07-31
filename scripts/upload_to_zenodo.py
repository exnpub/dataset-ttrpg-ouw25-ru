#!/usr/bin/env python3
"""
Скрипт программной выгрузки датасета и RAG-артефактов на Zenodo (с получением DOI).

Использует переменные окружения из .env:
    ZENODO_TOKEN - ваш Personal Access Token с правами deposit:actions и deposit:write

Использование:
    python3 scripts/upload_to_zenodo.py
"""

import os
import sys
import json
import requests
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).parent.parent
EXPORT_DIR = BASE_DIR / "hf_dataset_export"
DOTENV_PATH = BASE_DIR / ".env"
ZENODO_API_URL = "https://zenodo.org/api/deposit/depositions"

def main():
    print("🌐 Подготовка к выгрузке датасета на Zenodo (получение академического DOI)...")

    if not DOTENV_PATH.exists():
        print(f"❌ Файл .env не найден в {BASE_DIR}")
        print("Добавьте ZENODO_TOKEN в ваш .env файл.")
        sys.exit(1)

    load_dotenv(DOTENV_PATH)
    token = os.getenv("ZENODO_TOKEN")

    if not token or token == "zenodo_your_token_here":
        print("❌ ZENODO_TOKEN не задан в .env файле.")
        print("Получите токен в личном кабинете Zenodo (Settings -> Applications -> Personal Access Tokens).")
        sys.exit(1)

    headers = {"Authorization": f"Bearer {token}"}

    if not EXPORT_DIR.exists() or not list(EXPORT_DIR.glob("*.parquet")):
        print(f"❌ Артефакты не найдены в {EXPORT_DIR}. Сначала запустите prepare_for_huggingface.py")
        sys.exit(1)

    # 1. Создание новой записи (deposition)
    print("📂 Создание новой черновой записи на Zenodo...")
    metadata = {
        "metadata": {
            "title": "On Ulerior Waves (Укрытое море): TTRPG Corpus & RAG Vectors",
            "upload_type": "dataset",
            "description": "The official machine-learning and RAG dataset for the tabletop role-playing game <b>On Ulerior Waves (Укрытое море)</b> by Ex Nihilum Publishing. Featuring a unique decopunk, seacrawl, and weird fiction setting in Veah Toaoroah.<br><br><b>Contents:</b><br>- <b>Chunks</b>: 1378 semantic chunks optimized for RAG and vector retrieval.<br>- <b>Documents</b>: 39 fully normalized markdown chapters, supplements, and SRD.<br>- <b>Embeddings</b>: Precomputed 384-dimensional multilingual embeddings (multilingual-e5-small).<br>- <b>FAISS Index</b>: Pre-built binary index for instant vector search.<br>- <b>Knowledge Map & Concept</b>: Global knowledge graph and game concept manifest.<br><br><b>License:</b> Text contents are released under Public Domain (CC0).",
            "creators": [
                {
                    "name": "Ex Nihilum Publishing",
                    "affiliation": "Ex Nihilum"
                }
            ],
            "access_right": "open",
            "license": "cc-zero",
            "keywords": [
                "ttrpg",
                "seacrawl",
                "hexcrawl",
                "decopunk",
                "weird-fiction",
                "tabletop-rpg",
                "rag",
                "worldbuilding",
                "rulebook",
                "russian-nlp"
            ],
            "notes": "Corpus version v1.1.0. Prepared for ML, research, and RAG systems."
        }
    }

    res = requests.post(ZENODO_API_URL, json=metadata, headers={**headers, "Content-Type": "application/json"}, timeout=30)
    if res.status_code != 201:
        print(f"❌ Ошибка создания депозита ({res.status_code}): {res.text}")
        sys.exit(1)

    depo_data = res.json()
    depo_id = depo_data["id"]
    bucket_url = depo_data["links"]["bucket"]
    print(f"   ✓ Запись создана (ID: {depo_id})")

    # 2. Загрузка файлов через Bucket API
    # Включаем parquet, faiss, json, md, yaml
    files_to_upload = list(EXPORT_DIR.glob("*"))
    # Также захватим GAME_CONCEPT.md из корня если есть
    concept_file = BASE_DIR / "GAME_CONCEPT.md"
    if concept_file.exists() and concept_file not in files_to_upload:
        files_to_upload.append(concept_file)

    print(f"📤 Загрузка файлов на Zenodo bucket...")
    for file_path in files_to_upload:
        if file_path.is_file() and not file_path.name.startswith("."):
            print(f"   ⬆️  Загрузка {file_path.name}...")
            with open(file_path, "rb") as fp:
                upload_res = requests.put(
                    f"{bucket_url}/{file_path.name}",
                    data=fp,
                    headers={**headers, "Content-Type": "application/octet-stream"},
                    timeout=300
                )
                if upload_res.status_code not in [200, 201]:
                    print(f"      ✕ Ошибка при загрузке {file_path.name}: {upload_res.text}")
                else:
                    print(f"      ✓ Успешно")

    # 3. Публикация депозита для получения DOI
    print(f"🚀 Публикация записи на Zenodo...")
    publish_url = f"{ZENODO_API_URL}/{depo_id}/actions/publish"
    pub_res = requests.post(publish_url, headers=headers, timeout=30)

    if pub_res.status_code == 202:
        pub_data = pub_res.json()
        doi = pub_data.get("doi", "DOI будет назначен после модерации/обработки")
        concept_doi = pub_data.get("conceptdoi", "")
        record_url = pub_data.get("links", {}.get("html", f"https://zenodo.org/record/{depo_id}"))

        print(f"\n🎉 Датасет успешно опубликован на Zenodo!")
        print(f"📌 Ссылка на запись: {record_url}")
        print(f"🏷️  DOI: {doi}")
        if concept_doi:
            print(f"🔗 Concept DOI (для будущих версий): {concept_doi}")
    else:
        print(f"⚠️ Запись загружена, но статус публикации не 202 ({pub_res.status_code}): {pub_res.text}")
        print(f"Вы можете опубликовать её вручную в панели управления Zenodo: https://zenodo.org/deposit/{depo_id}")

if __name__ == "__main__":
    main()
