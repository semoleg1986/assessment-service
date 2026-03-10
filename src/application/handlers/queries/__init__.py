from src.application.handlers.queries.get_attempt_result import (
    handle_get_attempt_result,
)
from src.application.handlers.queries.get_child_diagnostics import (
    handle_get_child_diagnostics,
)
from src.application.handlers.queries.get_test_by_id import handle_get_test_by_id
from src.application.handlers.queries.list_assignments_by_child import (
    handle_list_assignments_by_child,
)
from src.application.handlers.queries.list_micro_skills import handle_list_micro_skills
from src.application.handlers.queries.list_subjects import handle_list_subjects
from src.application.handlers.queries.list_tests import handle_list_tests
from src.application.handlers.queries.list_topics import handle_list_topics

__all__ = [
    "handle_get_attempt_result",
    "handle_get_child_diagnostics",
    "handle_get_test_by_id",
    "handle_list_assignments_by_child",
    "handle_list_micro_skills",
    "handle_list_subjects",
    "handle_list_tests",
    "handle_list_topics",
]
