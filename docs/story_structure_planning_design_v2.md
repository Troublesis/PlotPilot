# 故事结构规划功能设计（优化版）

## 核心字段设计

### 必要字段（直接加到表中）

```sql
ALTER TABLE story_nodes ADD COLUMN planning_status TEXT DEFAULT 'draft'
  CHECK(planning_status IN ('draft', 'ai_generated', 'user_edited', 'confirmed'));

ALTER TABLE story_nodes ADD COLUMN planning_source TEXT DEFAULT 'manual'
  CHECK(planning_source IN ('manual', 'ai_macro', 'ai_act'));

-- 章节大纲（用于章节节点）
ALTER TABLE story_nodes ADD COLUMN outline TEXT;

-- 主题标签（用于部/卷/幕）
ALTER TABLE story_nodes ADD COLUMN themes TEXT;  -- JSON array: ["主题1", "主题2"]

-- 关键事件（用于幕）
ALTER TABLE story_nodes ADD COLUMN key_events TEXT;  -- JSON array: ["事件1", "事件2"]

-- 叙事弧线（用于幕）
ALTER TABLE story_nodes ADD COLUMN narrative_arc TEXT;

-- 冲突列表（用于幕）
ALTER TABLE story_nodes ADD COLUMN conflicts TEXT;  -- JSON array: ["冲突1", "冲突2"]

-- 预计章节数（用于部/卷/幕，规划时使用）
ALTER TABLE story_nodes ADD COLUMN suggested_chapter_count INTEGER;
```

### 扩展字段（放在 metadata 中）

```json
{
  "tags": ["用户自定义标签"],
  "notes": "用户备注",
  "custom_fields": {}
}
```

---

## 更新后的表结构

```sql
CREATE TABLE story_nodes (
    id TEXT PRIMARY KEY,
    novel_id TEXT NOT NULL,
    parent_id TEXT,
    node_type TEXT NOT NULL CHECK(node_type IN ('part', 'volume', 'act', 'chapter')),
    number INTEGER NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    order_index INTEGER NOT NULL,

    -- 规划相关（必要字段）
    planning_status TEXT DEFAULT 'draft'
      CHECK(planning_status IN ('draft', 'ai_generated', 'user_edited', 'confirmed')),
    planning_source TEXT DEFAULT 'manual'
      CHECK(planning_source IN ('manual', 'ai_macro', 'ai_act')),

    -- 章节范围（自动计算，仅用于 part/volume/act）
    chapter_start INTEGER,
    chapter_end INTEGER,
    chapter_count INTEGER DEFAULT 0,
    suggested_chapter_count INTEGER,  -- 规划时的预计章节数

    -- 章节内容（仅用于 chapter 类型）
    content TEXT,
    outline TEXT,  -- 章节大纲
    word_count INTEGER DEFAULT 0,
    status TEXT DEFAULT 'draft',

    -- 结构化规划信息（用于 part/volume/act）
    themes TEXT,  -- JSON array
    key_events TEXT,  -- JSON array
    narrative_arc TEXT,
    conflicts TEXT,  -- JSON array

    -- 扩展元数据（JSON 格式，仅用于真正的扩展）
    metadata TEXT DEFAULT '{}',

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (novel_id) REFERENCES novels(id) ON DELETE CASCADE,
    FOREIGN KEY (parent_id) REFERENCES story_nodes(id) ON DELETE CASCADE
);
```

---

## 字段使用说明

### 按节点类型分类

| 字段 | Part | Volume | Act | Chapter | 说明 |
|------|------|--------|-----|---------|------|
| `planning_status` | ✓ | ✓ | ✓ | ✓ | 所有节点都有规划状态 |
| `planning_source` | ✓ | ✓ | ✓ | ✓ | 所有节点都记录来源 |
| `suggested_chapter_count` | ✓ | ✓ | ✓ | - | 规划时的预计章节数 |
| `themes` | ✓ | ✓ | ✓ | - | 主题标签 |
| `key_events` | - | - | ✓ | - | 关键事件（幕级） |
| `narrative_arc` | - | - | ✓ | - | 叙事弧线（幕级） |
| `conflicts` | - | - | ✓ | - | 冲突列表（幕级） |
| `outline` | - | - | - | ✓ | 章节大纲 |

---

## 领域模型更新

