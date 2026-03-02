from dataclasses import dataclass


@dataclass(slots=True)
class CreateSubjectCommand:
    code: str
    name: str
