---
name: explain-project
description: 分析代码库（前端 Node/React/Vue 或后端 Java/Python）并在 `.agents/` 生成项目文档（AGENTS.md、rules、skills）。用于新成员上手、项目文档化、生成 AI 协作文档。`.claude` 作为 `.agents` 的软链接。
---

# 项目解析与文档生成技能

分析代码库并生成项目文档：
- **AI 协作文档**：存放在 `.agents/` 目录（AGENTS.md、rules、skills）
- **详尽项目文档**：`explaining-project.md` 放在项目根目录，供人类阅读

## 输出结构

```
[项目根目录]
├── explaining-project.md       # 详尽项目文档（人类阅读）
└── .agents/
    ├── AGENTS.md              # Agent 协作文档（主文件）
    ├── CLAUDE.md              # Claude Code 兼容入口（→ 内容直接写： @AGENTS.md ）
    ├── rules/
    │   ├── common-rules.md    # 通用 AI Coding 行为规则
    │   ├── coding-style.md    # 代码风格规则
    │   ├── architecture-rules.md  # 架构规则
    │   └── testing-rules.md   # 测试规则
    └── skills/
        └── {project-specific}/
            └── SKILL.md       # 项目特定开发技能
```

`.claude` → `.agents`（目录级软链接）

## 工作流程

### 0. 前置检查

检查 `.claude/` 和 `.agents/` 状态：

| 状态 | 处理方式 |
|------|----------|
| `.agents/` 已存在 | 直接进入分析流程 |
| `.claude/` 存在、`.agents/` 不存在 | 迁移 `.claude/` → `.agents/`，再创建软链接 |
| 两者都不存在 | 创建 `.agents/`，再创建软链接 |
| `.claude` 已是软链接 → `.agents` | 正常，直接操作 `.agents/` |

**迁移操作**：
```bash
# 1. 创建 .agents/ 并迁移内容
mkdir .agents
mv .claude/* .agents/ 2>/dev/null || true

# 2. 删除原 .claude/ 目录，创建软链接
rm -rf .claude
ln -sf .agents .claude
```

> **Windows 注意**：目录符号链接需要管理员权限或开发者模式。若失败，保留独立 `.claude/` 目录，仅在其内创建 `CLAUDE.md` → @ 引用文件`.agents/AGENTS.md` 。

---

### 1. 确认输出范围

**必须等待用户确认后再继续。**

询问用户需要生成哪些文档（可多选）：

| 输出 | 用途 | 路径 |
|------|------|------|
| `explaining-project.md` | 详尽项目文档，新成员上手 | `[项目根目录]/explaining-project.md` |
| `AGENTS.md` | Agent 协作核心文档 | `.agents/AGENTS.md` |
| `CLAUDE.md` | claude code 协作核心文档 | `.agents/CLAUDE.md` |
| `rules/` | AI Coding 规则补充 | `.agents/rules/*.md` |
| `skills/` | 项目特定开发技能 | `.agents/skills/*/SKILL.md` |

- 用户未指定时，询问是否默认生成全部（含 `explaining-project.md` + `.agents/` 全套）
- 用户明确指定后，只生成指定内容
- 若目标文档已存在，提示用户是「覆盖」还是「增量更新」

---

### 2. 识别仓库类型

判断仓库类型（可多选）：

| 类型 | 标记文件 |
|------|----------|
| **Node / 前端** | `package.json` |
| **JVM / Java** | `pom.xml`、`build.gradle` / `build.gradle.kts` |
| **Python** | `pyproject.toml`、`requirements.txt`、`setup.py` |

可选运行辅助脚本快速探测：
```bash
python scripts/analyze_project.py <项目根目录>
```
脚本失败时，手工读取上表中的标记文件。

---

### 3. 读取配置文件

**前端**：
```bash
Read package.json
Read tsconfig.json / jsconfig.json（若存在）
Read vite.config.* / webpack.config.* / next.config.*（若存在）
```

**Java**：
```bash
Read pom.xml 或 build.gradle / build.gradle.kts
Read src/main/resources/application*.yml 或 application*.properties（若存在）
```

**Python**：
```bash
Read pyproject.toml 或 setup.cfg / setup.py（若存在）
Read requirements.txt 或 requirements-*.txt 或 Pipfile（若存在）
Read 应用入口附近配置（如 manage.py、.env.example）
```

