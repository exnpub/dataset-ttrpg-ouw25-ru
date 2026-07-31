#!/usr/bin/env python3
"""
Скрипт тестирования подготовленного Hugging Face датасета.
Проверяет Parquet-файлы в hf_dataset_export перед загрузкой.

Использование:
    python3 scripts/test_hf_dataset.py
"""

import json
from pathlib import Path
import pandas as pd
import sys

# Настройки
BASE_DIR = Path(__file__).parent.parent
EXPORT_DIR = BASE_DIR / "hf_dataset_export"
SUMMARY_FILE = EXPORT_DIR / "dataset_summary.json"

def test_parquet_file(name: str):
    """Тестирование конкретного parquet-файла."""
    file_path = EXPORT_DIR / f"{name}.parquet"
    if not file_path.exists():
        print(f"❌ Файл не найден: {file_path}")
        return False
    
    print(f"\n🔍 Тестирование {name}.parquet...")
    try:
        df = pd.read_parquet(file_path)
        print(f"   ✓ Файл успешно прочитан")
        print(f"   ✓ Количество записей: {len(df)}")
        print(f"   ✓ Колонки: {', '.join(df.columns)}")
        
        # Проверка на пустые значения в критических полях
        if name == "chunks":
            missing_text = df["text"].isna().sum()
            if missing_text > 0:
                print(f"   ⚠️  Внимание: {missing_text} пустых текстов!")
            
        # Показать пример
        print(f"   📝 Пример данных (первая запись):")
        example = df.iloc[0].to_dict()
        for k, v in example.items():
            val_str = str(v)
            if len(val_str) > 100:
                val_str = val_str[:100] + "..."
            print(f"      - {k}: {val_str}")
            
        return True
    except Exception as e:
        print(f"   ❌ Ошибка при чтении файла: {e}")
        return False

def main():
    print("🧪 Начинаю локальное тестирование подготовленного датасета...")
    
    if not EXPORT_DIR.exists():
        print(f"❌ Директория экспорта не найдена: {EXPORT_DIR}")
        print("Сначала запустите scripts/prepare_for_huggingface.py")
        sys.exit(1)

    # 1. Проверка summary
    if SUMMARY_FILE.exists():
        with open(SUMMARY_FILE, 'r', encoding='utf-8') as f:
            summary = json.load(f)
            print(f"📊 Summary датасета:")
            print(f"   - Название: {summary.get('dataset_name')}")
            print(f"   - Версия: {summary.get('version')}")
            print(f"   - Статистика: {summary.get('stats')}")
    else:
        print("⚠️  Файл dataset_summary.json не найден.")

    # 2. Тестирование конфигов
    configs = ["chunks", "documents", "images"]
    results = []
    
    for config in configs:
        results.append(test_parquet_file(config))
        
    print("\n" + "="*50)
    if all(results):
        print("✅ Тестирование успешно завершено! Датасет готов к загрузке.")
        print("Используйте: python3 scripts/upload_to_huggingface.py")
    else:
        print("⚠️  Тестирование выявило проблемы. Проверьте логи выше.")
    print("="*50)

if __name__ == "__main__":
    main()
