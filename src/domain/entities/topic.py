from dataclasses import dataclass


@dataclass(slots=True)
class Topic:
    """
    Тема внутри предмета и класса.

    :param code: Уникальный код темы.
    :type code: str
    :param subject_code: Код предмета-владельца.
    :type subject_code: str
    :param grade: Класс, для которого применяется тема.
    :type grade: int
    :param name: Название темы.
    :type name: str
    """

    code: str
    subject_code: str
    grade: int
    name: str
