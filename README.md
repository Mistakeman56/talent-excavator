# 个人天赋发掘测评系统

> 毕业设计项目 · 基于 AI 深度访谈与标准化量表的人才识别系统

---

## 项目简介

**个人天赋发掘测评系统**是一个基于 Flask 的 Web 应用，通过 **AI 驱动的多轮深度访谈** 结合 **标准化天赋量表**，帮助用户识别自身底层天赋，并生成一份个性化的《个人天赋使用说明书 + 人类 3.0 发展诊断报告》。

系统核心理念：**这不是测试题，也不是快速贴标签。** 我们通过逐轮深度问题，挖出你真正的底层天赋，同时看清——你现在的生活结构，究竟是在放大它，还是在压住它。

---

## 核心功能

### 1. AI 深度访谈（人类 3.0 诊断）

- **8~20 轮** 渐进式深度对话，模拟人类学家的田野调查方法
- 后端强制控制 **8 个访谈方向**（A-H），确保覆盖全面：
  - **A** 童年模式 / 顽固缺点　　**B** 无意识胜任区　　**C** 能量审计　　**D** 嫉妒与压抑
  - **E** 社会可见优势　　　　　**F** 深层痛苦　　　　**G** 伪擅长区　　**H** 真实兴趣
- 每轮输出包含：**关键信号提取**、**天赋假设更新**、**HUMAN 3.0 四象限判断**、**下一道深度问题**
- 达到 8 轮后可生成 **14 章节 Markdown 报告**，包含天赋画像、四象限诊断、发展建议

### 2. 天赋维度筛查量表

- **一级量表**：20 题标准化测评，5 大维度（认知 / 创造 / 社交 / 系统 / 身体），雷达图可视化
- **二级量表**：针对 Top 维度深入 10 题，锁定具体天赋子类型（如"系统架构师型""模式捕手型"等）
- 每种子类型附带**职业路径映射**，连接天赋与现实选择

### 3. Human 词典

- 项目核心概念速查手册，涵盖 **天赋类型**、**HUMAN 3.0 框架**、**评估术语**、**心理学概念**、**AI 时代风险**
- 支持分类筛选与关键词搜索，点击词条查看详细定义、例子与相关概念

---

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端框架 | Flask 3.x (Python) |
| ORM | Flask-SQLAlchemy 3.1.x |
| 数据库 | SQLite |
| AI 调用 | OpenAI Python SDK（兼容 DeepSeek / Moonshot 等 OpenAI 格式 API） |
| 前端模板 | Jinja2 |
| 前端样式 | 原生 CSS（暗色主题，金色强调色） |
| 前端交互 | 原生 JavaScript + ECharts（雷达图） |

---

## 快速开始

### 环境准备

```powershell
# 进入项目目录
cd "d:\graduation project"

# 激活虚拟环境（Windows）
.\.venv\Scripts\Activate.ps1

# 若虚拟环境不存在，可新建
# python -m venv .venv
# .\.venv\Scripts\Activate.ps1
# pip install -r requirements.txt
```

### 启动服务

```powershell
python app.py
```

服务默认在 `http://127.0.0.1:5000` 启动，Flask debug 模式已开启。

浏览器访问 `http://127.0.0.1:5000` 即可开始使用。

---

## 项目结构

