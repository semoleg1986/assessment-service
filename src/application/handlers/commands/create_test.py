from uuid import uuid4

from src.application.commands.create_test import CreateTestCommand
from src.application.ports.unit_of_work import UnitOfWork
from src.domain.aggregates.test_aggregate import AssessmentTest
from src.domain.entities.question import Question
from src.domain.entities.question_option import QuestionOption
from src.domain.entities.text_distractor import TextDistractor
from src.domain.errors import NotFoundError


def handle_create_test(command: CreateTestCommand, uow: UnitOfWork) -> AssessmentTest:
    """
    Создать тест и привязать вопросы к узлам микро-умений.

    :param command: Команда создания теста.
    :type command: CreateTestCommand
    :param uow: Unit of Work.
    :type uow: UnitOfWork
    :return: Созданный тест.
    :rtype: AssessmentTest
    """
    for q in command.questions:
        if uow.micro_skills.get(q.node_id) is None:
            raise NotFoundError(f"micro skill node not found: {q.node_id}")
    test = AssessmentTest(
        test_id=uuid4(),
        subject_code=command.subject_code,
        grade=command.grade,
        questions=[
            Question(
                question_id=uuid4(),
                node_id=q.node_id,
                text=q.text,
                question_type=q.question_type,
                answer_key=q.answer_key,
                correct_option_id=q.correct_option_id,
                options=[
                    QuestionOption(
                        option_id=option.option_id,
                        text=option.text,
                        position=option.position,
                        diagnostic_tag=option.diagnostic_tag,
                    )
                    for option in q.options
                ],
                text_distractors=[
                    TextDistractor(
                        pattern=distractor.pattern,
                        match_mode=distractor.match_mode,
                        diagnostic_tag=distractor.diagnostic_tag,
                    )
                    for distractor in q.text_distractors
                ],
                max_score=q.max_score,
            )
            for q in command.questions
        ],
    )
    test.validate()
    uow.tests.save(test)
    uow.commit()
    return test
