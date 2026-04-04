"""基于文件的知识仓储（测试/文件后端）；单文件仍为 JSON，与 SQLite 关系化存储并行。"""
import logging
from typing import Any, Dict, Optional

from domain.knowledge.story_knowledge import StoryKnowledge
from domain.knowledge.chapter_summary import ChapterSummary
from domain.knowledge.knowledge_triple import KnowledgeTriple
from domain.knowledge.repositories.knowledge_repository import KnowledgeRepository
from infrastructure.persistence.storage.backend import StorageBackend

logger = logging.getLogger(__name__)


def _fact_to_dict(f: KnowledgeTriple) -> Dict[str, Any]:
    return {
        "id": f.id,
        "subject": f.subject,
        "predicate": f.predicate,
        "object": f.object,
        "chapter_id": f.chapter_id,
        "note": f.note,
        "entity_type": f.entity_type,
        "importance": f.importance,
        "location_type": f.location_type,
        "description": f.description,
        "first_appearance": f.first_appearance,
        "related_chapters": list(f.related_chapters),
        "tags": list(f.tags),
        "attributes": dict(f.attributes),
        "confidence": f.confidence,
        "source_type": f.source_type,
        "subject_entity_id": f.subject_entity_id,
        "object_entity_id": f.object_entity_id,
    }


def _fact_from_dict(fact: Dict[str, Any]) -> KnowledgeTriple:
    return KnowledgeTriple(
        id=fact["id"],
        subject=fact.get("subject", ""),
        predicate=fact.get("predicate", ""),
        object=fact.get("object", ""),
        chapter_id=fact.get("chapter_id"),
        note=fact.get("note", ""),
        entity_type=fact.get("entity_type"),
        importance=fact.get("importance"),
        location_type=fact.get("location_type"),
        description=fact.get("description"),
        first_appearance=fact.get("first_appearance"),
        related_chapters=fact.get("related_chapters", []),
        tags=fact.get("tags", []),
        attributes=fact.get("attributes", {}),
        confidence=fact.get("confidence"),
        source_type=fact.get("source_type"),
        subject_entity_id=fact.get("subject_entity_id"),
        object_entity_id=fact.get("object_entity_id"),
    )


class FileKnowledgeRepository(KnowledgeRepository):
    """使用 novel_knowledge.json 单文件快照（非 SQLite 路径）。"""

    def __init__(self, storage: StorageBackend):
        self.storage = storage

    def _get_path(self, novel_id: str) -> str:
        return f"novels/{novel_id}/novel_knowledge.json"

    def get_by_novel_id(self, novel_id: str) -> Optional[StoryKnowledge]:
        path = self._get_path(novel_id)
        if not self.storage.exists(path):
            return None
        try:
            data = self.storage.read_json(path)
            return self._from_dict(novel_id, data)
        except Exception as e:
            logger.error("Failed to load knowledge for %s: %s", novel_id, e)
            return None

    def save(self, knowledge: StoryKnowledge) -> None:
        path = self._get_path(knowledge.novel_id)
        data = self._to_dict(knowledge)
        self.storage.write_json(path, data)

    def save_all(self, novel_id: str, data: dict) -> None:
        """与 KnowledgeService.update_knowledge 对齐的批量写入。"""
        k = self._from_dict(
            novel_id,
            {
                "version": data.get("version", 1),
                "premise_lock": data.get("premise_lock", ""),
                "chapters": data.get("chapters", []),
                "facts": data.get("facts", []),
            },
        )
        self.save(k)

    def exists(self, novel_id: str) -> bool:
        return self.storage.exists(self._get_path(novel_id))

    def delete(self, novel_id: str) -> None:
        path = self._get_path(novel_id)
        if self.storage.exists(path):
            self.storage.delete(path)

    def _to_dict(self, knowledge: StoryKnowledge) -> dict:
        return {
            "version": knowledge.version,
            "premise_lock": knowledge.premise_lock,
            "chapters": [
                {
                    "chapter_id": ch.chapter_id,
                    "summary": ch.summary,
                    "key_events": ch.key_events,
                    "open_threads": ch.open_threads,
                    "consistency_note": ch.consistency_note,
                    "beat_sections": ch.beat_sections,
                    "sync_status": ch.sync_status,
                }
                for ch in knowledge.chapters
            ],
            "facts": [_fact_to_dict(f) for f in knowledge.facts],
        }

    def _from_dict(self, novel_id: str, data: dict) -> StoryKnowledge:
        chapters = [
            ChapterSummary(
                chapter_id=ch["chapter_id"],
                summary=ch.get("summary", ""),
                key_events=ch.get("key_events", ""),
                open_threads=ch.get("open_threads", ""),
                consistency_note=ch.get("consistency_note", ""),
                beat_sections=ch.get("beat_sections", []),
                sync_status=ch.get("sync_status", "draft"),
            )
            for ch in data.get("chapters", [])
        ]
        facts = [_fact_from_dict(f) for f in data.get("facts", [])]
        return StoryKnowledge(
            novel_id=novel_id,
            version=data.get("version", 1),
            premise_lock=data.get("premise_lock", ""),
            chapters=chapters,
            facts=facts,
        )
