from src.application.commands.save_attempt_answers import SaveAttemptAnswersCommand
from src.application.ports.unit_of_work import UnitOfWork
from src.domain.errors import NotFoundError


def handle_save_attempt_answers(
    command: SaveAttemptAnswersCommand,
    uow: UnitOfWork,
) -> dict[str, str | int]:
    if uow.attempts.get(command.attempt_id) is None:
        raise NotFoundError("attempt not found")
    return {
        "attempt_id": str(command.attempt_id),
        "saved_answers": len(command.answers),
    }
