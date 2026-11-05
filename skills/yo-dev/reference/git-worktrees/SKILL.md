---
name: git-worktrees
description: 在开始需要与当前工作区隔离的功能开发或执行实现计划时使用 — 通过原生工具或 git worktree 回退确保存在一个隔离的工作区
---

# 使用 Git Worktrees

## 概述

确保工作在隔离的工作区中进行。优先使用平台的原生工作树工具。仅在没有原生工具可用时回退到手动 git worktree。

**核心原则：** 先检测现有隔离状态。再使用原生工具。最后回退到 git。绝不与 harness 对抗。

**开始时声明：** "我正在使用 git-worktrees 技能来设置一个隔离的工作区。"

## 第 0 步：检测现有隔离

**在创建任何东西之前，检查你是否已经处于隔离工作区中。**

```bash
GIT_DIR=$(cd "$(git rev-parse --git-dir)" 2>/dev/null && pwd -P)
GIT_COMMON=$(cd "$(git rev-parse --git-common-dir)" 2>/dev/null && pwd -P)
BRANCH=$(git branch --show-current)
```

**子模块防护：** `GIT_DIR != GIT_COMMON` 在 git 子模块内部也为真。在得出"已在 worktree 中"的结论之前，请验证你不在子模块中：

```bash
# 如果返回路径，说明你在子模块中，而非 worktree — 按正常仓库处理
git rev-parse --show-superproject-working-tree 2>/dev/null
```

**如果 `GIT_DIR != GIT_COMMON`（且不是子模块）：** 你已处于链接的 worktree 中。跳到第 3 步（项目设置）。**不要**创建另一个 worktree。

按分支状态报告：
- 在分支上："已在隔离工作区 `<path>` 的分支 `<name>` 上。"
- 分离 HEAD："已在隔离工作区 `<path>` 中（分离 HEAD，外部管理）。需要在完成时创建分支。"

**如果 `GIT_DIR == GIT_COMMON`（或在子模块中）：** 你在正常的仓库检出中。

用户是否已在其指令中表明了对 worktree 的偏好？如果没有，在创建 worktree 之前征求同意：

> "您是否希望我设置一个隔离的 worktree？它可以保护您当前的分支免受更改影响。"

尊重任何已声明的偏好，无需再次询问。如果用户拒绝同意，就在原地工作并跳到第 3 步。

## 第 1 步：创建隔离工作区

**你有两种机制。按此顺序尝试。**

### 1a. 原生工作树工具（优先）

用户已请求隔离工作区（第 0 步同意）。你是否已有创建 worktree 的方式？它可能是名为 `EnterWorktree`、`WorktreeCreate`、一个 `/worktree` 命令或 `--worktree` 标志的工具。如果有，请使用它并跳到第 3 步。

原生工具自动处理目录放置、分支创建和清理。当你有原生工具时使用 `git worktree add` 会创建 harness 无法看到或管理的幽灵状态。

仅在第 1a 步不适用时进入第 1b 步。

### 1b. Git Worktree 回退

**仅在第 1a 步不适用时使用** — 你没有可用的原生工作树工具。使用 git 手动创建 worktree。

#### 目录选择

按以下优先级顺序。用户明确的偏好始终优先于文件系统状态。

1. **检查指令中是否声明了 worktree 目录偏好。** 如果用户已指定，直接使用，无需询问。

2. **检查是否存在项目本地 worktree 目录：**

   ```bash
   ls -d .worktrees 2>/dev/null     # 优先（隐藏）
   ls -d worktrees 2>/dev/null      # 备选
   ```

   如果找到，使用它。如果两者都存在，`.worktrees` 优先。

3. **检查是否存在全局目录：**

   ```bash
   project=$(basename "$(git rev-parse --show-toplevel)")
   ls -d ~/.config/yo/worktrees/$project 2>/dev/null
   ```

   如果找到，使用它（与遗留全局路径向后兼容）。

4. **如果没有其他指引可用**，默认使用项目根目录下的 `.worktrees/`。

#### 安全验证（仅限项目本地目录）

**必须在创建 worktree 前验证目录已被忽略：**

```bash
git check-ignore -q .worktrees 2>/dev/null || git check-ignore -q worktrees 2>/dev/null
```

**如果未被忽略：** 停止创建，向用户说明风险。用户同意修改 `.gitignore` 后再追加规则；不要自动提交。若用户不希望修改 `.gitignore`，改用已获认可的项目外目录。

