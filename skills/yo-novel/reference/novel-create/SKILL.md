---
name: novel-create
description: >
  初始化小说项目并创建标准目录结构与文件模板，或对小说进行动笔前的系统性设计规划（故事大纲、世界观、人物、核心主题等）。
  当用户提到"创建小说"、"新建小说项目"、"初始化小说"、"小说项目结构"、"开始写小说"、"novel project"、"setup novel"，
  或"设计小说"、"小说设定"、"写大纲"、"世界观"、"人物设定"、"角色设定"、"核心主题"、"故事大纲"、
  "novel design"、"novel outline"、"world building"或类似意图时触发。
  适用于从零搭建小说写作工程，或在已有工程里做前期设计规划；不适用于已开始正文写作后的续写、润色、修改，也不适用于只闲聊点子而不落盘文档。
---

# novel-create

novel-create 承担两项职责：**初始化一个标准、可维护的小说写作项目**（创建目录结构并填充起始模板），以及**动笔前的系统性设计规划**（大纲、世界观、人物、主题等）。两者可独立使用，也可串联：先搭骨架，再在其中做设计。

## When to Use

- 用户说"我想写本小说"、"帮我创建小说项目"、"初始化一个小说工程"——走**路径A：快速搭骨架**。
- 用户说"设计小说"、"写大纲"、"世界观设定"、"人物设定"、"角色设定"、"核心主题"、"故事大纲"、"novel design"、"world building"、"character design"、"story bible"——走**路径B：设计规划**。
- 用户既要建项目又要做设计——先 A 再 B。

## 输出位置

- 项目根目录默认在当前目录下创建 `ai-novel-<小说名>/`；用户指定目录则用指定目录。
- 设计文档默认输出到项目根目录下的 `presets/` 目录。
- 如果目标目录/文件已存在同名，**必须先询问用户是覆盖、合并还是跳过/中止**，禁止直接覆盖。

## 设计文档清单

设计规划时生成以下一个或多个文档，文件名与模板对应关系如下（路径A 会把对应模板作为起手骨架复制到 `presets/`）：

| 文档 | 输出文件 | 模板 |
|------|----------|------|
| 故事大纲 | `presets/outline.md` | `assets/presets/outline.md.template` |
| 人物设定 | `presets/characters.md` | `assets/presets/characters.md.template` |
| 世界观设定 | `presets/world.md` | `assets/presets/world.md.template` |
| 核心主题 | `presets/themes.md` | `assets/presets/themes.md.template` |
| 其他设定 | `presets/settings.md` | `assets/presets/settings.md.template` |
| 伏笔设计 | `presets/foreshadowing.md` | `assets/presets/foreshadowing.md.template` |

类型化设计指导参考 `references/novel-type.md`。

## 标准目录结构（路径A）

在项目根目录下创建：

```text
<project-root>/
├── AGENTS.md
├── rules.md
├── progress.md
├── checked.md
├── references.md
├── count_words.py
├── presets/
│   ├── outline.md
│   ├── characters.md
│   ├── world.md
│   ├── themes.md
│   ├── settings.md
│   ├── foreshadowing.md
│   └── check_dialogue_density.py
└── chapters/
    └── .gitkeep
```

`chapters/volume-NN/index.md` 分卷细纲与 `chapters/index.md` 全书总览由 `novel-chapters` 技能生成，路径A 阶段只创建空的 `chapters/` 目录。

## Workflow

### 路径选择

- 用户要从零建立工程 → **路径A**（可接路径B 继续设计）。
- 用户要在已有/新建工程里做大纲、基础人物、世界观、主题等整体设计 → **路径B**。
- 用户只要求深化主角、配角、反派、人物关系或弧光 → 转 **novel-character**，本技能不重复承担专项人物设计。
- 用户既要工程又要设计 → 先 A 再 B。伏笔登记以 `presets/foreshadowing.md` 为唯一数据源，其他文档只保留必要的摘要或引用。

### 路径A：快速搭骨架

1. **确认项目根目录（硬性门槛）**
   - 若用户指定目录，使用该目录；否则默认在当前目录下创建 `ai-novel-<小说名>/`。
   - 小说名从用户输入中提取；未提供则询问一个简短的小说名（英文或拼音，用于目录名）。
   - **创建任何文件前**，向用户展示计划创建的项目根目录与文件清单，等待用户明确回复（"确认""开始""ok"）后再继续。
   - **若目标目录已存在**：停止并询问用户是覆盖、合并还是中止；禁止直接覆盖。

2. **创建标准目录结构**
   - 按上方"标准目录结构"创建目录与文件。

3. **初始化文件内容**
   - 从本 skill 目录下的 `assets/` 中复制对应模板文件到目标项目。
   - 仅将 `<小说名>`、`<类型>`、`<创建日期>` 三个占位符替换为用户提供的实际值；不要改写、增删或润色模板中的其他文字。
   - 若用户未提供类型，使用"未指定类型"；若未提供日期，使用当前日期（YYYY-MM-DD）。
   - 这样做的目的是保证所有 novel-create 生成的项目具有一致的结构和可预测的参考文档，方便后续 AI Agent 协作。

4. **报告结果**
   - 列出已创建的文件与目录，简要说明每个核心文件的作用。
   - 提示用户下一步可进入路径B 填充 `presets/outline.md`、`presets/characters.md` 等，或直接打开模板填写。

### 路径B：设计规划

1. **理解需求**
   - 识别用户想设计的部分：大纲、人物、世界观、主题、其他设定。
   - 识别小说类型（如果没有，询问用户）。
   - 识别用户已有的灵感或约束（主角名字、关键设定、结局倾向等）。

