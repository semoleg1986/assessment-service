from dataclasses import dataclass
from uuid import UUID


@dataclass(slots=True)
class Question:
    """
    Вопрос теста, связанный с конкретным микро-умением.

    :param question_id: Идентификатор вопроса.
    :type question_id: UUID
    :param node_id: Идентификатор узла микро-умения.
    :type node_id: str
    :param text: Текст вопроса.
    :type text: str
    :param answer_key: Эталонный ответ.
    :type answer_key: str
    :param max_score: Максимальный балл за вопрос.
    :type max_score: int
    """

    question_id: UUID
    node_id: str
    text: str
    answer_key: str
    max_score: int = 1
