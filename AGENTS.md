# AGENTS.md — 个人天赋发掘测评系统

> 本文档供 AI 编程助手阅读。读者被假设为对该项目一无所知。
> 项目自然语言：**中文**（代码注释、文档、UI 文本均使用中文）。

---

## 项目概述

本项目是一个基于 Flask 的 Web 应用，名为**"个人天赋发掘测评系统"**（毕业设计项目）。

核心功能是通过 **AI 驱动的多轮深度访谈**，结合**标准化量表测评**，帮助用户识别底层天赋，并生成一份《个人天赋使用说明书 + 人类3.0发展诊断报告》。

系统包含三大模块：
1. **AI 深度访谈** — 8~20 轮对话，围绕 8 个访谈方向（A-H）展开，最终生成 Markdown 报告
2. **天赋维度筛查量表** — 一级量表（20题，5维度，雷达图可视化）+ 二级量表（10题/维度，锁定具体天赋子类型）
3. **Human 词典** — 项目核心概念速查，首次启动自动导入 SQLite

---

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端框架 | Flask 3.x (Python) |
| ORM | Flask-SQLAlchemy 3.1.x |
| 数据库 | SQLite (`instance/talent_assessment.db`) |
| AI 调用 | OpenAI Python SDK (`openai>=1.12.0`)，兼容 DeepSeek / Moonshot (Kimi) 等 OpenAI 格式 API |
| 配置管理 | 环境变量 + `config.py` 硬编码 fallback（`python-dotenv` 在依赖中列出，但代码中未显式调用 `load_dotenv()`） |
| 前端模板 | Jinja2 |
| 前端样式 | 原生 CSS（暗色主题，金色强调色 `#d4a853`） |
| 前端图表 | ECharts 5.x（CDN 引入） |
| 前端交互 | 原生 JavaScript（无框架），按页面拆分文件 |

Python 版本：项目虚拟环境 `.venv` 基于 **Python 3.14**（从 `__pycache__/*.cpython-314.pyc` 推断）。

---

## 项目结构

```
.
├── app.py                  # 主应用入口：所有 Flask 路由、会话管理、API 端点
├── config.py               # 配置类：AI 提供商切换、测评流程参数、API 密钥
├── models.py               # SQLAlchemy 模型：ScaleResult, UserProfile, HumanDictionary
├── scale_data.py           # 量表题目数据：PRIMARY_SCALE, SECONDARY_SCALE（纯 Python 字典常量）
├── dictionary_data.py      # Human 词典种子数据：DICTIONARY_ENTRIES（纯 Python 列表常量）
├── requirements.txt        # Python 依赖
├── services/
│   ├── __init__.py
│   └── ai_service.py       # AI 服务封装：System Prompt 构建、API 调用、四段式解析、方向检测
├── templates/              # Jinja2 模板
│   ├── base.html           # 基础模板（暗色主题、引入 style.css）
│   ├── index.html          # 首页 / AI 访谈主界面
│   ├── report.html         # 报告展示页
│   ├── scale.html          # 量表测评页
│   ├── scale_result.html   # 量表结果页（引入 ECharts CDN）
│   └── dictionary.html     # Human 词典页
├── static/
│   ├── css/style.css       # 全局样式（暗色主题，约 1500+ 行）
│   └── js/
│       ├── main.js         # AI 访谈页交互逻辑
│       ├── scale.js        # 量表测评页逻辑
│       ├── scale_result.js # 量表结果页逻辑（雷达图渲染）
│       └── dictionary.js   # 词典页逻辑
├── instance/
│   └── talent_assessment.db # SQLite 数据库（运行时自动生成；被 .gitignore 忽略）
└── .venv/                  # Python 虚拟环境（被 .gitignore 忽略，不应提交）
```

**架构特点**：
- 小型单体 Flask 应用，**未使用 Blueprints**，所有路由集中在 `app.py`。
- 数据（量表题目、词典词条）以 Python 模块中的**常量形式硬编码**，而非数据库或外部配置文件。
- AI 服务层 (`services/ai_service.py`) 通过 OpenAI SDK 统一封装，支持切换不同 API 提供商。
- 无用户登录系统，基于 **Flask Session** 实现匿名测评会话。

---

## 运行与启动

### 环境准备

虚拟环境已存在于项目根目录的 `.venv/` 中：

```powershell
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
```

