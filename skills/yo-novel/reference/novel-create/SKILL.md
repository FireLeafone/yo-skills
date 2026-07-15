---
name: novel-create
description: >
  初始化小说项目并创建标准目录结构与文件模板。
  当用户提到"创建小说"、"新建小说项目"、"初始化小说"、"小说项目结构"、"开始写小说"、"novel project"、"setup novel" 或类似意图时触发。
  适用于从零开始建立小说写作工程；不适用于已有小说项目的修改、续写、润色或单纯的内容生成。
---

# novel-create

初始化一个标准、可维护的小说写作项目，创建目录结构并填充必要的起始文件与模板。

## When to Use

- 用户说"我想写本小说"、"帮我创建小说项目"、"初始化一个小说工程"
- 用户提到"小说项目结构"、"novel project setup"、"novel template"
- 用户给出小说名称或类型，并希望得到可开始写作的工程骨架

When NOT to use:

- 用户已经有一个小说项目，只想修改、续写、润色或生成单章内容（使用 yo-novel 或其他相关技能）
- 用户只是询问写作技巧、剧情建议、人物设定等纯内容问题

## Workflow

1. **确认项目根目录（硬性门槛）**
   - 如果用户指定了目录，使用该目录；否则默认在项目当前目录下创建 `ai-novel-<小说名>/`。
   - 小说名从用户输入中提取；如果用户未提供，询问一个简短的小说名（英文或拼音，用于目录名）。
   - **创建任何文件前**，向用户展示计划创建的项目根目录与文件清单，等待用户明确回复（如"确认"、"开始"、"ok"）后再继续。
   - **若目标目录已存在**：必须停止并询问用户是覆盖、合并还是中止；禁止直接覆盖。

2. **创建标准目录结构**
   在项目根目录下创建：
   ```
   <project-root>/
   ├── AGENTS.md
   ├── rules.md
   ├── progress.md
   ├── checked.md
   ├── README.md
   ├── count_words.py
   ├── presets/
   │   ├── outline.md
   │   ├── characters.md
   │   ├── world.md
   │   └── settings.md
   └── chapters/
       └── .gitkeep
   ```

3. **初始化文件内容**
   - 从本 skill 目录下的 `assets/` 中复制对应模板文件到目标项目。
   - 仅将 `<小说名>`、`<类型>`、`<创建日期>` 三个占位符替换为用户提供的实际值；不要改写、增删或润色模板中的其他文字。
   - 若用户未提供类型，使用"未指定类型"；若未提供日期，使用当前日期（YYYY-MM-DD）。
   - 这样做的目的是保证所有 novel-create 生成的项目具有一致的结构和可预测的参考文档，方便后续 AI Agent 协作。

4. **报告结果**
   - 列出已创建的文件与目录。
   - 简要说明每个核心文件的作用。
   - 提示用户下一步可以填写 `presets/outline.md`、`presets/characters.md` 与 `rules.md`。

## Asset Files

本 skill 目录下 `assets/` 中存放了创建项目所需的模板与脚本：

- `assets/AGENTS.md.template` → 项目 `AGENTS.md`
- `assets/rules.md.template` → 项目 `rules.md`
- `assets/README.md.template` → 项目 `README.md`
- `assets/progress.md.template` → 项目 `progress.md`
- `assets/checked.md.template` → 项目 `checked.md`
- `assets/presets/outline.md.template` → 项目 `presets/outline.md`
- `assets/presets/characters.md.template` → 项目 `presets/characters.md`
- `assets/presets/world.md.template` → 项目 `presets/world.md`
- `assets/presets/settings.md.template` → 项目 `presets/settings.md`
- `assets/count_words.py` → 项目 `count_words.py`

## Output Format

完成后返回一段简洁的 Markdown 清单，例如：

```markdown
已创建小说项目 `ai-novel-<小说名>/`，结构如下：

- `AGENTS.md` — AI 编写指南（核心文档）
- `rules.md` — 写作规范要求
- `progress.md` — 进度追踪
- `checked.md` — 章节检查清单
- `count_words.py` — 字数统计脚本
- `presets/` — 大纲、人物、世界观、其他设定等
- `chapters/` — 章节正文目录

下一步建议：打开 `presets/outline.md` 填写故事大纲。
```

## Common Mistakes

- 在没有确认小说名的情况下就用"novel"作为目录名 → 先询问小说名。
- 在创建前没有展示清单并等待用户确认 → 必须先确认再落盘。
- 目标目录已存在却不提示用户 → 必须询问覆盖、合并还是中止。
- 把正文直接写进 `presets/` 下 → 正文应放入 `chapters/`。
- 遗漏 `count_words.py`、`AGENTS.md`、`rules.md` 或 `checked.md` → 按 Asset Files 完整复制。
- 没有从 `assets/` 复制模板，而是自行发挥重写 AGENTS.md / README.md / progress.md 等 → 这会破坏跨项目一致性，必须严格按模板输出。
- 在模板外额外添加大量小说设定或剧情内容 → 初始化阶段只填充模板占位符，具体设定由用户后续填写。
