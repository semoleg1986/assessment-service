# Доменная Модель

Контракт доменной модели сервиса `assessment-service`. Документ синхронизирован с текущим `main`.

## Агрегаты

### 1. AssessmentTest (Aggregate Root)

- Поля:
  - `test_id: UUID`
  - `subject_code: str`
  - `grade: int`
  - `questions: list[Question]`
  - `created_at: datetime`
  - `version: int`
- Инварианты:
  - тест содержит минимум один вопрос
  - `grade` в диапазоне `1..4`
  - каждый `question` проходит собственную валидацию

### 2. AssignmentAggregate (Aggregate Root)

- Поля:
  - `assignment_id: UUID`
  - `test_id: UUID`
  - `child_id: UUID`
  - `status: assigned | started | completed | expired | cancelled`
  - `assigned_at: datetime`
  - `version: int`
- Поведение:
  - `mark_started()`
  - `mark_completed()`

### 3. AttemptAggregate (Aggregate Root)

- Поля:
  - `attempt_id: UUID`
  - `assignment_id: UUID`
  - `child_id: UUID`
  - `status: started | submitted | cancelled`
  - `started_at: datetime`
  - `submitted_at: datetime | None`
  - `score: int`
  - `answers: list[Answer]`
  - `version: int`
- Поведение:
  - `submit(answers)`
- Инварианты:
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
- `question_type: text | single_choice`
- `answer_key: str | None`
- `correct_option_id: str | None`
- `options: list[QuestionOption]`
- `text_distractors: list[TextDistractor]`
- `max_score: int`

### QuestionOption

- `option_id: str`
- `text: str`
- `position: int`
- `diagnostic_tag: DiagnosticTag | None`

### TextDistractor

- `pattern: str`
- `match_mode: exact | normalized | regex`
- `diagnostic_tag: DiagnosticTag`

### Answer

- `question_id: UUID`
- `value: str | None`
- `selected_option_id: str | None`
- `resolved_diagnostic_tag: DiagnosticTag | None`
- `is_correct: bool`
- `awarded_score: int`

## Value Objects

- `AssignmentStatus`: `assigned | started | completed | expired | cancelled`
- `AttemptStatus`: `started | submitted | cancelled`
- `CriticalityLevel`: `low | medium | high`
- `MicroSkillStatus`: `draft | active | archived`
- `QuestionType`: `text | single_choice`
- `DiagnosticTag`: `inattention | misread_condition | calc_error | concept_gap | guessing | other`
- `TextMatchMode`: `exact | normalized | regex`

## Ключевые инварианты

- Assignment ссылается на существующие `child_id` и `test_id` (проверка в application/integration).
- Для одного assignment только одна активная attempt.
- Итоговый `score` детерминированно считается как сумма `awarded_score` ответов.
- `MicroSkillNode.topic_code` должен ссылаться на существующую `Topic` того же `subject_code` и `grade`.
- Для `Question.question_type=text`:
  - обязателен `answer_key`
  - запрещены `options` и `correct_option_id`
- Для `Question.question_type=single_choice`:
  - минимум 2 варианта в `options`
  - `option_id` уникальны в рамках вопроса
  - `position` уникальны и `>= 1`
  - `correct_option_id` обязан ссылаться на существующий `option_id`
  - `diagnostic_tag` у правильного варианта должен быть `null`
