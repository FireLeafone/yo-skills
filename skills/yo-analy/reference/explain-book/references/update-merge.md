# 更新/合并流程

对 `<输出目录>/<slug>/` 已有解析文档集执行更新/合并时（典型场景：系列小说下一卷、修订版、补充来源）。进入本流程前已完成 Step 0、1、1.5、2（输入检查、校验、内容类型识别、文本提取）。

旧版产物兼容：若已有目录的主文档是 `SKILL.md`（旧版"知识库 skill"布局）而非 `README.md`，同样适用本流程；合并时把主文档迁移为 `README.md`（去掉 frontmatter，保留结构与内容），并在报告中注明这次迁移。

## 1. 读取现有文档集结构
- 读 `README.md`：解析现有**章节索引**、**主题索引**、元数据（作者、总章数）、**核心速览**。
- 列出 `chapters/` 全部文件，找到最大章节号（如 `ch12`）。
- 读 outline.md、settings/ 各文件、mental-models.md、principles.md、writing-style.md、techniques.md、anti-patterns.md、glossary.md，看已索引哪些设定与术语。

## 2. 匹配内容，区分修订与新增
分析新提取的 `full_text.txt`：
- **修订**：新内容的某节直接更新/扩写已有章节的主题 → 读该章文件，合并新细节后重写。
- **新增**：新章节、新卷、新独立部分 → 在 `chapters/` 建**新章节文件**，编号接续现有最大号（已有到 `ch12` 则建 `ch13-*.md`、`ch14-*.md`…）。

## 3. 生成或更新章节文件
对每章（新或修订）：读新文本对应区段，按 [chapter-templates.md](chapter-templates.md) 的模板与预算生成，写入 `chapters/`。

## 4. 合并支撑文件
- **outline.md**：扩展主线/论证链，标注新增章节位置。
- **settings/characters.md**：已有角色追加新弧线与章节引用（如"关键转变（ch 5, ch 13）"）；新角色按模板新增。
- **settings/system.md / world.md**：新层级、新势力、新地点并入对应表格；修订与旧设定冲突时，以最新来源为准并注明。
- **glossary.md**：提取新术语，与现有合并后重排序；已有术语追加新章节引用。
- **mental-models.md / principles.md / techniques.md / anti-patterns.md**：追加新条目，保持格式一致、总量不超上限（超限时合并同类、淘汰最弱条目）。各文件格式与上限见 [support-files.md](support-files.md)。
- **writing-style.md**：仅当新来源展现了新手法或风格变化时更新，并注明。

## 5. 重新生成主 README.md
按 [main-readme-template.md](main-readme-template.md) 的模板重新生成，并合并新旧内容：
- **元数据**：更新章节总数、页数估计、来源名单、`生成日期`。
- **核心速览**：并入新内容中影响最大的框架/设定（总量仍 < 4,000 tokens；超限则淘汰最弱条目）。
- **章节索引**：追加新章节行并链接新文件。
- **主题索引**：合并新主题；已有主题若也被新章节覆盖，追加章节引用（如 `- **主题** → ch05, ch13`）。

## 6. 扫描、清理与报告
文件写完合并后，运行 **Step 9.5**（扫描），然后执行 **Step 10** 清理，并打印更新报告：新增章节、合并的术语数、更新的索引。
