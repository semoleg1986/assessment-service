# Слой Application

Документ фиксирует актуальный use-case слой `assessment-service`: команды/запросы, хендлеры и порты.

## Структура Application

```shell
src/application/
├── content/
│   ├── commands/
│   ├── handlers/
│   └── queries/
├── delivery/
│   ├── commands/
│   ├── handlers/
│   └── queries/
├── reporting/
│   ├── handlers/
│   └── queries/
└── ports/
    ├── unit_of_work.py
    └── fixture_cleanup.py
```

## Команды (write-side)

### `content.commands`

- `CreateSubject`
- `CreateTopic`
- `CreateMicroSkill`
- `UpdateMicroSkill`
- `DeleteMicroSkill`
- `LinkMicroSkillPredecessors`
- `CreateTest`
- `ImportContent`
- `CleanupFixtures`

### `delivery.commands`

- `AssignTest`
- `StartAttempt`
- `SaveAttemptAnswers`
- `SubmitAttempt`

## Запросы (read-side)

### `content.queries`

- `ListSubjects`
- `ListTopics`
- `ListMicroSkills`
- `ListTests`
- `GetTestById`

### `delivery.queries`

- `ListAssignmentsByChild`
- `GetAttemptResult`

### `reporting.queries`

- `GetChildResultsQuery`
- `GetChildSkillResultsQuery`
- `GetChildDiagnosticsQuery`

## Хендлеры

- Каждый use-case реализован отдельным handler-файлом в своем контексте:
  - `content/handlers/*`
  - `delivery/handlers/*`
  - `reporting/handlers/*`
- Handler принимает typed-command/query, использует `UnitOfWork` и доменные репозитории.

## Порты

### `UnitOfWork` (`ports/unit_of_work.py`)

- Репозитории:
  - `tests`, `assignments`, `attempts`, `subjects`, `topics`, `micro_skills`.
- Транзакционная граница:
  - `commit()`.

### `FixtureCleanupService` (`ports/fixture_cleanup.py`)

- Отдельный порт для dry-run/apply очистки тестовых фикстур с отчетом по счетчикам.

## Границы ответственности

1. Interface слой выполняет transport-валидацию и HTTP-маппинг.
2. Application слой оперирует командами/запросами и доменными типами.
3. Domain слой содержит бизнес-инварианты и ничего не знает о transport/ORM.
4. SQLAlchemy остается в infrastructure; application работает только через порты/UoW.

## Специфика `ImportContent` (`contract_version=v1.2`)

- Режимы:
  - `validate_only=true` — валидация без записи;
  - `validate_only=false` — upsert.
- Режим ошибок:
  - `collect`;
  - `fail_fast`.
- Для `tests/questions` действует entity-level isolation:
  - отдельные невалидные сущности попадают в `errors[]`;
  - валидные сущности продолжают импорт.
