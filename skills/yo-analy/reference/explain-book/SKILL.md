---
name: explain-book
description: "将书籍与文档（PDF、DOCX、HTML、Markdown、纯文本需 Calibre）解析为结构化知识库：框架大纲、设定（人物/等级/社会/环境）、心智模型、原则、写作风格、技巧与反模式；虚构与非虚构自动路由。当用户想深度解析一本书、提炼小说世界观与设定、学习作者的写作手法，或把书籍变成可反复查询调用的知识库时使用。"
---

# explain-book · 书籍知识解析器

把一本书解析成结构化知识库 —— 提取结构，而不是写读后感。

## 解析哲学

书籍（无论虚构还是非虚构）凝结了两类知识：**方法论知识**（框架、心智模型、原则、技巧、反模式）与**设定知识**（人物、等级体系、社会、环境、世界观）。本 skill 把这两类知识提取为 agent 可反复调用的格式。

**提取结构，不是写摘要。** 知识库不是读书报告，而是工具箱：
- 框架大纲（全书的结构地图：论证主线或情节脉络）
- 设定集（人物档案、等级/力量体系、社会与环境）
- 心智模型（"当 Y 时用 X"的思考工具）
- 原则（指导决策的规则）
- 写作风格（作者如何表达：视角、节奏、语言、标志性手法）
- 技巧（可复用的方法/手法）
- 反模式（应当避免的做法及其原因）

**保留原名精度。** 框架名、境界名、招式名、地名、组织名保持原文 —— "筑基期"不可泛化为"中级阶段"，"5 Whys"不可写成"多问几次为什么"。

**深度分层。** 小书出小库；大部头（10+ 框架或复杂世界观）出带章节文件、按需加载的完整知识库。

---

## 运行模式

按用户意图路由，共三种模式：

### 1. 完整解析（默认）
**触发：** 用户提供文档/目录/glob 路径，无特殊指令
**动作：** 执行下方全部步骤（Step 0–10）
**产出：** 完整知识库 skill（SKILL.md + chapters/ + outline + settings/ + 各支撑文件）

### 2. 仅解析报告
**触发：** 用户说"只解析""先分析""我想先看看再生成"
**动作：** 执行 Step 0–3，产出结构化解析报告（发现的框架、设定、原则、技巧）。停止 —— 不生成知识库文件。
**产出：** 供用户审阅的解析报告

### 3. 更新 / 合并（已有知识库）
**触发：** 用户提供新来源（如系列小说的下一卷、修订版），并指向已有知识库目录或已有 slug
**动作：** 执行 Step 0、1、1.5、2，然后跳到 Step 5 识别已有路径，走 **更新/合并流程**（见文末）
**产出：** 合并后的更新版知识库

---

## 生成的知识库的位置

**生成的知识库写到哪里**，用户未指定，则默认当前项目下的`explain-book`目录。

---

## Step 0 — 输入检查

未提供任何参数时，停止并回复：
> "explain-book 需要文档路径、目录或 glob 模式。用法：`explain-book <文档路径|目录|glob>... [知识库名称slug]`"

整个流程中：
- 识别输入路径与可选 slug。
- 最后一个参数若不是已存在的文件/目录/可匹配的 glob，且形似 slug（小写连字符、字母数字），视为 `SKILL_NAME`。
- 其余参数视为 `INPUT_PATHS`。
- 若任一输入路径是已生成的知识库目录（含 `SKILL.md` 与 `chapters/` 子目录），或 `SKILL_NAME` 与 `SKILLS_HOME` 中已有 slug 相同，标记为 **更新/合并**（模式 3）。

---

## Step 1 — 校验输入

确认 `INPUT_PATHS` 中至少有一个受支持的文件、目录或 glob。对目录和 glob 展开匹配支持的扩展名：`.pdf`、`.docx`、`.txt`、`.md`、`.markdown`、`.html`。

找不到受支持文件时，以明确错误信息停止。

---

## Step 1.5 — 识别内容类型（决定路由与提取方式）

提取前问用户**一个问题**：

> "这些来源属于哪种内容？这决定我用哪套解析维度和提取方式。
>
> 1. **虚构类** — 小说、网文、剧本、故事集（产出重点：设定、人物、写作风格）
> 2. **非虚构·文字类** — 商业、社科、传记、方法论等以散文为主的（产出重点：框架、心智模型、原则）
> 3. **非虚构·技术类** — 含大量代码、表格、公式（技术书、论文、架构指南）
> 4. **不确定 / 混合** — 如小说体商业书、纪实文学；我用快速提取，质量受限时提醒你"

