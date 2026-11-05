# AGENTS.md

本文件面向在本仓库工作的 AI 编码代理。项目文档和技能说明以中文为主；修改文档时沿用中文，代码标识符、命令和配置键保持英文。

## 项目概览

`yo-skills` 是遵循 Agent Skills 开放标准的个人/团队技能库，可作为 Claude Code、Codex、Kimi Code CLI 插件安装，也可把单个技能链接到 Cursor 等 agent 的技能目录。

它不是需要编译或启动服务的应用。核心交付物是带 YAML frontmatter 的 `SKILL.md`、按需加载的 Markdown 参考资料、HTML 模板以及 Python 辅助脚本。agent 在运行时读取入口技能，入口技能根据用户意图路由到嵌套子技能，子技能再按说明读取资源或执行脚本。

`skills/` 是本库技能源码的唯一事实来源（SSOT）。当前有 5 个集合入口和 34 个嵌套子技能。

## 技术栈与关键配置

- **技能定义**：Markdown + YAML frontmatter；编写模板为 `templates/SKILL.md`。
- **校验与大多数辅助工具**：Python 3，使用 `pathlib`、`argparse` 和现代类型标注。根目录 `requirements.txt` 只安装校验器必需的 `pyyaml>=6.0`。
- **版本脚本**：Node.js CommonJS，入口为 `scripts/version.js`；不需要构建或打包。
- **Windows 本地试装**：`scripts/install-local-skill.ps1` 是 `scripts/link-skills.py` 的 PowerShell 包装器。
- **静态展示资源**：HTML/CSS/内联 JavaScript；仓库没有前端构建流程。
- **`package.json`**：`private: true`，无 npm 依赖，仅提供校验、链接和版本更新命令；没有 `build` 或 `test` 脚本。
- **插件清单**：`.claude-plugin/plugin.json`、`.claude-plugin/marketplace.json`、`.codex-plugin/plugin.json`、`.kimi-plugin/plugin.json`，均通过 `"skills": "./skills/"` 指向源码目录。
- **其他文档**：`README.md` 面向使用者，包含安装和调用方式；`CHANGELOG.md` 记录版本；根目录 `CLAUDE.md` 通过 `@AGENTS.md` 引入本文件。

根目录没有 `pyproject.toml`、锁定的 npm 依赖、Docker 配置或 CI 工作流。不要假设存在未在仓库中声明的框架或工具链。

## 目录与模块划分

```text
skills/
├── yo-analy/   # 分析、解释、文档沉淀与技能优化
├── yo-dev/     # 需求、设计、计划、开发执行与代码审查
├── yo-life/    # 旅行策划、路书交付与文本去 AI 痕迹
├── yo-novel/   # 小说设计、写作、进度和风格分析
└── yo-ui/      # UI 布局、配色、动效、适配、性能与评审
```

每个集合入口都是 `skills/<集合>/SKILL.md`，具体子技能位于该集合的 `reference/<子技能>/SKILL.md`。入口负责显式路由、关键词推断和歧义处理，本身不执行具体任务。

| 集合 | 子技能 |
| --- | --- |
| `yo-analy` | `explain-code`、`explain-project`、`agents-docs`、`explain-book`、`grill-me`、`extract-chat`、`tell-story`、`tell-me`、`skill-optimizer` |
| `yo-dev` | `to-prd`、`brainstorm`、`impl-plans`、`git-worktrees`、`subagent-development`、`execute-plans`、`request-code-review`、`frontend-code-review` |
| `yo-life` | `travel-planner`、`rm-ai-style`、`unslop` |
| `yo-novel` | `novel-create`、`novel-character`、`novel-write`、`novel-chapters`、`novel-progress`、`novel-style`、`novel-storyline` |
| `yo-ui` | `layout`、`color`、`animate`、`adapt`、`optimize`、`polish`、`critique` |

其他目录的职责：

