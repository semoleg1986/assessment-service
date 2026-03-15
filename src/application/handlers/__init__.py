from src.application.content.handlers.cleanup_fixtures import handle_cleanup_fixtures
from src.application.content.handlers.create_micro_skill import (
    handle_create_micro_skill,
)
from src.application.content.handlers.create_subject import handle_create_subject
from src.application.content.handlers.create_test import handle_create_test
from src.application.content.handlers.create_topic import handle_create_topic
from src.application.content.handlers.delete_micro_skill import (
    handle_delete_micro_skill,
)
from src.application.content.handlers.get_test_by_id import handle_get_test_by_id
from src.application.content.handlers.import_content import handle_import_content
from src.application.content.handlers.link_micro_skill_predecessors import (
    handle_link_micro_skill_predecessors,
)
from src.application.content.handlers.list_micro_skills import handle_list_micro_skills
from src.application.content.handlers.list_subjects import handle_list_subjects
from src.application.content.handlers.list_tests import handle_list_tests
from src.application.content.handlers.list_topics import handle_list_topics
from src.application.content.handlers.update_micro_skill import (
    handle_update_micro_skill,
)
from src.application.delivery.handlers.assign_test import handle_assign_test
from src.application.delivery.handlers.get_attempt_result import (
    handle_get_attempt_result,
)
from src.application.delivery.handlers.list_assignments_by_child import (
    handle_list_assignments_by_child,
)
from src.application.delivery.handlers.save_attempt_answers import (
    handle_save_attempt_answers,
)
from src.application.delivery.handlers.start_attempt import handle_start_attempt
from src.application.delivery.handlers.submit_attempt import handle_submit_attempt
from src.application.reporting.handlers.get_child_diagnostics import (
    handle_get_child_diagnostics,
)
from src.application.reporting.handlers.get_child_results import (
    handle_get_child_results,
)
from src.application.reporting.handlers.get_child_skill_results import (
    handle_get_child_skill_results,
)

__all__ = [
    "handle_assign_test",
    "handle_cleanup_fixtures",
    "handle_create_micro_skill",
    "handle_create_subject",
    "handle_create_test",
    "handle_create_topic",
    "handle_delete_micro_skill",
    "handle_get_attempt_result",
    "handle_get_child_diagnostics",
    "handle_get_child_results",
    "handle_get_child_skill_results",
    "handle_get_test_by_id",
    "handle_import_content",
    "handle_link_micro_skill_predecessors",
    "handle_list_assignments_by_child",
    "handle_list_micro_skills",
    "handle_list_subjects",
    "handle_list_tests",
    "handle_list_topics",
    "handle_save_attempt_answers",
    "handle_start_attempt",
    "handle_submit_attempt",
    "handle_update_micro_skill",
]