存储答案：
- 选项 1 → `BOOK_KIND=fiction`，`EXTRACT_MODE=text`
- 选项 2 → `BOOK_KIND=nonfiction`，`EXTRACT_MODE=text`
- 选项 3 → `BOOK_KIND=nonfiction`，`EXTRACT_MODE=technical`
- 选项 4 → `BOOK_KIND=mixed`，`EXTRACT_MODE=text`

**`EXTRACT_MODE=technical` 时**告知用户：
> "📐 技术模式 —— 用 Docling 做结构感知提取（表格、代码块、公式保留为 markdown）。约 1.5 秒/页，长文档需几分钟，现在开始…"

**`EXTRACT_MODE=text` 时**告知：
> "📄 文字模式 —— 按文件类型选用最快的提取器。纯文本/Markdown/HTML 通常秒级完成；PDF 有 pdftotext 时优先使用。"

`BOOK_KIND` 决定 Step 7 用哪套章节模板、Step 8 生成哪些支撑文件：
- `fiction` → 设定集（settings/）是重点；心智模型/原则体量通常较小但不省略
- `nonfiction` → 默认不建 settings/；心智模型/原则是重点
- `mixed` → 按实际内容逐卷判断，只建确有内容的文件，并在报告中说明取舍

---

## Step 2 — 提取文本

运行提取脚本：

```bash
SCRIPT_PATH=""
for candidate in \
  "$HOME/.kimi-code/skills/explain-book/scripts/extract.py" \
  "$HOME/.copilot/skills/explain-book/scripts/extract.py" \
  "$HOME/.agents/skills/explain-book/scripts/extract.py" \
  "$HOME/.claude/skills/explain-book/scripts/extract.py" \
  ".kimi-code/skills/explain-book/scripts/extract.py" \
  ".github/skills/explain-book/scripts/extract.py" \
  ".claude/skills/explain-book/scripts/extract.py" \
  ".agents/skills/explain-book/scripts/extract.py" \
  "$HOME/.config/agents/skills/explain-book/scripts/extract.py" \
  "$HOME/.config/amp/skills/explain-book/scripts/extract.py"
do
  if [ -f "$candidate" ]; then
    SCRIPT_PATH="$candidate"
    break
  fi
done

if [ -z "$SCRIPT_PATH" ]; then
  echo "找不到 explain-book 的 scripts/extract.py" >&2
  exit 1
fi

PYTHON_BIN="${PYTHON_BIN:-python3}"
if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  PYTHON_BIN="python"
fi

"$PYTHON_BIN" "$SCRIPT_PATH" $INPUT_PATHS --mode <EXTRACT_MODE> --install-missing ask
```

提取前脚本会检查当前格式需要的可选 Python 包；缺更好的提取器时提示用户可用的降级方案。非交互会话默认降级，除非安装模式显式为 `yes`。

**提示 — 环境预检：** 运行 `"$PYTHON_BIN" "$SCRIPT_PATH" --check` 可打印各格式的提取器安装报告及缺失项的安装命令，不处理任何文件。用户报告安装或质量问题时用它。

产出：
- `<tempdir>/explain_book_work/full_text.txt` — 全部来源合并文本，来源间有清晰分界。
- `<tempdir>/explain_book_work/metadata.json` — 合并体量、词数、页数、token 估算，以及逐来源的 `sources` 明细。

读取 `metadata.json` 查看结果。（工作目录可用环境变量 `EXPLAIN_BOOK_WORKDIR` 覆盖。）

---

## Step 2.5 — 成本预估（生成前）

读 `metadata.json`，**在生成任何文件前**向用户展示预估：

```
📖 检测到来源：<total_sources> 个
<逐来源列出文件名与格式>
📄 合并页数/节数：~<N> | 词数：~<N> | 总 token：~<N>K

💰 预估 token 成本（完整解析/更新）：
   输入（阅读 + 提示词）：~<N>K tokens
   输出（生成的知识库文件）：~<N>K tokens
   合计：~<N>K tokens

   费用：将以上 token 数乘以你当前模型的每百万 token 输入/输出价格
   （价格与模型名经常变动 —— 不要硬编码；引用当日价格并注明是估算）。

   ⏱  预估耗时：~<N> 分钟

📁 将生成的文件：
   SKILL.md + chapters/ + outline.md + settings/（虚构类）
   + mental-models / principles / writing-style / techniques / anti-patterns + glossary

➡  继续完整解析？（或回复"只解析"先出报告）
```

