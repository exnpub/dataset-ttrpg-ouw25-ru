import questionary
import sys
import os

def main():
    print("\n--- Ouw25 LM Pipeline Configuration ---")
    
    # 1. Режим сборки
    build_mode = questionary.select(
        "Выберите режим сборки корпуса:",
        choices=[
            {"name": "Incremental (только новые/измененные)", "value": "incremental"},
            {"name": "Full Rebuild (пересобрать всё)", "value": "full"}
        ]
    ).ask()

    # 2. Подготовка для HF
    do_hf_prepare = questionary.confirm("Подготовить данные для Hugging Face (Parquet/FAISS)?", default=True).ask()

    # 3. Публикация
    do_publish = questionary.confirm("Запустить публикацию на Hugging Face/Kaggle после завершения?", default=False).ask()

    # Выводим параметры для bash-скрипта
    results = []
    if build_mode == "full": results.append("BUILD_FULL=true")
    if do_hf_prepare: results.append("HF_PREPARE=true")
    if do_publish: results.append("DO_PUBLISH=true")
    
    # Сохраняем во временный файл для bash
    with open(".tui_config", "w") as f:
        f.write("\n".join(results))

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(1)
