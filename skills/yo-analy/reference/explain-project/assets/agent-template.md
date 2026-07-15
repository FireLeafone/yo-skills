# AGENTS.md

> 本文件供 Agent / Claude Code 等 AI 工具理解项目。适用于：Agent 上下文注入、项目结构理解。

## 1. 项目背景

### 1.1 项目简介
[项目名称] - [一句话描述项目核心目标]

[核心功能]：主要业务功能

### 1.2 项目类型
- [ ] 前端（Node/React/Vue/Angular）
- [ ] 后端（Java Spring / Python Django/FastAPI）

---

## 2. 技术栈

### 2.1 前端（不限，如适用）

| 类别 | 技术 |
|------|------|
| 框架 | [React 18 / Vue 3 / Angular 17 / Next.js 14 / etc] |
| 状态管理 | [Redux Toolkit / Zustand / Pinia / Vuex] |
| UI 库 | [Ant Design / Element Plus / Material-UI / Tailwind CSS] |
| 样式方案 | [CSS Modules / Styled Components / Less / Sass] |
| 构建工具 | [Vite / Webpack / esbuild] |
| 包管理器 | [npm / yarn / pnpm] |
| TypeScript | [是/否] |

### 2.2 后端（不限，如适用）

| 类别 | 技术 |
|------|------|
| 语言/运行时 | [Java 17 / Python 3.11 / Node.js 20] |
| 主框架 | [Spring Boot 3 / Django 5 / FastAPI / Express] |
| 构建工具 | [Maven / Gradle / pip / poetry / uv] |
| 数据库 | [MySQL 8 / PostgreSQL / SQLite / Redis] |
| ORM | [JPA / SQLAlchemy / Prisma / TypeORM] |

---

## 3. 环境变量

| 变量名 | 用途 | 示例值 |
|--------|------|--------|
| [VITE_API_URL] | [后端 API 地址] | [http://localhost:8080] |

---

## 4. 常用命令

```bash
# 安装依赖
[pnpm install / npm install / mvn install / etc]

# 开发模式
[pnpm dev / npm run dev / mvn spring-boot:run]

# 构建
[pnpm build / npm run build / mvn package]

# 测试
[pnpm test / npm run test / mvn test]

# 代码检查
[pnpm lint / npm run lint / pnpm type-check]
```

---

## 5. 注意事项

- [重要提醒 1]
- [重要提醒 2]
- [常见问题/已知坑]

---

## 6. AI Rules（`.agents/rules/`）

代码风格、架构、测试等约定详见以下文件，**不要在 AGENTS.md 中重复** rules 已覆盖的内容：

| 规则文件 | 内容 |
|----------|------|
| `common-rules.md` | 通用 AI Coding 行为规则（思考方式、简洁性、变更范围、目标驱动） |
| `coding-style.md` | 命名规范、缩进格式、注释规范、Git 规范 |
| `architecture-rules.md` | 项目目录架构、分层约定、模块边界、依赖方向、数据流 |
| `testing-rules.md` | 测试策略、Mock 规范、覆盖率要求 |
