# 前端项目分析指南

**适用范围**：以 **Node / 前端**（`package.json` 驱动）为主的仓库分析。

若仓库为 **Java / Python 后端**或 **全栈**（同时含前端与后端工程），请结合 `references/backend-analysis-guide.md` 分别填写文档中的前端与后端章节。

本文档提供前端项目分析的详细指导，帮助快速理解项目结构和关键信息。

## 分析步骤

### 1. 识别项目类型和框架

**关键文件**：
- `package.json` - 查看 dependencies 识别框架
- `tsconfig.json` / `jsconfig.json` - 确认是否使用 TypeScript
- 配置文件 - `vite.config.js`, `webpack.config.js`, `next.config.js` 等

**常见框架特征**：
- **React**: 依赖 `react`, `react-dom`，通常有 `src/App.jsx` 或 `src/App.tsx`
- **Vue**: 依赖 `vue`，通常有 `src/App.vue`，可能使用 `vue-router`, `vuex`/`pinia`
- **Angular**: 依赖 `@angular/core`，有 `angular.json`，使用 `.component.ts` 文件
- **Next.js**: 依赖 `next`，有 `pages/` 或 `app/` 目录
- **Nuxt**: 依赖 `nuxt`，有 `nuxt.config.js`

### 2. 提取技术栈信息

从 `package.json` 中识别：

**状态管理**：
- Redux: `redux`, `react-redux`, `@reduxjs/toolkit`
- MobX: `mobx`, `mobx-react`
- Zustand: `zustand`
- Vuex: `vuex`
- Pinia: `pinia`

**UI 组件库**：
- Ant Design: `antd`
- Material-UI: `@mui/material`
- Element Plus: `element-plus`
- Chakra UI: `@chakra-ui/react`
- Tailwind CSS: `tailwindcss`

**构建工具**：
- Vite: `vite`
- Webpack: `webpack`
- Rollup: `rollup`
- Parcel: `parcel`

**路由**：
- React Router: `react-router-dom`
- Vue Router: `vue-router`
- TanStack Router: `@tanstack/react-router`

### 3. 分析项目结构

**标准目录结构**：
```
src/
├── components/     # 公共组件
├── pages/         # 页面组件
├── hooks/         # 自定义 Hooks (React)
├── composables/   # 组合式函数 (Vue)
├── utils/         # 工具函数
├── services/      # API 服务
├── store/         # 状态管理
├── types/         # TypeScript 类型定义
├── constants/     # 常量定义
├── styles/        # 全局样式
└── assets/        # 静态资源
```

**关键文件位置**：
- 路由配置：`src/router/`, `src/routes/`, `pages/`
- API 接口：`src/api/`, `src/services/`, `src/utils/request.js`
- 类型定义：`src/types/`, `src/@types/`, `*.d.ts`
- 配置文件：`src/config/`, `src/constants/`

### 4. 识别开发约定

**样式方案**：
- CSS Modules: 文件名 `*.module.css`
- Styled Components: 导入 `styled-components`
- Emotion: 导入 `@emotion/react`
- Less/Sass: 文件扩展名 `.less`, `.scss`
- Tailwind: `tailwind.config.js` 存在

**命名规范**：
- 组件文件：PascalCase (`Button.tsx`) 或 kebab-case (`button.tsx`)
- 工具函数：camelCase (`formatDate.js`)
- 常量：UPPER_SNAKE_CASE (`API_BASE_URL`)
- Hooks: `use` 前缀 (`useAuth.ts`)

**代码组织模式**：
- 功能模块化：按功能分组 (`features/auth/`, `features/dashboard/`)
- 类型分组：按类型分组 (`components/`, `hooks/`, `utils/`)
- 页面路由：按路由结构 (`pages/home/`, `pages/user/profile/`)

### 5. 提取通用资源

**公共组件**：
- 查找 `src/components/` 目录
- 识别可复用组件：Button, Modal, Form, Table 等
- 记录组件的 props 接口

**自定义 Hooks (React)**：
- 查找 `src/hooks/` 或以 `use` 开头的文件
- 常见 Hooks: `useAuth`, `useRequest`, `useLocalStorage`

**工具函数**：
- 查找 `src/utils/`, `src/helpers/` 目录
- 常见工具：日期格式化、数据验证、请求封装

**常量和枚举**：
- 查找 `src/constants/`, `src/enums/` 目录
- API 端点、配置项、枚举值

**TypeScript 类型**：
- 查找 `src/types/`, `src/@types/` 目录
- 全局类型定义、接口定义

### 6. 环境和启动配置

**环境变量**：
- `.env`, `.env.local`, `.env.development`, `.env.production`
- 变量前缀：`VITE_`, `REACT_APP_`, `VUE_APP_`, `NEXT_PUBLIC_`

**启动命令**：
从 `package.json` 的 `scripts` 字段提取：
- 开发：`dev`, `start`, `serve`
- 构建：`build`
- 测试：`test`, `test:unit`, `test:e2e`
- 代码检查：`lint`, `format`

**Node 版本要求**：
- 查看 `package.json` 的 `engines` 字段
- 查看 `.nvmrc` 或 `.node-version` 文件

## 输出格式

使用提供的模板 `assets/explaining-pm-template.md` 作为输出格式，填充分析得到的信息。

## 注意事项

1. **优先读取配置文件**：先读取 `package.json`, `tsconfig.json` 等配置文件
2. **使用 Glob 查找文件**：使用 Glob 工具快速定位关键文件
3. **提取代码示例**：为通用资源提供实际的代码示例
4. **保持简洁**：只记录重要和常用的资源，避免列出所有文件
5. **验证路径**：确保记录的文件路径是正确的
