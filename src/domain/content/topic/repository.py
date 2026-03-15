from abc import ABC, abstractmethod

from src.domain.content.topic.entity import Topic


class TopicRepository(ABC):
    @abstractmethod
    def save(self, topic: Topic) -> None: ...

    @abstractmethod
    def get(self, code: str) -> Topic | None: ...

    @abstractmethod
    def list(self) -> list[Topic]: ...