---

### 4. 识别技术栈与结构

**前端**：识别框架、状态管理、UI 库、构建工具、包管理器。详见 `references/frontend-analysis-guide.md`。

**后端 Java**：识别 Maven/Gradle、Spring Boot、模块结构。详见 `references/backend-analysis-guide.md` Java 部分。

**后端 Python**：识别 Django/FastAPI/Flask、依赖管理工具。详见 `references/backend-analysis-guide.md` Python 部分。

使用 Glob 查找关键目录和文件：

```text
# 前端
Glob: "src/**/*.{tsx,ts,jsx,js,vue}"
Glob: "src/api/**/*.{ts,js}"
Glob: "src/hooks/**/*.{ts,js}" 或 "src/**/use*.{ts,js}"

# Java
Glob: "src/main/java/**/*.java"
Glob: "src/test/java/**/*.java"
Glob: "**/application*.yml" 或 "**/application*.properties"

# Python
Glob: "**/*.py"
Glob: "**/settings.py" 或 "**/config*.py"
Glob: "tests/**/*.py" 或 "**/test_*.py"
```

---

### 5. 提取开发约定与通用资源

**前端**：样式方案、组件命名、路由与状态管理组织。见 `references/frontend-analysis-guide.md`。

**后端**：分层/包约定、异常与校验、日志、API 风格。见 `references/backend-analysis-guide.md`。

提取通用资源（附简短示例）：
- 前端：公共组件、自定义 Hooks、工具函数、常量、TypeScript 类型
- 后端：可复用模块、配置封装、中间件/过滤器、数据访问层

---

### 6. 生成或更新文档

#### 6.1 explaining-project.md

- 使用模板：`assets/explaining-project-template.md`
- 输出路径：`[项目根目录]/explaining-project.md`
- **层级定位**：最详尽的项目文档，覆盖项目概述、技术栈、结构、开发约定、测试、部署、常见问题等
- **已有文档时**：先读取，保留历史沉淀的「已知坑」「特定配置说明」，用分析结果覆盖/更新变化部分
- **无文档时**：按模板填充，删除不适用章节（标注「仅前端 / 仅后端」的按仓库类型取舍）
- `AGENTS.md` 可引用此文档：「详见 `explaining-project.md`」

#### 6.2 AGENTS.md & CLAUDE.md

**AGENTS.md**：
- 使用模板：`assets/agent-template.md`
- 输出路径：`.agents/AGENTS.md`
- **定位**：精炼的项目概览与入口文档，**不重复** `rules/` 已覆盖的代码风格、Git 规范等内容
- **已有文档时**：先读取，保留历史沉淀信息，增量更新变化部分
- **无文档时**：按模板填充分析结果，删除不适用章节

**CLAUDE.md**：
- 输出路径：`.agents/CLAUDE.md`
- **定位**：Claude Code 兼容入口，内容与 AGENTS.md 一致
- **实现**：`.agents/CLAUDE.md` → @ 引用 `.agents/AGENTS.md` 

#### 6.3 Rules（`.agents/rules/`）

根据项目分析结果生成以下规则文件（使用 `assets/rules-templates/` 模板）：

| 文件 | 内容 | 触发条件 |
|------|------|----------|
| `common-rules.md` | 通用 AI Coding 行为规则（思考方式、简洁性、变更范围、目标驱动） | 始终生成 |
| `coding-style.md` | 命名规范、缩进格式、注释规范、Git 规范 | 项目有明确代码风格时 |
| `architecture-rules.md` | 分层约定、模块边界、依赖方向、数据流 | 项目有特定架构模式时 |
| `testing-rules.md` | 测试策略、Mock 规范、覆盖率要求 | 项目有测试体系时，没有测试体系，则不生成 |

**Rules 编写原则**：只写该项目**特有**的约定和本skill 内置的，不写通用常识（项目自己添加）。

#### 6.4 Skills（`.agents/skills/`）

根据项目特点生成项目特定 skill：

| 典型 skill | 用途 | 示例目录名 |
|-----------|------|-----------|
| 前端开发规范 | 组件开发、状态管理、路由约定 | `{project}-frontend-dev` |
| 后端开发规范 | API 设计、分层开发、数据访问 | `{project}-backend-dev` |
| API 调用封装 | 前后端接口调用模式 | `{project}-api-client` |
| 部署与运维 | 构建、部署、环境配置 | `{project}-deployment` |

