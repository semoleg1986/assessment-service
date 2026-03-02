# Слой Application

## Команды
- CreateTest
- UpdateTest
- AssignTest
- StartAttempt
- SubmitAttempt
- CancelAssignment

## Запросы
- ListTests
- ListAssignmentsByChild
- GetAttemptResult
- GetChildSkillMap
- GetTopicSignals

## Хендлеры
- `handlers/commands/*` — изменения состояния.
- `handlers/queries/*` — чтение.

## Порты
- TestRepository
- AssignmentRepository
- AttemptRepository
- ChildReadModel (интеграция с user-children)
- ScoringEngine
- RecommendationEngine
- UnitOfWork

## Примечания
- HTTP-детали не должны попадать в handlers.
- Доменные события публикуются после успешного commit (дальше через outbox).
