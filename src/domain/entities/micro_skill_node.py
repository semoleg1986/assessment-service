from dataclasses import dataclass, field

from src.domain.value_objects.statuses import CriticalityLevel


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
    """

    node_id: str
    subject_code: str
    grade: int
    section_code: str
    section_name: str
    micro_skill_name: str
    predecessor_ids: list[str] = field(default_factory=list)
    criticality: CriticalityLevel = CriticalityLevel.MEDIUM
    source_ref: str | None = None
