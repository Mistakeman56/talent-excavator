<!-- AGENTS.md — 个人天赋发掘测评系统 -->

> 本文档供 AI 编程助手阅读。读者被假设为对该项目一无所知。
> 项目自然语言：**中文**（代码注释、文档字符串、UI 文本均使用中文）。

---

## 项目概述

本项目是一个基于 Flask 的 Web 应用，名为**"个人天赋发掘测评系统"**（毕业设计项目）。

核心功能是通过 **AI 驱动的多轮深度访谈**，结合**标准化量表测评**与**天赋类型学测评（类似 MBTI）**，帮助用户识别底层天赋，并生成一份《个人天赋使用说明书 + 人类3.0发展诊断报告》。

系统包含七大模块：
1. **AI 深度访谈** — 8~20 轮对话，围绕 8 个访谈方向（A-H）展开，最终生成 Markdown 报告
2. **天赋维度筛查量表** — 一级量表（20题，5维度，含反向计分题，雷达图可视化）+ 二级量表（10题/维度，锁定具体天赋子类型）
3. **天赋类型学测评** — 40 道情境迫选题，输出 4 字母类型代码（类似 MBTI），附带详细解读报告，支持平局检测
4. **Human 词典** — 项目核心概念速查，首次启动自动导入 SQLite
5. **历史记录** — 登录用户可查看个人所有测评历史（AI 访谈、量表、天赋类型学）
6. **管理后台** — 管理员可查看统计数据、用户列表、测评记录，并可在后台管理 AI 配置（切换提供商、修改 API 密钥）
7. **个人天赋档案** — 跨测评交叉验证，整合三种测评结果生成个人天赋画像

---

## 技术栈

| 层级 | 技术 | 版本/说明 |
|------|------|----------|
| Python | CPython | 3.14.0 |
| 后端框架 | Flask | `>=3.0.0` |
| ORM | Flask-SQLAlchemy | `>=3.1.0` |
| 认证 | Flask-Login | `>=0.6.3`（已在 `requirements.txt` 中列出）|
| 数据库 | SQLite | `instance/talent_assessment.db` |
| AI SDK | OpenAI Python SDK | `>=1.12.0`（兼容 DeepSeek / Moonshot API）|
| 环境变量 | python-dotenv | `>=1.0.0`（`app.py` 启动时调用 `load_dotenv()`）|
| 生产服务器 | Gunicorn | `>=22.0.0` |
| 前端模板 | Jinja2 | Flask 内置 |
| 前端样式 | 原生 CSS | Apple Design System 风格，CSS 变量系统 |
| 前端图表 | ECharts 5.x | CDN 引入 |
| 前端 Markdown | marked.js | CDN 引入 |
| 前端交互 | 原生 JavaScript | 无框架，按页面拆分文件 |

---

## 项目结构

