from dataclasses import dataclass


@dataclass(slots=True)
class Subject:
    """
    Предмет учебной программы.

    :param code: Уникальный код предмета.
    :type code: str
    :param name: Отображаемое название предмета.
    :type name: str
    """

    code: str
    name: str
