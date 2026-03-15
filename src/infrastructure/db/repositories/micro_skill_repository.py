from __future__ import annotations

from sqlalchemy import select

from src.domain.content.micro_skill.entity import MicroSkillNode
from src.domain.content.micro_skill.repository import MicroSkillNodeRepository
from src.infrastructure.db.mappers import micro_skill_from_model
from src.infrastructure.db.models import MicroSkillNodeModel
from src.infrastructure.db.session import SessionLike


class SqlAlchemyMicroSkillNodeRepository(MicroSkillNodeRepository):
    def __init__(self, session: SessionLike) -> None:
        self._session = session

    def save(self, node: MicroSkillNode) -> None:
        model = self._session.get(MicroSkillNodeModel, node.node_id)
        if model is None:
            model = MicroSkillNodeModel(
                node_id=node.node_id,
                subject_code=node.subject_code,
                grade=node.grade,
                topic_code=node.topic_code,
                section_code=node.section_code,
                section_name=node.section_name,
                micro_skill_name=node.micro_skill_name,
                predecessor_ids=list(node.predecessor_ids),
                criticality=node.criticality.value,
                source_ref=node.source_ref,
                description=node.description,
                status=node.status.value,
                external_ref=node.external_ref,
                version=node.version,
                created_at=node.created_at,
                updated_at=node.updated_at,
            )
            self._session.add(model)
            return

        model.subject_code = node.subject_code
        model.grade = node.grade
        model.topic_code = node.topic_code
        model.section_code = node.section_code
        model.section_name = node.section_name
        model.micro_skill_name = node.micro_skill_name
        model.predecessor_ids = list(node.predecessor_ids)
        model.criticality = node.criticality.value
        model.source_ref = node.source_ref
        model.description = node.description
        model.status = node.status.value
        model.external_ref = node.external_ref
        model.version = node.version
        model.created_at = node.created_at
        model.updated_at = node.updated_at

    def get(self, node_id: str) -> MicroSkillNode | None:
        model = self._session.get(MicroSkillNodeModel, node_id)
        if model is None:
            return None
        return micro_skill_from_model(model)

    def list(self) -> list[MicroSkillNode]:
        rows = self._session.scalars(
            select(MicroSkillNodeModel).order_by(MicroSkillNodeModel.node_id)
        ).all()
        return [micro_skill_from_model(r) for r in rows]

    def delete(self, node_id: str) -> None:
        model = self._session.get(MicroSkillNodeModel, node_id)
        if model is not None:
            self._session.delete(model)