```
.
├── app.py                  # 主应用入口：创建 Flask 实例、初始化扩展、注册 Blueprint、自动建表
├── config.py               # 配置类：AI 提供商切换、测评流程参数、API 密钥
├── models.py               # SQLAlchemy 模型：User, InterviewSession, ScaleResult, UserProfile, HumanDictionary
├── scale_data.py           # 量表题目数据：PRIMARY_SCALE, SECONDARY_SCALE（常量字典）
├── dictionary_data.py      # Human 词典种子数据：DICTIONARY_ENTRIES（常量列表）
├── requirements.txt        # Python 依赖
├── test_simple.py          # 临时调试脚本
├── test_chinese.py         # 临时调试脚本
├── test_long.py            # 临时调试脚本
├── test_quotes.py          # 临时调试脚本
├── services/               # 服务端逻辑包
│   ├── __init__.py
│   └── ai_service.py       # AI 服务封装：System Prompt 构建、API 调用、四段式解析
├── routes/                 # Flask Blueprint 路由包
│   ├── __init__.py         # 统一导出所有 Blueprint
│   ├── auth.py             # 认证路由：注册、登录、登出、登录状态检查
│   ├── main.py             # 主页、报告展示页
│   ├── interview.py        # AI 访谈 API：开始、聊天、生成报告、重置
│   ├── scale.py            # 量表 API：获取题目、提交答案、二级量表
│   └── dictionary.py       # 词典 API：列表查询、分类筛选、单条详情、首次导入
├── templates/              # Jinja2 模板
│   ├── base.html           # 基础模板（暗色主题、CDN 资源引入）
│   ├── index.html          # 首页 / AI 访谈主界面（含登录状态展示）
│   ├── login.html          # 登录页
│   ├── register.html       # 注册页
│   ├── report.html         # 报告展示页（marked.js 渲染 Markdown）
│   ├── scale.html          # 量表测评页
│   ├── scale_result.html   # 量表结果页（ECharts 雷达图）
│   └── dictionary.html     # Human 词典页
├── static/
│   ├── css/
│   │   └── style.css       # 全局暗色主题样式（CSS 变量 + 金色强调色）
│   └── js/
│       ├── main.js         # AI 访谈页交互逻辑
│       ├── scale.js        # 量表测评页逻辑
│       ├── scale_result.js # 量表结果页逻辑（雷达图渲染 + 二级量表内嵌答题）
│       └── dictionary.js   # 词典页交互逻辑
└── instance/
    └── talent_assessment.db # SQLite 数据库（运行时自动生成；被 .gitignore 忽略）
```

---

## 配置说明

编辑 `config.py` 可调整以下关键参数：

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `MIN_QUESTIONS` | 8 | 最少完成轮数才能生成报告 |
| `SUGGEST_REPORT_AT` | 12 | 建议生成报告的轮数 |
| `MAX_QUESTIONS` | 20 | 强制生成报告的最大轮数 |
| `PROVIDER` | `deepseek` | AI 提供商：`deepseek` 或 `kimi` |

AI 提供商切换：

```powershell
# 使用 DeepSeek（默认）
python app.py

# 使用 Moonshot (Kimi)
$env:PROVIDER="kimi"
python app.py
```

> ⚠️ 生产环境请通过环境变量注入 API 密钥，不要依赖代码中的硬编码 fallback。

---

## 使用流程

1. **进入首页** → 选择"开始 AI 深度访谈"或"天赋维度筛查量表"
2. **AI 访谈模式**：逐轮回答问题，每轮 AI 会提取关键信号并更新天赋假设
3. **量表模式**：20 题快速筛查 → 查看雷达图与 Top 维度 → 可选深入二级量表
4. **生成报告**：访谈达到 8 轮后，点击"生成天赋报告"获取完整诊断
5. **随时查词**：点击导航进入 Human 词典，查阅项目中的核心概念

---

## 核心机制亮点

- **后端方向硬控制**：8 个访谈方向由后端队列管理，即使 AI 偏离也会被检测并修正，确保访谈覆盖完整性
- **四段式输出解析**：AI 每轮回复强制分为「关键信号 / 天赋假设 / HUMAN 3.0 判断 / 下一题」，结构化提取信息
- **用户登录系统**：基于 Flask-Login 的认证体系，AI 访谈与报告生成需登录后使用；量表与词典无需登录
- **服务端会话持久化**：AI 访谈数据存储在 `InterviewSession` 表中（对话历史、阶段、答案、报告），不再依赖客户端 Cookie
- **数据热加载**：量表题目、词典词条以 Python 常量形式维护，修改后重启即可生效

---

## 作者

毕业设计项目

---

*本项目仅用于学术研究目的。*