```
.
├── app.py                  # 主应用入口：创建 Flask 实例、初始化扩展、注册 Blueprint、自动建表
├── config.py               # 配置类：从环境变量读取 AI 密钥、测评流程参数
├── models.py               # SQLAlchemy 模型：User, InterviewSession, ScaleResult, TalentTypeResult, HumanDictionary, VisitLog
├── utils.py                # 统一业务错误码（ERR_NOT_LOGGED_IN 等）与 api_error() 辅助函数
├── scale_data.py           # 量表题目数据：PRIMARY_SCALE, SECONDARY_SCALE（纯 Python 字典常量）
├── talent_type_data.py     # 天赋类型学数据：40 道题、计分逻辑、72 型名称与解读报告（纯 Python 常量）
├── dictionary_data.py      # Human 词典种子数据：DICTIONARY_ENTRIES（纯 Python 列表常量）
├── gunicorn.conf.py        # Gunicorn 生产部署配置（4 worker, 120s 超时）
├── requirements.txt        # Python 依赖（6 项，含 flask-login 和 gunicorn）
├── .env.example            # 环境变量模板
├── deploy/
│   └── talent-app.service  # systemd 服务文件（开机自启、崩溃重启）
├── docs/                   # 项目文档
│   ├── 安装说明.md         # 详细安装部署指南
│   ├── 使用说明.md         # 功能使用手册
│   ├── AGENTS.md           # 本文档
│   ├── 项目学习手册.md     # 项目学习与理解指南
│   ├── 需求规格说明书.md   # 需求分析文档
│   └── 毕业设计报告.md     # 毕业设计论文
├── services/
│   ├── __init__.py         # 空包文件
│   └── ai_service.py       # AI 服务封装：System Prompt 构建、API 调用、四段式解析、方向关键词库
├── routes/                 # Flask Blueprint 路由包
│   ├── __init__.py         # 统一导出所有 Blueprint
│   ├── auth.py             # 认证路由：注册、登录、登出、登录状态检查
│   ├── main.py             # 主页、报告展示页、天赋类型学页面入口（结果页需登录）
│   ├── interview.py        # AI 访谈 API：开始、聊天、生成报告、重置
│   ├── scale.py            # 量表 API：获取题目、提交答案、二级量表、结果查询
│   ├── dictionary.py       # 词典 API：列表查询、分类筛选、单条详情、首次导入
│   ├── talent_type.py      # 天赋类型学 API：获取题目、提交答案、查询结果
│   ├── history.py          # 历史记录 API：汇总三种测评结果、详情查询
│   └── admin.py            # 管理后台 API：统计数据、用户管理、记录管理、AI 配置管理
├── templates/              # Jinja2 模板
│   ├── base.html           # 基础模板
│   ├── _nav.html           # 导航栏片段（各页面 include，含主题切换按钮）
│   ├── _footer.html        # Footer 片段（各页面 include）
│   ├── index.html          # 首页 / AI 访谈主界面（含登录状态展示）
│   ├── login.html          # 登录页
│   ├── register.html       # 注册页
│   ├── report.html         # 报告展示页（使用 marked.js + DOMPurify 渲染 Markdown）
│   ├── scale.html          # 量表测评页
│   ├── scale_result.html   # 量表结果页（引入 ECharts CDN）
│   ├── talent_type.html    # 天赋类型学测评页（含返回首页按钮）
│   ├── talent_type_result.html # 天赋类型学结果页
│   ├── dictionary.html     # Human 词典页
│   ├── history.html        # 历史记录汇总页
│   ├── admin.html          # 管理后台页面（含 AI 配置管理）
│   └── errors/             # 错误页面
│       ├── 404.html        # 404 页面
│       └── 500.html        # 500 页面
├── static/
│   ├── css/style.css       # 全局样式（Apple Design System 风格，CSS 变量系统，支持暗色模式）
│   └── js/
│       ├── utils.js        # 公共工具函数（escapeHtml、apiFetch 统一 API 调用）
│       ├── theme.js        # 深色模式切换逻辑（太阳/月亮图标，localStorage 持久化）
│       ├── main.js         # AI 访谈页交互逻辑
│       ├── scale.js        # 量表测评页逻辑
│       ├── scale_result.js # 量表结果页逻辑（雷达图渲染 + 二级量表内嵌答题）
│       ├── talent_type.js      # 天赋类型学测评页逻辑
│       ├── talent_type_result.js # 天赋类型学结果页逻辑
│       ├── dictionary.js   # 词典页逻辑
│       └── history.js      # 历史记录页逻辑
├── instance/
│   └── talent_assessment.db # SQLite 数据库（运行时自动生成；被 .gitignore 忽略）
└── .venv/                  # Python 虚拟环境（被 .gitignore 忽略，不应提交）
```

**架构特点**：
- 使用 **Flask Blueprint** 拆分路由，8 个 Blueprint 在 `app.py` 中统一注册。
- 数据（量表题目、词典词条、天赋类型学题目）以 Python 模块中的**常量形式硬编码**，而非数据库或外部配置文件。
- AI 服务层 (`services/ai_service.py`) 通过 OpenAI SDK 统一封装，支持切换不同 API 提供商。
- **用户登录系统**基于 Flask-Login，AI 访谈、报告生成、量表测评、天赋类型学测评和历史记录均需要登录后才能使用。
- AI 访谈数据**存储在服务端**：`InterviewSession` 表存储完整对话历史、当前阶段、用户答案和报告内容，不再存放在客户端 Cookie 中。
- `ScaleResult` 与 `TalentTypeResult` 使用 `session_id`（UUID）作为主查询键，同时带有 `user_id` 外键关联用户。
- **访问追踪**使用内存缓冲 + 批量写入（50条/次），通过 `threading.Lock` 保证线程安全。
- **全局错误处理**：404 和 500 错误有专门的错误页面，API 请求返回统一 JSON 格式。
- **统一鉴权**：`utils.py` 定义业务错误码（`ERR_NOT_LOGGED_IN=1001` 等）和 `api_error()` 辅助函数，所有 API 端点返回格式一致的错误响应。

