# react-review

审查React组件，以了解最佳实践、性能问题以及常见模式，重点关注函数式组件设计、Hooks 的正确性、状态管理（本地和外部）、渲染性能、副作用和数据获取、路由和代码拆分以及可访问性。

## 核心目标

**主要目标**：针对给定的代码范围，生成一份 React 框架调查结果列表，涵盖组件设计、hook 正确性、状态管理、渲染性能、副作用、路由/代码拆分和可访问性。

成功标准（必须全部满足）：

- ✅仅限 React 框架范围：仅审查 React 框架约定；不进行范围选择、安全性或架构分析。
- ✅涵盖 React 的七个维度：组件设计、Hooks 正确性、状态管理、渲染性能、副作用/数据获取、路由/代码拆分以及可访问性（如适用）均已进行评估。
- ✅调查结果格式符合规范：每项调查结果均包含地点、类别（framework-react）、严重程度、标题、描述以及可选建议。
- ✅组件/文件引用：所有发现结果均引用特定文件：行或组件名称
- ✅排除非 React 代码：除非明确包含在作用域内，否则不会对非 React 文件进行 React 特定规则的分析。

## 范围边界

- 函数式组件设计（单一职责、组合模式、属性类型/默认值、子组件模式）
- Hooks 正确性（依赖数组、过时的闭包、自定义 hooks 提取、hooks 规则、useEffect 中的清理）
- 状态管理（本地状态与全局状态、上下文使用、reducer 模式、外部存储（如 Zustand/Redux）、服务器状态）
- 渲染性能（memo/useMemo/useCallback 的使用、列表中键的稳定性、避免不必要的重新渲染、大型列表的虚拟化）
- 副作用和数据获取（useEffect 模式、竞态条件、中止控制器、加载/错误状态、数据获取库）
- 路由和代码分割（React.lazy、Suspense 边界、基于路由的分割、错误边界）

## workflow

- 分析React组件的性能问题（不必要的重新渲染、large bundless） 
- 检查React最佳实践（hooks 使用、prop模式、状态管理、React.memo 是否需要） 
- 识别反模式（prop钻取、useEffect滥用、缺少keys） 
- 建议优化（记忆化、代码拆分、延迟加载） 
- 审查TypeScript使用情况和类型安全

## 输出格式

```markdown
## React Component Review

### Component: UserProfile.tsx

**Issues Found:**
1. 性能问题：接收对象 props 的组件缺少 React.memo
2. 最佳实践：useEffect缺少依赖数组
3. 类型安全：缺少用于 props 的 TypeScript 接口

**建议:**
1. 使用 React.memo 包裹组件
2. 为 useEffect 添加依赖数组
3. 为组件 props 创建 interface

**Code Suggestions:**
```typescript
interface UserProfileProps {
  user: User;
  onUpdate: (user: User) => void;
}

const UserProfile = React.memo(({ user, onUpdate }: UserProfileProps) => {
  // implementation
});
```

## 注意

- 聚焦于React 18+的模式和最佳实践 
- 同时考虑类组件和函数组件
- React.memo 不能滥用，是否真的影响性能
- 包含TypeScript和JavaScript两种变体 
- 参考官方React文档和社区模式