**估算方法：**
- 输入 tokens ≈ metadata 的 `estimated_tokens` × 1.3（逐章解析的提示词开销）
- 输出 tokens ≈ 章节数 × 每章预算 + 4,000（主 SKILL.md）+ 6,000（各支撑文件合计）
  - 每章预算中位数：`text` ≈ 1,000，`technical` ≈ 1,800（Step 4 确定的 DEPTH 可能上调，见 Step 7 矩阵）
- 费用：报 token 数并按用户当前每百万 token 费率折算。不要硬编码金额 —— 若给出金额，注明是估算并标注日期。

等用户确认再继续。用户说"只解析"则切换到模式 2。

---

## Step 2.6 — 大书探测（> 50k tokens）

把 `full_text.txt` 当作可查询语料库，而不是一次性读入。整本读入会烧掉后续生成所需的预算。

超过 ~50k tokens 时，优先用程序化探测，而不是不带范围地 `Read(full_text.txt)`：

```bash
# 任何 Read 之前先看体量
wc -w "$FULL_TEXT_PATH"

# 不加载全文，定位章节偏移（中英文章节头都匹配）
grep -n -E "^\s*(第[0-9一二三四五六七八九十百千零两]+[章回节卷部]|Chapter [0-9]+|CHAPTER [0-9]+)" "$FULL_TEXT_PATH" | head -60

# 只取需要的章节（start..end 行，含两端）
sed -n '<start>,<end>p' "$FULL_TEXT_PATH"

# 声称某设定/框架存在前，先验证它真的出现过
grep -c -i "筑基\|金丹" "$FULL_TEXT_PATH"

# 带 offset/limit 的定点 Read，避免整文件倾倒
# Read(file_path=full_text.txt, offset=<行号>, limit=<行数>)
```

Step 3（结构分析）、Step 7（逐章解析）、Step 8（支撑文件提取）都用这种方式。50k tokens 以下的书，单次 `Read` 即可。

为什么重要：一本 200 页的书约 75k tokens。逐章重读一遍（28 趟）约耗 2M 输入 tokens；用 grep + sed 只取相关切片，生成成本与产出成正比，而不是与原文成正比。

---

## Step 3 — 分析全书结构

读提取文本 `full_text.txt` 的前 8,000 字符，识别：
- **书名**与**作者**
- **章节结构**（"第N章"、"Chapter N"、"PART I"、"卷/部"、编号标题、目录）
- **核心主题**与领域；虚构类 additionally：世界观类型、主角、主线冲突
- 大致章节数

有目录则读目录部分，映射全部章节。

**模式为"仅解析报告"时**：此时产出报告并停止。结构：

```
## 解析报告 —— 《书名》

### 内容类型与路由
<BOOK_KIND 判定及依据；计划使用的模板与支撑文件>

### 核心框架 / 世界观骨架
- **<框架名 / 体系名>**：<是什么，何时/何处适用>

### 关键原则 / 主题
- <原则或主题>：<可执行的表述>

### 技巧与方法
- <技巧>：<步骤或写法>

### 反模式
- <应避免什么>：<为什么>

### 设定预览（虚构类）
- 人物：<主角及核心配角名单>
- 体系：<等级/力量体系的层级一览>
- 世界：<主要地点与势力>

### 建议知识库名称
`<作者姓或书名>-<核心概念>` —— 如 `meadows-systems`、`fanren-xiuxian`

### 检测到的章节
| # | 标题 | 主要框架/内容 |
```

---

## Step 4 — 询问用途（仅完整解析）

生成前问用户：

> "这个知识库主要帮你做什么？（可多选）
> 1. 学习、模仿作者的写作风格与技巧（写作向）
> 2. 应用书中的框架、心智模型与原则（实践向）
> 3. 查询设定、人物与章节细节（资料库向）
> 4. 以上全部"

用答案决定主 SKILL.md 核心速览的侧重与各支撑文件的详略：
- 含 1 → writing-style.md、techniques.md、anti-patterns.md 从详；章节模板的"写作技巧"部分必填
- 含 2 → mental-models.md、principles.md 从详；cheatsheet 式决策规则优先
- 仅 3 → 各文件从简，索引从详