---

## 运行与启动

### 环境准备

虚拟环境已存在于项目根目录的 `.venv/` 中：

```bash
# macOS / Linux
source .venv/bin/activate

# Windows PowerShell
.\.venv\Scripts\Activate.ps1
```

或新建环境：
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 配置环境变量

复制模板文件并填写真实密钥：

```bash
cp .env.example .env
```

`.env` 文件需包含以下变量：

```env
SECRET_KEY=your-strong-secret-key
PROVIDER=deepseek
DEEPSEEK_API_KEY=sk-your-key
KIMI_API_KEY=sk-your-key
```

- `SECRET_KEY`：Flask session 密钥，生产环境必须为强随机字符串
- `PROVIDER`：`deepseek`（默认）或 `kimi`
- `DEEPSEEK_API_KEY` / `KIMI_API_KEY`：对应 AI 提供商的 API 密钥

**当前 `config.py` 不再包含任何硬编码 fallback 密钥**。若环境变量缺失，应用启动时会直接抛出 `ValueError`。

### 启动开发服务器

```bash
python app.py
```

默认在 `http://0.0.0.0:5001` 启动，Flask debug 模式通过 `FLASK_DEBUG` 环境变量控制（默认关闭）。

### 依赖列表

见 `requirements.txt`：
- `flask>=3.0.0`
- `flask-sqlalchemy>=3.1.0`
- `flask-login>=0.6.3`
- `openai>=1.12.0`
- `python-dotenv>=1.0.0`
- `gunicorn>=22.0.0`

---

## 配置说明

配置集中在 `config.py` 的 `Config` 类中，全部从环境变量读取。

### AI 提供商切换

通过环境变量 `PROVIDER` 切换：
- `deepseek`（默认）：使用 DeepSeek API，`AI_MODEL = 'deepseek-v4-flash'`
- `kimi`：使用 Moonshot (Kimi) API，`AI_MODEL = 'moonshot-v1-128k'`

管理员可在管理后台的"AI 配置"页面直接切换提供商和修改 API 密钥，无需手动编辑 `.env` 文件。配置保存后立即更新环境变量，无需重启服务。

### 关键配置项

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `SECRET_KEY` | 从 `SECRET_KEY` 环境变量读取 | Flask session 密钥 |
| `MIN_QUESTIONS` | 8 | 最少完成轮数才能生成报告 |
| `SUGGEST_REPORT_AT` | 12 | 建议生成报告的轮数 |
| `MAX_QUESTIONS` | 20 | 强制生成报告的最大轮数 |
| `REPORT_TITLE` | 个人天赋使用说明书 + 人类3.0发展诊断报告 | 报告标题 |
| `AI_API_KEY` | 根据 PROVIDER 自动选择 | AI 服务 API 密钥 |
| `AI_BASE_URL` | 提供商对应地址 | OpenAI 兼容 API 基础地址 |
| `AI_MODEL` | `deepseek-v4-flash` / `moonshot-v1-128k` | 模型名称 |
| `SQLALCHEMY_DATABASE_URI` | `sqlite:///talent_assessment.db` | 数据库连接字符串 |
| `HOST` | `0.0.0.0` | 服务器监听地址 |
| `PORT` | `5001` | 服务器监听端口 |
| `DEBUG` | `false` | Flask debug 模式 |

---

## 数据模型

### User（用户账户）
- `id`, `username`, `password_hash`, `created_at`
- 使用 `werkzeug.security.generate_password_hash` 存储密码哈希
- `UserMixin` 支持 Flask-Login

