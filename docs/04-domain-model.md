# Доменная Модель

Контракт Domain Layer сервиса `assessment-service` в текущей контекстной структуре.

## Структура Domain

```shell
src/domain/
├── content/
│   ├── subject/{entity,repository}.py
│   ├── topic/{entity,repository}.py
│   ├── micro_skill/{entity,policies,repository}.py
│   └── test/{entity,question,question_option,text_distractor,repository}.py
├── delivery/
│   ├── assignment/{entity,repository}.py
│   └── attempt/{entity,answer,repository}.py
├── shared/{questions,statuses}.py
└── errors.py
```

## Контекст `content`

### `AssessmentTest` (Aggregate Root)

- Поля: `test_id`, `subject_code`, `grade`, `questions`, `created_at`, `version`.
- Поведение:
  - `validate()` — проверка инвариантов;
  - `revise(...)` — ревизия контента + `version += 1`.
- Инварианты:
  - минимум 1 вопрос;
  - `grade` в диапазоне `1..4`;
  - каждый `Question` валиден.

### `MicroSkillNode` (Aggregate Root)

- Поля: `node_id`, `subject_code`, `topic_code`, `grade`, разделы, `predecessor_ids`,
  `criticality`, `status`, `description`, `external_ref`, `version`, timestamps.
- Поведение:
  - `update_details(...)` — обновление метаданных с контрольным `changed`;
  - `relink_predecessors(...)` — изменение зависимостей узла.
- Политики:
  - `micro_skill/policies.py` проверяет граф зависимостей (включая cycle detection).

### `Subject`, `Topic`

- Простые доменные сущности справочников контента.

### `Question` + дочерние объекты

- `Question` поддерживает типы:
  - `text`;
  - `single_choice`.
- `QuestionOption` — вариант выбора для `single_choice`.
- `TextDistractor` — шаблон ошибок для text-ответа:
  - `match_mode: exact | normalized | regex`;
  - `diagnostic_tag`.

## Контекст `delivery`

### `AssignmentAggregate` (Aggregate Root)

- Поля: `assignment_id`, `test_id`, `child_id`, `status`, `assigned_at`, `version`.
- Поведение: `mark_started()`, `mark_completed()`.

### `AttemptAggregate` (Aggregate Root)

- Поля: `attempt_id`, `assignment_id`, `child_id`, `status`, `started_at`,
  `submitted_at`, `score`, `answers`, `version`.
- Поведение:
  - `save_answers(...)` — сохраняет черновик ответов при `status=started`;
  - `submit(...)` — завершает попытку, фиксирует score и `submitted_at`.

### `Answer`

- Поля:
  - `question_id`, `value`, `selected_option_id`, `resolved_diagnostic_tag`,
    `is_correct`, `awarded_score`.

## Value Objects / Enums (`src/domain/shared/*`)

- `AssignmentStatus`: `assigned | started | completed | expired | cancelled`
- `AttemptStatus`: `started | submitted | cancelled`
- `CriticalityLevel`: `low | medium | high`
- `MicroSkillStatus`: `draft | active | archived`
- `QuestionType`: `text | single_choice`
- `DiagnosticTag`: `inattention | misread_condition | calc_error | concept_gap | guessing | other`
- `TextMatchMode`: `exact | normalized | regex`

## Ключевые инварианты

1. Для `Question(question_type=text)` обязателен `answer_key`, запрещены `options/correct_option_id`.
2. Для `Question(question_type=single_choice)`:
   - минимум 2 `options`;
   - уникальные `option_id` и `position >= 1`;
   - `correct_option_id` обязан ссылаться на существующий `option_id`;
   - у правильного варианта `diagnostic_tag` должен быть `null`.
3. `AttemptAggregate.submit()` и `save_answers()` разрешены только из `started`.
4. Итоговый `score` считается детерминированно как сумма `awarded_score`.
5. Domain Layer изолирован от HTTP/SQLAlchemy/FastAPI.
