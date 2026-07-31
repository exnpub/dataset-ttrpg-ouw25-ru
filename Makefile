# Управление корпусом «Укрытое море 2025»

PYTHON = python3
SCRIPTS_DIR = scripts

.PHONY: setup build index validate hf-prepare publish full-pipeline security-check clean

setup:
	$(PYTHON) -m pip install -r examples/requirements_rag.txt
	$(PYTHON) -m pip install questionary huggingface-hub pillow

build:
	$(PYTHON) $(SCRIPTS_DIR)/build_corpus.py

index:
	$(PYTHON) $(SCRIPTS_DIR)/build_indexes.py

validate:
	$(PYTHON) $(SCRIPTS_DIR)/validate_corpus.py

hf-prepare:
	$(PYTHON) $(SCRIPTS_DIR)/prepare_for_huggingface.py

security-check:
	gitleaks detect --source . --no-git --config .gitleaks.toml --verbose

publish:
	$(PYTHON) $(SCRIPTS_DIR)/upload_to_huggingface.py

full-pipeline: build index validate hf-prepare security-check
