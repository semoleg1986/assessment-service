from __future__ import annotations

from uuid import UUID

from sqlalchemy import select

from src.domain.content.test.entity import AssessmentTest
from src.domain.content.test.repository import TestRepository
from src.infrastructure.persistence.sqlalchemy.mappers import assessment_test_from_model
from src.infrastructure.persistence.sqlalchemy.models import QuestionModel, TestModel
from src.infrastructure.persistence.sqlalchemy.session_types import SessionLike


class SqlAlchemyTestRepository(TestRepository):
    def __init__(self, session: SessionLike) -> None:
        self._session = session

    def save(self, test: AssessmentTest) -> None:
        model = self._session.get(TestModel, test.test_id)
        if model is None:
            model = TestModel(
                test_id=test.test_id,
                subject_code=test.subject_code,
                grade=test.grade,
                created_at=test.created_at,
                version=test.version,
            )
            self._session.add(model)
        else:
            model.subject_code = test.subject_code
            model.grade = test.grade
            model.version = test.version

        self._session.query(QuestionModel).filter(
            QuestionModel.test_id == test.test_id
        ).delete(synchronize_session=False)
        for question in test.questions:
            self._session.add(
                QuestionModel(
                    question_id=question.question_id,
                    test_id=test.test_id,
                    node_id=question.node_id,
                    text=question.text,
                    question_type=question.question_type.value,
                    answer_key=question.answer_key,
                    correct_option_id=question.correct_option_id,
                    options=[
                        {
                            "option_id": option.option_id,
                            "text": option.text,
                            "position": option.position,
                            "diagnostic_tag": (
                                option.diagnostic_tag.value
                                if option.diagnostic_tag is not None
                                else None
                            ),
                        }
                        for option in question.options
                    ],
                    text_distractors=[
                        {
                            "pattern": distractor.pattern,
                            "match_mode": distractor.match_mode.value,
                            "diagnostic_tag": distractor.diagnostic_tag.value,
                        }
                        for distractor in question.text_distractors
                    ],
                    max_score=question.max_score,
                )
            )

    def get(self, test_id: UUID) -> AssessmentTest | None:
        model = self._session.get(TestModel, test_id)
        if model is None:
            return None
        return assessment_test_from_model(model)

    def list(self) -> list[AssessmentTest]:
        rows = self._session.scalars(
            select(TestModel).order_by(TestModel.created_at)
        ).all()
        return [assessment_test_from_model(r) for r in rows]