**为何关键：** 防止意外将 worktree 内容提交到仓库，同时避免为了创建工作区而产生未经请求的提交。

全局目录（`~/.config/yo/worktrees/`）无需验证。

#### 创建 Worktree

```bash
project=$(basename "$(git rev-parse --show-toplevel)")

# 根据选定的位置确定路径
# 项目本地: path="$LOCATION/$BRANCH_NAME"
# 全局: path="~/.config/yo/worktrees/$project/$BRANCH_NAME"

git worktree add "$path" -b "$BRANCH_NAME"
cd "$path"
```

**沙箱回退：** 如果 `git worktree add` 因权限错误（沙箱拒绝）而失败，告知用户沙箱阻止了 worktree 创建，你将改在当前目录工作。然后在原地运行设置和基线测试。

## 第 3 步：项目设置

先读取项目文档、包管理器清单和锁文件，只使用项目已经声明的工具与命令。不要仅凭存在 `pyproject.toml` 就假定使用 Poetry，也不要把 npm 当成所有 Node 项目的默认包管理器。

- 安装会修改环境或锁文件前，说明命令和影响；优先使用项目文档的既定安装命令。
- 依赖已在共享环境可用时，可跳过重复安装并记录验证方式。
- 缺少项目声明的工具或安装失败时停止设置并报告，不擅自更换包管理器或全局安装。

## 第 4 步：验证干净基线

运行项目实际声明且适用于本次工作的测试或检查命令；不存在测试时运行可用的静态检查，并明确说明没有测试，不编造测试数量。

**如果检查失败：** 记录为既有基线问题，报告失败并询问是否继续或调查。

**如果检查通过：** 报告实际命令和结果。

### 报告

```text
Worktree 已就绪，位于 <完整路径>
基线验证：<实际命令及结果；未运行的项目明确标注>
准备实现 <功能名称>
```

## 速查参考

| 情况 | 操作 |
|-----------|--------|
| 已在链接的 worktree 中 | 跳过创建（第 0 步） |
| 在子模块中 | 按正常仓库处理（第 0 步防护） |
| 有原生工作树工具可用 | 使用它（第 1a 步） |
| 无原生工具 | Git worktree 回退（第 1b 步） |
| `.worktrees/` 存在 | 使用它（验证是否被忽略） |
| `worktrees/` 存在 | 使用它（验证是否被忽略） |
| 两者都存在 | 使用 `.worktrees/` |
| 都不存在 | 检查指令文件，然后默认 `.worktrees/` |
| 全局路径存在 | 使用它（向后兼容） |
| 目录未被忽略 | 暂停；经同意后修改 .gitignore，不自动提交 |
| 创建时权限错误 | 报告原因，经用户同意后原地工作 |
| 基线检查失败 | 报告失败 + 询问 |
| 无依赖清单 | 跳过依赖安装并说明 |

## 常见错误

### 与 harness 对抗

- **问题：** 当平台已提供隔离时使用 `git worktree add`
- **修复：** 第 0 步检测现有隔离。第 1a 步优先使用原生工具。

### 跳过检测

- **问题：** 在现有 worktree 内部创建嵌套 worktree
- **修复：** 创建任何东西前始终运行第 0 步

### 跳过忽略验证

- **问题：** Worktree 内容被跟踪，污染 git 状态
- **修复：** 创建项目本地 worktree 前始终使用 `git check-ignore`

### 假设目录位置

- **问题：** 造成不一致，违反项目约定
- **修复：** 遵循优先级：现有 > 全局遗留 > 指令文件 > 默认

### 测试失败仍继续

- **问题：** 无法区分新 bug 与既有问题
- **修复：** 报告失败，获取明确的继续许可

## 红旗警示

**绝不：**

- 当第 0 步检测到现有隔离时创建 worktree
- 有原生工作树工具时绕过它使用 `git worktree add`
- 未经同意修改 `.gitignore`、提交、推送或全局安装依赖
- 创建项目本地 worktree 前未验证忽略规则
- 没有任何测试时编造通过结果
- 未经询问就在基线检查失败时继续

**始终：**

- 先运行第 0 步检测
- 优先使用原生工具而非 Git 回退
- 遵循目录优先级：用户指定 > 项目现有 > 全局遗留 > 默认
- 验证项目本地目录是否被忽略
- 按项目文档、清单和锁文件选择设置命令
- 运行实际存在的基线检查并报告未覆盖项