- `scripts/validate-skills.py`：Agent Skills 规范静态校验。
- `scripts/link-skills.py`：把顶层集合链接到本地测试项目；支持 `claude`（默认）、`codex`、`cursor`、`kimi`。
- `scripts/version.js`：同步版本并生成 changelog。
- `templates/`：新技能模板，不参与校验或安装。
- `.agents/skills/`：项目级外部技能，如 `skill-creator`、`skill-optimizer`，不是 `skills/` 下本库技能的源码，也不参与本库发布。
- `.claude/skills/`：本地 Claude 兼容副本或链接，不作为修改源头。
- `skills-lock.json`：记录外部技能来源和哈希，且在 `.gitignore` 中；不要用它替代本库源码。
- `docs/`、`examples/`、`presets/`：设计资料、示例产物和风格预设，不是插件入口。
- 子技能内部的 `references/`、`scripts/`、`assets/`、`resources/`、`tools/`：由对应子技能按需加载或调用，命名和用途以该子技能的 `SKILL.md` 为准。

两个较复杂的子系统：

- `yo-analy/reference/explain-book/` 内含 `explain_book` Python 包，负责 PDF、DOCX、HTML、RTF 和纯文本提取。`scripts/extract.py --check` 可预检可选依赖；部分格式有标准库降级路径，技术 PDF 可使用 Docling。
- `yo-life/reference/travel-planner/` 内含路书录入、内容增强、配图、校验和 HTML/PDF 交付脚本。`scripts/deliver_roadbook_v2.py` 是默认交付流水线；图片增强的可选依赖单列在 `requirements-roadbook-images.txt`（Pillow、ImageHash）。

## 环境准备与常用命令

在仓库根目录执行：

```bash
# 安装根校验器依赖；npm install 不是根工具链的必要步骤
python -m pip install -r requirements.txt

# 校验全部顶层集合入口
npm run skills:validate
# 等价命令
python scripts/validate-skills.py

# 只校验一个顶层集合
python scripts/validate-skills.py --skill yo-novel

# 校验某集合下的全部嵌套子技能
python scripts/validate-skills.py --skills-dir skills/yo-novel/reference

# 校验一个嵌套子技能
python scripts/validate-skills.py --skills-dir skills/yo-novel/reference --skill novel-write

# 本地试装前预览；目标目录必须已经存在
npm run skills:link -- --target D:/path/to/project --agent claude --dry-run
npm run skills:link -- --target D:/path/to/project --skill yo-dev --agent codex --dry-run
```

去掉 `--dry-run` 才会实际创建链接。Windows 下优先创建 symlink，失败时回退为 junction；`--force` 只用于替换已有链接，脚本会拒绝覆盖普通非链接路径。PowerShell 等价入口：

```powershell
.\scripts\install-local-skill.ps1 -Target D:\path\to\project -SkillName yo-dev -Agent claude -DryRun
```

## 开发与代码风格约定

1. **不得未经用户明确询问或许可主动执行 `git commit`。**
2. 新增、删除或重命名子技能时，同步更新所属集合的 `skills/yo-*/SKILL.md`：可用子技能表、显式路由、关键词推断及注意事项都要一致。当前可安装子技能使用单数目录 `reference/<skill>`；不要与资源目录 `references/` 混淆。
3. 新技能从 `templates/SKILL.md` 开始；目录名必须等于 frontmatter 的 `name`，使用小写 hyphen-case。
4. `description` 聚焦“何时触发”，不要把完整工作流塞进去；正文必须非空，单个 `SKILL.md` 不超过 500 行，细节拆到按需加载的资源中。
5. frontmatter 只允许 `name`、`description`、`license`、`compatibility`、`metadata`、`allowed-tools`、`disable-model-invocation`、`argument-hint`。`name` 最长 64 字符，`description` 最长 1024 字符。低频高危技能按 README 约定设置 `disable-model-invocation: true`。
6. 修改 Python 时沿用现有脚本的 `pathlib`、`argparse`、类型标注和明确退出码风格；修改 `version.js` 时沿用 CommonJS。新增依赖必须在对应说明和依赖文件中明确记录，不能假定环境已经安装。
7. 技能可能被安装到任意位置，也可能从任意 cwd 调用。脚本和资源路径应相对 `SKILL.md` 或 `__file__` 定位，不要硬编码本机仓库路径，也不要依赖 shell 变量跨命令保留。
8. 修改工作流后，同步清理仍描述旧行为的注释、README、参考文档和入口路由。只改 `skills/` 中的源码，不把 `.agents/` 或 `.claude/` 的副本当作源头反向同步。