**由答案推导 `DEPTH`（不额外提问）：**
- 仅选 3 → `DEPTH=reference` —— 精简、速查型章节
- 含 1、2 或 4 → `DEPTH=study` —— 更深的章节，含实例拆解与推导

`DEPTH` 与 `EXTRACT_MODE` 共同决定 Step 7 的每章 token 预算。**不要**单独再问"学习还是速查" —— 已在此推断。（模式 2/3 跳过本步时，默认 `DEPTH=study`。）

---

## Step 5 — 确定知识库名称与位置

若已提供 `SKILL_NAME`，直接用作 slug。否则提两个方案让用户选：
- **按作者-概念**（非虚构首选）：`{作者姓}-{核心概念}`，如 `cialdini-influence`
- **按书名**（虚构首选）：书名的小写连字符形式，如 `lord-of-mysteries`；系列书加卷号，如 `fanren-xiuxian-v1`

选择目标 skill 根目录（`SKILLS_HOME`）。探测用户文件系统，按**当前宿主**选择：

| 宿主 agent | 个人 skill 根目录（按序探测） | 项目级根目录 |
|---|---|---|
| **Kimi Code** | `~/.kimi-code/skills` | `.kimi-code/skills` |
| **GitHub Copilot CLI** | `~/.copilot/skills` → `~/.agents/skills` | `.github/skills` → `.claude/skills` → `.agents/skills` |
| **Amp** | `~/.agents/skills` → `~/.config/agents/skills` → `~/.config/amp/skills` | `.agents/skills` |
| **Claude Code** | `~/.claude/skills` | `.claude/skills` |
| **OpenAI Codex** | `~/.agents/skills`（原生发现，跟随软链） | `.agents/skills` |

选择规则：
1. 该宿主的候选根目录**恰好一个**存在于磁盘 → 直接使用，不问。
2. **都不存在**（全新机器）→ 问用户创建哪个 —— 给出该宿主的候选并在本次会话记住选择。不要默默选。
3. 用户明确要求项目级产出 → 用项目级那一列。
4. 无法识别宿主 → 问："你现在用的是哪个 agent —— Kimi Code、GitHub Copilot CLI、Amp、Codex 还是 Claude Code？"

设定 `SKILLS_HOME` 后检查 `$SKILLS_HOME/<skill_name>/` 是否已存在。若存在，让用户三选一：
1. **更新/合并**（模式 3）—— 把新内容并入已有知识库
2. **覆盖** —— 删除并从头重新生成
3. **改名** —— 追加 `-2` 或换 slug

用户选**更新/合并** → 跳到文末 **更新/合并流程**（跳过 Step 3、4、6、7、8、9）。

---

## Step 6 — 创建目录结构

```bash
mkdir -p "$SKILLS_HOME/<skill_name>/chapters"
# 虚构类（或 mixed 且确有设定内容）再加：
mkdir -p "$SKILLS_HOME/<skill_name>/settings"
```

---

## Step 7 — 逐章解析

**TOKEN 预算规则 —— 关键（自适应）：**

每章预算随 `EXTRACT_MODE` 与 `DEPTH` 缩放：

| | `DEPTH=reference` | `DEPTH=study` |
|---|---|---|
| `EXTRACT_MODE=text` | 800–1,200 tokens | 1,000–1,800 tokens |
| `EXTRACT_MODE=technical` | 1,200–1,800 tokens | 2,000–3,000 tokens |

- 这是每文件目标而非硬性上限 —— 信息密度高的章可超，薄的章可低。密度永远优先于长度（质量规则 3）：绝不为凑数注水。
- 章节文件按需加载，更大的章节只在真正被读时才占 tokens。
- 在两格之间犹豫时（如混合内容），取较低预算，用精度而非体量补深度。

**`DEPTH=study` 靠内容挣得，不是靠调高数字。** 标准模板自然落在 700–900 tokens。要诚实地达到 study 预算 —— 而非注水 —— 章节必须补充具体材料：
- **复现一个实例/场景**（`## 实例解析` / `## 关键场景拆解`）：非虚构复现作者走完的完整案例（一份示例文档、一段对话、一个决策全程）；虚构拆解一个代表性场景的写法。这是学习者回头找的东西，是单个最大杠杆。
- 把每个框架/技巧的"怎么做"展开为明确步骤或判断标准，而不是一句话。
- 给排前 1–2 的框架/手法加一小段"为什么有效 / 何时失效"。

某章确实没有实例、无法展开时，让它落在 study 下限之下，并在核心观点里注明该章较薄 —— 不要注水。`reference` 深度的章节则刻意省略实例拆解，只留决策就绪的要点。

