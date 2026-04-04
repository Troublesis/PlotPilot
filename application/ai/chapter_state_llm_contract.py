"""章节状态提取：LLM JSON 契约与 ChapterState 映射。

与 `StateExtractor` 共用：提示词与 Pydantic 根对象 `extra=forbid`，避免模型塞无关顶层字段。
列表元素为 object（dict），内部键保持宽松，与现有 StateUpdater 消费方式一致。
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from application.ai.llm_json_extract import parse_llm_json_to_dict
from domain.novel.value_objects.chapter_state import ChapterState

# 防止异常大响应拖垮下游；正常章节提取远小于此
_MAX_ITEMS = 500


class ChapterStateLlmPayload(BaseModel):
    """LLM 应返回的根对象：仅允许下列六个数组键。"""

    model_config = ConfigDict(extra="forbid")

    new_characters: List[Dict[str, Any]] = Field(default_factory=list, max_length=_MAX_ITEMS)
    character_actions: List[Dict[str, Any]] = Field(default_factory=list, max_length=_MAX_ITEMS)
    relationship_changes: List[Dict[str, Any]] = Field(default_factory=list, max_length=_MAX_ITEMS)
    foreshadowing_planted: List[Dict[str, Any]] = Field(default_factory=list, max_length=_MAX_ITEMS)
    foreshadowing_resolved: List[Dict[str, Any]] = Field(default_factory=list, max_length=_MAX_ITEMS)
    events: List[Dict[str, Any]] = Field(default_factory=list, max_length=_MAX_ITEMS)


_CHAPTER_STATE_SYSTEM = """你是一个专业的小说内容分析助手。你的任务是从章节内容中提取结构化信息。

请提取以下信息并以 JSON 格式返回（根对象**仅允许**下列六个键，不要增加其他顶层字段）：
1. new_characters: 新出现的角色列表，每项为对象，包含 name、description、first_appearance（章节号）
2. character_actions: 角色行为列表，每项包含 character_id、action、chapter
3. relationship_changes: 关系变化列表，每项包含 char1、char2、old_type、new_type、chapter
4. foreshadowing_planted: 埋下的伏笔列表，每项包含 description、chapter
5. foreshadowing_resolved: 解决的伏笔列表，每项包含 foreshadowing_id、chapter
6. events: 事件列表，每项包含 type、description、involved_characters（数组）、chapter

只返回一个 JSON 对象，不要 markdown 代码块、不要前后解释文字。"""


def build_chapter_state_extraction_system_prompt() -> str:
    return _CHAPTER_STATE_SYSTEM


def parse_chapter_state_llm_response(
    raw: str,
) -> Tuple[Optional[ChapterStateLlmPayload], List[str]]:
    data, errs = parse_llm_json_to_dict(raw)
    if data is None:
        return None, errs
    try:
        return ChapterStateLlmPayload.model_validate(data), []
    except ValidationError as e:
        err_list = e.errors()
        msg = "; ".join(
            f"{'/'.join(str(x) for x in err.get('loc', ()))}: {err.get('msg', '')}"
            for err in err_list[:12]
        )
        return None, [msg or str(e)]


def chapter_state_payload_to_domain(payload: ChapterStateLlmPayload) -> ChapterState:
    return ChapterState(
        new_characters=[dict(x) for x in payload.new_characters],
        character_actions=[dict(x) for x in payload.character_actions],
        relationship_changes=[dict(x) for x in payload.relationship_changes],
        foreshadowing_planted=[dict(x) for x in payload.foreshadowing_planted],
        foreshadowing_resolved=[dict(x) for x in payload.foreshadowing_resolved],
        events=[dict(x) for x in payload.events],
    )


def empty_chapter_state() -> ChapterState:
    """契约校验失败时的安全回退（与旧版 _EMPTY_STATE 语义一致）。"""
    return ChapterState(
        new_characters=[],
        character_actions=[],
        relationship_changes=[],
        foreshadowing_planted=[],
        foreshadowing_resolved=[],
        events=[],
    )


def chapter_state_openai_function_tool() -> Dict[str, Any]:
    """可选：接入 function calling 时使用。"""
    schema = ChapterStateLlmPayload.model_json_schema(mode="validation")
    return {
        "type": "function",
        "function": {
            "name": "submit_chapter_state_extraction",
            "description": "提交从章节正文提取的结构化状态；根对象仅含六个约定数组键。",
            "parameters": schema,
        },
    }
