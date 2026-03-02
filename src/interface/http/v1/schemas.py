from uuid import UUID

from pydantic import BaseModel, Field

from src.domain.value_objects.statuses import CriticalityLevel


class QuestionCreateRequest(BaseModel):
    node_id: str
    text: str
    answer_key: str
    max_score: int = 1


class CreateTestRequest(BaseModel):
    subject_code: str
    grade: int = Field(ge=1, le=4)
    questions: list[QuestionCreateRequest]


class QuestionResponse(BaseModel):
    question_id: UUID
    node_id: str
    text: str
    max_score: int


class TestResponse(BaseModel):
    test_id: UUID
    subject_code: str
    grade: int
    version: int
    questions: list[QuestionResponse]


class AssignTestRequest(BaseModel):
    test_id: UUID
    child_id: UUID


class AssignmentResponse(BaseModel):
    assignment_id: UUID
    test_id: UUID
    child_id: UUID
    status: str


class StartAttemptRequest(BaseModel):
    assignment_id: UUID
    child_id: UUID


class StartAttemptResponse(BaseModel):
    attempt_id: UUID
    assignment_id: UUID
    child_id: UUID
    status: str


class SubmittedAnswerRequest(BaseModel):
    question_id: UUID
    value: str


class SubmitAttemptRequest(BaseModel):
    answers: list[SubmittedAnswerRequest]


class SubmitAttemptResponse(BaseModel):
    attempt_id: str
    status: str
    score: int
    max_score: int
    signal: str


class AttemptAnswerResponse(BaseModel):
    question_id: str
    value: str
    is_correct: bool
    awarded_score: int


class AttemptResultResponse(BaseModel):
    attempt_id: str
    status: str
    score: int
    answers: list[AttemptAnswerResponse]


class SubjectCreateRequest(BaseModel):
    code: str
    name: str


class SubjectResponse(BaseModel):
    code: str
    name: str


class TopicCreateRequest(BaseModel):
    code: str
    subject_code: str
    grade: int = Field(ge=1, le=11)
    name: str


class TopicResponse(BaseModel):
    code: str
    subject_code: str
    grade: int
    name: str


class MicroSkillCreateRequest(BaseModel):
    node_id: str
    subject_code: str
    grade: int = Field(ge=1, le=11)
    section_code: str
    section_name: str
    micro_skill_name: str
    predecessor_ids: list[str] = Field(default_factory=list)
    criticality: CriticalityLevel = CriticalityLevel.MEDIUM
    source_ref: str | None = None


class MicroSkillLinkRequest(BaseModel):
    predecessor_ids: list[str]


class MicroSkillResponse(BaseModel):
    node_id: str
    subject_code: str
    grade: int
    section_code: str
    section_name: str
    micro_skill_name: str
    predecessor_ids: list[str]
    criticality: CriticalityLevel
    source_ref: str | None
    blocks_count: int
