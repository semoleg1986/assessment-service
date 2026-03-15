# Слой Interface

## Назначение

Interface Layer реализует HTTP API `assessment-service`, включая раздельные admin/user маршруты, import API и transport-схемы по bounded-context.

## Структура

```shell
src/interface/http/
├── app.py
├── main.py
├── health.py
├── middleware.py
├── dependencies.py
├── di/providers.py
└── v1/
    ├── router.py
    ├── content_import.py
    ├── admin/
    │   ├── router.py
    │   ├── _helpers.py
    │   ├── content_crud.py
    │   ├── tests.py
    │   ├── imports.py
    │   ├── assignments.py
    │   ├── results.py
    │   └── maintenance.py
    ├── user/router.py
    └── schemas/
        ├── content.py
        ├── delivery.py
        ├── imports.py
        └── reporting.py
```

## Что делает слой

- Разделяет endpoint'ы по сценариям:
  - `admin/*`: контент, импорт, назначение, отчеты, cleanup.
  - `user/router.py`: чтение назначений/результатов и попытки ребенка.
- Использует контекстные transport-схемы (`schemas/content|delivery|imports|reporting.py`).
- Обрабатывает request-level concerns: middleware, request_id, HTTP error mapping.
- Делегирует бизнес-операции в application handlers.

## Границы ответственности

- Interface не работает напрямую с SQLAlchemy моделями/сессией.
- Interface не содержит доменной scoring/validation логики.
- Любая бизнес-валидация после transport уровня находится в application/domain.