或新建环境：
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 启动开发服务器

```powershell
python app.py
```

默认在 `http://0.0.0.0:5000` 启动，Flask debug 模式已开启。

### 依赖列表

见 `requirements.txt`：
- `flask>=3.0.0`
- `flask-sqlalchemy>=3.1.0`
- `openai>=1.12.0`
- `python-dotenv>=1.0.0`

---

## 配置说明

配置集中在 `config.py` 的 `Config` 类中。

### AI 提供商切换

通过环境变量 `PROVIDER` 切换：
- `deepseek`（默认）：使用 DeepSeek API
- `kimi`：使用 Moonshot (Kimi) API

```powershell
$env:PROVIDER="kimi"
python app.py
```

### 关键配置项

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `SECRET_KEY` | 硬编码 dev key | Flask session 密钥 |
| `MIN_QUESTIONS` | 8 | 最少完成轮数才能生成报告 |
| `SUGGEST_REPORT_AT` | 12 | 建议生成报告的轮数 |
| `MAX_QUESTIONS` | 20 | 强制生成报告的最大轮数 |
| `AI_API_KEY` | 硬编码 fallback | AI 服务 API 密钥 |
| `AI_BASE_URL` | 提供商对应地址 | OpenAI 兼容 API 基础地址 |
| `AI_MODEL` | `deepseek-chat` / `moonshot-v1-128k` | 模型名称 |

> ⚠️ **注意**：当前 `config.py` 中存在硬编码的 API 密钥作为 fallback。修改配置时应注意不要意外将密钥提交到版本控制。

---

## 数据模型

### ScaleResult（量表结果）
- `session_id`: 测评会话标识
- `scale_type`: `'primary'` 或 `'secondary'`
- `answers`, `scores`, `top_dimensions`: JSON 字符串存储
- `talent_type`: 二级量表锁定的天赋类型名称

### UserProfile（用户背景）
- 存储用户人口统计学信息（年龄、性别、城市类型、教育、专业、父母教养方式、是否独生、MBTI）
- **当前代码中尚未在实际流程中使用**，模型已定义但无写入逻辑

### HumanDictionary（Human 词典）
- `term`, `category`, `definition`, `example`, `related_terms`
- 首次启动时 `app.py` 中的 `init_dictionary()` 自动从 `dictionary_data.py` 导入
- 如需更新词条，修改 `dictionary_data.py` 后删除数据库文件或清空表，重启即可重新导入

---

## AI 访谈核心机制

### 8 个访谈方向（A-H）

`AIService` 中定义了 8 个访谈方向，用于引导 AI 覆盖用户生活的不同维度：

- **A**: 童年模式 / 顽固缺点
- **B**: 无意识胜任区
- **C**: 能量审计
- **D**: 嫉妒与压抑
- **E**: 社会可见优势
- **F**: 深层痛苦
- **G**: 伪擅长区
- **H**: 真实兴趣

### 方向覆盖机制（被动跟踪 + Prompt 引导，非强制替换）

当前实现为**后端被动跟踪 + 系统提示词引导**，而非早期版本的硬编码强制替换：

1. **关键词检测**：`detect_direction()` 通过预设的中文关键词库，判断 AI 提出的问题属于哪个方向（A-H）。
2. **状态传递**：后端将已覆盖 / 未覆盖方向列表写入 system prompt，告知 AI。
3. **AI 自主选题**：由 AI 根据提示词自主选择下一个问题方向，后端**不强制替换问题**。
4. **防重复兜底**：`app.py` 的 `chat()` 路由中，如果检测到 AI 提出的问题与历史问题相似（Jaccard 相似度 >= 0.65），会追加一条 system 消息要求 AI 重试一次，用新的问题替换重复问题。

### 四段式输出格式

AI 被强制要求每轮输出分为四个部分：
1. `---关键信号---`
2. `---天赋假设---`
3. `---HUMAN 3.0 判断---`
4. `---下一题---`

`ai_service.py` 中的 `parse_response()` 负责用正则解析这四部分。如果解析失败，全部内容会作为 `question` 返回。

### 报告生成

达到 `MIN_QUESTIONS`（默认 8 轮）后，用户可以点击生成报告。后端会在对话历史后追加一条用户消息触发报告生成，AI 输出一份要求覆盖 14 个章节的 Markdown 报告。

---

## 代码风格与开发约定

