from dataclasses import dataclass


@dataclass(slots=True)
class QuestionInput:
    node_id: str
    text: str
    answer_key: str
    max_score: int = 1


@dataclass(slots=True)
class CreateTestCommand:
    subject_code: str
    grade: int
    questions: list[QuestionInput]
