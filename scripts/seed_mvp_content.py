from __future__ import annotations

from dataclasses import dataclass

from src.application.commands.create_micro_skill import CreateMicroSkillCommand
from src.application.commands.create_subject import CreateSubjectCommand
from src.application.commands.create_topic import CreateTopicCommand
from src.application.handlers.commands.create_micro_skill import (
    handle_create_micro_skill,
)
from src.application.handlers.commands.create_subject import handle_create_subject
from src.application.handlers.commands.create_topic import handle_create_topic
from src.domain.value_objects.statuses import CriticalityLevel
from src.infrastructure.uow import AppSettings, build_uow


@dataclass(frozen=True)
class TopicSeed:
    code: str
    subject_code: str
    grade: int
    name: str


@dataclass(frozen=True)
class MicroSkillSeed:
    node_id: str
    subject_code: str
    grade: int
    section_code: str
    section_name: str
    micro_skill_name: str
    predecessor_ids: list[str]
    criticality: CriticalityLevel
    source_ref: str


SUBJECTS: tuple[tuple[str, str], ...] = (
    ("math", "Математика"),
    ("ru", "Русский язык"),
)

TOPICS: tuple[TopicSeed, ...] = (
    TopicSeed("M2-ADD", "math", 2, "Сложение"),
    TopicSeed("M2-SUB", "math", 2, "Вычитание"),
    TopicSeed("R2-ORTH", "ru", 2, "Орфография"),
)

MICRO_SKILLS: tuple[MicroSkillSeed, ...] = (
    MicroSkillSeed(
        node_id="M2-ADD-01",
        subject_code="math",
        grade=2,
        section_code="R1",
        section_name="Числа и операции",
        micro_skill_name="Сложение в пределах 20 без перехода",
        predecessor_ids=[],
        criticality=CriticalityLevel.MEDIUM,
        source_ref="seed:v0.2.1",
    ),
    MicroSkillSeed(
        node_id="M2-ADD-02",
        subject_code="math",
        grade=2,
        section_code="R1",
        section_name="Числа и операции",
        micro_skill_name="Сложение в пределах 20 с переходом",
        predecessor_ids=["M2-ADD-01"],
        criticality=CriticalityLevel.HIGH,
        source_ref="seed:v0.2.1",
    ),
    MicroSkillSeed(
        node_id="M2-SUB-01",
        subject_code="math",
        grade=2,
        section_code="R1",
        section_name="Числа и операции",
        micro_skill_name="Вычитание в пределах 20",
        predecessor_ids=["M2-ADD-01"],
        criticality=CriticalityLevel.MEDIUM,
        source_ref="seed:v0.2.1",
    ),
    MicroSkillSeed(
        node_id="R2-ORTH-01",
        subject_code="ru",
        grade=2,
        section_code="R1",
        section_name="Правописание",
        micro_skill_name="Проверяемые безударные гласные",
        predecessor_ids=[],
        criticality=CriticalityLevel.HIGH,
        source_ref="seed:v0.2.1",
    ),
)


def main() -> None:
    settings = AppSettings.from_env()
    if not settings.database_url:
        raise SystemExit("DATABASE_URL is required for seed script")

    uow = build_uow()

    created_subjects = 0
    created_topics = 0
    created_skills = 0

    for code, name in SUBJECTS:
        if uow.subjects.get(code) is not None:
            continue
        handle_create_subject(CreateSubjectCommand(code=code, name=name), uow=uow)
        created_subjects += 1

    for topic in TOPICS:
        if uow.topics.get(topic.code) is not None:
            continue
        handle_create_topic(
            CreateTopicCommand(
                code=topic.code,
                subject_code=topic.subject_code,
                grade=topic.grade,
                name=topic.name,
            ),
            uow=uow,
        )
        created_topics += 1

    for node in MICRO_SKILLS:
        if uow.micro_skills.get(node.node_id) is not None:
            continue
        handle_create_micro_skill(
            CreateMicroSkillCommand(
                node_id=node.node_id,
                subject_code=node.subject_code,
                grade=node.grade,
                section_code=node.section_code,
                section_name=node.section_name,
                micro_skill_name=node.micro_skill_name,
                predecessor_ids=node.predecessor_ids,
                criticality=node.criticality,
                source_ref=node.source_ref,
            ),
            uow=uow,
        )
        created_skills += 1

    print(
        "seed completed:",
        {
            "subjects_created": created_subjects,
            "topics_created": created_topics,
            "micro_skills_created": created_skills,
        },
    )


if __name__ == "__main__":
    main()
