---
name: explain-book
description: "将书籍与文档（PDF、DOCX、HTML、Markdown、纯文本等）解析为结构化解析文档集：框架大纲、设定（人物/等级/社会/环境）、心智模型、原则、写作风格、技巧与反模式；虚构与非虚构自动路由。产出是普通的 markdown 文档目录，不是可安装的 skill。当用户想深度解析一本书、提炼小说世界观与设定、学习作者的写作手法，或把书籍变成可反复查询的解析文档时使用。"
---

# explain-book · 书籍知识解析器

把一本书解析成结构化解析文档集 —— 提取结构，而不是写读后感。产出是一组普通 markdown 文档，供人与 agent 随时查阅，**不生成、不安装任何 skill**。

## 解析哲学

书籍（无论虚构还是非虚构）凝结了两类知识：**方法论知识**（框架、心智模型、原则、技巧、反模式）与**设定知识**（人物、等级体系、社会、环境、世界观）。本 skill 把这两类知识提取为可反复查询调用的文档。

**提取结构，不是写摘要。** 解析文档集不是读书报告，而是工具箱：
- 框架大纲（全书的结构地图：论证主线或情节脉络）
- 设定集（人物档案、等级/力量体系、社会与环境）
- 心智模型（"当 Y 时用 X"的思考工具）
- 原则（指导决策的规则）
- 写作风格（作者如何表达：视角、节奏、语言、标志性手法）
- 技巧（可复用的方法/手法）
- 反模式（应当避免的做法及其原因）

**保留原名精度。** 框架名、境界名、招式名、地名、组织名保持原文 —— "筑基期"不可泛化为"中级阶段"，"5 Whys"不可写成"多问几次为什么"。

**深度分层。** 小书出小库；大部头（10+ 框架或复杂世界观）出带章节文件、按需加载的完整文档集。

---

## 运行模式

按用户意图路由，共三种模式：

### 1. 完整解析（默认）
**触发：** 用户提供文档/目录/glob 路径，无特殊指令
**动作：** 执行下方全部步骤（Step 0–10）
**产出：** 完整解析文档集（README.md + chapters/ + outline + settings/ + 各支撑文件）

### 2. 仅解析报告
**触发：** 用户说"只解析""先分析""我想先看看再生成"
**动作：** 执行 Step 0–3，产出结构化解析报告（发现的框架、设定、原则、技巧）。停止 —— 不生成任何文件。
**产出：** 供用户审阅的解析报告

### 3. 更新 / 合并（已有解析文档集）
**触发：** 用户提供新来源（如系列小说的下一卷、修订版），并指向已有解析文档目录或已有 slug
**动作：** 执行 Step 0、1、1.5、2，然后跳到 Step 5 识别已有路径，走 **更新/合并流程**（见 [references/update-merge.md](references/update-merge.md)）
**产出：** 合并后的更新版解析文档集

---

## 解析文档集的位置

产出写到 `<输出目录>/<slug>/`：

1. 用户指定了输出目录 → 用用户指定的。
2. 未指定 → 默认当前项目下的 `explain-book/` 目录，即 `./explain-book/<slug>/`。

slug 的确定见 Step 5。

---

## Step 0 — 输入检查

未提供任何参数时，停止并回复：
> "explain-book 需要文档路径、目录或 glob 模式。用法：`explain-book <文档路径|目录|glob>... [文档集名称slug]`"

整个流程中：
- 识别输入路径与可选 slug。
- 最后一个参数若不是已存在的文件/目录/可匹配的 glob，且形似 slug（小写连字符、字母数字），视为 `DOCSET_NAME`。
- 其余参数视为 `INPUT_PATHS`。
- 若任一输入路径是已生成的解析文档目录（含 `README.md`（或旧版 `SKILL.md`）与 `chapters/` 子目录），或 `DOCSET_NAME` 与输出目录中已有 slug 相同，标记为 **更新/合并**（模式 3）。

---

## Step 1 — 校验输入

确认 `INPUT_PATHS` 中至少有一个受支持的文件、目录或 glob。对目录和 glob 展开匹配支持的扩展名：`.pdf`、`.docx`、`.txt`、`.md`、`.markdown`、`.html`、`.rst`、`.adoc`、`.rtf`。

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

运行提取脚本。脚本就在本 skill 目录内：**优先用本 SKILL.md 所在目录的 `scripts/extract.py`**；仅当该路径不可得（如 skill 被裁剪分发）时，再按候选列表探测：