2. **确认设计计划（硬性门槛，但允许快速路径）**
   - **常规路径**：向用户展示设计计划——计划生成的文档清单、每个文档覆盖的主要内容、文件存放路径。等待用户明确回复（"确认""开始""ok"）后再继续。
   - **快速路径**：用户已明确指定单一文档（如"只写人物设定"）且信息足够，可直接生成，但仍需先告知将创建哪个文件并等待确认。

   设计计划示例：

   ```markdown
   计划为这本都市言情小说生成以下设计文档，存放在 `presets/`：
   - `presets/characters.md` — 女主（律师）、男主（咖啡店老板）的角色卡与关系网
   - `presets/outline.md` — 情感线大纲，从重逢到和解的关键节点
   - `presets/themes.md` — 核心主题与情感基调

   确认后我开始生成。
   ```

3. **头脑风暴与讨论**
   - 不要一次性输出完整文档后结束。
   - 对关键设计选择，先给出 2-3 个可选方案或方向，说明利弊，邀请用户确认。
   - 当用户提出修改时，立即更新对应部分，并检查是否与其他部分冲突。

4. **生成设计文档**
   - 按确认的计划使用对应模板结构生成文档。
   - 内容完整、逻辑清晰、设定合理。
   - 保持类型一致性：参考 `references/novel-type.md`。

5. **自洽性检查**
   - 世界规则是否自相矛盾。
   - 人物动机是否与目标、背景一致。
   - 大纲节点是否依赖尚未建立的设定。
   - 如发现冲突，向用户指出并给出修改建议。

6. **报告结果**
   - 列出已生成的文件及路径，简要说明每个文件的内容重点。
   - 提示用户下一步可以开始基于这些设计写正文（`novel-write`）或按卷规划章节（`novel-chapters`）。

## Asset Files

本 skill 目录下 `assets/` 中存放了创建项目所需的模板与脚本：

- `assets/AGENTS.md.template` → 项目 `AGENTS.md`
- `assets/rules.md.template` → 项目 `rules.md`
- `assets/progress.md.template` → 项目 `progress.md`
- `assets/checked.md.template` → 项目 `checked.md`
- `assets/references.md.template` → 项目 `references.md`
- `assets/presets/outline.md.template` → 项目 `presets/outline.md`（结构化富模板：三幕大纲、角色、世界观、分卷、伏笔设计期总览）
- `assets/presets/characters.md.template` → 项目 `presets/characters.md`（结构化富模板：心理维度、关系网、角色弧线）
- `assets/presets/world.md.template` → 项目 `presets/world.md`（结构化富模板：地理/社会/文化/体系/历史/势力）
- `assets/presets/themes.md.template` → 项目 `presets/themes.md`（核心主题、情感基调、冲突、价值观）
- `assets/presets/settings.md.template` → 项目 `presets/settings.md`（命名术语、关键道具、待解决问题）
- `assets/presets/foreshadowing.md.template` → 项目 `presets/foreshadowing.md`（伏笔唯一数据源：登记规则、状态图例、伏笔总表）
- `assets/presets/check_dialogue_density.py` → 项目 `presets/check_dialogue_density.py`（章节字数与对话密度检查脚本）
- `assets/count_words.py` → 项目 `count_words.py`

## Output Format

完成后返回一段简洁的 Markdown 清单，例如：

```markdown
已创建小说项目 `ai-novel-<小说名>/`，结构如下：

- `AGENTS.md` — AI 编写指南（核心文档）
- `rules.md` — 写作规范要求
- `progress.md` — 进度追踪
- `checked.md` — 章节检查清单
- `references.md` — 参考资料、灵感、优秀小说作品等
- `count_words.py` — 字数统计脚本
- `presets/` — 大纲、人物、世界观、主题、其他设定、伏笔清单与对话密度检查脚本
- `chapters/` — 章节正文目录（分卷细纲由 novel-chapters 生成）

下一步建议：进入设计规划填充 `presets/outline.md`。
```

## 构建原则

1. **内部一致性**：规则不能自相矛盾。
2. **服务故事**：世界为故事服务，不要过度构建。
3. **展示而非讲述**：通过情节展现世界，不要只写说明文。
4. **留有空间**：给读者和后续创作保留想象空间。

## Gotchas / Common Mistakes

- 在没有确认小说名的情况下就用"novel"作为目录名 → 先询问小说名。
- 在创建/落盘前没有展示清单并等待用户确认 → 必须先确认再落盘。
- 目标目录或 `presets/` 下已有同名文件却不提示用户 → 必须询问覆盖、合并还是中止/跳过。
- 把正文直接写进 `presets/` 下 → 正文应放入 `chapters/`。
- 遗漏 `count_words.py`、`AGENTS.md`、`rules.md`、`checked.md`、`references.md`、`presets/foreshadowing.md` 和 `presets/check_dialogue_density.py` → 按 Asset Files 完整复制。
- 没有从 `assets/` 复制模板，而是自行发挥重写 AGENTS.md / progress.md 等 → 这会破坏跨项目一致性，必须严格按模板输出；路径A 只替换三个占位符，不润色其他文字。
- 把伏笔登记进 `presets/settings.md` 或 `progress.md` → 伏笔唯一数据源是 `presets/foreshadowing.md`，其他文件只保留设计期总览。
- 在路径A 阶段往模板里塞大量小说设定或剧情内容 → 初始化阶段只填充模板占位符，具体设定由路径B 或用户后续填写。
- 路径B 信息不足时直接落盘 5 个完整文档 → 用户只给一句话灵感时，先进入头脑风暴，而不是直接落盘。
- 修改人物设定后不回头检查大纲和世界规则 → 保持跨文档一致。

## 参考文档

- `references/novel-type.md` — 不同类型小说（玄幻/科幻/悬疑/言情/都市/历史/恐怖等）的设计侧重点与常见结构。