```python
from enum import Enum
from dataclasses import dataclass, field
from typing import List, Optional
import json

class PlanningStatus(str, Enum):
    """规划状态"""
    DRAFT = "draft"              # 草稿（未规划）
    AI_GENERATED = "ai_generated"  # AI 已生成
    USER_EDITED = "user_edited"    # 用户已编辑
    CONFIRMED = "confirmed"        # 已确认

class PlanningSource(str, Enum):
    """规划来源"""
    MANUAL = "manual"        # 手动创建
    AI_MACRO = "ai_macro"    # AI 宏观规划
    AI_ACT = "ai_act"        # AI 幕级规划

@dataclass
class StoryNode:
    """故事结构节点"""
    id: str
    novel_id: str
    node_type: NodeType
    number: int
    title: str
    order_index: int
    parent_id: Optional[str] = None
    description: Optional[str] = None

    # 规划相关
    planning_status: PlanningStatus = PlanningStatus.DRAFT
    planning_source: PlanningSource = PlanningSource.MANUAL

    # 章节范围（仅用于 part/volume/act）
    chapter_start: Optional[int] = None
    chapter_end: Optional[int] = None
    chapter_count: int = 0
    suggested_chapter_count: Optional[int] = None

    # 章节内容（仅用于 chapter 类型）
    content: Optional[str] = None
    outline: Optional[str] = None
    word_count: int = 0
    status: str = "draft"

    # 结构化规划信息
    themes: List[str] = field(default_factory=list)
    key_events: List[str] = field(default_factory=list)
    narrative_arc: Optional[str] = None
    conflicts: List[str] = field(default_factory=list)

    # 扩展元数据
    metadata: dict = field(default_factory=dict)

    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        """类型转换"""
        if isinstance(self.node_type, str):
            self.node_type = NodeType(self.node_type)
        if isinstance(self.planning_status, str):
            self.planning_status = PlanningStatus(self.planning_status)
        if isinstance(self.planning_source, str):
            self.planning_source = PlanningSource(self.planning_source)

        # JSON 字段解析
        if isinstance(self.themes, str):
            self.themes = json.loads(self.themes) if self.themes else []
        if isinstance(self.key_events, str):
            self.key_events = json.loads(self.key_events) if self.key_events else []
        if isinstance(self.conflicts, str):
            self.conflicts = json.loads(self.conflicts) if self.conflicts else []

    def is_planned(self) -> bool:
        """是否已规划"""
        return self.planning_status in [
            PlanningStatus.AI_GENERATED,
            PlanningStatus.USER_EDITED,
            PlanningStatus.CONFIRMED
        ]

    def to_dict(self) -> dict:
        """转换为字典"""
        result = {
            "id": self.id,
            "novel_id": self.novel_id,
            "parent_id": self.parent_id,
            "node_type": self.node_type.value,
            "number": self.number,
            "title": self.title,
            "description": self.description,
            "order_index": self.order_index,

            # 规划相关
            "planning_status": self.planning_status.value,
            "planning_source": self.planning_source.value,

            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

        # 章节范围（仅用于 part/volume/act）
        if self.node_type != NodeType.CHAPTER:
            result.update({
                "chapter_start": self.chapter_start,
                "chapter_end": self.chapter_end,
                "chapter_count": self.chapter_count,
                "suggested_chapter_count": self.suggested_chapter_count,
                "themes": self.themes,
            })

        # 幕级字段
        if self.node_type == NodeType.ACT:
            result.update({
                "key_events": self.key_events,
                "narrative_arc": self.narrative_arc,
                "conflicts": self.conflicts,
            })

        # 章节内容（仅用于 chapter）
        if self.node_type == NodeType.CHAPTER:
            result.update({
                "content": self.content,
                "outline": self.outline,
                "word_count": self.word_count,
                "status": self.status,
            })

        return result
```

---

## 数据库迁移脚本

