# Методист — Runbook (Content Ops)

Документ для ежедневной работы методиста/контент-менеджера с контентом диагностики.

## 1. Что должно быть запущено

- `auth-service` (`:8000`)
- `user-children-service` (`:8001`)
- `assessment-service` (`:8003`)
- `admin-web` (`:3001`)

Быстрая проверка:

```bash
curl -i http://127.0.0.1:8000/healthz
curl -i http://127.0.0.1:8001/healthz
curl -i http://127.0.0.1:8003/healthz
curl -I http://127.0.0.1:3001
```

## 2. Рабочий цикл методиста

### Шаг A — Validate (без записи в БД)

В `admin-web` открой `Content Ops` и отправь import с:

- `contract_version = v1.2`
- `validate_only = true`

Ожидаемые статусы:

- `validated` — всё валидно.
- `validated_with_errors` — часть `tests/questions` невалидна (entity-level isolation в `v1.2`).

Перед apply обязательно проверь `errors[]` и `details.tests_failed/questions_failed`.

### Шаг B — Apply (запись в БД)

Повтори import с тем же payload:

- `validate_only = false`

Ожидаемые статусы:

- `completed`
- `completed_with_errors` (часть сущностей пропущена, детали в `errors[]`).

### Шаг C — Idempotency check

Повтори тот же apply ещё раз:

- ожидаемо `imported = 0`.

## 3. Формирование вопросов (v1.2)

### `text` question

- Обязательные поля:
  - `question_type = text`
  - `answer_key`
- Опционально:
  - `text_distractors[]` для классификации типовых ошибок.

### `single_choice` question

- Обязательные поля:
  - `question_type = single_choice`
  - `options[]` (минимум 2)
  - `correct_option_id`
- Ограничения:
  - `option_id` должны быть уникальны
  - `correct_option_id` должен ссылаться на один из `option_id`
  - у правильной опции `diagnostic_tag` должен быть пустым (`null`)

### Минимальный пример payload-фрагмента

```json
{
  "tests": [
    {
      "external_id": "math-check-1",
      "subject_code": "math",
      "grade": 2,
      "questions": [
        {
          "external_id": "q-text-1",
          "node_id": "MATH-ADD-01",
          "text": "2 + 2 = ?",
          "question_type": "text",
          "answer_key": "4",
          "text_distractors": [
            {
              "pattern": "5",
              "match_mode": "exact",
              "diagnostic_tag": "calc_error"
            }
          ],
          "max_score": 1
        },
        {
          "external_id": "q-choice-1",
          "node_id": "MATH-ADD-02",
          "text": "Выбери правильный ответ: 3 + 2",
          "question_type": "single_choice",
          "correct_option_id": "B",
          "options": [
            { "option_id": "A", "text": "4", "position": 1, "diagnostic_tag": "calc_error" },
            { "option_id": "B", "text": "5", "position": 2, "diagnostic_tag": null },
            { "option_id": "C", "text": "6", "position": 3, "diagnostic_tag": "inattention" }
          ],
          "max_score": 1
        }
      ]
    }
  ]
}
```

## 4. Cleanup test fixtures

Для чистки тестовых данных (`math_v0xx*`, `MV0xx*`) используй:

1. Dry-run (`dry_run=true`) — сначала только план.
2. Apply (`dry_run=false`) — фактическое удаление.

Ориентир в ответе:

- `matched` — сколько найдено.
- `deleted` — сколько реально удалено.

## 5. Проверки после apply

### 5.1 Assessment catalog

Проверь, что новые сущности видны:

- `GET /v1/admin/subjects`
- `GET /v1/admin/topics`
- `GET /v1/admin/micro-skills`
- `GET /v1/admin/tests`

### 5.2 Связь с user-children-service

Проверь, что child-контур доступен и админ видит данные:

- `GET /v1/admin/users`
- `GET /v1/admin/users/{user_id}/children`
- `GET /v1/admin/audit/events`

## 6. Частые ошибки

- `UNKNOWN_REFERENCE` — ссылка на несуществующий `subject/topic/node`.
- `CYCLE_DETECTED` — цикл в `predecessor_ids`.
- `TOPIC_MISMATCH` — `topic_code` не соответствует `subject_code/grade`.
- `ENTITY_VALIDATION_FAILED` — ошибка в одной test/question-сущности.

Правило: в `v1.2` ошибки по `tests/questions` не валят весь импорт, но должны быть разобраны до релиза контента.

## 7. Минимальный релизный чек-лист

1. `validate_only=true` прошёл (`validated`/`validated_with_errors` с понятными причинами).
2. apply завершился (`completed`/`completed_with_errors`).
3. повторный apply дал `imported=0`.
4. `admin-web` показывает новые данные в `Assessment`/`Content Ops`.
5. smoke e2e зелёный.
