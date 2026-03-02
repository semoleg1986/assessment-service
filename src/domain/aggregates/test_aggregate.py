from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID

from src.domain.entities.question import Question
from src.domain.errors import InvariantViolationError


@dataclass(slots=True)
class AssessmentTest:
    """
    Агрегат теста: предмет, класс и набор вопросов.

    :param test_id: Идентификатор теста.
    :type test_id: UUID
    :param subject_code: Код предмета.
    :type subject_code: str
    :param grade: Класс, для которого предназначен тест.
    :type grade: int
    :param questions: Набор вопросов теста.
    :type questions: list[Question]
    :param created_at: Время создания теста.
    :type created_at: datetime
    :param version: Версия агрегата.
    :type version: int
    """

    test_id: UUID
    subject_code: str
    grade: int
    questions: list[Question] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    version: int = 1

    def validate(self) -> None:
        """Проверить инварианты теста перед сохранением."""
        if not self.questions:
            raise InvariantViolationError("test must contain at least one question")
        if self.grade not in {1, 2, 3, 4}:
            raise InvariantViolationError("grade must be in [1..4]")
