from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, Field

from src.application.contracts.questions import DiagnosticTag


class AssignTestRequest(BaseModel):
    test_id: UUID
    child_id: UUID
    retake: bool = False


class AssignmentResponse(BaseModel):
    assignment_id: UUID
    test_id: UUID
    child_id: UUID
    status: str
    attempt_no: int


class AssignmentListItemResponse(BaseModel):
    assignment_id: UUID
    test_id: UUID
    test_title: str | None = None
    status: str
    attempt_no: int
    due_at: str | None = None


class StartAttemptRequest(BaseModel):
    assignment_id: UUID
    child_id: UUID


class StartAttemptByAssignmentRequest(BaseModel):
    child_id: UUID


class StartAttemptResponse(BaseModel):
    attempt_id: UUID
    assignment_id: UUID
    child_id: UUID
    status: str


class SubmittedAnswerRequest(BaseModel):
    question_id: UUID
    value: str | None = None
    selected_option_id: str | None = None
    time_spent_ms: int | None = Field(default=None, ge=0)


class SubmitAttemptRequest(BaseModel):
    answers: list[SubmittedAnswerRequest]


class SubmitAttemptResponse(BaseModel):
    attempt_id: str
    status: str
    score: int
    max_score: int
    signal: str


class SaveAttemptAnswersRequest(BaseModel):
    answers: list[SubmittedAnswerRequest]


class SaveAttemptAnswersResponse(BaseModel):
    attempt_id: str
    saved_answers: int


class AttemptAnswerResponse(BaseModel):
    question_id: str
    value: str | None
    selected_option_id: str | None
    resolved_diagnostic_tag: DiagnosticTag | None
    time_spent_ms: int | None = None
    is_correct: bool
    awarded_score: int


class AttemptResultResponse(BaseModel):
    attempt_id: str
    status: str
    score: int
    answers: list[AttemptAnswerResponse]
