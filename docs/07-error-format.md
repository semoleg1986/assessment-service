# Формат Ошибок (RFC 7807)

Assessment Service возвращает ошибки как `application/problem+json`.

## Пример
```json
{
  "type": "https://example.com/problems/invariant-violation",
  "title": "Invariant Violation",
  "status": 409,
  "detail": "Attempt can be submitted only from started status",
  "instance": "/v1/attempts/7f7b8e4a-0a84-4b8a-a4a2-0fb0c58f4b55/submit",
  "request_id": "3e748ced-d50a-4c5a-8b6f-1f2f7fe8b1b5"
}
```

## Поля
- `type`
- `title`
- `status`
- `detail`
- `instance`
- `request_id`
