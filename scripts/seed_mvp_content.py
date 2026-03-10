from __future__ import annotations

import argparse
import logging
from dataclasses import dataclass
from os import getenv

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

logger = logging.getLogger("assessment.seed")


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
    topic_code: str
    grade: int
    section_code: str
    section_name: str
    micro_skill_name: str
    predecessor_ids: list[str]
    criticality: CriticalityLevel
    source_ref: str


PROD_MIN_SUBJECTS: tuple[tuple[str, str], ...] = (
    ("math", "Математика"),
    ("ru", "Русский язык"),
)

PROD_MIN_TOPICS: tuple[TopicSeed, ...] = (
    TopicSeed("M2-ADD", "math", 2, "Сложение"),
    TopicSeed("M2-SUB", "math", 2, "Вычитание"),
    TopicSeed("R2-ORTH", "ru", 2, "Орфография"),
)

PROD_MIN_MICRO_SKILLS: tuple[MicroSkillSeed, ...] = (
    MicroSkillSeed(
        node_id="M2-ADD-01",
        subject_code="math",
        topic_code="M2-ADD",
        grade=2,
        section_code="R1",
        section_name="Числа и операции",
        micro_skill_name="Сложение в пределах 20 без перехода",
        predecessor_ids=[],
        criticality=CriticalityLevel.MEDIUM,
        source_ref="seed:prod-min:v0.2.3",
    ),
    MicroSkillSeed(
        node_id="M2-ADD-02",
        subject_code="math",
        topic_code="M2-ADD",
        grade=2,
        section_code="R1",
        section_name="Числа и операции",
        micro_skill_name="Сложение в пределах 20 с переходом",
        predecessor_ids=["M2-ADD-01"],
        criticality=CriticalityLevel.HIGH,
        source_ref="seed:prod-min:v0.2.3",
    ),
    MicroSkillSeed(
        node_id="M2-SUB-01",
        subject_code="math",
        topic_code="M2-SUB",
        grade=2,
        section_code="R1",
        section_name="Числа и операции",
        micro_skill_name="Вычитание в пределах 20",
        predecessor_ids=["M2-ADD-01"],
        criticality=CriticalityLevel.MEDIUM,
        source_ref="seed:prod-min:v0.2.3",
    ),
    MicroSkillSeed(
        node_id="R2-ORTH-01",
        subject_code="ru",
        topic_code="R2-ORTH",
        grade=2,
        section_code="R1",
        section_name="Правописание",
        micro_skill_name="Проверяемые безударные гласные",
        predecessor_ids=[],
        criticality=CriticalityLevel.HIGH,
        source_ref="seed:prod-min:v0.2.3",
    ),
)

DEMO_SUBJECTS: tuple[tuple[str, str], ...] = PROD_MIN_SUBJECTS + (
    ("demo_science", "Demo: Окружающий мир"),
)

DEMO_TOPICS: tuple[TopicSeed, ...] = PROD_MIN_TOPICS + (
    TopicSeed("D2-WORLD-01", "demo_science", 2, "Живая и неживая природа"),
)

DEMO_MICRO_SKILLS: tuple[MicroSkillSeed, ...] = PROD_MIN_MICRO_SKILLS + (
    MicroSkillSeed(
        node_id="D2-WORLD-01",
        subject_code="demo_science",
        topic_code="D2-WORLD-01",
        grade=2,
        section_code="D1",
        section_name="Demo section",
        micro_skill_name="Различает объекты живой/неживой природы",
        predecessor_ids=[],
        criticality=CriticalityLevel.LOW,
        source_ref="seed:demo:v0.2.3",
    ),
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Seed MVP content to database")
    parser.add_argument(
        "--profile",
        choices=("prod-min", "demo"),
        default="prod-min",
        help="Seed profile. Default: prod-min",
    )
    parser.add_argument(
        "--confirm-demo",
        action="store_true",
        help="Required for --profile demo in non-dev environments",
    )
    return parser.parse_args()


def resolve_seed_profile(
    profile: str,
) -> tuple[
    tuple[tuple[str, str], ...],
    tuple[TopicSeed, ...],
    tuple[MicroSkillSeed, ...],
]:
    if profile == "prod-min":
        return PROD_MIN_SUBJECTS, PROD_MIN_TOPICS, PROD_MIN_MICRO_SKILLS
    return DEMO_SUBJECTS, DEMO_TOPICS, DEMO_MICRO_SKILLS


def main() -> None:
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s"
    )
    args = parse_args()
    settings = AppSettings.from_env()
    if not settings.database_url:
        raise SystemExit("DATABASE_URL is required for seed script")
    logger.info(
        "metric=assessment_seed_runs_total status=started value=1 profile=%s",
        args.profile,
    )

    app_env = getenv("APP_ENV", "dev").strip().lower()
    if args.profile == "demo" and app_env not in {"dev", "local"}:
        if not args.confirm_demo:
            raise SystemExit(
                "Demo profile requires --confirm-demo outside dev/local APP_ENV"
            )

    subjects, topics, micro_skills = resolve_seed_profile(args.profile)
    uow = build_uow()

    created_subjects = 0
    created_topics = 0
    created_skills = 0

    for code, name in subjects:
        if uow.subjects.get(code) is not None:
            continue
        handle_create_subject(CreateSubjectCommand(code=code, name=name), uow=uow)
        created_subjects += 1

    for topic in topics:
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

    for node in micro_skills:
        if uow.micro_skills.get(node.node_id) is not None:
            continue
        handle_create_micro_skill(
            CreateMicroSkillCommand(
                node_id=node.node_id,
                subject_code=node.subject_code,
                topic_code=node.topic_code,
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

    logger.info(
        (
            "metric=assessment_seed_runs_total status=succeeded value=1 profile=%s "
            "subjects_created=%s topics_created=%s micro_skills_created=%s"
        ),
        args.profile,
        created_subjects,
        created_topics,
        created_skills,
    )
    print(
        "seed completed:",
        {
            "profile": args.profile,
            "subjects_created": created_subjects,
            "topics_created": created_topics,
            "micro_skills_created": created_skills,
        },
    )


if __name__ == "__main__":
    try:
        main()
    except Exception:
        logger.exception("metric=assessment_seed_runs_total status=failed value=1")
        raise
