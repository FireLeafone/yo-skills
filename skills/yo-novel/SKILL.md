---
name: yo-novel
description: >
  Yo-Novel 技能集合的入口索引。当用户输入 `/yo-novel` 或提及 "yo-novel" 时触发。
  用于根据用户意图自动匹配并调用对应的子技能。
  用户可以通过 `/yo-novel <子技能名> [target]` 显式指定，也可以只输入 `/yo-novel` 由本技能自动推断最合适的子技能。
argument-hint: "[{{sub_skill}}] [target]"
---

# Yo-Novel 技能索引

Yo-Novel 是多个小说编写辅助技能的集合入口。根据你的需求，自动路由到最合适的子技能。

## 可用子技能

**可以使用 `/yo-novel help` 列出下面所有子技能**

| 子技能 | 路径 | 用途 | 典型触发语 |
|--------|------|------|-----------|
| novel-create | `reference/novel-create/SKILL.md` | 初始化小说项目，创建标准目录结构与文件模板 | "我想写本小说"、"新建小说项目"、"novel project setup" |
| novel-design | `reference/novel-design/SKILL.md` | 小说动笔前的设计规划：大纲、世界观、人物、主题等 | "设计小说"、"写大纲"、"世界观设定"、"人物设定"、"novel design" |
| novel-write | `reference/novel-write/SKILL.md` | 基于大纲与设定撰写或续写小说章节正文 | "写第 X 章"、"续写小说"、"开始写正文"、"novel chapter"、"write chapter" |
| novel-chapters | `reference/novel-chapters/SKILL.md` | 按卷规划小说章节：主题、说明、人物、阶段章节划分与伏笔清单 | "分卷"、"章节规划"、"卷规划"、"划分章节"、"按卷写大纲" |
| novel-progress | `reference/novel-progress/SKILL.md` | 更新 `progress.md` 进度追踪表（章节、人物、时间线、伏笔） | "更新进度"、"progress.md"、"写完第 X 章"、"标记大纲完成"、"新增伏笔" |
| novel-style | `reference/novel-style/SKILL.md` | 从一本已有小说逆向提取写作风格档案：联网检索书评 + 多维度总结 + 防跑偏清单，输出 【书名】-style-skill.md | "提取 XX 小说的写作风格"、"分析 XX 文风"、"仿写 XX 风格"、"生成 XX 风格指南"、"XX 风格 skill"、"novel style guide" |
| novel-storyline | `reference/novel-storyline/SKILL.md` | 把小说/书籍/文章总结为 Git 分支式"人物进程图"交互 HTML：人物彩色进程线 + 事件节点 + 交汇分开 + 时间轴 + 图例显隐 | "人物进程图"、"人物情节线"、"故事线可视化"、"把小说画成图"、"总结小说人物线"、"人物命运走向" |

## 路由规则

### 1. 显式指定（优先）

如果用户输入包含 `/yo-novel <子技能名>`，直接使用对应子技能。

例如：
- `/yo-novel novel-create` → 使用 `reference/novel-create/SKILL.md`
- `/yo-novel novel-design` → 使用 `reference/novel-design/SKILL.md`
- `/yo-novel novel-write` → 使用 `reference/novel-write/SKILL.md`
- `/yo-novel novel-chapters` → 使用 `reference/novel-chapters/SKILL.md`
- `/yo-novel novel-progress` → 使用 `reference/novel-progress/SKILL.md`
- `/yo-novel novel-style` → 使用 `reference/novel-style/SKILL.md`
- `/yo-novel novel-storyline` → 使用 `reference/novel-storyline/SKILL.md`

### 2. 自动推断

如果用户没有显式指定子技能，根据意图关键词自动推断：

- **创建 / 初始化 / 新建小说项目** → `novel-create`
  - 关键词示例："创建小说"、"新建小说项目"、"初始化小说"、"小说项目结构"、"开始写小说"、"novel project"、"setup novel"
- **设计 / 规划 / 大纲 / 设定** → `novel-design`
  - 关键词示例："设计小说"、"小说设定"、"写大纲"、"世界观"、"人物设定"、"角色设定"、"核心主题"、"novel design"、"novel outline"、"world building"、"character design"
- **写正文 / 写章节 / 续写** → `novel-write`
  - 关键词示例："写第 X 章"、"写一章"、"续写小说"、"开始写正文"、"novel chapter"、"write chapter"、"continue novel"、"next chapter"
- **分卷 / 章节规划 / 卷规划 / 按卷划分章节** → `novel-chapters`
  - 关键词示例："分卷"、"章节规划"、"卷规划"、"划分章节"、"volume planning"、"chapter outline by volume"、"按卷写大纲"、"规划章节"
- **更新进度 / 进度表 / 伏笔回收** → `novel-progress`
  - 关键词示例："更新进度"、"进度表"、"progress.md"、"写完第 X 章"、"标记大纲完成"、"新增伏笔"、"回收伏笔"
- **提取风格 / 分析文风 / 仿写风格 / 风格指南** → `novel-style`
  - 关键词示例："提取小说风格"、"分析写作风格"、"总结文风"、"仿写 XX 风格"、"生成风格指南"、"XX 风格 skill"、"风格档案"、"novel style guide"、"style extraction"、"learn writing style from"
- **人物进程图 / 故事线可视化 / 人物情节总结** → `novel-storyline`
  - 关键词示例："人物进程图"、"人物情节线"、"故事线可视化"、"人物关系时间线"、"把小说画成图"、"总结小说里每个人物的经历"、"人物命运走向"、"git 分支图 人物"、"storyline visualization"、"character map"

## 工作流程

1. **解析用户输入**：检查是否包含 `/yo-novel <子技能名>` 的显式指定
2. **匹配子技能**：
   - 显式指定 → 直接使用对应子技能
   - 未指定 → 根据意图关键词自动推断
3. **加载并执行**：读取对应子技能的 SKILL.md，按其子技能的指令完成任务
4. **结果汇总**：将子技能的执行结果返回给用户

## 注意事项

- 本技能本身不执行具体任务，只负责路由到正确的子技能
- 子技能在 `reference/` 目录下
- 子技能的详细工作流程和规则，请参考各自的 SKILL.md
