from typing import TypedDict

from src.application.commands.submit_attempt import SubmitAttemptCommand
from src.application.ports.unit_of_work import UnitOfWork
from src.domain.entities.answer import Answer
from src.domain.errors import NotFoundError
from src.domain.value_objects.questions import QuestionType
from src.domain.value_objects.statuses import AttemptStatus


class SubmitAttemptResult(TypedDict):
    attempt_id: str
    status: str
    score: int
    max_score: int
    signal: str


def handle_submit_attempt(
    command: SubmitAttemptCommand, uow: UnitOfWork
) -> SubmitAttemptResult:
    """
    Завершить попытку, оценить ответы и вернуть результат.

    :param command: Команда отправки попытки.
    :type command: SubmitAttemptCommand
    :param uow: Unit of Work.
    :type uow: UnitOfWork
    :return: Результат отправки (балл и сигнал).
    :rtype: SubmitAttemptResult
    """
    attempt = uow.attempts.get(command.attempt_id)
    if attempt is None:
        raise NotFoundError("attempt not found")

    assignment = uow.assignments.get(attempt.assignment_id)
    if assignment is None:
        raise NotFoundError("assignment not found")

    test = uow.tests.get(assignment.test_id)
    if test is None:
        raise NotFoundError("test not found")

    by_id = {q.question_id: q for q in test.questions}
    answers = []
    for a in command.answers:
        q = by_id.get(a.question_id)
        if q is None:
            continue
        value = a.value
        selected_option_id = a.selected_option_id
        resolved_diagnostic_tag = None
        if q.question_type == QuestionType.SINGLE_CHOICE:
            is_correct = selected_option_id == q.correct_option_id
            selected_option = next(
                (
                    option
                    for option in q.options
                    if option.option_id == selected_option_id
                ),
                None,
            )
            if selected_option and not is_correct:
                resolved_diagnostic_tag = selected_option.diagnostic_tag
            if value is None and selected_option_id is not None:
                value = selected_option_id
        else:
            text_value = (value or "").strip()
            expected = (q.answer_key or "").strip()
            is_correct = bool(expected) and text_value == expected
            if not is_correct:
                for distractor in q.text_distractors:
                    if distractor.matches(text_value):
                        resolved_diagnostic_tag = distractor.diagnostic_tag
                        break
        answers.append(
            Answer(
                question_id=a.question_id,
                value=value,
                selected_option_id=selected_option_id,
                resolved_diagnostic_tag=resolved_diagnostic_tag,
                is_correct=is_correct,
                awarded_score=q.max_score if is_correct else 0,
            )
        )

    attempt.submit(answers)
    assignment.mark_completed()

    uow.attempts.save(attempt)
    uow.assignments.save(assignment)
    uow.commit()

    max_score = sum(q.max_score for q in test.questions)
    ratio = attempt.score / max_score if max_score else 0
    if ratio >= 0.85:
        signal = "norm"
    elif ratio >= 0.70:
        signal = "risk"
    elif ratio >= 0.50:
        signal = "gap"
    else:
        signal = "critical_gap"

    return {
        "attempt_id": str(attempt.attempt_id),
        "status": AttemptStatus.SUBMITTED.value,
        "score": attempt.score,
        "max_score": max_score,
        "signal": signal,
    }
