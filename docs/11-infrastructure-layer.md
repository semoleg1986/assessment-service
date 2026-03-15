# Слой Infrastructure

## Назначение

Infrastructure Layer реализует persistence и системные адаптеры `assessment-service`: SQLAlchemy репозитории/UoW и maintenance-инструменты.

## Структура

```shell
src/infrastructure/
├── db/
│   ├── session.py
│   ├── models.py
│   ├── mappers.py
│   ├── uow.py
│   └── repositories/
│       ├── subject_repository.py
│       ├── topic_repository.py
│       ├── micro_skill_repository.py
│       ├── assessment_test_repository.py
│       ├── assignment_repository.py
│       ├── attempt_repository.py
│       └── in_memory.py
├── maintenance/
│   └── fixture_cleanup.py
├── observability/
└── messaging/
```

## Что делает слой

- Реализует порты `UnitOfWork` и domain-repositories через SQLAlchemy.
- Обеспечивает in-memory адаптеры для тестов.
- Содержит технический maintenance-адаптер `fixture_cleanup.py`.

## Границы ответственности

- Infrastructure не должен определять HTTP DTO/роутинг.
- Infrastructure не содержит use-case orchestration и policy checks.
- Domain не импортирует инфраструктурные реализации.