### InterviewSession（AI 访谈会话）
- `user_id`（外键关联 `users.id`，带索引，非空）
- `messages`：JSON 字符串，存储完整对话历史
- `stage`：整数 0~7，对应 `INTERVIEW_FLOW` 的方向索引
- `answers`：JSON 字符串，按方向（A-H）汇总用户答案
- `report_content`：最终生成的 Markdown 报告
- `created_at` / `updated_at`
- **关键说明**：每个用户最多只有一条活跃访谈记录；开始新访谈时会删除旧记录

### ScaleResult（量表结果）
- `user_id`（外键关联 `users.id`，带索引）
- `session_id`：测评会话标识（UUID）
- `scale_type`：`'primary'` 或 `'secondary'`
- `answers`, `scores`, `top_dimensions`：JSON 字符串存储
- `talent_type`：二级量表锁定的天赋类型名称

### TalentTypeResult（天赋类型学测评结果）
- `user_id`（外键关联 `users.id`，带索引）
- `session_id`：测评会话标识（UUID），带索引
- `type_code`：4 字母类型代码，如 `"CDAM"`
- `answers`, `scores`, `dimensions`, `report`：JSON 字符串存储
- `created_at`

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

### 方向覆盖机制（后端队列控制 + Prompt 引导）

当前实现由 **后端阶段队列** 控制访谈方向：

1. **阶段索引**：`interview.py` 通过 `INTERVIEW_FLOW[stage]`（`stage` 为 0~7 的整数）确定当前应访谈的方向。
2. **Prompt 注入**：将当前方向的描述和参考问题写入 system prompt，引导 AI 在该方向内提问。
3. **阶段推进**：每完成一轮对话，`stage` 递增（`stage = (stage + 1) % 8`），超过 8 轮后循环遍历所有方向。
4. **防重复兜底**：`interview.py` 中如果检测到 AI 提出的问题与最近 3 轮问题前缀重复，会追加 system 消息要求 AI 重试一次。

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

## 天赋类型学测评机制

- 40 道情境迫选题，分 4 个模组（Module I~IV），每个模组对应不同的计分维度
- Module I（t1-t12）：决定第 1 位字母（C/R/B/S），对应天赋信号（童年模式、无意识胜任区、社会可见优势）
- Module II（t13-t22）：决定第 2 位字母（D/R/V），对应能量与学习方式
- Module III（t23-t30）：决定第 3 位字母（A/H），对应驱动力来源
- Module IV（t31-t40）：决定第 4 位字母（M/C/P），对应兴趣指向
- 最终输出 4 字母类型代码（如 `CDAM`）及详细解读报告
- 计分逻辑和类型解读全部硬编码在 `talent_type_data.py` 中
- 总组合 = 4 × 3 × 2 × 3 = **72 种天赋类型**，每种配有专属中文名称与标语
- 支持平局检测：当某维度出现多个选项得分相同时，返回 `ties` 字段标记歧义维度

---

## 历史记录机制

`routes/history.py` 为登录用户提供统一的测评历史汇总：

- **AI 访谈**：查询 `InterviewSession` 中 `report_content` 不为空的记录
- **量表**：查询 `ScaleResult` 中关联当前用户的记录，区分一级/二级量表
- **天赋类型学**：查询 `TalentTypeResult` 中关联当前用户的记录
- 三种结果按 `created_at` 合并倒序展示
- 提供详情 API：`/api/history/interview/<id>`、`/api/history/scale/<session_id>`

---

## 代码风格与开发约定

### 语言与命名
- 代码注释、文档字符串、用户界面文本**主要使用中文**。
- 变量和函数命名使用英文小写 + 下划线（snake_case）。
- **无 Python 类型注解**（代码中未使用 type hints）。

### 文件组织
- 路由按功能拆分到 `routes/` 包，通过 `__init__.py` 统一导出。
- 数据常量单独放在 `*_data.py` 文件中。
- 服务端逻辑放在 `services/` 包中。
- 前端按页面拆分 JS 文件，每个文件管理对应页面的 DOM 状态和 API 调用。

### 前端
- 使用 CSS 变量定义设计系统色彩（`--primary`, `--canvas`, `--surface-tile-*` 等），采用 Apple Design System 风格。
- 模板继承 `base.html`，通过 `{% block %}` 注入页面级 CSS/JS。
- 暗色主题与亮色主题通过 CSS 变量切换，主色调为蓝色系（`#0066cc` / `#0071e3`）。
- 所有 API 调用使用 `apiFetch()` 统一处理认证错误，自动跳转登录页。