## 测试策略与验收

仓库目前没有 `tests/`、单元测试文件、`npm test` 或 CI 配置。现有质量门槛是**规范静态校验 + 本地链接 + 真实技能场景验证**，不能把模板中出现的 pytest/Jest 示例当成本仓库的测试命令。

- 修改入口或 frontmatter：至少运行 `npm run skills:validate`。
- 修改嵌套子技能：额外对该 `reference/` 目录运行校验；根校验器只扫描 `skills/` 第一层，**不会自动校验嵌套子技能**。
- 修改链接脚本：先用 `--dry-run` 覆盖默认 agent、指定 `--skill` 和目标 agent；实际链接只在用户指定的测试项目中进行。
- 修改 Python 业务脚本：用小型、可控的输入执行真实命令，检查退出码和产物，而不只做导入或语法检查。
- 修改 HTML 模板或可视化技能：生成实际 HTML，并在浏览器中检查布局、交互和资源路径。
- 修改旅行路书流水线：区分 strict 交付与明示的离线草稿，核对退出码 `0`（成功）和 `2`（降级）；不要为测试擅自触发有费用或大量网络请求的完整流水线。
- 测试产生的临时文件、缓存和示例输出应清理，除非它们本身就是任务要求的交付物。

## 安装、版本与发布流程

插件安装不需要构建：各宿主通过对应清单直接加载 `skills/`。详细的市场、GitHub 和本地路径安装命令见 `README.md`。本地开发优先使用链接脚本，修改源码后可在目标项目实时生效；agent 会话可能需要重启或重新加载插件。

版本命令必须在仓库根目录执行：

```bash
npm run version:patch
npm run version:minor
npm run version:major
# 也支持显式版本
node scripts/version.js 1.2.3
```

`version.js` 会更新 `package.json` 和四个插件/市场 JSON 文件（包括 marketplace 中的插件条目），并根据最近 tag、release commit 和已有记录更新 `CHANGELOG.md`。它**不会**自动 commit、tag 或发布。执行后应检查所有版本号和 changelog diff；提交、打标和对外发布需要单独确认。仓库没有自动部署或发布流水线。

## 安全与副作用注意事项

- 不主动提交 Git；不擅自推送、打标、发布或安装到全局环境。
- `travel-planner` 可调用 TikHub、OpenAI 兼容接口和可选 `flyai` CLI。密钥位于该技能目录的 `.env`，不得打印、复制到示例或提交；网络搜索、LLM 润色和配图可能产生费用或泄露输入，严格按用户任务和技能说明执行。
- 路书报价、班次、酒店信息等不得编造；保留“实查 / 参考 / 估算”标识，降级产物必须明确提示人工核对。
- `explain-book` 的 `--install-missing yes` 会执行 pip 安装；非必要不自动安装依赖，交互默认是询问或使用降级方案。其默认中间文件位于系统临时目录，可用 `EXPLAIN_BOOK_WORKDIR` 覆盖。
- 技能可能向用户项目写入文档、修改 JSON、生成 HTML 或调用外部工具。先确认输出路径和影响范围，不假设所有操作都应发生在本仓库。
- 使用 `--force`、覆盖已有文件、安装缺失依赖或执行完整外部服务流水线前，检查现有说明中的确认门槛；能用 dry-run 时先预览。
