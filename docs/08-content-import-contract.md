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
- `source_id` (string): source/system identifier for deterministic IDs.
- `contract_version` (string): must start with `v1`.
  - `v1.0/v1.1`: strict mode (любой `errors[]` => `status=failed`).
  - `v1.2`: entity-level isolation for `tests/questions`.
- `validate_only` (bool, default `false`):
  - `true`: validate and predict changes only, no persistence.
  - `false`: apply upsert changes.
- `error_mode` (`collect|fail_fast`, default `collect`):
  - `collect`: return all found validation/domain issues.
  - `fail_fast`: return only the first issue.
- `payload` (object): import content body.

### Payload entities
- `subjects[]`: `code`, `name`
- `topics[]`: `code`, `subject_code`, `grade`, `name`
- `micro_skills[]`: `node_id`, `subject_code`, `grade`, `section_code`, `section_name`,
  `topic_code`, `micro_skill_name`, `predecessor_ids[]`, `criticality`, `source_ref`,
  `description?`, `status?`, `external_ref?`
- `tests[]`: `external_id`, `subject_code`, `grade`, `questions[]`
- `questions[]`: `external_id`, `node_id`, `text`, `answer_key`, `max_score`

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
- `validated`: `validate_only=true`, payload is valid, nothing applied.
- `validated_with_errors`: `validate_only=true`, `v1.2`, часть test entities невалидна.
- `completed`: apply mode succeeded.
- `completed_with_errors`: apply mode, `v1.2`, валидные entities применены, невалидные пропущены.

## Error model
`errors[]` contains:
- `code`: machine-readable issue code.
- `message`: human-readable explanation.
- `path`: payload path.

Known codes:
- `UNSUPPORTED_CONTRACT_VERSION`
- `DUPLICATE_IDENTIFIER`
- `UNKNOWN_REFERENCE`
- `CYCLE_DETECTED`
- `TOPIC_MISMATCH`
- `ENTITY_VALIDATION_FAILED`

## Domain rules currently enforced
- Unique IDs in payload sections.
- All references (`subject_code`, `node_id`, `predecessor_ids`) must be resolvable from
  existing data or current payload.
- Predecessor graph must be acyclic.
- Re-import of unchanged entities is idempotent (`imported = 0`).
- `v1.2`: invalid test/question entities do not abort entire import; reported per-entity in `errors[]`.

## Notes
- Test and question IDs are deterministic (`uuid5`) from `source_id + external_id`.
- `details` reports only actual changes (`created/updated`), not scanned entities.
- `details.tests_failed` and `details.questions_failed` report skipped invalid entities for `v1.2`.
- For micro-skills, `version`/`created_at`/`updated_at` are server-managed metadata.

## Fixtures Cleanup
Endpoint: `POST /v1/admin/fixtures/cleanup`

Назначение: очистка тестовых фикстур (`math_v0xx*`, `MV0xx*`) без ручных SQL.

Request:
```json
{
  "dry_run": true,
  "subject_code_patterns": ["^math_v\\d{2}.*$"],
  "topic_code_patterns": ["^MV\\d{2}.*$"],
  "node_id_patterns": ["^MV\\d{2}.*$"]
}
```

- `dry_run=true` — только план удаления (`status=planned`).
- `dry_run=false` — фактическое удаление (`status=completed`).
- В ответе возвращаются `matched` и `deleted` счётчики по `subjects/topics/micro_skills/tests/questions/assignments/attempts/answers`.

## Nightly Import Check (CI)
- workflow: `.github/workflows/nightly-import-check.yml`
- сценарий: nightly `validate_only=true` запрос к `/v1/admin/content/import`
- цель: ранняя проверка совместимости import-контракта с продовым стендом.
