from __future__ import annotations

from dataclasses import dataclass

from src.domain.shared.questions import DiagnosticTag


@dataclass(slots=True, frozen=True)
class QuestionOption:
    """
    Вариант ответа для single-choice вопроса.

    :param option_id: Идентификатор варианта внутри вопроса.
    :type option_id: str
    :param text: Текст варианта ответа.
    :type text: str
    :param position: Порядок отображения.
    :type position: int
    :param diagnostic_tag: Классификация типичной ошибки для отчётов.
    :type diagnostic_tag: DiagnosticTag | None
    """

    option_id: str
    text: str
    position: int
    diagnostic_tag: DiagnosticTag | None = None