对 Step 3 识别的**每一章/大节**：
读 `full_text.txt` 对应区段（用字符偏移或 grep 章节标题），按 `BOOK_KIND` 选择模板创建 `$SKILLS_HOME/<skill_name>/chapters/ch<NN>-<slug>.md`。

### 非虚构章节模板

```markdown
# 第 N 章：<完整标题>

## 核心观点
<1–2 句：本章教的最重要的一件事>

## 提出的框架
- **<框架名>**：<精确表述 —— 保留作者命名>
  - 何时用：<具体情境>
  - 怎么做：<步骤或判断标准>

## 关键概念
- **<术语>**：<一句话精确定义>
（本章最重要的 5–10 个术语）

## 心智模型
<2–4 个思考工具。写成"当 Y 时用 X"或"把 X 想成 Y">

## 反模式
- **<应避免什么>**：<为什么失败>

## 代码示例 *（仅 EXTRACT_MODE=technical；text 模式省略）*
<!-- 复制本章最有教学价值的片段，缩进原样保留 -->
```<language>
<关键代码示例>
```
- **展示了什么**：<一行>

## 参考表格 *（仅 EXTRACT_MODE=technical；text 模式省略）*
<!-- 复现本章的比较矩阵、参数表或决策表 -->

## 写作技巧观察
<1–3 条：作者本章如何表达 —— 论证结构、举证方式、修辞手法；写入 writing-style.md 的素材>

## 实例解析 *（仅 DEPTH=study；reference 省略）*
<!-- 复现作者走完的一个具体实例：示例文档、对话、填好的模板、
     前后对比，或端到端的一个决策。忠于来源；不长段照抄 —— 紧凑重构。 -->

## 要点
1. <可执行洞见>
（3–7 条实践者必须记住的）

## 关联
- **第 N 章**：<为何相关>
- **<概念>**：<关联的外部概念或标准>
```

### 虚构章节模板

```markdown
# 第 N 章：<完整标题>

## 本章梗概
<2–3 句：本章推进了什么；不是逐场复述，是情节/信息增量>

## 设定揭示
<本章新出现或更新的设定，逐条标注归属文件>
- **<人物名>** → characters：<新揭示的身份/动机/能力>
- **<体系条目>** → system：<新等级/规则/代价>
- **<地点/势力>** → world：<新地理环境或社会关系>

## 人物动态
<动机揭示、关系变化、弧光进展；无实质进展则写"本章人物无变化">

## 写作技巧
- **<手法名>**：<本章何处使用、效果如何>（钩子、视角控制、节奏、伏笔、对话、信息揭示顺序等）

## 心智模型与原则
<角色决策体现的思维模式，或本章承载的主题原则；写成"当 Y 时用 X"或主题陈述>

## 反模式与警示
- **<作品内警示>**：<角色/势力的失败模式及其代价>（修炼走火、决策失误、组织崩坏 —— 作者刻意展示的后果）
- **<写作警示>**：<本章险些套路化却被作者化解之处，或确实拖沓/降智之处>（客观标注，供写作向参考）

## 关键场景拆解 *（仅 DEPTH=study；reference 省略）*
<!-- 选一个代表性场景，拆解其写法：场景目标、冲突结构、信息揭示节奏、
     视角运用。忠于原文；紧凑重构，不长段照抄。 -->

## 伏笔与悬念
- <本章埋下的伏笔 / 制造的悬念及指向>

## 关联
- **第 N 章**：<为何相关>
- **<人物/设定条目>**：<呼应的设定>
```

---

## Step 8 — 生成支撑文件

按 `BOOK_KIND` 生成（每项注明 token 上限；只建确有内容的文件）：

### outline.md —— 框架大纲（上限 1,500 tokens）
- 非虚构：全书论证地图 —— 核心问题 → 主线逻辑 → 结论；各部分/章节在论证链中的位置
- 虚构：情节结构图 —— 卷/幕划分、主线与副线、关键转折点、时间线；标注对应章节号
- 格式：层级大纲 + 一行式节点说明，不是散文

### settings/characters.md —— 人物（虚构类；上限 2,000 tokens）
```markdown
## <人物名>
**定位**：<主角/导师/反派/功能角色> | **首现**：ch<N>
- 身份与背景：<…>
- 动机：<想要什么，为什么>
- 弧线：<起点 → 关键转变（ch N）→ 当前状态>
- 关系：<与关键人物的关系及变化>
- 写作看点：<作者塑造该人物的手法>（写作向素材）
```
- 主次分明：主角群从详，功能角色一两行
- 每条信息可溯源（标注 ch N）

