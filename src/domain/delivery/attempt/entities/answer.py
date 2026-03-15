from dataclasses import dataclass
from uuid import UUID

from src.domain.shared.questions import DiagnosticTag


@dataclass(slots=True)
class Answer:
    """
    Ответ ученика на конкретный вопрос теста.

    :param question_id: Идентификатор вопроса.
    :type question_id: UUID
    :param value: Значение ответа.
    :type value: str | None
    :param selected_option_id: Выбранный вариант ответа для single_choice.
    :type selected_option_id: str | None
    :param resolved_diagnostic_tag: Рассчитанная классификация ошибки.
    :type resolved_diagnostic_tag: DiagnosticTag | None
    :param time_spent_ms: Время решения вопроса в миллисекундах.
    :type time_spent_ms: int | None
    :param is_correct: Признак корректности ответа.
    :type is_correct: bool
    :param awarded_score: Начисленный балл за ответ.
    :type awarded_score: int
    """

    question_id: UUID
    is_correct: bool = False
    awarded_score: int = 0
    value: str | None = None
    selected_option_id: str | None = None
    resolved_diagnostic_tag: DiagnosticTag | None = None
    time_spent_ms: int | None = None
