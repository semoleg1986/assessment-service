# assessment-service

Сервис диагностики учебных достижений (Learning Assessment context) для 1-4 классов.

## Назначение
`assessment-service` отвечает за:
- структуру тестов (предметы, темы, микро-умения, вопросы)
- назначения тестов детям
- жизненный цикл попыток прохождения
- расчет результата и сигналов пробелов
- базовые рекомендации для коррекции

## Что в зоне ответственности
- `Test`
- `Assignment`
- `Attempt`
- `Question`
- `Answer`
- сигналы: `norm | risk | gap | critical_gap`

## Что вне зоны ответственности
- аутентификация и выпуск JWT (`auth-service`)
- владение профилем ребенка (`user-children-service`)
- доставка уведомлений (`notification-service`)
- UI/BFF-оркестрация (`user-web`, `admin-web`, `admin-bff`)

## Документация
- Архитектура и домен:
  - `/Users/olegsemenov/Programming/monitoring/assessment-service/docs/00-vision.md`
  - `/Users/olegsemenov/Programming/monitoring/assessment-service/docs/01-context-and-scope.md`
  - `/Users/olegsemenov/Programming/monitoring/assessment-service/docs/02-ubiquitous-language.md`
  - `/Users/olegsemenov/Programming/monitoring/assessment-service/docs/03-actors-and-use-cases.md`
  - `/Users/olegsemenov/Programming/monitoring/assessment-service/docs/04-domain-model.md`
  - `/Users/olegsemenov/Programming/monitoring/assessment-service/docs/05-invariants-and-policies.md`
  - `/Users/olegsemenov/Programming/monitoring/assessment-service/docs/06-application-layer.md`
  - `/Users/olegsemenov/Programming/monitoring/assessment-service/docs/07-error-format.md`

- Диаграммы (PlantUML):
  - `/Users/olegsemenov/Programming/monitoring/assessment-service/docs/diagrams/context.puml`
  - `/Users/olegsemenov/Programming/monitoring/assessment-service/docs/diagrams/architecture.puml`
  - `/Users/olegsemenov/Programming/monitoring/assessment-service/docs/diagrams/domain-model.puml`

## Целевой MVP API (план)
- Admin knowledge graph:
  - `POST /v1/admin/subjects`
  - `GET /v1/admin/subjects`
  - `POST /v1/admin/topics`
  - `GET /v1/admin/topics`
  - `POST /v1/admin/micro-skills`
  - `POST /v1/admin/micro-skills/{node_id}/links`
  - `GET /v1/admin/micro-skills`
- Assessment flow:
- `POST /v1/tests`
- `GET /v1/tests`
- `POST /v1/assignments`
- `GET /v1/user/assignments/{child_id}`
- `POST /v1/attempts/start`
- `POST /v1/attempts/{attempt_id}/submit`

Важно:
- при создании теста каждый вопрос обязан ссылаться на `node_id` существующего `MicroSkill`.

## Интеграции
- `auth-service`: идентификация актора и роли.
- `user-children-service`: проверка ребенка и принадлежности.
- `user-web`/`admin-web`: чтение/запись через BFF API.

## Статус
- Домен и архитектурные документы готовы.
- Реализован MVP-каркас сервиса (in-memory + Postgres persistence при наличии `DATABASE_URL`):
  - `POST /v1/admin/subjects`
  - `GET /v1/admin/subjects`
  - `POST /v1/admin/topics`
  - `GET /v1/admin/topics`
  - `POST /v1/admin/micro-skills`
  - `POST /v1/admin/micro-skills/{node_id}/links`
  - `GET /v1/admin/micro-skills`
  - `POST /v1/tests`
  - `GET /v1/tests`
  - `POST /v1/assignments`
  - `POST /v1/admin/tests`
  - `GET /v1/admin/tests`
  - `POST /v1/admin/tests/{test_id}/publish`
  - `POST /v1/admin/assignments`
  - `GET /v1/user/children/{child_id}/assignments`
  - `POST /v1/user/assignments/{assignment_id}/start`
  - `POST /v1/user/attempts/{attempt_id}/answers`
  - `POST /v1/user/attempts/{attempt_id}/submit`
  - `GET /v1/user/attempts/{attempt_id}/result`
  - `GET /v1/admin/diagnostics/children/{child_id}`
  - `POST /v1/admin/content/import`
  - `POST /v1/attempts/start`
  - `POST /v1/attempts/{attempt_id}/submit`
  - `GET /v1/attempts/{attempt_id}`
- Тесты: `6 passed`.

## Локальный запуск MVP
```bash
cd /Users/olegsemenov/Programming/monitoring/assessment-service
make install
make db-upgrade
make run
```

Health:
- `GET http://localhost:8003/healthz`

## Интеграционные тесты (Postgres)
Проверяют сценарий:
- `alembic upgrade head`
- `seed_mvp_content.py --profile prod-min`
- повторный `upgrade + seed` (эмуляция restart, проверка idempotency)

Запуск:

```bash
cd /Users/olegsemenov/Programming/monitoring/assessment-service
make test-integration
```

Требования:
- локально доступен Docker daemon
- доступен образ `postgres:16`
- в окружении установлен `psycopg`

## Запуск в Docker
```bash
cd /Users/olegsemenov/Programming/monitoring/assessment-service
cp .env.example .env
make docker-up
```

Если используется Postgres, при запуске Docker-контейнера миграции применяются автоматически
(`AUTO_MIGRATE_ON_START=true` по умолчанию). Параметры ретраев:
- `MIGRATION_MAX_RETRIES`
- `MIGRATION_RETRY_DELAY`

Минимальная observability:
- при старте контейнера entrypoint пишет metric-логи миграций:
  - `metric=assessment_migration_runs_total status=started|succeeded|failed`
- HTTP middleware добавляет/пробрасывает `x-request-id` и пишет request-логи:
  - `request_completed ... request_id=<id>`
  - `request_failed ... request_id=<id>`
- seed-скрипт пишет metric-логи:
  - `metric=assessment_seed_runs_total status=started|succeeded|failed`

Ручной запуск миграций (опционально):

```bash
cd /Users/olegsemenov/Programming/monitoring/assessment-service
make db-upgrade
```

Заполнить стартовый контент (idempotent):

```bash
cd /Users/olegsemenov/Programming/monitoring/assessment-service
make seed-mvp
```

Профили seed:
- `prod-min` (по умолчанию) — минимальный боевой набор.
- `demo` — расширенный demo-набор (требует явного подтверждения вне dev/local).

Примеры:

```bash
python scripts/seed_mvp_content.py --profile prod-min
python scripts/seed_mvp_content.py --profile demo --confirm-demo
```

Для already-running Docker контейнера используйте:

```bash
docker exec -it assessment-service python -m scripts.seed_mvp_content --profile prod-min
```

Проверка:
```bash
curl -i http://localhost:8003/healthz
```