### settings/system.md —— 等级与体系（虚构类；上限 2,000 tokens）
- 力量/修炼/职业等级：**层级表**（等级名保持原文）+ 晋级条件 + 代价与限制
- 规则体系：世界运行的硬规则（作者明确的"什么不能发生"）
- 其他体系：经济、门派/职业、装备/道具分级等，按书中实际存在建小节
- 表格优先；每条标注首现章节

### settings/world.md —— 社会与环境（虚构类；上限 2,000 tokens)
- 地理环境：世界/地图结构、关键地点（标注 ch N）
- 势力组织：门派/国家/公司/家族 —— 结构、立场、相互关系
- 社会结构：阶层、制度、文化习俗
- 历史背景：影响当下的历史事件
- 矩阵/关系表优先于散文

### mental-models.md —— 心智模型（上限 1,500 tokens）
- 非虚构：作者的思考工具，格式 `**<模型名>** — 当 <情境> 时用。核心：<一句>（ch N）`
- 虚构：角色的决策模式与世界观运作逻辑（"这个世界里，力量差距意味着 X"），同格式
- 按使用频率/重要性排序，不按章节顺序

### principles.md —— 原则（上限 1,500 tokens）
- 格式：`**<原则>** — <可执行表述>。因为 <理由>（ch N）`
- 只收作者明确主张或作品明确表达的原则，不收读者感想

### writing-style.md —— 写作风格（上限 1,500 tokens）
作者表达方式的解剖，写作向的核心文件：
- **视角与人称**：第几人称、视角切换规则、限知/全知
- **节奏**：章节长度模式、场景/sequel 结构、张弛安排
- **语言特征**：句式长短、词汇密度、白话/书面程度、标志性措辞
- **对话风格**：占比、功能（推进/塑造/信息）、特点
- **描写密度**：环境/动作/心理的比例与时机
- **标志性手法**：反复使用的结构性手法（多线交织、章末钩子、视角反转等）
- **声音校准**：模仿该作者时"该做/不该做"各 3–5 条（写成可执行检查项）

### techniques.md —— 技巧（上限 2,000 tokens）
```markdown
## <技巧名>
**何时用**：<情境>
**怎么做**：<步骤或写法要点>
**代价/注意**：<局限、失效条件>
**出处**：ch<N>
```
- 非虚构：方法论技巧；虚构：写作技巧（与 writing-style.md 的关系：style 是整体声音，techniques 是可拆解的单个手法）

### anti-patterns.md —— 反模式（上限 1,500 tokens）
- 格式：`**<应避免什么>** — <为什么失败>（ch N）`
- 非虚构：作者明确反对的做法
- 虚构：双轨 —— 作品内警示（角色/势力的失败模式）+ 写作警示（套路化风险点及作者如何化解）

### glossary.md —— 术语与专有名词表（上限 1,500 tokens）
- 全书重要术语，字母/拼音序排列
- 格式：`**<术语>** — <定义>（ch N）`
- 虚构类重点收专有名词：人名、地名、境界名、招式名、物品名、组织名 —— 保持原文

---

## Step 9 — 生成主 SKILL.md

**关键 TOKEN 预算：主 SKILL.md 正文 < 4,000 tokens。**
压缩截断从尾部开始 —— 最重要的内容放最前。

创建 `$SKILLS_HOME/<skill_name>/SKILL.md`：

