---
name: explain-project
description: 分析代码库（前端 Node/React/Vue 或后端 Java/Python）并生成详尽的人读项目文档 `explain-project.md`，放在项目根目录。用于新成员上手、项目文档化。
---

# 项目解析与文档生成技能（人读文档）

分析代码库并生成**面向人类阅读**的详尽项目文档 `explain-project.md`，输出到项目根目录。

## 输出结构

```
[项目根目录]
└── explain-project.md       # 详尽项目文档（人类阅读）
```

## 工作流程

### 1. 确认输出范围

**必须等待用户确认后再继续。**

- 默认生成 `[项目根目录]/explain-project.md`
- 若该文档已存在，提示用户选择「覆盖」还是「增量更新」
  - **增量更新**：先读取已有文档，保留历史沉淀的「已知坑」「特定配置说明」等，只用分析结果覆盖/更新变化部分
  - **覆盖**：按模板重新填充

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

### 6. 生成或更新 `explain-project.md`

- 使用模板：`assets/explain-pm-template.md`
- 输出路径：`[项目根目录]/explain-project.md`
- **层级定位**：最详尽的项目文档，覆盖项目概述、技术栈、结构、开发约定、测试、部署、常见问题等
- **已有文档时**：先读取，保留历史沉淀的「已知坑」「特定配置说明」，用分析结果覆盖/更新变化部分
- **无文档时**：按模板填充，删除不适用章节（标注「仅前端 / 仅后端」的按仓库类型取舍）

---

## 输出要求

### explain-project.md

最详尽的项目文档，按仓库实际类型组织章节：
- **共性**：项目概述、快速开始、项目结构、开发约定、测试、部署、常见问题、参考资源
- **前端为主时侧重**：技术栈（Node/框架/UI）、页面与路由、样式与交互约定、组件与 Hooks、状态管理、前端侧 API 调用约定
- **后端 Java/Python 为主时侧重**：运行时与构建、模块与分层、配置与多环境、对外 API、数据访问与集成、后端测试与打包运行

---

## Gotchas

1. **全栈项目易遗漏**：同时有 `package.json` 和 `pom.xml`/`build.gradle` 时，模型容易只分析前端。必须分别扫描两套入口，文档中分「前端 / 后端」两节。
2. **更新时覆盖历史信息**：已有 `explain-project.md` 中的「已知坑」「特定配置说明」等历史沉淀，更新前必须先读取并保留，只覆盖分析结果会变化的部分。
3. **脚本失败不阻塞**：`analyze_project.py` 失败时，改为手工读取配置文件，不要因此中断产出。

---

## 参考资源

- `references/frontend-analysis-guide.md` — 前端（Node）项目分析指南
- `references/backend-analysis-guide.md` — Java / Python 后端分析指南
- `assets/explain-pm-template.md` — 详尽项目文档模板
- `scripts/analyze_project.py` — 多生态项目信息探测辅助脚本（与 `agents-docs` 共享）
