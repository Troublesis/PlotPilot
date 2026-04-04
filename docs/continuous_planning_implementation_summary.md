# AI 持续规划系统 - 实现总结

## ✅ 已完成部分

### 1. 核心服务层
**文件**: `aitext/application/services/continuous_planning_service.py`

实现了统一的 `ContinuousPlanningService` 类，整合了三大功能：

#### 宏观规划
- `generate_macro_plan()` - 生成部-卷-幕结构框架
- `confirm_macro_plan()` - 确认并保存宏观规划

#### 幕级规划
- `plan_act_chapters()` - 为指定幕生成章节规划
- `confirm_act_planning()` - 确认并创建章节节点

#### AI 续规划
- `continue_planning()` - 自动判断当前幕是否完成
- `create_next_act_auto()` - 创建下一幕

### 2. API 路由层
**文件**: `aitext/interfaces/api/v1/continuous_planning_routes.py`

实现了 12 个统一的 API 接口：

#### 宏观规划 (2个)
- `POST /api/v1/planning/novels/{novel_id}/macro/generate`
- `POST /api/v1/planning/novels/{novel_id}/macro/confirm`

#### 幕级规划 (2个)
- `POST /api/v1/planning/acts/{act_id}/chapters/generate`
- `POST /api/v1/planning/acts/{act_id}/chapters/confirm`

#### AI 续规划 (2个)
- `POST /api/v1/planning/novels/{novel_id}/continue`
- `POST /api/v1/planning/acts/{act_id}/create-next`

#### 查询接口 (3个)
- `GET /api/v1/planning/novels/{novel_id}/structure`
- `GET /api/v1/planning/acts/{act_id}`
- `GET /api/v1/planning/chapters/{chapter_id}`

### 3. 前端 API 封装
**文件**: `aitext/web-app/src/api/planning.ts`

创建了 `planningApi` 对象，包含所有规划相关的 API 调用方法。

### 4. 主应用集成
**文件**: `aitext/interfaces/main.py`

- 导入新的 `continuous_planning_routes`
- 注册路由到 FastAPI 应用
- 移除旧的 `planning_routes` 导入

---

## ⬜ 待完成部分

### 1. 前端宏观规划组件
**文件**: `aitext/web-app/src/components/MacroPlanningModal.vue`

需要实现：
- 生成宏观规划表单
- 结构树编辑器
- 确认并保存功能

### 2. 前端幕级规划组件
**文件**: `aitext/web-app/src/components/ActPlanningModal.vue`

需要实现：
- 生成章节规划表单
- 章节列表编辑器
- Bible 元素选择器
- 确认并创建功能

### 3. 结构树右键菜单
**文件**: `aitext/web-app/src/components/StoryStructureTree.vue`

需要添加：
- 右键菜单（规划章节、编辑、删除）
- 调用幕级规划弹窗

### 4. AI 续规划集成
**文件**: `aitext/web-app/src/views/Workbench.vue` 或章节生成相关文件

需要实现：
- 章节生成完成后自动调用 `continuePlanning` API
- 根据返回结果显示提示
- 询问用户是否创建新幕

---

## 🔄 工作流程

### 用户视角的完整流程

```
1. 创建小说 + 生成 Bible
   ↓
2. 点击"开始宏观规划"
   ↓
3. AI 生成部-卷-幕结构
   ↓
4. 用户编辑并确认
   ↓
5. 在结构树中右键点击某个幕
   ↓
6. 选择"规划章节"
   ↓
7. AI 生成章节规划（包含大纲、人物、地点）
   ↓
8. 用户编辑并确认
   ↓
9. 开始写作第 1-5 章
   ↓
10. 写完第 5 章后，系统自动判断
    ↓
11. 提示"第一幕已完成，是否开始第二幕？"
    ↓
12. 用户确认，AI 创建第二幕
    ↓
13. 循环往复...
```

---

## 📝 API 使用示例

### 1. 宏观规划
```typescript
// 生成宏观规划
const result = await planningApi.generateMacro('novel-123', {
  target_chapters: 100,
  structure: {
    parts: 3,
    volumes_per_part: 3,
    acts_per_volume: 3
  }
})

// 用户编辑 result.structure...

// 确认规划
await planningApi.confirmMacro('novel-123', {
  structure: editedStructure
})
```

### 2. 幕级规划
```typescript
// 生成章节规划
const result = await planningApi.generateActChapters('act-123', {
  chapter_count: 5
})

// 用户编辑 result.chapters...

// 确认规划
await planningApi.confirmActChapters('act-123', {
  chapters: editedChapters
})
```

### 3. AI 续规划
```typescript
// 写完章节后自动调用
const result = await planningApi.continuePlanning('novel-123', {
  current_chapter: 5
})

if (result.act_completed && result.suggest_create_next) {
  // 询问用户是否创建新幕
  const confirmed = await dialog.confirm('第一幕已完成，是否创建下一幕？')

  if (confirmed) {
    const nextAct = await planningApi.createNextAct(result.current_act.id)
    // 显示成功提示
  }
}
```

---

## 🎯 下一步工作

按优先级排序：

1. **P0**: 实现前端宏观规划组件（MacroPlanningModal.vue）
2. **P0**: 实现前端幕级规划组件（ActPlanningModal.vue）
3. **P1**: 在结构树中添加右键菜单
4. **P1**: 集成 AI 续规划到章节生成流程
5. **P2**: 完善提示词（目前是简化版）
6. **P2**: 添加错误处理和加载状态
7. **P3**: 添加单元测试

---

## 📊 代码统计

- 核心服务: ~400 行
- API 路由: ~200 行
- 前端 API: ~60 行
- 总计: ~660 行

---

## ✨ 核心优势

1. **统一接口**: 不再有重复的规划功能
2. **分层设计**: 宏观 → 幕级 → 续规划，清晰明确
3. **可编辑**: 所有 AI 生成的内容都可以编辑后确认
4. **Bible 集成**: 章节规划自动关联人物、地点、道具
5. **自动化**: AI 自动判断何时创建新幕

---

## 🐛 已知问题

1. LLM 提示词是简化版，需要完善
2. 错误处理不够完善
3. 缺少前端组件实现
4. 缺少单元测试

---

## 📚 相关文档

- 设计文档: `aitext/docs/story_structure_complete_design.md`
- API 对比: `aitext/docs/api_comparison_plan_vs_initialize.md`