- 使用模板：`assets/skill-template.md`
- 目录命名：kebab-case，与 skill 的 `name` 字段一致
- 每个 skill 只聚焦一个具体开发场景

---

### 7. 创建 `.claude` 软链接

完成文档生成后，确保 `.claude` 正确指向 `.agents`：

```bash
# Unix / macOS
ln -sf .agents .claude

# Windows PowerShell
New-Item -ItemType SymbolicLink -Path .claude -Target .agents
```

若环境无权限创建目录软链接：提示获取管理员权限，再创建

---

## 输出要求

### explaining-project.md

最详尽的项目文档，按仓库实际类型组织章节：
- **共性**：项目概述、快速开始、项目结构、开发约定、测试、部署、常见问题、参考资源
- **前端为主时侧重**：技术栈（Node/框架/UI）、页面与路由、样式与交互约定、组件与 Hooks、状态管理、前端侧 API 调用约定
- **后端 Java/Python 为主时侧重**：运行时与构建、模块与分层、配置与多环境、对外 API、数据访问与集成、后端测试与打包运行

### AGENTS.md

精炼的项目概览与入口文档，聚焦 Agent 快速理解项目所需的核心信息：
- 项目背景、技术栈、环境配置、常用命令、项目主要架构
- 引用 `.agents/rules/`（不在 AGENTS.md 中重复 rules 已覆盖的代码风格、Git 规范等）

### CLAUDE.md

`.agents/CLAUDE.md` 内容，@引用 `.agents/AGENTS.md` 的文件，作为 Claude Code 的兼容入口。引用后可以不单独维护。

### Rules

每条规则应具备：
- **Scope**：适用场景（文件类型、目录范围）
- **Rule**：具体约定（必须/禁止/推荐）
- **Example**：正例/反例代码片段
- **Rationale**：原因说明（可选）

### Skills

每个 skill 应具备：
- 标准 frontmatter（`name`、`description`）
- 明确的工作流程
- 与该项目技术栈强相关的具体步骤
- 适用触发条件

---

## Gotchas

1. **Windows 软链接权限**：目录符号链接在 Windows 默认需要管理员权限。优先尝试，失败时降级为文件级软链接方案。
2. **已有 `.claude/` 内容迁移**：迁移前先确认 `.claude/` 内文件清单，避免误删用户的 settings.json 等配置。建议先复制再删除。
3. **全栈项目易遗漏**：同时有 `package.json` 和 `pom.xml`/`build.gradle` 时，模型容易只分析前端。必须分别扫描两套入口，文档中分「前端 / 后端」两节。
4. **更新时覆盖历史信息**：已有 `AGENTS.md` 中的「已知坑」「特定配置说明」等历史沉淀，更新前必须先读取并保留，只覆盖分析结果会变化的部分。
5. **Rules 不要写通用常识**：如「React 组件用大驼峰」「Java 类名用大驼峰」等通用知识不应写入 rules。只写该项目特有的、从代码库中提炼出的约定。
6. **AGENTS.md 不要重复 rules 内容**：代码风格、Git 规范、命名约定等已由 `rules/coding-style.md` 承载，AGENTS.md 只保留项目概览和指向 rules 的引用。避免两份文档写同一件事。
7. **Skills 不要过度设计**：每个 skill 聚焦一个具体场景（如「如何添加新页面」「如何新增 API」），不要试图做一个涵盖所有开发的万能 skill。
8. **脚本失败不阻塞**：`analyze_project.py` 失败时，改为手工读取配置文件，不要因此中断产出。

---

## 参考资源

- `references/frontend-analysis-guide.md` — 前端（Node）项目分析指南
- `references/backend-analysis-guide.md` — Java / Python 后端分析指南
- `assets/explaining-project-template.md` — 详尽项目文档模板
- `assets/agent-template.md` — Agent 协作文档模板
- `assets/rules-templates/common-rules.md` — 通用 AI Coding 行为规则模板
- `assets/rules-templates/coding-style.md` — 代码风格规则模板
- `assets/rules-templates/architecture-rules.md` — 架构规则模板
- `assets/rules-templates/testing-rules.md` — 测试规则模板
- `assets/skill-template.md` — 项目特定 skill 模板
- `scripts/analyze_project.py` — 多生态项目信息探测辅助脚本
