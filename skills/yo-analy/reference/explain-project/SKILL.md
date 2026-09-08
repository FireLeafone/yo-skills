---
name: explain-project
description: 分析代码库（前端 Node/React/Vue 或后端 Java/Python），生成详尽的人读项目文档 `explain-project.md`（技术维度），并可按端生成业务维度文档 `explain-business-*.md`。用于新成员上手、项目文档化、业务语义沉淀。
---

# 项目解析与文档生成技能（人读文档）

分析代码库并生成**面向人类阅读**的详尽项目文档，输出到项目根目录。分两个维度：

- **技术维度** `explain-project.md`：讲「项目怎么开发的」——技术栈、结构、约定、资源、部署。
- **业务维度** `explain-business-*.md`：讲「项目做什么、为什么」——业务总结、功能模块、接口场景、权限、数据模型、上下游、日志、流程图、核心交互。

## 输出结构

```
[项目根目录]
├── explain-project.md               # 技术维度文档（整仓一份，前后端分节）
├── explain-business-frontend.md     # 业务维度·前端（仅前端工程时产出）
└── explain-business-backend.md       # 业务维度·后端（仅后端工程时产出）
```

产出规则：
- 仅有前端工程 → 只产出 `explain-business-frontend.md`
- 仅有后端工程 → 只产出 `explain-business-backend.md`
- 全栈（前后端共存）→ 两份业务文档都产出；共享业务上下文（业务总结/角色/术语）以后端业务文档为主，前端文档引用之

## 工作流程

### 1. 确认输出范围

**必须等待用户确认后再继续。**

先确认产出维度与文档策略：

- **维度选择**（默认两者都产出）：
  - 仅技术维度 → 只生成 `explain-project.md`
  - 仅业务维度 → 只生成 `explain-business-*.md`
  - 两者 → 技术 + 业务文档
- 若对应业务文档已存在，提示用户选择「覆盖」还是「增量更新」
  - **增量更新**：先读取已有文档，保留历史沉淀的「已知坑」「特定配置说明」等，只用分析结果覆盖/更新变化部分
  - **覆盖**：按模板重新填充
- 默认生成 `[项目根目录]/explain-project.md` 与 `[项目根目录]/explain-business-*.md`

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

### 6. 业务维度分析

若 Step 1 选定产出业务文档，则按端分析业务语义。详见 `references/business-analysis-guide.md`。

- **端判定**：沿用 Step 2 的仓库类型识别结果，决定产出 `explain-business-frontend.md` / `explain-business-backend.md` / 两份
- **信息来源**：README、路由/页面/菜单、Controller/Service、数据库 schema/实体/迁移、配置中的第三方与 MQ、日志切面/中间件、枚举/错误码
- **章节清单**（按端取舍）：业务总结、业务角色与参与者、主要功能模块、接口及使用场景、权限设计及控制、数据库设计（仅后端）、上下游关联服务、日志设计及控制、领域事件/通知（仅后端）、业务流程图(mermaid)、关键状态机(mermaid)、业务规则与约束、业务核心交互明细、业务术语表
- **全栈去重**：共享业务上下文（业务总结/角色/术语）以后端业务文档为主，前端文档引用之，不重复长篇

业务语义**基于代码可验证信息归纳，勿编造**；无法确认的写「待补充」或「推测：…」。

---

### 7. 生成或更新文档

- 技术维度模板：`assets/explain-pm-template.md`
- 业务维度模板：`assets/explain-business-template.md`
- 输出路径：`[项目根目录]/explain-project.md`、`[项目根目录]/explain-business-*.md`
- **层级定位**：技术文档覆盖项目概述、技术栈、结构、开发约定、测试、部署、常见问题；业务文档覆盖业务语义、功能模块、接口场景、权限、数据、上下游、日志、流程
- **已有文档时**：先读取，保留历史沉淀的「已知坑」「特定配置说明」，用分析结果覆盖/更新变化部分
- **无文档时**：按模板填充，删除不适用章节（标注「仅前端 / 仅后端」的按端取舍）
- **边界清晰**：技术/业务两份文档重叠章节（如「主要功能模块」）侧重不同——技术文档写目录与代码组织，业务文档写业务语义与用户价值，勿重复大段

---

## 输出要求

### explain-project.md（技术维度）

最详尽的技术文档，按仓库实际类型组织章节：
- **共性**：项目概述、快速开始、项目结构、开发约定、测试、部署、常见问题、参考资源
- **前端为主时侧重**：技术栈（Node/框架/UI）、页面与路由、样式与交互约定、组件与 Hooks、状态管理、前端侧 API 调用约定
- **后端 Java/Python 为主时侧重**：运行时与构建、模块与分层、配置与多环境、对外 API、数据访问与集成、后端测试与打包运行

### explain-business-*.md（业务维度）

按端产出，讲业务语义而非代码构建：
- **共性**：业务总结、业务角色与参与者、主要功能模块、接口及使用场景、权限设计及控制、业务流程图、关键状态机、业务规则与约束、业务核心交互明细、业务术语表
- **前端侧重**：页面/功能域、调用的后端接口及场景、路由与前端权限控制、前端可见状态机、核心交互
- **后端侧重**：对外接口设计及场景、鉴权与权限模型、数据库设计(ER图)、上下游关联服务、日志设计及控制、领域事件/通知、业务状态机、核心链路

---

## Gotchas

1. **全栈项目易遗漏**：同时有 `package.json` 和 `pom.xml`/`build.gradle` 时，模型容易只分析前端。必须分别扫描两套入口，技术文档中分「前端 / 后端」两节；**业务文档分两份**，不合并。
2. **更新时覆盖历史信息**：已有 `explain-project.md` / `explain-business-*.md` 中的「已知坑」「特定配置说明」等历史沉淀，更新前必须先读取并保留，只覆盖分析结果会变化的部分。
3. **脚本失败不阻塞**：`analyze_project.py` 失败时，改为手工读取配置文件，不要因此中断产出。
4. **业务/技术边界勿重复**：两份文档重叠章节（如「主要功能模块」）侧重不同，技术文档写目录与代码组织，业务文档写业务语义与用户价值，勿复制大段。
5. **业务语义勿编造**：业务文档基于代码可验证信息归纳；无法确认的写「待补充」或「推测：…」，不要当事实写。
6. **前端权限只是体验层**：前端业务文档写权限时须注明真实权限以后端为准。

---

## 参考资源

- `references/frontend-analysis-guide.md` — 前端（Node）项目分析指南（技术维度）
- `references/backend-analysis-guide.md` — Java / Python 后端分析指南（技术维度）
- `references/business-analysis-guide.md` — 业务维度分析指南（前端 / 后端，端判定与去重约定）
- `assets/explain-pm-template.md` — 技术维度文档模板
- `assets/explain-business-template.md` — 业务维度文档模板
- `scripts/analyze_project.py` — 多生态项目信息探测辅助脚本
