# yo-skills

一套适配个人/团队工作流的 **Agent Skills** 库，遵循 [Agent Skills 开放标准](https://agentskills.io/specification)。

支持三种安装方式：

| 方式 | 适用场景 |
|------|----------|
| **Claude 插件** | 在 Claude Code 中一键安装整套 skills |
| **Codex 插件** | 在 Codex CLI / App 中从插件市场安装 |
| **单独安装 skill** | 只装某一个 skill 到全局或项目目录 |

## 项目结构

```
yo-skills/
├── .claude-plugin/
│   ├── plugin.json              # Claude Code 插件清单
│   └── marketplace.json         # Claude Code 插件市场注册表
├── .codex-plugin/plugin.json    # Codex 插件清单
├── templates/                   # 新建 skill 的模板（不参与校验/安装）
├── skills/                      # Skills 唯一源码目录（SSOT）
│   └── xxx/                     # 本库 skills
├── .agents/skills/              # 团队项目级外部 skill（非本库维护，不参与校验/发布）
├── .claude                      # .agents 软链接
├── scripts/
│   ├── validate-skills.py       # 校验 skill 规范
│   └── version.js               # 版本更新
├── package.json                 # npm scripts 快捷命令
└── requirements.txt             # Python 校验依赖
```

## 环境准备

```bash
# Python 校验工具（推荐）
pip install -r requirements.txt

# 或使用 npm scripts
npm run skills:validate
```

## 安装方式

### 1. Claude Code 插件模式

**从插件市场安装（推荐）：**

```bash
# 1. 添加插件市场（只需一次）
/plugin marketplace add <your-org>/yo-skills

# 2. 安装插件
/plugin install yo-skills@yo-skills

# 3. 重新加载插件
/reload-plugins
```

**本地路径安装（开发调试）：**

```bash
# 方式一：直接安装本地路径
/plugin install D:/xxx/ai/yo-skills

# 方式二：用 --plugin-dir 启动（不安装到缓存，实时生效）
claude --plugin-dir D:/xxx/ai/yo-skills
```

安装后 Claude 自动发现 `skills/` 下所有 skill。插件中的 skill 以命名空间形式调用（如 `/yo-skills:yo`）。

### 2. Codex 插件模式

**插件市场（发布后）：**

```bash
/plugins
# 搜索 yo-skills → Install Plugin
```

**本地开发：** 将本仓库注册为 Codex 插件源，或直接使用 `skills/` 目录（见下方单独安装）。

Codex 通过 `.codex-plugin/plugin.json` 中的 `"skills": "./skills/"` 加载 skills。

### 3. 单独安装 Skill

**方式 A — npx skills CLI（推荐，跨平台）：**

```bash
# 安装单个 skill 到全局
npx skills add <git-url>/skills --skill creating-yo-skills -y --global

# 安装到当前项目
npx skills add <git-url>/skills --skill creating-yo-skills -y

# 查看已安装
npx skills list
```

**各 Agent 默认 skill 目录：**

| Agent | 全局目录 | 项目目录 |
|-------|----------|----------|
| Claude Code | `~/.claude/skills/` | — |
| Codex | `~/.agents/skills/`、`~/.codex/skills/` | `.agents/skills/` |
| Cursor | `~/.cursor/skills/` | `.cursor/skills/` |

安装后**重启 agent 会话**以加载新 skill。

## 开发新 Skill

```bash
# 1. 可以使用 skill-creator 创建，再使用 skill-optimizer 优化skill

/skill-creator  ....
/skill-optimizer ...

# 2. review skills/xxx

# 3. 校验
python scripts/validate-skills.py --skill xxx

# 4. 本地试装
.\scripts\install-local-skill.ps1 -Target D:\path\to\your-project
.\scripts\install-local-skill.ps1 -Target D:\path\to\your-project -SkillName test-skill
.\scripts\install-local-skill.ps1 -Target D:\path\to\your-project -Force
npm run skills:link -- --target D:/path/to/your-project
npm run skills:link -- --target D:/path/to/your-project --skill my-skill
```

编写规范详见 `templates/SKILL.md`。

### 编写要点

- **description 只写触发条件**（WHEN），不要写完整工作流（避免 agent 跳过正文）
- **目录名 = frontmatter `name`**，使用 hyphen-case
- **SKILL.md 控制在 500 行以内**，详细内容放 `references/`
- **低频高危 skill** 加 `disable-model-invocation: true`

## npm 快捷命令

```bash
npm run skills:validate   # 校验全部 skills
npm run version:patch
npm run version:minor
npm run version:major
```

## 参考

- [Agent Skills 规范](https://agentskills.io/specification)
- [Claude Code 插件结构](https://docs.anthropic.com/en/docs/claude-code/plugins)
- [Codex Skills 文档](https://developers.openai.com/codex/skills/)
- [npx skills CLI](https://github.com/vercel-labs/skills)

## License

MIT
