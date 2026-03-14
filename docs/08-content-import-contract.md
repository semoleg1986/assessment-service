# Content Import Contract v1.2

Endpoint: `POST /v1/admin/content/import`

## Request

```json
{
  "source_id": "partner-x",
  "contract_version": "v1.2",
  "validate_only": false,
  "error_mode": "collect",
  "payload": {
    "subjects": [],
    "topics": [],
    "micro_skills": [],
    "tests": []
  }
}
```

### Top-level fields

- `source_id` (string): identifier of source system, used for deterministic IDs.
- `contract_version` (string): must start with `v1`.
  - `v1.0/v1.1`: strict mode (любая ошибка => `status=failed`).
  - `v1.2`: entity-level isolation для `tests/questions`.
- `validate_only` (bool, default `false`):
  - `true`: validate only (no DB write)
  - `false`: apply upsert
- `error_mode` (`collect|fail_fast`, default `collect`)
- `payload` (object): entities for import.

## Payload entities

- `subjects[]`:
  - `code`, `name`
- `topics[]`:
  - `code`, `subject_code`, `grade`, `name`
- `micro_skills[]`:
  - `node_id`, `subject_code`, `topic_code`, `grade`
  - `section_code`, `section_name`, `micro_skill_name`
  - `predecessor_ids[]`, `criticality`, `source_ref`
  - optional: `description`, `status`, `external_ref`
- `tests[]`:
  - `external_id`, `subject_code`, `grade`, `questions[]`
- `questions[]`:
  - required: `external_id`, `node_id`, `text`, `question_type`, `max_score`
  - for `question_type=text`:
    - `answer_key`
    - optional `text_distractors[]`
  - for `question_type=single_choice`:
    - `correct_option_id`
    - `options[]` (min 2)

### `questions[].options[]`

- `option_id` (string)
- `text` (string)
- `position` (int, `>=1`)
- `diagnostic_tag` (nullable):
  - `inattention | misread_condition | calc_error | concept_gap | guessing | other`

### `questions[].text_distractors[]`

- `pattern` (string)
- `match_mode`:
  - `exact | normalized | regex`
- `diagnostic_tag`:
  - `inattention | misread_condition | calc_error | concept_gap | guessing | other`

## Response

```json
{
  "import_id": "uuid",
  "source_id": "partner-x",
  "imported": 4,
  "status": "completed",
  "errors": [],
  "warnings": [],
  "details": {
    "subjects_created": 1,
    "subjects_updated": 0,
    "topics_created": 1,
    "topics_updated": 0,
    "micro_skills_created": 1,
    "micro_skills_updated": 0,
    "tests_created": 1,
    "tests_updated": 0,
    "tests_failed": 0,
    "questions_failed": 0
  }
}
```

### Status values

- `failed`: validation/domain errors detected, nothing applied.
- `validated`: `validate_only=true`, payload fully valid.
- `validated_with_errors`: `validate_only=true`, `v1.2`, часть test entities невалидна.
- `completed`: apply mode succeeded.
- `completed_with_errors`: apply mode, `v1.2`, валидные entities применены, невалидные пропущены.

## Error model

`errors[]` item:

- `code`
- `message`
- `path`

Known codes:

- `UNSUPPORTED_CONTRACT_VERSION`
- `DUPLICATE_IDENTIFIER`
- `UNKNOWN_REFERENCE`
- `CYCLE_DETECTED`
- `TOPIC_MISMATCH`
- `ENTITY_VALIDATION_FAILED`

## Validation rules (current)

- Unique identifiers inside each payload section.
- References must be resolvable from DB state + current payload:
  - `subject_code`, `topic_code`, `node_id`, `predecessor_ids`
- `predecessor_ids` graph must be acyclic.
- `question_type=text` requires `answer_key`.
- `question_type=single_choice` requires:
  - `options.length >= 2`
  - unique `option_id`
  - valid `correct_option_id`
  - correct option `diagnostic_tag = null`
- Re-import of unchanged entities is idempotent (`imported=0`).

## v1.2 entity-level isolation

- Invalid `tests/questions` do not abort entire import.
- Errors are returned per-entity in `errors[]`.
- Counters:
  - `details.tests_failed`
  - `details.questions_failed`

## Notes

- Test and question IDs are deterministic (`uuid5`) from `source_id + external_id`.
- `details.*_created/*_updated` count only actual state changes.
- `version/created_at/updated_at` for micro-skills are managed by server.

## Fixtures Cleanup

Endpoint: `POST /v1/admin/fixtures/cleanup`

Назначение: безопасная очистка тестовых фикстур (`math_v0xx*`, `MV0xx*`) без ручных SQL.

Request:

```json
{
  "dry_run": true,
  "subject_code_patterns": ["^math_v\\d{2}.*$"],
  "topic_code_patterns": ["^MV\\d{2}.*$"],
  "node_id_patterns": ["^MV\\d{2}.*$"]
}
```

- `dry_run=true`: только план удаления (`status=planned`).
- `dry_run=false`: фактическое удаление (`status=completed`).
- В ответе есть `matched` и `deleted` по сущностям:
  - `subjects/topics/micro_skills/tests/questions/assignments/attempts/answers`.

## Nightly Import Check (CI)

- workflow: `.github/workflows/nightly-import-check.yml`
- сценарий: nightly `validate_only=true` запрос к `/v1/admin/content/import`
- цель: ранняя проверка совместимости import-контракта с продовым стендом.
