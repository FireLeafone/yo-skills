# novel-create

小说项目结构创建，使用此技能，初始化小说项目，创建目录结构和文件初始化

项目结构参考：

```
ai-novel-xxx/
├── AGENTS.md                    # AI Agent 小说编写（流程）操作指南（核心文档）
├── progress.md                  # 写作进度追踪表：完成（大纲）进度、章节进度、人物进度、时间进度等
├── README.md                    # 项目说明
├── count_words.py               # 章节字数统计脚本、小说总字数
├── presets                      # 各种设定
    ├── outline.md               # 完整小说大纲
    ├── characters.md            # 人物设定
    ├── word.md                  # 世界观、技能设定等
    └── ...
└── chapters/                    # 小说正文目录
    ├── 001_[章节名].md
    ├── 002_[章节名].md
    └── ...
```
