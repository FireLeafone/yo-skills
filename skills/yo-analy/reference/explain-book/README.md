# explain-book

**把书籍解析为结构化解析文档集：框架大纲、设定（人物/等级/社会/环境）、心智模型、原则、写作风格、技巧与反模式 —— 虚构与非虚构自动路由。产出是普通 markdown 文档目录。**

本项目是 [book-to-skill](https://github.com/virgiliojr94/book-to-skill) 的衍生改造：沿用了它的"提取结构，不写摘要"哲学与完整工作流，但把提取维度从"技术书方法论"扩展为双路由：

| | 非虚构路由 | 虚构路由 |
|---|---|---|
| 重点产出 | 框架、心智模型、原则、技巧、反模式 | 设定集（人物档案、等级/力量体系、社会与环境）、写作风格、写作技巧 |
| 章节模板 | 核心观点 → 框架 → 反模式 → 实例 | 梗概 → 设定揭示 → 人物动态 → 写作技巧 → 场景拆解 |

两者都会生成 `outline.md`（框架大纲）、`writing-style.md`、`techniques.md`、`anti-patterns.md`、`glossary.md` 与逐章解析文件，全部按需加载。

## 生成的解析文档集长什么样

```
<slug>/
├── README.md             # 核心速览 + 全部索引（正文 < 4,000 tokens）
├── chapters/             # 逐章解析，按需加载
├── outline.md            # 框架大纲：论证地图（非虚构）或情节结构图（虚构）
├── settings/             # 设定集（虚构类重点）
│   ├── characters.md     #   人物：身份/动机/弧线/关系，可溯源到章
│   ├── system.md         #   等级与体系：层级表、晋级规则、代价与限制
│   └── world.md          #   社会与环境：地理、势力、文化、历史
├── mental-models.md      # 心智模型（"当 Y 时用 X"）
├── principles.md         # 原则
├── writing-style.md      # 写作风格解剖 + 声音校准
├── techniques.md         # 技巧
├── anti-patterns.md      # 反模式
└── glossary.md           # 术语与专有名词表
```

## 使用

```
/explain-book ./某本书.pdf
/explain-book ./小说卷一.pdf fanren-v1
/explain-book ./notes/ --只解析        # 先出解析报告，不生成文件
```

产出默认写到当前项目的 `explain-book/<slug>/` 目录（可指定其他位置）—— 是一组可直接阅读、可被 agent 按需查询的普通 markdown 文档，**不会安装成新的 skill**。

工作流（内容类型识别 → 文本提取 → 成本预估 → 逐章解析 → 支撑文件 → 主索引 → 安全扫描）详见 [SKILL.md](SKILL.md)；章节模板、支撑文件规格、主 README 模板与更新/合并流程在 [references/](references/) 下。

## 仓库结构

```
explain-book/
├── SKILL.md              # skill 定义 + 分步解析规范（生成器规格）
├── references/           # 章节模板、支撑文件规格、主 README 模板、更新/合并流程（按需加载）
├── scripts/
│   └── extract.py        # 提取入口（薄封装）
├── explain_book/         # 提取器包（vendored from book-to-skill，MIT）
│   ├── config.py         #   扩展名、路径、依赖常量
│   ├── dependencies.py   #   可选依赖探测 + --check
│   ├── exceptions.py     #   ExtractionError（单源失败不拖垮批处理）
│   ├── sanitize.py       #   提取文本消毒（隐形码点等）
│   ├── utils.py          #   CLI 解析、多源合并、章节检测
│   └── parsers/          #   各格式解析器（pdf/docx/html/rtf/text）
└── tools/
    └── scan_generated_skill.py  # 生成物的提示词注入/越权扫描
```

支持的输入格式：PDF、DOCX、HTML、Markdown、纯文本、reStructuredText、AsciiDoc、RTF。可选依赖检查：`python scripts/extract.py --check`。

## 版权

本仓库不附带任何书籍内容。解析在你本地完成；生成的解析文档是你的结构化笔记，第三方版权书籍的解析文档请保持私有。

## 归属与许可

- 提取引擎（`explain_book/`、`scripts/extract.py`、`tools/scan_generated_skill.py`）vendored 自 [book-to-skill](https://github.com/virgiliojr94/book-to-skill)，原作者 Virgilio Jr.，MIT 许可。如它为你节省了时间，可赞助上游：<https://github.com/sponsors/virgiliojr94>
- 本项目的改动与 `SKILL.md` 的解析规范同样以 MIT 发布。MIT 仅适用于转换器代码与 skill 定义，不适用于你用它处理的任何书籍。
