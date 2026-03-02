class DomainError(Exception):
    pass


class InvariantViolationError(DomainError):
    pass


class NotFoundError(DomainError):
    pass
