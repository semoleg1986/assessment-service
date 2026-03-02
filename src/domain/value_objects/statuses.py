from enum import StrEnum


class AssignmentStatus(StrEnum):
    ASSIGNED = "assigned"
    STARTED = "started"
    COMPLETED = "completed"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class AttemptStatus(StrEnum):
    STARTED = "started"
    SUBMITTED = "submitted"
    CANCELLED = "cancelled"


class CriticalityLevel(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
