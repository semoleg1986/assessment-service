from dataclasses import dataclass, field
from datetime import UTC, datetime

from src.domain.value_objects.statuses import CriticalityLevel, MicroSkillStatus


@dataclass(slots=True)
class MicroSkillNode:
    """
    Узел микро-умения в графе знаний предмета.

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
