from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _build_operation_id(path: str, method: str) -> str:
    raw_segments = [segment for segment in path.split("/") if segment]
    resource_parts: list[str] = []
    param_parts: list[str] = []
    for segment in raw_segments:
        if re.fullmatch(r"v\d+", segment):
            continue
        if segment.startswith("{") and segment.endswith("}"):
            param_parts.append(_to_pascal(segment[1:-1]))
            continue
        resource_parts.append(_to_pascal(segment))

    stem = "".join(resource_parts) or "Root"
    operation_id = f"{method.lower()}{stem}"
    if param_parts:
        operation_id += f"By{'And'.join(param_parts)}"
    return operation_id


def _to_pascal(value: str) -> str:
    parts = re.split(r"[^a-zA-Z0-9]+", value)
    normalized = [part for part in parts if part]
    if not normalized:
        return "Value"
    return "".join(part[:1].upper() + part[1:] for part in normalized)


def _looks_auto_operation_id(operation_id: str | None, method: str) -> bool:
    if not operation_id:
        return True
    method_suffix = f"_{method.lower()}"
    return (
        "__" in operation_id
        or "_v1_" in operation_id
        or operation_id.endswith(method_suffix)
    )


def _resolve_ref(schema: dict[str, Any], spec: dict[str, Any]) -> dict[str, Any] | None:
    ref = schema.get("$ref")
    if not isinstance(ref, str) or not ref.startswith("#/components/schemas/"):
        return None
    name = ref.split("/")[-1]
    components = spec.get("components")
    if not isinstance(components, dict):
        return None
    schemas = components.get("schemas")
    if not isinstance(schemas, dict):
        return None
    candidate = schemas.get(name)
    if not isinstance(candidate, dict):
        return None
    return candidate


def _example_from_schema(
    schema: dict[str, Any] | None,
    spec: dict[str, Any],
    *,
    depth: int = 0,
    seen_refs: set[str] | None = None,
) -> Any:
    if schema is None:
        return None
    if depth > 5:
        return None
    if seen_refs is None:
        seen_refs = set()

    if "$ref" in schema:
        ref = schema.get("$ref")
        if not isinstance(ref, str) or ref in seen_refs:
            return None
        target = _resolve_ref(schema, spec)
        if target is None:
            return None
        return _example_from_schema(
            target,
            spec,
            depth=depth + 1,
            seen_refs=seen_refs | {ref},
        )

    for key in ("oneOf", "anyOf", "allOf"):
        variants = schema.get(key)
        if isinstance(variants, list) and variants:
            for variant in variants:
                if not isinstance(variant, dict):
                    continue
                candidate = _example_from_schema(
                    variant,
                    spec,
                    depth=depth + 1,
                    seen_refs=seen_refs,
                )
                if candidate is not None:
                    return candidate

    if "enum" in schema and isinstance(schema["enum"], list) and schema["enum"]:
        return schema["enum"][0]

    schema_type = schema.get("type")
    if schema_type == "object" or (
        not schema_type and isinstance(schema.get("properties"), dict)
    ):
        properties = schema.get("properties")
        if not isinstance(properties, dict):
            additional = schema.get("additionalProperties")
            if isinstance(additional, dict):
                value = _example_from_schema(
                    additional,
                    spec,
                    depth=depth + 1,
                    seen_refs=seen_refs,
                )
                return {"key": value if value is not None else "value"}
            return {}
        example: dict[str, Any] = {}
        required = schema.get("required")
        required_set = set(required) if isinstance(required, list) else set(properties)
        for name, prop in properties.items():
            if name not in required_set and len(example) >= 5:
                continue
            if not isinstance(prop, dict):
                continue
            value = _example_from_schema(
                prop,
                spec,
                depth=depth + 1,
                seen_refs=seen_refs,
            )
            if value is None:
                continue
            example[name] = value
        return example

    if schema_type == "array":
        items = schema.get("items")
        if isinstance(items, dict):
            value = _example_from_schema(
                items,
                spec,
                depth=depth + 1,
                seen_refs=seen_refs,
            )
            if value is not None:
                return [value]
        return []

    if schema_type == "boolean":
        return True
    if schema_type == "integer":
        minimum = schema.get("minimum")
        if isinstance(minimum, int):
            return minimum
        return 1
    if schema_type == "number":
        minimum = schema.get("minimum")
        if isinstance(minimum, (int, float)):
            return minimum
        return 1
    if schema_type == "string" or schema_type is None:
        fmt = schema.get("format")
        if fmt == "uuid":
            return "00000000-0000-4000-8000-000000000000"
        if fmt == "date-time":
            return "2026-03-13T00:00:00Z"
        return "string"
    return None


def _add_example_to_content(content: Any, spec: dict[str, Any]) -> None:
    if not isinstance(content, dict):
        return
    for media_type in ("application/json", "application/problem+json"):
        media = content.get(media_type)
        if not isinstance(media, dict):
            continue
        if "example" in media or "examples" in media:
            continue
        schema = media.get("schema")
        if not isinstance(schema, dict):
            continue
        example = _example_from_schema(schema, spec)
        if example is not None:
            media["example"] = example