### 语言与命名
- 代码注释、文档字符串、用户界面文本**主要使用中文**。
- 变量和函数命名使用英文小写 + 下划线（snake_case）。
- **无 Python 类型注解**（代码中未使用 type hints）。

### 文件组织
- 路由全部写在 `app.py`，按功能区块用注释分隔（如 `# ============================================================ # 量表模块路由`）。
- 数据常量单独放在 `*_data.py` 文件中。
- 服务端逻辑放在 `services/` 包中。

### 前端
- 使用 CSS 变量定义暗色主题色彩系统（`--bg-primary`, `--accent` 等）。
- JavaScript 按页面拆分文件，每个文件管理对应页面的 DOM 状态和 API 调用。
- 模板继承 `base.html`，通过 `{% block %}` 注入页面级 CSS/JS。

### 当前缺失的规范
- **无测试框架**（未配置 pytest/unittest，无测试文件）。
- **无代码格式化 / lint 工具**（未配置 black/ruff/flake8）。
- **无 CI/CD 配置**。
- **无部署配置**（如 Dockerfile、Gunicorn 配置、WSGI 入口等）。
- **无 pyproject.toml / setup.py**。

---

## 已知问题与运行注意事项

### Session Cookie 过大
`app.py` 将完整的 AI 对话历史（`messages` 列表）存储在 Flask Session 中。随着对话轮数增加，session 数据会迅速膨胀。**日志中已出现 Werkzeug 警告**：cookie 值超过 4093 字节限制，浏览器可能静默丢弃。这是当前架构的一个已知瓶颈。

### 开发服务器警告
`app.py` 使用 `app.run(debug=True, host='0.0.0.0')` 启动，这是 Flask 内置开发服务器，**不适合生产环境**。生产部署应使用 Gunicorn、uWSGI 等 WSGI 服务器。

---

## 安全注意事项

1. **硬编码密钥**：`config.py` 包含硬编码的 AI API 密钥 fallback 值。生产环境应严格通过环境变量注入。
2. **Flask Debug 模式**：`app.py` 中 `app.run(debug=True, ...)` 在开发环境开启，生产部署必须关闭。
3. **Session 安全**：`SECRET_KEY` 存在硬编码 fallback，生产环境必须替换为强随机密钥。
4. **输入校验**：当前仅做了最基本的空值检查，未对用户输入做严格的 XSS/SQL 注入防护（SQLAlchemy ORM 提供了一定保护）。
5. **SQLite 文件**：`instance/talent_assessment.db` 包含用户测评数据，注意访问权限和备份。
6. **Session 体积**：对话历史存储在客户端 cookie 中，既存在体积限制，也存在信息泄露风险。如需改进，应考虑将会话数据迁移到服务端存储（如 Redis 或数据库）。

---

## 常见修改场景指引

### 修改 AI 提示词或访谈逻辑
- 编辑 `services/ai_service.py` 中的 `get_system_prompt()` 方法。
- 8 个方向的关键词、描述、参考问题在该类的类属性中定义（`DIRECTION_KEYWORDS`, `DIRECTION_DESCRIPTIONS`, `DIRECTION_QUESTIONS`）。
- 调整报告生成要求也在 `get_system_prompt()` 的 `is_report=True` 分支中。

### 修改量表题目
- 编辑 `scale_data.py` 中的 `PRIMARY_SCALE` 或 `SECONDARY_SCALE` 字典。
- 注意二级量表的 `mapping` 决定分数归属到哪个天赋子类型。

### 修改词典词条
- 编辑 `dictionary_data.py` 中的 `DICTIONARY_ENTRIES` 列表。
- 修改后删除 SQLite 数据库文件或清空 `human_dictionary` 表，重启应用即可重新导入。

### 修改前端样式
- 全局样式在 `static/css/style.css`。
- 页面级交互逻辑在对应的 `static/js/*.js` 中。

### 修改测评流程参数（轮数等）
- 编辑 `config.py` 中的 `MIN_QUESTIONS`, `SUGGEST_REPORT_AT`, `MAX_QUESTIONS`。

---

## 外部依赖与 API

- **DeepSeek API**: `https://api.deepseek.com/v1`
- **Moonshot (Kimi) API**: `https://api.moonshot.cn/v1`
- 两者均通过 OpenAI 兼容接口调用，模型名称和密钥在 `config.py` 中配置。
