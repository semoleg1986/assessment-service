# Доменная Модель

## Агрегаты
- Test (Aggregate Root)
  - Поля: `test_id`, `subject_id`, `grade`, `status`, `version`, `created_at`, `updated_at`.
  - Содержит: `Question[*]`.

- Assignment (Aggregate Root)
  - Поля: `assignment_id`, `child_id`, `test_id`, `status`, `assigned_at`, `expires_at`, `version`.
  - Статусы: `assigned | started | completed | expired | cancelled`.

- Attempt (Aggregate Root)
  - Поля: `attempt_id`, `assignment_id`, `child_id`, `status`, `started_at`, `submitted_at`, `score`, `version`.
  - Содержит: `Answer[*]`.
  - Статусы: `started | submitted | cancelled`.

## Сущности
- Question: `question_id`, `type`, `prompt`, `options`, `correct_answer`, `max_score`, `topic_id`, `micro_skill_id`.
- Answer: `answer_id`, `question_id`, `value`, `is_correct`, `awarded_score`.

## Value Objects
- SignalLevel: `norm | risk | gap | critical_gap`.
- GradeLevel: `1 | 2 | 3 | 4`.

## Инварианты
- Assignment ссылается на существующего ребенка и тест.
- Для одного assignment только одна активная attempt.
- Отправка попытки разрешена только из `started`.
- Итоговый score детерминированно считается из ответов и весов вопросов.
