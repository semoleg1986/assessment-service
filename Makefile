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

db-upgrade: ## Применить alembic миграции до head
	alembic upgrade head

db-downgrade: ## Откатить alembic миграции на один шаг
	alembic downgrade -1

docker-up: ## Запустить assessment-service через Docker Compose
	docker compose up --build -d

docker-down: ## Остановить Docker Compose окружение
	docker compose down

docker-logs: ## Показать логи Docker Compose
	docker compose logs -f --tail=200

docker-pull: ## Забрать свежий образ (image mode)
	docker compose pull

docker-restart: ## Перезапустить сервис из образа
	docker compose up -d --force-recreate

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
