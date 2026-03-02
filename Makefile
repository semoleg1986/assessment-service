# ========================
# Requirements
# ========================

requirements: ## Скомпилировать requirements.in в requirements.txt
	pip-compile requirements.in

install: requirements ## Установить зависимости
	pip install -r requirements.txt

# ========================
# Test
# ========================

test: ## Запустить все тесты
	pytest -q

test-cov: ## Запустить тесты с покрытием
	pytest --cov=src -q

# ========================
# Code Quality
# ========================

format: ## Автоформатирование (isort + black)
	isort .
	black .

lint: ## Проверка стиля и типов (flake8 + mypy)
	flake8 .
	mypy .

check: format lint test ## Полная проверка качества

# ========================
# Run
# ========================

run: ## Запустить HTTP сервис
	uvicorn src.interface.http.main:app --host 0.0.0.0 --port 8003 --reload

# ========================
# API Contract
# ========================

openapi-export: ## Сгенерировать openapi.yaml
	python scripts/export_openapi.py --output openapi.yaml

openapi-check: ## Проверить синхронизацию openapi.yaml
	python scripts/export_openapi.py --output openapi.yaml --check

contract-provider: openapi-check test ## Проверка provider-контракта

# ========================
# Pre-commit
# ========================

precommit: ## Запуск pre-commit хуков на всех файлах
	pre-commit run --all-files

# ========================
# Help
# ========================

help: ## Показать список доступных команд
	@echo "Доступные команды:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
	| sort \
	| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'
