from __future__ import annotations

import re
from dataclasses import dataclass

from src.domain.shared.questions import DiagnosticTag, TextMatchMode


@dataclass(slots=True, frozen=True)
class TextDistractor:
    """
    Шаблон типичной ошибки для text-вопроса.

    :param pattern: Шаблон/значение для сопоставления.
    :type pattern: str
    :param match_mode: Режим сопоставления (exact/normalized/regex).
    :type match_mode: TextMatchMode
    :param diagnostic_tag: Классификация ошибки.
    :type diagnostic_tag: DiagnosticTag
    """

    pattern: str
    match_mode: TextMatchMode
    diagnostic_tag: DiagnosticTag

    def matches(self, value: str) -> bool:
        if self.match_mode == TextMatchMode.EXACT:
            return value == self.pattern
        if self.match_mode == TextMatchMode.NORMALIZED:
            return value.strip().casefold() == self.pattern.strip().casefold()
        return re.fullmatch(self.pattern, value.strip()) is not None