```markdown
---
name: <skill_name>
description: "由《<书名>》（<作者>）解析生成的知识库。用于<按 Step 4 答案填 3–6 个关键词：如 模仿其写作风格 / 应用其 X 框架 / 查询人物与设定>、研读原书或查阅其概念时。"
---

<!-- argument-hint: [主题、人物名、框架名或章节号] -->

# 《<书名>》知识库
**作者**：<作者> | **类型**：<虚构/非虚构> | **页数**：~<N> | **章节**：<N> | **生成日期**：<YYYY-MM-DD>

## 如何使用本知识库

- **不带参数** —— 加载下方核心速览
- **带主题** —— 问 `人物 张三`、`境界体系`、`ch05` 或任何索引主题；我先读对应章节文件再回答
- **浏览** —— 问"有哪些章节 / 人物 / 设定？"查看完整索引

当你问的主题不在下方核心速览中时，我会先读对应章节文件再回答 —— 不凭印象编造。

---

## 核心速览
<!-- ~2,000 tokens。虚构类：世界观一句话 + 主线脉络 + 核心体系速查表 +
     主要人物一行式速查 + 作者风格一句话。非虚构类：作者最重要的命名框架
     与原则工具箱。保留原名。写成"当 Y 时用 X"。这是工具箱，不是摘要。 -->

<生成约 2,000 tokens 的最关键内容>

---

## 章节索引

| # | 标题 | 关键框架/内容 |
|---|------|----------------|
| [ch01](chapters/ch01-<slug>.md) | <标题> | <内容1>、<内容2> |
...

## 主题索引

<!-- 按字母/拼音序。重要术语/人物/体系 → 覆盖它们的章节。 -->
- **<术语/人物>** → ch<N>[, ch<N>]

## 支撑文件

<只列实际生成的文件>
- [outline.md](outline.md) —— 全书框架大纲
- [settings/characters.md](settings/characters.md) —— 人物档案
- [settings/system.md](settings/system.md) —— 等级与体系
- [settings/world.md](settings/world.md) —— 社会与环境
- [mental-models.md](mental-models.md) —— 心智模型
- [principles.md](principles.md) —— 原则
- [writing-style.md](writing-style.md) —— 写作风格解剖
- [techniques.md](techniques.md) —— 技巧
- [anti-patterns.md](anti-patterns.md) —— 反模式
- [glossary.md](glossary.md) —— 术语与专有名词

---

## 范围与限制

本知识库只覆盖原书内容。落地实现请结合你的项目工具；超出原书的主题，
查阅相关知识库或直接问 agent。条目与原文有出入时，以原书为准。
```

---

## Step 9.5 — 扫描生成的知识库

报告成功、在另一会话加载、或发布之前，运行建议性安全扫描：

```bash
SKILL_CONVERTER_ROOT="$(cd "$(dirname "$SCRIPT_PATH")/.." && pwd)"
"$PYTHON_BIN" "$SKILL_CONVERTER_ROOT/tools/scan_generated_skill.py" "$SKILLS_HOME/<skill_name>"
```

扫描器非零退出时，停止并请人工复核其文件/行号发现。不要默默改写生成的文件；在发现被解决或明确接受前，不要加载或发布该知识库。

---

## Step 10 — 清理与报告

```bash
PYTHON_BIN="${PYTHON_BIN:-python3}"
if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  PYTHON_BIN="python"
fi

"$PYTHON_BIN" - <<'PY'
import os
import shutil
import tempfile
from pathlib import Path
shutil.rmtree(
    os.environ.get("EXPLAIN_BOOK_WORKDIR", Path(tempfile.gettempdir()) / "explain_book_work"),
    ignore_errors=True,
)
PY
```

然后向用户报告：

```
✅ 知识库已创建：$SKILLS_HOME/<skill_name>/

📚 原书：《<书名>》 —— <作者>（<虚构/非虚构>）
📄 页数：~<N> | 章节：<N>

生成的文件：
  SKILL.md          —— 核心速览 + 索引        (~X tokens)
  chapters/         —— <N> 个逐章解析          (~X tokens/个，共 ~X)
  outline.md        —— 框架大纲               (~X tokens)
  settings/         —— 人物/体系/世界（虚构类） (~X tokens)
  mental-models.md  —— 心智模型               (~X tokens)
  principles.md     —— 原则                   (~X tokens)
  writing-style.md  —— 写作风格               (~X tokens)
  techniques.md     —— 技巧                   (~X tokens)
  anti-patterns.md  —— 反模式                 (~X tokens)
  glossary.md       —— 术语表                 (~X tokens)
  ─────────────────────────────────────────────
  知识库总体积：~X tokens（按需加载，不会一次全载入）

💡 提示：用你 agent 的会话用量命令查看实际 token 消耗。

用法：
  直接提 <skill_name>                → 加载核心速览
  问 <skill_name> 关于 <主题>        → 定位并讲解主题
  问 <skill_name> 第 <N> 章          → 深入该章
  问 <skill_name> 人物 <名字>        → 查人物档案（虚构类）

重新加载（若你的 agent 不自动发现新 skill）：
  Kimi Code / Claude Code：重启会话
  GitHub Copilot CLI：/skills reload
  Amp：重启会话
```

---

## 更新/合并流程

