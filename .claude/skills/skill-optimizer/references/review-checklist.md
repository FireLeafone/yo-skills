# Skill Review Checklist

按需审查，不必每次穷举所有项目。若用户已指定优化方向，先覆盖对应部分。

本文件职责：**逐条检查项**。模式判断和设计质量评估用 [skill-design-review-framework.md](skill-design-review-framework.md)。

## 1. Triggering

- `name` 只含小写字母、数字、连字符，与目录名完全一致
- `description` 同时说明"做什么"和"何时使用"，包含用户真实会说的关键词
- `description` 用第三人称，避免空泛描述（如"帮助处理各种内容")
- 技能边界写清楚，避免和相邻 skill 抢触发

## 2. Workflow

- 有明确步骤顺序
- 必须确认的步骤有等待确认的门槛
- 说明输入、输出、落盘位置或交付格式
- 对失败场景给出降级策略
- "应该做"和"禁止做"写清楚

## 3. Progressive Disclosure

- SKILL.md 只保留核心流程
- 详细规则/示例/长说明拆到 `references/`
- 所有 `references/` 直接从 SKILL.md 链接（一级深度）
- 无多层嵌套引用
- 无 SKILL.md 与 references 的大段内容重复

## 4. Resource Strategy

- 反复手写且适合脚本化的操作有 `scripts/` 封装
- 稳定执行所需的模板/脚本/参考资料齐全
- `assets/` 只放输出资源，不放说明文档
- 无不必要的 README/CHANGELOG 等噪音文件

## 5. Output Contract

- 输出可直接给用户或下游 agent 使用
- 区分"审查结论""优化计划""最终修改结果"
- 确认回复的触发条件写清（如"确认""开始修改")
- 最终汇报列出已修改文件和剩余风险

## 6. Prioritization

问题按此顺序排序：
1. 高优先级：触发失败、确认缺失、工作流错误、明显冲突
2. 中优先级：结构臃肿、资源组织差、上下文浪费
3. 低优先级：措辞打磨、示例增强、展示优化
