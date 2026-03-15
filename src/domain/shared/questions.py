from enum import StrEnum


class QuestionType(StrEnum):
    TEXT = "text"
    SINGLE_CHOICE = "single_choice"


class DiagnosticTag(StrEnum):
    INATTENTION = "inattention"
    MISREAD_CONDITION = "misread_condition"
    CALC_ERROR = "calc_error"
    CONCEPT_GAP = "concept_gap"
    GUESSING = "guessing"
    OTHER = "other"


class TextMatchMode(StrEnum):
    EXACT = "exact"
    NORMALIZED = "normalized"
    REGEX = "regex"