```bash
SCRIPT_PATH=""
for candidate in \
  "<本SKILL.md所在目录>/scripts/extract.py" \
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
   输出（生成的文档文件）：~<N>K tokens
   合计：~<N>K tokens

   费用：将以上 token 数乘以你当前模型的每百万 token 输入/输出价格
   （价格与模型名经常变动 —— 不要硬编码；引用当日价格并注明是估算）。

   ⏱  预估耗时：~<N> 分钟

📁 将生成的文件：
   README.md + chapters/ + outline.md + settings/（虚构类）
   + mental-models / principles / writing-style / techniques / anti-patterns + glossary

➡  继续完整解析？（或回复"只解析"先出报告）
```

**估算方法：**
- 输入 tokens ≈ metadata 的 `estimated_tokens` × 1.3（逐章解析的提示词开销）
- 输出 tokens ≈ 章节数 × 每章预算 + 4,000（主 README.md）+ 6,000（各支撑文件合计）
  - 每章预算中位数：`text` ≈ 1,000，`technical` ≈ 1,800（Step 4 确定的 DEPTH 可能上调，见 [references/chapter-templates.md](references/chapter-templates.md) 的预算矩阵）
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

### 建议文档集名称（slug）
`<作者姓或书名>-<核心概念>` —— 如 `meadows-systems`、`fanren-xiuxian`

### 检测到的章节
| # | 标题 | 主要框架/内容 |
```

---

## Step 4 — 询问用途（仅完整解析）

生成前问用户：

> "这套解析文档主要帮你做什么？（可多选）
> 1. 学习、模仿作者的写作风格与技巧（写作向）
> 2. 应用书中的框架、心智模型与原则（实践向）
> 3. 查询设定、人物与章节细节（资料库向）
> 4. 以上全部"

用答案决定主 README.md 核心速览的侧重与各支撑文件的详略：
- 含 1 → writing-style.md、techniques.md、anti-patterns.md 从详；章节模板的"写作技巧"部分必填
- 含 2 → mental-models.md、principles.md 从详；cheatsheet 式决策规则优先
- 仅 3 → 各文件从简，索引从详

**由答案推导 `DEPTH`（不额外提问）：**
- 仅选 3 → `DEPTH=reference` —— 精简、速查型章节
- 含 1、2 或 4 → `DEPTH=study` —— 更深的章节，含实例拆解与推导

`DEPTH` 与 `EXTRACT_MODE` 共同决定 Step 7 的每章 token 预算。**不要**单独再问"学习还是速查" —— 已在此推断。（模式 2/3 跳过本步时，默认 `DEPTH=study`。）

---

## Step 5 — 确定文档集名称与位置

若已提供 `DOCSET_NAME`，直接用作 slug。否则提两个方案让用户选：
- **按作者-概念**（非虚构首选）：`{作者姓}-{核心概念}`，如 `cialdini-influence`
- **按书名**（虚构首选）：书名的小写连字符形式，如 `lord-of-mysteries`；系列书加卷号，如 `fanren-xiuxian-v1`

输出目录按「解析文档集的位置」一节的规则确定。然后检查 `<输出目录>/<slug>/` 是否已存在。若存在，让用户三选一：
1. **更新/合并**（模式 3）—— 把新内容并入已有文档集
2. **覆盖** —— 删除并从头重新生成
3. **改名** —— 追加 `-2` 或换 slug

用户选**更新/合并** → 跳到 [references/update-merge.md](references/update-merge.md)（跳过 Step 3、4、6、7、8、9）。

---

## Step 6 — 创建目录结构

```bash
mkdir -p "<输出目录>/<slug>/chapters"
# 虚构类（或 mixed 且确有设定内容）再加：
mkdir -p "<输出目录>/<slug>/settings"
```

---

## Step 7 — 逐章解析

对 Step 3 识别的**每一章/大节**：读 `full_text.txt` 对应区段（用 Step 2.6 的探测方式定位），按 `BOOK_KIND` 选择模板创建 `<输出目录>/<slug>/chapters/ch<NN>-<slug>.md`。

每章 token 预算（随 `EXTRACT_MODE` × `DEPTH` 缩放）、`DEPTH=study` 的达标要求、非虚构/虚构两套章节模板，全部见 [references/chapter-templates.md](references/chapter-templates.md)。

核心原则（细则见该文件）：密度优先于长度，绝不为凑预算注水；预算不够的薄章如实注明，不硬撑。

---

## Step 8 — 生成支撑文件

按 `BOOK_KIND` 生成 outline.md、settings/（虚构类）、mental-models.md、principles.md、writing-style.md、techniques.md、anti-patterns.md、glossary.md。

每个文件的格式模板与 token 上限见 [references/support-files.md](references/support-files.md)。只建确有内容的文件。

---

## Step 9 — 生成主 README.md

**关键 TOKEN 预算：主 README.md 正文 < 4,000 tokens。**
压缩截断从尾部开始 —— 最重要的内容放最前。

创建 `<输出目录>/<slug>/README.md`（普通 markdown，**不要 frontmatter**）：

```markdown
# 《<书名>》解析
**作者**：<作者> | **类型**：<虚构/非虚构> | **页数**：~<N> | **章节**：<N> | **生成日期**：<YYYY-MM-DD>

