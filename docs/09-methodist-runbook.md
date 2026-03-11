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

### Шаг B — Apply (запись в БД)

Повтори import с тем же payload:

- `validate_only = false`

Ожидаемые статусы:

- `completed`
- `completed_with_errors` (часть сущностей пропущена, детали в `errors[]`).

### Шаг C — Idempotency check

Повтори тот же apply ещё раз:

- ожидаемо `imported = 0`.

## 3. Cleanup test fixtures

Для чистки тестовых данных (`math_v0xx*`, `MV0xx*`) используй:

1. Dry-run (`dry_run=true`) — сначала только план.
2. Apply (`dry_run=false`) — фактическое удаление.

Ориентир в ответе:

- `matched` — сколько найдено.
- `deleted` — сколько реально удалено.

## 4. Проверки после apply

### 4.1 Assessment catalog

Проверь, что новые сущности видны:

- `GET /v1/admin/subjects`
- `GET /v1/admin/topics`
- `GET /v1/admin/micro-skills`
- `GET /v1/admin/tests`

### 4.2 Связь с user-children-service

Проверь, что child-контур доступен и админ видит данные:

- `GET /v1/admin/users`
- `GET /v1/admin/users/{user_id}/children`
- `GET /v1/admin/audit/events`

## 5. Частые ошибки

- `UNKNOWN_REFERENCE` — ссылка на несуществующий `subject/topic/node`.
- `CYCLE_DETECTED` — цикл в `predecessor_ids`.
- `TOPIC_MISMATCH` — `topic_code` не соответствует `subject_code/grade`.
- `ENTITY_VALIDATION_FAILED` — ошибка в одной test/question-сущности.

Правило: в `v1.2` ошибки по `tests/questions` не валят весь импорт, но должны быть разобраны до релиза контента.

## 6. Минимальный релизный чек-лист

1. `validate_only=true` прошёл (`validated`/`validated_with_errors` с понятными причинами).
2. apply завершился (`completed`/`completed_with_errors`).
3. повторный apply дал `imported=0`.
4. `admin-web` показывает новые данные в `Assessment`/`Content Ops`.
5. smoke e2e зелёный.
