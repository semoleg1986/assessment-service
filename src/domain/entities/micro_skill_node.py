from dataclasses import dataclass, field
from datetime import UTC, datetime

from src.domain.value_objects.statuses import CriticalityLevel, MicroSkillStatus


@dataclass(slots=True)
class MicroSkillNode:
    """
    Агрегатный корень микро-умения в графе знаний предмета.

    :param node_id: Стабильный идентификатор узла.
    :type node_id: str
    :param subject_code: Код предмета.
    :type subject_code: str
    :param grade: Класс обучения.
    :type grade: int
    :param topic_code: Код темы.
    :type topic_code: str | None
    :param section_code: Код раздела в рамках предмета.
    :type section_code: str
    :param section_name: Название раздела.
    :type section_name: str
    :param micro_skill_name: Название микро-умения.
    :type micro_skill_name: str
    :param predecessor_ids: Список зависимостей (предшественников).
    :type predecessor_ids: list[str]
    :param criticality: Критичность узла для учебной траектории.
    :type criticality: CriticalityLevel
    :param source_ref: Ссылка на источник контента.
    :type source_ref: str | None
    :param description: Описание микро-умения.
    :type description: str | None
    :param status: Статус жизненного цикла узла.
    :type status: MicroSkillStatus
    :param external_ref: Внешний идентификатор в контент-системе.
    :type external_ref: str | None
    :param version: Версия узла для отслеживания изменений.
    :type version: int
    :param created_at: Время создания узла.
    :type created_at: datetime
    :param updated_at: Время последнего обновления узла.
    :type updated_at: datetime
    """

    node_id: str
    subject_code: str
    grade: int
    topic_code: str | None
    section_code: str
    section_name: str
    micro_skill_name: str
    predecessor_ids: list[str] = field(default_factory=list)
    criticality: CriticalityLevel = CriticalityLevel.MEDIUM
    source_ref: str | None = None
    description: str | None = None
    status: MicroSkillStatus = MicroSkillStatus.ACTIVE
    external_ref: str | None = None
    version: int = 1
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def relink_predecessors(self, predecessor_ids: list[str]) -> bool:
        """
        Обновить связи-предшественники узла.

        :param predecessor_ids: Новый список predecessor-узлов.
        :type predecessor_ids: list[str]
        :return: True, если агрегат изменился.
        :rtype: bool
        """
        if self.predecessor_ids == predecessor_ids:
            return False
        self.predecessor_ids = predecessor_ids
        self._touch()
        return True

    def update_details(
        self,
        *,
        subject_code: str,
        topic_code: str | None,
        grade: int,
        section_code: str,
        section_name: str,
        micro_skill_name: str,
        predecessor_ids: list[str],
        criticality: CriticalityLevel,
        source_ref: str | None,
        description: str | None,
        status: MicroSkillStatus,
        external_ref: str | None,
    ) -> bool:
        """
        Обновить метаданные агрегата микро-умения.

        :return: True, если агрегат изменился.
        :rtype: bool
        """
        changed = (
            self.subject_code != subject_code
            or self.topic_code != topic_code
            or self.grade != grade
            or self.section_code != section_code
            or self.section_name != section_name
            or self.micro_skill_name != micro_skill_name
            or self.predecessor_ids != predecessor_ids
            or self.criticality != criticality
            or self.source_ref != source_ref
            or self.description != description
            or self.status != status
            or self.external_ref != external_ref
        )
        if not changed:
            return False

        self.subject_code = subject_code
        self.topic_code = topic_code
        self.grade = grade
        self.section_code = section_code
        self.section_name = section_name
        self.micro_skill_name = micro_skill_name
        self.predecessor_ids = predecessor_ids
        self.criticality = criticality
        self.source_ref = source_ref
        self.description = description
        self.status = status
        self.external_ref = external_ref
        self._touch()
        return True

    def _touch(self) -> None:
        self.version += 1
        self.updated_at = datetime.now(UTC)
