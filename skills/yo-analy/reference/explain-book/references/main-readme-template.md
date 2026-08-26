# 主 README.md 模板

Step 9 的完整模板。在 `<输出目录>/<slug>/README.md` 创建普通 markdown 文件（**不要 frontmatter**），正文 < 4,000 tokens，压缩截断从尾部开始。

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
