from dataclasses import dataclass


@dataclass(slots=True)
class CreateTopicCommand:
    code: str
    subject_code: str
    grade: int
    name: str