---

## 测试策略

- **无正式测试框架**。项目未配置 pytest、unittest 或其他测试工具。
- 根目录下的 `test_*.py`（`test_simple.py`, `test_chinese.py`, `test_long.py`, `test_quotes.py`）为临时调试脚本，非正式测试，可安全删除。
- 量表和天赋类型学的计分逻辑集中在各自的 `*_data.py` 中，修改后建议手动运行一遍完整答题流程验证结果正确性。

---

## 已知问题与运行注意事项

### 开发服务器警告
`app.py` 使用 `app.run(debug=Config.DEBUG, host=Config.HOST, port=Config.PORT)` 启动，这是 Flask 内置开发服务器，**不适合生产环境**。生产部署应使用 Gunicorn、uWSGI 等 WSGI 服务器。

### SQLAlchemy 2.0 兼容警告
`models.py` 和 `routes/` 中多处使用 `User.query.get(int(user_id))` 和 `Model.query.filter_by(...).first()` 等语法，这是 SQLAlchemy 1.x 的 legacy API，在 2.0 中会触发 `LegacyAPIWarning`。当前代码仍可正常运行，但未来升级 SQLAlchemy 时可能需要改写为 `db.session.get(User, int(user_id))` 等新 API。

### 依赖缺失
- `flask-login` 已安装并已在 `requirements.txt` 中列出。
- `python-dotenv` 已安装并在 `app.py` 开头调用 `load_dotenv()`。

### 数据库迁移
`app.py` 启动时会自动检查 `scale_results` 和 `talent_type_results` 表是否存在 `user_id` 列，若不存在则通过 `ALTER TABLE` 添加。这是一种轻量级兼容性处理，**不是正式的数据库迁移方案**（如 Alembic）。

---

## 生产部署

项目已内置生产部署配置：

- **Gunicorn 配置**：`gunicorn.conf.py`（4 worker, 120s 超时, 2000 请求自动重启）
- **systemd 服务**：`deploy/talent-app.service`（开机自启, 崩溃自动重启）

生产环境启动命令：

```bash
gunicorn -c gunicorn.conf.py app:app
```

建议使用反向代理（Nginx / Lucky）对外暴露服务并配置 SSL 证书。详细部署步骤见 `docs/安装说明.md`。

---

## 安全注意事项

1. **环境变量强制校验**：`config.py` 不再包含硬编码 API 密钥。若 `SECRET_KEY` 或对应提供商的 API 密钥未设置，应用启动即失败并抛出 `ValueError`。这避免了开发时不小心提交密钥，但也意味着**本地必须配置 `.env` 文件才能启动**。
2. **Flask Debug 模式**：通过 `FLASK_DEBUG` 环境变量控制（默认关闭），生产部署必须关闭。
3. **Session 安全**：`SECRET_KEY` 通过环境变量注入，开发时请勿使用弱密钥。
4. **输入校验**：量表提交有服务端校验（题目 ID 和分数范围），其他接口仅做基本空值检查。
5. **XSS 防护**：
   - 所有 JS 文件的 `innerHTML` 插入点均使用 `escapeHtml()` 消毒（通过 `utils.js` 公共函数）
   - `report.html` 和 `history.html` 使用 DOMPurify 对 `marked.parse()` 输出进行消毒
   - 所有事件绑定使用 `addEventListener` + 事件委托，消除了内联 `onclick` 的 XSS 注入面
6. **统一鉴权**：`utils.py` 定义业务错误码（`ERR_NOT_LOGGED_IN=1001` 等），所有 API 返回格式一致。前端通过 `apiFetch()` 统一处理未登录错误并自动跳转。
7. **CSRF 防护缺失**：所有表单和 API 端点均无 CSRF token 保护。
8. **SQLite 文件**：`instance/talent_assessment.db` 包含用户测评数据，注意访问权限和备份。
9. **Rate Limiting 缺失**：登录、注册、AI 聊天等端点均无速率限制。

---

## 常见修改场景指引

