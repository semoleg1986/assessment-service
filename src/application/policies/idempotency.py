from __future__ import annotations

from uuid import NAMESPACE_URL, UUID, uuid5


def stable_uuid(*parts: str) -> UUID:
    """
    Build deterministic UUID (v5) from stable idempotency parts.

    Used in content import so re-applying the same source/payload keys
    keeps entity identifiers stable.
    """

    return uuid5(NAMESPACE_URL, ":".join(parts))
