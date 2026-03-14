# Слой Application

Документ описывает use-case слой: команды/запросы, их хендлеры и порты.

## Команды (write-side)

- `CreateSubject`
- `CreateTopic`
- `CreateMicroSkill`
- `LinkMicroSkillPredecessors`
- `CreateTest`
- `AssignTest`
- `StartAttempt`
- `SaveAttemptAnswers`
- `SubmitAttempt`
- `ImportContent`
- `CleanupFixtures`

## Запросы (read-side)

- `ListSubjects`
- `ListTopics`
- `ListMicroSkills`
- `ListTests`
- `GetTestById`
- `ListAssignmentsByChild`
- `GetAttemptResult`
- `GetChildDiagnostics`

## Хендлеры

- `src/application/handlers/commands/*` — изменение состояния агрегатов.
- `src/application/handlers/queries/*` — чтение проекций/репозиториев.
- Хендлеры работают только с application-командами и портами.

## Порты

- `UnitOfWork`
- `TestRepository`
- `AssignmentRepository`
- `AttemptRepository`
- `SubjectRepository`
- `TopicRepository`
- `MicroSkillNodeRepository`
- `FixtureCleanupService`

## Границы ответственности

- Валидация HTTP payload и маппинг DTO выполняются на interface-слое.
- Application-слой оперирует типизированными командами и доменными сущностями.
- Транзакционная граница — `UnitOfWork.commit()`.
- Интеграционные проверки ссылочной целостности выполняются в хендлерах import/create команд.

## Специфика `ImportContent` (`v1.2`)

- Поддерживает два режима:
  - `validate_only=true` — только проверка
  - `validate_only=false` — upsert
- Поддерживает два профиля обработки ошибок:
  - `collect`
  - `fail_fast`
- Для `tests/questions` используется entity-level isolation:
  - невалидная сущность фиксируется в `errors[]`
  - остальная валидная часть payload продолжает обработку

## Примечания по Clean Architecture

- Interface не должен обращаться к SQLAlchemy напрямую: только через `Dishka`/портовые зависимости.
- Domain не знает про HTTP/Pydantic/SQLAlchemy.
- Application не содержит деталей транспорта (headers, cookies, status codes).