def _ensure_content_examples(spec: dict[str, Any]) -> None:
    for path_item in spec.get("paths", {}).values():
        if not isinstance(path_item, dict):
            continue
        for operation in path_item.values():
            if not isinstance(operation, dict):
                continue
            request_body = operation.get("requestBody")
            if isinstance(request_body, dict):
                _add_example_to_content(request_body.get("content"), spec)
            responses = operation.get("responses")
            if not isinstance(responses, dict):
                continue
            for status_code in ("200", "201", "202"):
                response = responses.get(status_code)
                if isinstance(response, dict):
                    _add_example_to_content(response.get("content"), spec)


def _harden_contract(spec: dict[str, Any], *, local_port: int) -> dict[str, Any]:
    info = spec.setdefault("info", {})
    info["version"] = os.getenv("OPENAPI_INFO_VERSION", "v0.3.1")

    spec["servers"] = [
        {"url": f"http://localhost:{local_port}", "description": "Local"},
        {
            "url": os.getenv("OPENAPI_SERVER_URL", "https://api.monitoring.example"),
            "description": "Production",
        },
    ]

    components = spec.setdefault("components", {})
    security_schemes = components.setdefault("securitySchemes", {})
    security_schemes["bearerAuth"] = {
        "type": "http",
        "scheme": "bearer",
        "bearerFormat": "JWT",
    }

    schemas = components.setdefault("schemas", {})
    schemas.setdefault(
        "ProblemDetails",
        {
            "type": "object",
            "title": "ProblemDetails",
            "required": ["type", "title", "status"],
            "properties": {
                "type": {"type": "string"},
                "title": {"type": "string"},
                "status": {"type": "integer"},
                "detail": {"type": "string"},
                "instance": {"type": "string"},
                "request_id": {"type": "string"},
                "code": {"type": "string"},
            },
        },
    )

    responses = components.setdefault("responses", {})
    responses["Unauthorized"] = {
        "description": "Unauthorized",
        "content": {
            "application/problem+json": {
                "schema": {"$ref": "#/components/schemas/ProblemDetails"},
                "example": {
                    "type": "https://example.com/problems/authentication",
                    "title": "Unauthorized",
                    "status": 401,
                    "detail": "Bearer access token is required",
                    "code": "UNAUTHORIZED",
                    "request_id": "00000000-0000-4000-8000-000000000000",
                },
            }
        },
    }
    responses["Forbidden"] = {
        "description": "Forbidden",
        "content": {
            "application/problem+json": {
                "schema": {"$ref": "#/components/schemas/ProblemDetails"},
                "example": {
                    "type": "https://example.com/problems/access-denied",
                    "title": "Forbidden",
                    "status": 403,
                    "detail": "Access denied",
                    "code": "FORBIDDEN",
                    "request_id": "00000000-0000-4000-8000-000000000000",
                },
            }
        },
    }
    responses["TooManyRequests"] = {
        "description": "Too Many Requests",
        "content": {
            "application/problem+json": {
                "schema": {"$ref": "#/components/schemas/ProblemDetails"},
                "example": {
                    "type": "https://example.com/problems/too-many-requests",
                    "title": "Too Many Requests",
                    "status": 429,
                    "detail": "Rate limit exceeded",
                    "code": "RATE_LIMITED",
                    "request_id": "00000000-0000-4000-8000-000000000000",
                },
            }
        },
    }

    spec["security"] = [{"bearerAuth": []}]
    public_operations = {
        ("/healthz", "get"),
        ("/readyz", "get"),
    }

    for path, path_item in spec.get("paths", {}).items():
        if not isinstance(path_item, dict):
            continue
        for method, operation in path_item.items():
            if method.startswith("x-") or not isinstance(operation, dict):
                continue

            operation_id = operation.get("operationId")
            if _looks_auto_operation_id(
                operation_id if isinstance(operation_id, str) else None,
                method,
            ):
                operation["operationId"] = _build_operation_id(path, method)

            responses_obj = operation.setdefault("responses", {})
            if not isinstance(responses_obj, dict):
                continue

            if (path, method.lower()) in public_operations:
                operation["security"] = []
                continue

            operation["security"] = [{"bearerAuth": []}]
            responses_obj.setdefault(
                "401", {"$ref": "#/components/responses/Unauthorized"}
            )
            responses_obj.setdefault(
                "403", {"$ref": "#/components/responses/Forbidden"}
            )
            responses_obj.setdefault(
                "429", {"$ref": "#/components/responses/TooManyRequests"}
            )

    _ensure_content_examples(spec)
    return spec


def main() -> None:
    from src.interface.http.app import create_app

    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    app = create_app()
    spec = _harden_contract(app.openapi(), local_port=8003)
    output = Path(args.output)

    if args.check:
        if not output.exists():
            raise SystemExit(f"{output} does not exist")
        current = yaml.safe_load(output.read_text(encoding="utf-8"))
        if json.dumps(current, sort_keys=True) != json.dumps(spec, sort_keys=True):
            raise SystemExit("OpenAPI artifact is out of sync. Run make openapi-export")
        return

    output.write_text(
        yaml.safe_dump(spec, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
