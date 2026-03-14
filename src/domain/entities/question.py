from dataclasses import dataclass, field
from uuid import UUID

from src.domain.entities.question_option import QuestionOption
from src.domain.entities.text_distractor import TextDistractor
from src.domain.errors import InvariantViolationError
from src.domain.value_objects.questions import QuestionType


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
    :param question_type: Тип вопроса (text/single_choice).
    :type question_type: QuestionType
    :param answer_key: Эталонный ответ.
    :type answer_key: str | None
    :param correct_option_id: Идентификатор правильного варианта
        для single_choice вопроса.
    :type correct_option_id: str | None
    :param options: Варианты ответа для single_choice.
    :type options: list[QuestionOption]
    :param text_distractors: Шаблоны типичных ошибок для text-вопроса.
    :type text_distractors: list[TextDistractor]
    :param max_score: Максимальный балл за вопрос.
    :type max_score: int
    """

    question_id: UUID
    node_id: str
    text: str
    question_type: QuestionType = QuestionType.TEXT
    answer_key: str | None = None
    correct_option_id: str | None = None
    options: list[QuestionOption] = field(default_factory=list)
    text_distractors: list[TextDistractor] = field(default_factory=list)
    max_score: int = 1

    def validate(self) -> None:
        """Проверить инварианты вопроса."""
        if self.max_score < 1:
            raise InvariantViolationError("question max_score must be >= 1")
        if self.question_type == QuestionType.TEXT:
            if not (self.answer_key or "").strip():
                raise InvariantViolationError("text question must contain answer_key")
            if self.options:
                raise InvariantViolationError("text question must not contain options")
            if self.correct_option_id is not None:
                raise InvariantViolationError(
                    "text question must not contain correct_option_id"
                )
            return

        if self.question_type != QuestionType.SINGLE_CHOICE:
            raise InvariantViolationError("unsupported question_type")

        if len(self.options) < 2:
            raise InvariantViolationError(
                "single_choice question must contain at least 2 options"
            )
        option_ids = [option.option_id for option in self.options]
        if len(option_ids) != len(set(option_ids)):
            raise InvariantViolationError(
                "option_id must be unique in question options"
            )
        positions = [option.position for option in self.options]
        if len(positions) != len(set(positions)):
            raise InvariantViolationError("position must be unique in question options")
        if any(position < 1 for position in positions):
            raise InvariantViolationError("position must be >= 1 in question options")
        if self.correct_option_id not in set(option_ids):
            raise InvariantViolationError(
                "correct_option_id must reference existing option_id"
            )
        correct_option = next(
            option
            for option in self.options
            if option.option_id == self.correct_option_id
        )
        if correct_option.diagnostic_tag is not None:
            raise InvariantViolationError(
                "diagnostic_tag for correct option must be null"
            )