### 修改 AI 提示词或访谈逻辑
- 编辑 `services/ai_service.py` 中的 `get_system_prompt()` 方法。
- 8 个方向的关键词、描述、参考问题在该类的类属性中定义（`DIRECTION_KEYWORDS`, `DIRECTION_DESCRIPTIONS`, `DIRECTION_QUESTIONS`）。
- 调整报告生成要求也在 `get_system_prompt()` 的 `is_report=True` 分支中。
- 访谈轮次控制和阶段推进逻辑在 `routes/interview.py` 中。

### 修改量表题目
- 编辑 `scale_data.py` 中的 `PRIMARY_SCALE` 或 `SECONDARY_SCALE` 字典。
- 注意二级量表的 `mapping` 决定分数归属到哪个天赋子类型。

### 修改天赋类型学测评
- 编辑 `talent_type_data.py` 中的题目、选项分值、`DETAILED_REPORTS` 解读报告。
- 计分核心在 `calculate_type_code()` 函数中。

### 修改词典词条
- 编辑 `dictionary_data.py` 中的 `DICTIONARY_ENTRIES` 列表。
- 修改后删除 SQLite 数据库文件或清空 `human_dictionary` 表，重启应用即可重新导入。

### 修改前端样式
- 全局样式在 `static/css/style.css`。
- 页面级交互逻辑在对应的 `static/js/*.js` 中。

### 修改测评流程参数（轮数等）
- 编辑 `config.py` 中的 `MIN_QUESTIONS`, `SUGGEST_REPORT_AT`, `MAX_QUESTIONS`。

### 修改认证逻辑
- 编辑 `routes/auth.py`。
- 登录状态检查端点为 `/api/auth/check`，返回 `{authenticated, username}`。

### 修改历史记录逻辑
- 编辑 `routes/history.py`。
- 前端展示逻辑在 `static/js/history.js` 和 `templates/history.html` 中。

---

## Git 分支策略

本项目采用**标准三件套分支模型**（Git Flow 轻量版）：

### 分支说明

| 分支 | 用途 | 规则 |
|:-----|:-----|:-----|
| `main` | 生产分支，稳定版本 | **保护分支**，只能通过 PR/Merge 从 `develop` 合并进入，禁止直接推送 |
| `develop` | 开发主分支，日常集成 | 所有开发完成的功能先合并到这里，测试稳定后再进 `main` |
| `feat/<功能名>` | 功能开发分支 | 从 `develop` 切出，开发完成后合并回 `develop`，然后删除 |
| `fix/<bug名>` | Bug 修复分支 | 从 `develop` 切出（紧急 Bug 可从 `main` 切），修复后合并回来源分支 |
| `docs/<内容>` | 文档更新分支 | 从 `develop` 切出，完成后合并回 `develop` |
| `chore/<内容>` | 配置/依赖/杂项 | 从 `develop` 切出，完成后合并回 `develop` |

### 日常开发流程

```bash
# 1. 确保在 develop 上且是最新的
git checkout develop
git pull origin develop

# 2. 创建功能分支
git checkout -b feat/xxx

# 3. 开发、提交、推送
git add .
git commit -m "feat: xxx"
git push -u origin feat/xxx

# 4. 完成后合并回 develop
git checkout develop
git merge feat/xxx
git push origin develop

# 5. 删除本地和远程的功能分支
git branch -d feat/xxx
git push origin --delete feat/xxx

# 6. develop 稳定后，合并到 main 发布
git checkout main
git merge develop
git push origin main
```

### 命名规范

- 功能分支：`feat/ai-interview-loading`、`feat/talent-type-72-names`
- 修复分支：`fix/report-truncation`、`fix/naN-progress-bar`
- 文档分支：`docs/readme-update`、`docs/agents-md`
- 杂项分支：`chore/update-deps`、`chore/clean-test-files`

> **当前默认工作分支为 `develop`**。每次接到新任务，先从 `develop` 切出对应的功能分支，不要直接在 `main` 或 `develop` 上修改代码。

---

## 外部依赖与 API

- **DeepSeek API**: `https://api.deepseek.com/v1`
- **Moonshot (Kimi) API**: `https://api.moonshot.cn/v1`
- 两者均通过 OpenAI 兼容接口调用，模型名称和密钥在 `config.py` 中根据 `PROVIDER` 环境变量自动选择。