对 `$SKILLS_HOME/<skill_name>/` 已有知识库执行更新/合并时（典型场景：系列小说下一卷、修订版、补充来源）：

### 1. 读取现有知识库结构
- 读 `SKILL.md`：解析现有**章节索引**、**主题索引**、元数据（作者、总章数）、**核心速览**。
- 列出 `chapters/` 全部文件，找到最大章节号（如 `ch12`）。
- 读 outline.md、settings/ 各文件、mental-models.md、principles.md、writing-style.md、techniques.md、anti-patterns.md、glossary.md，看已索引哪些设定与术语。

### 2. 匹配内容，区分修订与新增
分析新提取的 `full_text.txt`：
- **修订**：新内容的某节直接更新/扩写已有章节的主题 → 读该章文件，合并新细节后重写。
- **新增**：新章节、新卷、新独立部分 → 在 `chapters/` 建**新章节文件**，编号接续现有最大号（已有到 `ch12` 则建 `ch13-*.md`、`ch14-*.md`…）。

### 3. 生成或更新章节文件
对每章（新或修订）：读新文本对应区段，按 Step 7 的模板与预算生成，写入 `chapters/`。

### 4. 合并支撑文件
- **outline.md**：扩展主线/论证链，标注新增章节位置。
- **settings/characters.md**：已有角色追加新弧线与章节引用（如"关键转变（ch 5, ch 13）"）；新角色按模板新增。
- **settings/system.md / world.md**：新层级、新势力、新地点并入对应表格；修订与旧设定冲突时，以最新来源为准并注明。
- **glossary.md**：提取新术语，与现有合并后重排序；已有术语追加新章节引用。
- **mental-models.md / principles.md / techniques.md / anti-patterns.md**：追加新条目，保持格式一致、总量不超上限（超限时合并同类、淘汰最弱条目）。
- **writing-style.md**：仅当新来源展现了新手法或风格变化时更新，并注明。

### 5. 重新生成主 SKILL.md
- **元数据**：更新章节总数、页数估计、来源名单、`生成日期`。
- **核心速览**：并入新内容中影响最大的框架/设定（总量仍 < 4,000 tokens；超限则淘汰最弱条目）。
- **章节索引**：追加新章节行并链接新文件。
- **主题索引**：合并新主题；已有主题若也被新章节覆盖，追加章节引用（如 `- **主题** → ch05, ch13`）。

### 6. 扫描、清理与报告
文件写完合并后，运行 **Step 9.5**，然后执行 **Step 10** 清理，并打印更新报告：新增章节、合并的术语数、更新的索引。

---

## 质量规则

1. **提取结构，不写摘要** —— 收命名框架、精确表述、设定条目、反模式；不收章节梗概式复述
2. **保留原名精度** —— 框架名、境界名、招式名、地名、组织名保持原文，不翻译、不泛化
3. **密度优先** —— 1,000 tokens 的提炼胜过 10,000 tokens 的摘录
4. **实践者视角** —— 非虚构写"当 Y 时用 X"；写作向写"写 X 时学 Y 手法"；不写"书中讲解了 X"
5. **主 SKILL.md 前重后轻** —— 压缩保留前 ~5,000 tokens，最重要内容放最前
6. **章节文件按需加载** —— 未被加载前不占预算
7. **绝不照抄原文** —— 永远合成、提炼、取信号；尊重版权
8. **主题索引是关键导航** —— agent 靠它找到正确的章节文件
9. **虚构/非虚构各用其模板** —— 不混排；`mixed` 逐卷判断并说明取舍
10. **设定可溯源** —— 每条设定、术语、人物信息标注出处章节（ch N）；查不到出处的条目宁可不写

---

## 版权与合理使用

explain-book 不附带任何书籍内容 —— 它是你指向自己已有文件的转换器。

- **处理在本地。** 提取与解析都在你的机器上运行。（若你的 agent 模型在云端，你喂给它的文本遵循该服务商的数据条款 —— 与任何提示词相同。）
- **用你自己的副本。** 你买的书、公司拥有的文档、你有权阅读的论文。
- **产出是你的笔记。** 生成的知识库是结构化合成衍生物 —— 框架名、设定条目、要点 —— 不是原文复制（见质量规则 7）。视同手写学习笔记：个人使用。
- **不要转发。** 把版权书籍生成的知识库公开或分发可能侵权。第三方书籍的知识库保持私有；内部文档、自己的作品、开放授权内容可在其许可范围内分享。
