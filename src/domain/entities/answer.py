from dataclasses import dataclass
from uuid import UUID


@dataclass(slots=True)
class Answer:
    """
    Ответ ученика на конкретный вопрос теста.

    :param question_id: Идентификатор вопроса.
    :type question_id: UUID
    :param value: Значение ответа.
    :type value: str
    :param is_correct: Признак корректности ответа.
    :type is_correct: bool
    :param awarded_score: Начисленный балл за ответ.
    :type awarded_score: int
    """

    question_id: UUID
    value: str
    is_correct: bool
    awarded_score: int
