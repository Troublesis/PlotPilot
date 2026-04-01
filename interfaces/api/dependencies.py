"""依赖注入配置

提供 FastAPI 依赖注入函数，用于创建服务和仓储实例。
"""
import os
from pathlib import Path
from functools import lru_cache

from application.paths import DATA_DIR
from infrastructure.persistence.storage.file_storage import FileStorage
from infrastructure.persistence.repositories.file_novel_repository import FileNovelRepository
from infrastructure.persistence.repositories.file_chapter_repository import FileChapterRepository
from infrastructure.persistence.repositories.file_bible_repository import FileBibleRepository
from infrastructure.persistence.repositories.file_cast_repository import FileCastRepository
from infrastructure.persistence.repositories.file_knowledge_repository import FileKnowledgeRepository
from infrastructure.persistence.repositories.file_chat_repository import FileChatRepository
from infrastructure.ai.providers.anthropic_provider import AnthropicProvider
from infrastructure.ai.config.settings import Settings

from application.services.novel_service import NovelService
from application.services.chapter_service import ChapterService
from application.services.bible_service import BibleService
from application.services.cast_service import CastService
from application.services.ai_generation_service import AIGenerationService
from application.services.knowledge_service import KnowledgeService
from application.services.chat_service import ChatService


# 全局存储实例
_storage = None


def get_storage() -> FileStorage:
    """获取存储后端实例

    Returns:
        FileStorage 实例
    """
    global _storage
    if _storage is None:
        _storage = FileStorage(DATA_DIR)
    return _storage


# Repository 依赖
def get_novel_repository() -> FileNovelRepository:
    """获取 Novel 仓储

    Returns:
        FileNovelRepository 实例
    """
    return FileNovelRepository(get_storage())


def get_chapter_repository() -> FileChapterRepository:
    """获取 Chapter 仓储

    Returns:
        FileChapterRepository 实例
    """
    return FileChapterRepository(get_storage())


def get_bible_repository() -> FileBibleRepository:
    """获取 Bible 仓储

    Returns:
        FileBibleRepository 实例
    """
    return FileBibleRepository(get_storage())


def get_cast_repository() -> FileCastRepository:
    """获取 Cast 仓储

    Returns:
        FileCastRepository 实例
    """
    return FileCastRepository(get_storage())


def get_knowledge_repository() -> FileKnowledgeRepository:
    """获取 Knowledge 仓储

    Returns:
        FileKnowledgeRepository 实例
    """
    return FileKnowledgeRepository(get_storage())


def get_chat_repository() -> FileChatRepository:
    """获取 Chat 仓储

    Returns:
        FileChatRepository 实例
    """
    return FileChatRepository(get_storage())


# Service 依赖
def get_novel_service() -> NovelService:
    """获取 Novel 服务

    Returns:
        NovelService 实例
    """
    return NovelService(get_novel_repository())


def get_chapter_service() -> ChapterService:
    """获取 Chapter 服务

    Returns:
        ChapterService 实例
    """
    return ChapterService(get_chapter_repository(), get_novel_repository())


def get_bible_service() -> BibleService:
    """获取 Bible 服务

    Returns:
        BibleService 实例
    """
    return BibleService(get_bible_repository())


def get_cast_service() -> CastService:
    """获取 Cast 服务

    Returns:
        CastService 实例
    """
    storage = get_storage()
    # Determine storage root based on storage base path
    storage_root = storage.base_path
    return CastService(get_cast_repository(), storage_root)


def get_ai_generation_service() -> AIGenerationService:
    """获取 AI 生成服务

    Returns:
        AIGenerationService 实例
    """
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY environment variable is not set")

    settings = Settings(api_key=api_key)
    llm_service = AnthropicProvider(settings)

    return AIGenerationService(
        llm_service,
        get_novel_repository(),
        get_bible_repository()
    )


def get_knowledge_service() -> KnowledgeService:
    """获取 Knowledge 服务

    Returns:
        KnowledgeService 实例
    """
    return KnowledgeService(get_knowledge_repository())


def get_chat_service() -> ChatService:
    """获取 Chat 服务

    读取消息等不依赖 LLM；未配置 ANTHROPIC_API_KEY 时仍可拉取历史，发送/流式时再报错。

    Returns:
        ChatService 实例
    """
    api_key = os.getenv("ANTHROPIC_API_KEY")
    llm_service = None
    if api_key:
        settings = Settings(api_key=api_key)
        llm_service = AnthropicProvider(settings)

    return ChatService(
        get_chat_repository(),
        llm_service,
        get_novel_repository(),
        get_bible_repository(),
        get_cast_repository(),
        get_knowledge_repository()
    )