## 如何使用本解析文档集

- **先读本文件** —— 下方核心速览覆盖全书最高密度的内容
- **查具体主题** —— 按下方主题索引找到对应章节文件，读它再回答；不凭印象编造
- **浏览全部** —— 章节索引列全部章节，支撑文件列全部跨章提炼

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

本解析文档集只覆盖原书内容。落地实现请结合你的项目工具；超出原书的主题，
查阅其他资料或直接问 agent。条目与原文有出入时，以原书为准。
```

---

## Step 9.5 — 扫描生成的文档集

报告成功或把文档集交给他人之前，运行建议性安全扫描（生成的内容源自外部书籍文本，扫描提示词注入与越权表述）：

```bash
SKILL_CONVERTER_ROOT="$(cd "$(dirname "$SCRIPT_PATH")/.." && pwd)"
"$PYTHON_BIN" "$SKILL_CONVERTER_ROOT/tools/scan_generated_skill.py" "<输出目录>/<slug>"
```

扫描器非零退出时，停止并请人工复核其文件/行号发现。不要默默改写生成的文件；在发现被解决或明确接受前，不要交付或传播该文档集。

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
✅ 解析文档集已创建：<输出目录>/<slug>/

📚 原书：《<书名>》 —— <作者>（<虚构/非虚构>）
📄 页数：~<N> | 章节：<N>

生成的文件：
  README.md         —— 核心速览 + 索引        (~X tokens)
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
  文档集总体积：~X tokens（按需加载，不会一次全载入）

💡 提示：用你 agent 的会话用量命令查看实际 token 消耗。

用法：
  让我读 <输出目录>/<slug>/README.md     → 看核心速览与全部索引
  问 "《书名》第 <N> 章讲了什么"          → 我读对应 chapters/ 文件再答
  问 "《书名》的 <人物/体系/框架>"        → 我按主题索引定位文件再答
```

---

## 更新/合并流程

对已有解析文档集执行更新/合并（系列小说下一卷、修订版、补充来源）时，走 [references/update-merge.md](references/update-merge.md)：读取现有结构 → 区分修订与新增 → 章节编号接续 → 合并支撑文件 → 重新生成主 README.md → 扫描、清理与报告。旧版"知识库 skill"布局（主文档为 SKILL.md）的目录也可走该流程，合并时会迁移为 README.md。

---

## 质量规则

1. **提取结构，不写摘要** —— 收命名框架、精确表述、设定条目、反模式；不收章节梗概式复述
2. **保留原名精度** —— 框架名、境界名、招式名、地名、组织名保持原文，不翻译、不泛化
3. **密度优先** —— 1,000 tokens 的提炼胜过 10,000 tokens 的摘录
4. **实践者视角** —— 非虚构写"当 Y 时用 X"；写作向写"写 X 时学 Y 手法"；不写"书中讲解了 X"
5. **主 README.md 前重后轻** —— 正文 < 4,000 tokens，压缩截断从尾部开始，最重要内容放最前
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
- **产出是你的笔记。** 生成的解析文档是结构化合成衍生物 —— 框架名、设定条目、要点 —— 不是原文复制（见质量规则 7）。视同手写学习笔记：个人使用。
- **不要转发。** 把版权书籍生成的解析文档公开或分发可能侵权。第三方书籍的解析文档保持私有；内部文档、自己的作品、开放授权内容可在其许可范围内分享。
