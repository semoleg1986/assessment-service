from __future__ import annotations

from src.application.content.commands.import_content import (
    ImportContentCommand,
    ImportContentPayloadInput,
    ImportContentResult,
    ImportMicroSkillInput,
    ImportQuestionInput,
    ImportQuestionOptionInput,
    ImportSubjectInput,
    ImportTestInput,
    ImportTextDistractorInput,
    ImportTopicInput,
)
from src.application.content.handlers.import_content import handle_import_content
from src.application.facade.inputs import ImportContentPayloadInput as FacadeImportInput
from src.application.ports.unit_of_work import UnitOfWork


class AssessmentImportFacade:
    """Фасад application-слоя для bulk import контекста."""

    def __init__(self, *, uow: UnitOfWork) -> None:
        self._uow = uow

    def import_content(self, *, command: ImportContentCommand) -> ImportContentResult:
        return handle_import_content(command, uow=self._uow)

    def import_content_payload(
        self, *, payload: FacadeImportInput
    ) -> ImportContentResult:
        return handle_import_content(
            ImportContentCommand(
                source_id=payload.source_id,
                contract_version=payload.contract_version,
                validate_only=payload.validate_only,
                error_mode=payload.error_mode,
                payload=ImportContentPayloadInput(
                    subjects=[
                        ImportSubjectInput(code=item["code"], name=item["name"])
                        for item in payload.payload.get("subjects", [])
                    ],
                    topics=[
                        ImportTopicInput(
                            code=item["code"],
                            subject_code=item["subject_code"],
                            grade=item["grade"],
                            name=item["name"],
                        )
                        for item in payload.payload.get("topics", [])
                    ],
                    micro_skills=[
                        ImportMicroSkillInput(
                            node_id=item["node_id"],
                            subject_code=item["subject_code"],
                            topic_code=item["topic_code"],
                            grade=item["grade"],
                            section_code=item["section_code"],
                            section_name=item["section_name"],
                            micro_skill_name=item["micro_skill_name"],
                            predecessor_ids=item.get("predecessor_ids", []),
                            criticality=item["criticality"],
                            source_ref=item.get("source_ref"),
                            description=item.get("description"),
                            status=item.get("status"),
                            external_ref=item.get("external_ref"),
                        )
                        for item in payload.payload.get("micro_skills", [])
                    ],
                    tests=[
                        ImportTestInput(
                            external_id=item["external_id"],
                            subject_code=item["subject_code"],
                            grade=item["grade"],
                            questions=[
                                ImportQuestionInput(
                                    external_id=question["external_id"],
                                    node_id=question["node_id"],
                                    text=question["text"],
                                    question_type=question.get("question_type", "text"),
                                    answer_key=question.get("answer_key"),
                                    correct_option_id=question.get("correct_option_id"),
                                    options=[
                                        ImportQuestionOptionInput(
                                            option_id=option["option_id"],
                                            text=option["text"],
                                            position=option["position"],
                                            diagnostic_tag=option.get("diagnostic_tag"),
                                        )
                                        for option in question.get("options", [])
                                    ],
                                    text_distractors=[
                                        ImportTextDistractorInput(
                                            pattern=distractor["pattern"],
                                            match_mode=distractor.get(
                                                "match_mode", "exact"
                                            ),
                                            diagnostic_tag=distractor.get(
                                                "diagnostic_tag", "other"
                                            ),
                                        )
                                        for distractor in question.get(
                                            "text_distractors", []
                                        )
                                    ],
                                    max_score=question["max_score"],
                                )
                                for question in item.get("questions", [])
                            ],
                        )
                        for item in payload.payload.get("tests", [])
                    ],
                ),
            ),
            uow=self._uow,
        )
