# vue-review

审查Vue组件，以了解最佳实践、性能问题以及常见模式。重点关注组合式 API 、响应式（ref/reactive、computed/watch）、组件边界和 props/emits、状态（Pinia/store）、路由和守卫、性能（例如 v-memo）以及相关的可访问性。

## 核心目标

**主要目标**：针对给定的代码范围，生成一份 Vue 3 框架调查结果列表，涵盖组合 API 使用情况、响应式正确性、组件边界、状态管理、路由、性能和可访问性。

成功标准（必须全部满足）：

- ✅仅限 Vue 3 框架：仅审查 Vue 3 框架规范；不进行范围选择、安全性或架构分析。
- ✅涵盖了 Vue 的七个维度：组合 API/脚本设置、响应式（ref/reactive/computed/watch）、组件边界/props/emits、状态（Pinia）、路由/守卫、渲染性能以及可访问性（在相关情况下进行评估）。
- ✅调查结果格式符合规范：每项调查结果均包含地点、类别（framework-vue）、严重程度、标题、描述以及可选建议。
- ✅组件/文件引用：所有发现结果均引用特定文件：行或组件名称
- ✅非 Vue 代码已排除：除非明确包含在分析范围内，否则不会对非 Vue 文件应用 Vue 特定规则。

## 范围边界

- 组合式 API 和<script setup>正确性（defineProps、defineEmits、defineExpose、生命周期钩子）
- 反应性正确性（引用与反应式、计算式与监视式、属性突变、深度反应性）
- 组件边界设计（props/emits 合约、prop 钻孔、提供/注入）
- 状态管理（Pinia/Vuex：动作与直接修改，避免服务器状态重复）
- 路由（Vue Router、导航守卫、延迟加载、路由参数/查询处理）
- 性能（v-memo（不能滥用，除非真的影响性能）、v-for 关键稳定性、不必要的重新渲染）
- 辅助功能（语义化 HTML、ARIA、表单标签、焦点管理）

## workflow

- 分析Vue组件的性能问题（不必要的重新渲染、large bundless） 
- 检查Vue最佳实践（组合式 API、hooks 使用、prop模式、状态管理） 
- 识别反模式（prop钻取、缺少keys等） 
- 建议优化（记忆化、代码拆分、延迟加载等） 
- 审查TypeScript使用情况和类型安全

## 输出格式

```markdown
## Vue Component Review

### Component: UserProfile.vue

**Issues Found:**
1. 性能问题：接收对象 props 的组件未使用 v-memo 或 shallowRef
2. 最佳实践：watch 缺少 immediate/deep 等必要选项
3. 类型安全：缺少用于 props 的 TypeScript 接口定义

**建议:**
1. 使用 defineOptions 或 v-memo 优化子组件渲染
2. 为 watch 添加合适的选项（immediate、deep、flush）
3. 使用 defineProps 的泛型或 withDefaults 定义 props 类型

**Code Suggestions:**
```vue
<script setup lang="ts">
interface User {
  id: string;
  name: string;
}

interface Props {
  user: User;
}

const props = withDefaults(defineProps<Props>(), {});

const emit = defineEmits<{
  update: [user: User];
}>();

// 使用 computed 避免不必要的响应式追踪
const displayName = computed(() => props.user.name);
</script>

<template>
  <div v-memo="[user]">
    {{ displayName }}
  </div>
</template>
```
```

## 注意

- 聚焦于vue@3的模式和最佳实践 
- 同时考虑多种模式的vue组件
- v-memo不能滥用，除非真的影响性能
- 包含TypeScript和JavaScript两种变体 
- 参考官方Vue文档和社区模式