```python
#!/usr/bin/env python3
"""
数据库迁移：添加故事结构规划字段
"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "aitext.db"

def migrate():
    """执行迁移"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        print("添加规划相关字段...")

        # 检查字段是否已存在
        cursor.execute("PRAGMA table_info(story_nodes)")
        existing_columns = {col[1] for col in cursor.fetchall()}

        # 添加规划状态字段
        if 'planning_status' not in existing_columns:
            cursor.execute("""
                ALTER TABLE story_nodes
                ADD COLUMN planning_status TEXT DEFAULT 'draft'
                CHECK(planning_status IN ('draft', 'ai_generated', 'user_edited', 'confirmed'))
            """)
            print("✓ 添加 planning_status")

        if 'planning_source' not in existing_columns:
            cursor.execute("""
                ALTER TABLE story_nodes
                ADD COLUMN planning_source TEXT DEFAULT 'manual'
                CHECK(planning_source IN ('manual', 'ai_macro', 'ai_act'))
            """)
            print("✓ 添加 planning_source")

        # 添加章节大纲
        if 'outline' not in existing_columns:
            cursor.execute("ALTER TABLE story_nodes ADD COLUMN outline TEXT")
            print("✓ 添加 outline")

        # 添加预计章节数
        if 'suggested_chapter_count' not in existing_columns:
            cursor.execute("ALTER TABLE story_nodes ADD COLUMN suggested_chapter_count INTEGER")
            print("✓ 添加 suggested_chapter_count")

        # 添加主题
        if 'themes' not in existing_columns:
            cursor.execute("ALTER TABLE story_nodes ADD COLUMN themes TEXT")
            print("✓ 添加 themes")

        # 添加关键事件
        if 'key_events' not in existing_columns:
            cursor.execute("ALTER TABLE story_nodes ADD COLUMN key_events TEXT")
            print("✓ 添加 key_events")

        # 添加叙事弧线
        if 'narrative_arc' not in existing_columns:
            cursor.execute("ALTER TABLE story_nodes ADD COLUMN narrative_arc TEXT")
            print("✓ 添加 narrative_arc")

        # 添加冲突
        if 'conflicts' not in existing_columns:
            cursor.execute("ALTER TABLE story_nodes ADD COLUMN conflicts TEXT")
            print("✓ 添加 conflicts")

        conn.commit()
        print("\n✅ 迁移完成！")

    except Exception as e:
        conn.rollback()
        print(f"\n❌ 迁移失败: {e}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
```

---

## API 设计（简化版）

### 1. 生成宏观规划
```
POST /api/v1/structure/novels/{novel_id}/macro-plan/generate

Request:
{
  "target_chapters": 100,
  "structure_preference": {
    "parts": 3,
    "volumes_per_part": 3,
    "acts_per_volume": 3
  }
}

Response:
{
  "parts": [
    {
      "number": 1,
      "title": "第一部：起源",
      "description": "...",
      "suggested_chapter_count": 30,
      "themes": ["主题1", "主题2"],
      "volumes": [...]
    }
  ]
}
```

### 2. 确认宏观规划
```
POST /api/v1/structure/novels/{novel_id}/macro-plan/confirm

Request:
{
  "structure": [/* 用户编辑后的结构 */]
}

Response:
{
  "created_nodes": 27,
  "nodes": [/* 创建的节点列表 */]
}
```

### 3. 生成幕级规划
```
POST /api/v1/structure/acts/{act_id}/plan/generate

Response:
{
  "chapters": [
    {
      "number": 1,
      "title": "章节标题",
      "outline": "章节大纲",
      "key_points": ["要点1", "要点2"]
    }
  ],
  "narrative_arc": "叙事弧线",
  "conflicts": ["冲突1"]
}
```

### 4. 确认幕级规划
```
POST /api/v1/structure/acts/{act_id}/plan/confirm

Request:
{
  "chapters": [/* 用户编辑后的章节 */]
}

Response:
{
  "created_chapters": 5,
  "chapters": [/* 创建的章节节点 */]
}
```

---

## 总结

### 必要字段（加到表中）
- `planning_status`: 规划状态
- `planning_source`: 规划来源
- `outline`: 章节大纲
- `suggested_chapter_count`: 预计章节数
- `themes`: 主题标签
- `key_events`: 关键事件
- `narrative_arc`: 叙事弧线
- `conflicts`: 冲突列表

### 扩展字段（metadata）
- `tags`: 用户自定义标签
- `notes`: 用户备注
- `custom_fields`: 其他扩展

这样设计的好处：
1. **必要信息直接查询**：不需要解析 JSON
2. **性能更好**：可以直接在 SQL 中过滤和排序
3. **类型安全**：数据库层面有约束
4. **清晰明确**：字段用途一目了然
