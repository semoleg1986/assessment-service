# Доменная Модель

## Purpose

Контракт доменной модели сервиса `assessment-service`.
Документ синхронизирован с реализацией `v0.2.0`.

## Агрегаты

### 1. AssessmentTest (Aggregate Root)

- **Поля**:
  - `test_id: UUID`
  - `subject_code: str`
  - `grade: int`
  - `questions: list[Question]`
  - `created_at: datetime`
  - `version: int`
- **Инварианты**:
  - тест содержит минимум один вопрос
  - `grade` в диапазоне `1..4`

### 2. AssignmentAggregate (Aggregate Root)

- **Поля**:
  - `assignment_id: UUID`
  - `test_id: UUID`
  - `child_id: UUID`
  - `status: assigned | started | completed | expired | cancelled`
  - `assigned_at: datetime`
  - `version: int`
- **Поведение**:
  - `mark_started()`
  - `mark_completed()`

### 3. AttemptAggregate (Aggregate Root)

- **Поля**:
  - `attempt_id: UUID`
  - `assignment_id: UUID`
  - `child_id: UUID`
  - `status: started | submitted | cancelled`
  - `started_at: datetime`
  - `submitted_at: datetime | None`
  - `score: int`
  - `answers: list[Answer]`
  - `version: int`
- **Поведение**:
  - `submit(answers)`
- **Инварианты**:
  - отправка попытки разрешена только из `started`

## Сущности

### Subject

- `code: str`
- `name: str`

### Topic

- `code: str`
- `subject_code: str`
- `grade: int`
- `name: str`

### MicroSkillNode

- `node_id: str`
- `subject_code: str`
- `grade: int`
- `topic_code: str | None`
- `section_code: str`
- `section_name: str`
- `micro_skill_name: str`
- `predecessor_ids: list[str]`
- `criticality: low | medium | high`
- `source_ref: str | None`
- `description: str | None`
- `status: draft | active | archived`
- `external_ref: str | None`
- `version: int`
- `created_at: datetime`
- `updated_at: datetime`

### Question

- `question_id: UUID`
- `node_id: str`
- `text: str`
- `answer_key: str`
- `max_score: int`

### Answer

- `question_id: UUID`
- `value: str`
- `is_correct: bool`
- `awarded_score: int`

## Value Objects

- `AssignmentStatus`: `assigned | started | completed | expired | cancelled`
- `AttemptStatus`: `started | submitted | cancelled`
- `CriticalityLevel`: `low | medium | high`
- `MicroSkillStatus`: `draft | active | archived`

## Инварианты

- Assignment ссылается на существующие `child_id` и `test_id` (проверка в application/integration).
- Для одного assignment только одна активная attempt.
- Итоговый `score` детерминированно считается как сумма `awarded_score` ответов.
- `MicroSkillNode.topic_code` должен ссылаться на существующую `Topic` того же
  `subject_code` и `grade`.
