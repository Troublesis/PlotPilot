-- SQLite — 业务数据均为关系列/子表，不在库内存 JSON 文本列（Bible 等文件存储另议）

CREATE TABLE IF NOT EXISTS novels (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    slug TEXT UNIQUE NOT NULL,
    target_chapters INTEGER NOT NULL DEFAULT 0,
    premise TEXT DEFAULT '',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS chapters (
    id TEXT PRIMARY KEY,
    novel_id TEXT NOT NULL,
    number INTEGER NOT NULL,
    title TEXT,
    content TEXT,
    outline TEXT,
    status TEXT DEFAULT 'draft',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (novel_id) REFERENCES novels(id) ON DELETE CASCADE,
    UNIQUE(novel_id, number)
);

-- 三元组主行（无 JSON 列）
CREATE TABLE IF NOT EXISTS triples (
    id TEXT PRIMARY KEY,
    novel_id TEXT NOT NULL,
    subject TEXT NOT NULL,
    predicate TEXT NOT NULL,
    object TEXT NOT NULL,
    chapter_number INTEGER,
    note TEXT,
    entity_type TEXT,
    importance TEXT,
    location_type TEXT,
    description TEXT,
    first_appearance INTEGER,
    confidence REAL,
    source_type TEXT,
    subject_entity_id TEXT,
    object_entity_id TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (novel_id) REFERENCES novels(id) ON DELETE CASCADE,
    FOREIGN KEY (novel_id, chapter_number) REFERENCES chapters(novel_id, number) ON DELETE SET NULL
);

-- 除主 chapter_number 外，另有关联章节（多对多）
CREATE TABLE IF NOT EXISTS triple_more_chapters (
    triple_id TEXT NOT NULL,
    novel_id TEXT NOT NULL,
    chapter_number INTEGER NOT NULL,
    PRIMARY KEY (triple_id, chapter_number),
    FOREIGN KEY (triple_id) REFERENCES triples(id) ON DELETE CASCADE,
    FOREIGN KEY (novel_id, chapter_number) REFERENCES chapters(novel_id, number) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS triple_tags (
    triple_id TEXT NOT NULL,
    tag TEXT NOT NULL,
    PRIMARY KEY (triple_id, tag),
    FOREIGN KEY (triple_id) REFERENCES triples(id) ON DELETE CASCADE
);

-- 扩展键值，值一律 TEXT（非 JSON）
CREATE TABLE IF NOT EXISTS triple_attr (
    triple_id TEXT NOT NULL,
    attr_key TEXT NOT NULL,
    attr_value TEXT NOT NULL DEFAULT '',
    PRIMARY KEY (triple_id, attr_key),
    FOREIGN KEY (triple_id) REFERENCES triples(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS knowledge (
    id TEXT PRIMARY KEY,
    novel_id TEXT UNIQUE NOT NULL,
    version INTEGER DEFAULT 1,
    premise_lock TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (novel_id) REFERENCES novels(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS chapter_summaries (
    id TEXT PRIMARY KEY,
    knowledge_id TEXT NOT NULL,
    chapter_number INTEGER NOT NULL,
    summary TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (knowledge_id) REFERENCES knowledge(id) ON DELETE CASCADE,
    UNIQUE(knowledge_id, chapter_number)
);

CREATE INDEX IF NOT EXISTS idx_chapters_novel_id ON chapters(novel_id);
CREATE INDEX IF NOT EXISTS idx_chapters_number ON chapters(novel_id, number);
CREATE INDEX IF NOT EXISTS idx_triples_novel_id ON triples(novel_id);
CREATE INDEX IF NOT EXISTS idx_triples_subject ON triples(novel_id, subject);
CREATE INDEX IF NOT EXISTS idx_triples_predicate ON triples(predicate);
CREATE INDEX IF NOT EXISTS idx_triples_entity_type ON triples(novel_id, entity_type);
CREATE INDEX IF NOT EXISTS idx_triples_chapter ON triples(novel_id, chapter_number);
CREATE INDEX IF NOT EXISTS idx_triples_source ON triples(novel_id, source_type);
CREATE INDEX IF NOT EXISTS idx_triple_more_chapters_triple ON triple_more_chapters(triple_id);
CREATE INDEX IF NOT EXISTS idx_triple_tags_triple ON triple_tags(triple_id);
CREATE INDEX IF NOT EXISTS idx_triple_attr_triple ON triple_attr(triple_id);
CREATE INDEX IF NOT EXISTS idx_chapter_summaries_knowledge_id ON chapter_summaries(knowledge_id);

-- 三元组溯源：关联 story_nodes / chapter_elements（推断证据链，非 JSON 列）
CREATE TABLE IF NOT EXISTS triple_provenance (
    id TEXT PRIMARY KEY,
    triple_id TEXT NOT NULL,
    novel_id TEXT NOT NULL,
    story_node_id TEXT,
    chapter_element_id TEXT,
    rule_id TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'primary',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (triple_id) REFERENCES triples(id) ON DELETE CASCADE,
    FOREIGN KEY (novel_id) REFERENCES novels(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_triple_provenance_triple ON triple_provenance(triple_id);
CREATE INDEX IF NOT EXISTS idx_triple_provenance_novel ON triple_provenance(novel_id);
CREATE INDEX IF NOT EXISTS idx_triple_provenance_story_node ON triple_provenance(story_node_id);

-- 同一三元组下同规则+章节节点+元素行只保留一条（INSERT OR IGNORE 依赖）
CREATE UNIQUE INDEX IF NOT EXISTS ux_triple_provenance_with_element
ON triple_provenance (triple_id, rule_id, story_node_id, chapter_element_id)
WHERE chapter_element_id IS NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS ux_triple_provenance_null_element
ON triple_provenance (triple_id, rule_id, IFNULL(story_node_id, ''))
WHERE chapter_element_id IS NULL;

-- 故事结构（知识图谱推断依赖；不设 characters/locations 外键以免缺表）
CREATE TABLE IF NOT EXISTS story_nodes (
    id TEXT PRIMARY KEY,
    novel_id TEXT NOT NULL,
    parent_id TEXT,
    node_type TEXT NOT NULL CHECK(node_type IN ('part', 'volume', 'act', 'chapter')),
    number INTEGER NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    order_index INTEGER NOT NULL,
    planning_status TEXT DEFAULT 'draft'
      CHECK(planning_status IN ('draft', 'ai_generated', 'user_edited', 'confirmed')),
    planning_source TEXT DEFAULT 'manual'
      CHECK(planning_source IN ('manual', 'ai_macro', 'ai_act')),
    chapter_start INTEGER,
    chapter_end INTEGER,
    chapter_count INTEGER DEFAULT 0,
    suggested_chapter_count INTEGER,
    content TEXT,
    outline TEXT,
    word_count INTEGER DEFAULT 0,
    status TEXT DEFAULT 'draft',
    themes TEXT,
    key_events TEXT,
    narrative_arc TEXT,
    conflicts TEXT,
    pov_character_id TEXT,
    timeline_start TEXT,
    timeline_end TEXT,
    metadata TEXT DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (novel_id) REFERENCES novels(id) ON DELETE CASCADE,
    FOREIGN KEY (parent_id) REFERENCES story_nodes(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_story_nodes_novel_id ON story_nodes(novel_id);

CREATE TABLE IF NOT EXISTS chapter_elements (
    id TEXT PRIMARY KEY,
    chapter_id TEXT NOT NULL,
    element_type TEXT NOT NULL CHECK(element_type IN ('character', 'location', 'item', 'organization', 'event')),
    element_id TEXT NOT NULL,
    relation_type TEXT NOT NULL CHECK(relation_type IN (
        'appears', 'mentioned', 'scene', 'uses', 'involved', 'occurs'
    )),
    importance TEXT DEFAULT 'normal' CHECK(importance IN ('major', 'normal', 'minor')),
    appearance_order INTEGER,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (chapter_id) REFERENCES story_nodes(id) ON DELETE CASCADE,
    UNIQUE(chapter_id, element_type, element_id, relation_type)
);

CREATE INDEX IF NOT EXISTS idx_chapter_elements_chapter ON chapter_elements(chapter_id);
CREATE INDEX IF NOT EXISTS idx_chapter_elements_element ON chapter_elements(element_type, element_id);

CREATE TABLE IF NOT EXISTS chapter_scenes (
    id TEXT PRIMARY KEY,
    chapter_id TEXT NOT NULL,
    scene_number INTEGER NOT NULL,
    location_id TEXT,
    timeline TEXT,
    summary TEXT,
    purpose TEXT,
    content TEXT,
    word_count INTEGER DEFAULT 0,
    characters TEXT,
    order_index INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (chapter_id) REFERENCES story_nodes(id) ON DELETE CASCADE,
    UNIQUE(chapter_id, scene_number)
);

CREATE INDEX IF NOT EXISTS idx_chapter_scenes_chapter ON chapter_scenes(chapter_id);
