from dataclasses import dataclass


@dataclass(slots=True)
class CleanupFixturesCommand:
    dry_run: bool
    subject_code_patterns: tuple[str, ...]
    topic_code_patterns: tuple[str, ...]
    node_id_patterns: tuple[str, ...]
