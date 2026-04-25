<div align="center">

# ◈ 个人天赋发掘测评系统

**毕业设计项目 · 基于 AI 深度访谈与标准化量表的人才识别系统**

[![Python](https://img.shields.io/badge/Python-3.14-blue?logo=python)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.x-black?logo=flask)](https://flask.palletsprojects.com/)
[![DeepSeek](https://img.shields.io/badge/AI-DeepSeek%20V4-5b8ff9)](https://platform.deepseek.com/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

</div>

> **这不是测试题，也不是快速贴标签。**
> 
> 我们通过 AI 驱动的多轮深度访谈，挖出你真正的底层天赋，同时看清——你现在的生活结构，究竟是在放大它，还是在压住它。

---

## ✨ 功能概览

### 🤖 AI 深度访谈（人类 3.0 诊断）

- **8~20 轮** 渐进式深度对话，模拟人类学家的田野调查方法
- 后端强制控制 **8 个访谈方向**（A-H），确保覆盖全面
- 每轮输出包含：**关键信号提取**、**天赋假设更新**、**HUMAN 3.0 四象限判断**、**下一道深度问题**
- 达到 8 轮后可生成 **14 章节 Markdown 报告**

| 方向 | 主题 | 核心问题 |
|:----:|:-----|:---------|
| A | 童年模式 / 顽固缺点 | 16岁前没人逼你也会沉进去做的事 |
| B | 无意识胜任区 | 别人觉得难但你觉得很自然的事 |
| C | 能量审计 | 做完身体累但精神极度亢奋的事 |
| D | 嫉妒与压抑 | 强烈嫉妒过的人/能力/生活状态 |
| E | 社会可见优势 | 别人通常为什么来找你 |
| F | 深层痛苦 | 最反复痛苦/受伤/执着的主题 |
| G | 伪擅长区 | 做得不错但越做越空的事 |
| H | 真实兴趣 | 没赚到钱但一谈起来眼睛发亮的事 |

### 📊 天赋维度筛查量表

- **一级量表**：20 题标准化测评，5 大维度，**雷达图可视化**
- **二级量表**：针对 Top 维度深入 10 题，锁定具体天赋子类型
- 每种子类型附带**职业路径映射**

### 📖 Human 词典

- 项目核心概念速查手册，涵盖天赋类型、HUMAN 3.0 框架、评估术语
- 支持分类筛选与关键词搜索，点击词条查看详细定义、例子与相关概念

---

## 🛠 技术栈

| 层级 | 技术 |
|:-----|:-----|
| 后端框架 | Flask 3.x + Flask-Login + Flask-SQLAlchemy |
| 数据库 | SQLite |
| AI SDK | OpenAI Python SDK（兼容 DeepSeek / Moonshot）|
| 前端模板 | Jinja2 |
| 前端样式 | 原生 CSS（暗色主题 · 金色强调色 `#d4a853`）|
| 图表 | ECharts 5.x（雷达图）|
| Markdown | marked.js |

---

## 🚀 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/Mistakeman56/talent-excavator.git
cd talent-excavator
```

### 2. 创建虚拟环境

```bash
python3 -m venv .venv
source .venv/bin/activate        # macOS / Linux
# .\.venv\Scripts\Activate.ps1  # Windows
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 配置环境变量

```bash
cp .env.example .env
```

编辑 `.env` 文件，填入你的 API 密钥：

```env
# Flask 安全密钥（生产环境必须替换为强随机字符串）
SECRET_KEY=your-strong-secret-key

# AI 提供商: deepseek | kimi
PROVIDER=deepseek

# DeepSeek API 密钥（默认使用）
DEEPSEEK_API_KEY=sk-your-deepseek-key

# Moonshot (Kimi) API 密钥（可选）
KIMI_API_KEY=sk-your-kimi-key
```

> 🔑 密钥申请地址：
> - [DeepSeek](https://platform.deepseek.com/) · [Moonshot](https://platform.moonshot.cn/)

### 5. 启动服务

```bash
python app.py
```

服务默认在 `http://127.0.0.1:5001` 启动，浏览器访问即可开始使用。

---

## 📁 项目结构

```
.
├── app.py                  # Flask 应用入口：初始化扩展、注册 Blueprint、自动建表
├── config.py               # 配置中心：环境变量读取、AI 提供商切换、测评参数
├── models.py               # SQLAlchemy 数据模型
├── scale_data.py           # 量表题目数据（常量字典）
├── dictionary_data.py      # Human 词典种子数据（常量列表）
├── requirements.txt        # Python 依赖
├── .env.example            # 环境变量模板
├── services/
│   └── ai_service.py       # AI 服务封装：Prompt 构建、API 调用、四段式解析
├── routes/                 # Flask Blueprint 路由
│   ├── auth.py             # 用户认证（注册 / 登录 / 登出）
│   ├── interview.py        # AI 访谈 API（开始 / 聊天 / 报告 / 重置）
│   ├── scale.py            # 量表 API（题目 / 提交 / 二级量表）
│   ├── dictionary.py       # 词典 API（列表 / 筛选 / 详情 / 导入）
│   └── main.py             # 主页、报告展示页
├── templates/              # Jinja2 模板
│   ├── base.html
│   ├── index.html          # AI 访谈主界面
│   ├── scale.html / scale_result.html
│   ├── dictionary.html
│   ├── report.html
│   ├── login.html / register.html
│   └── ...
├── static/
│   ├── css/style.css       # 全局暗色主题样式
│   └── js/                 # 各页面交互逻辑
└── instance/               # SQLite 数据库（运行时生成，已加入 .gitignore）
```

---

## ⚙️ 配置说明

编辑 `.env` 或系统环境变量可调整以下参数：

| 环境变量 | 默认值 | 说明 |
|:---------|:-------|:-----|
| `PROVIDER` | `deepseek` | AI 提供商：`deepseek` 或 `kimi` |
| `MIN_QUESTIONS` | 8 | 最少完成轮数才能生成报告 |
| `SUGGEST_REPORT_AT` | 12 | 建议生成报告的轮数 |
| `MAX_QUESTIONS` | 20 | 强制生成报告的最大轮数 |

AI 模型切换（`config.py`）：

```python
# DeepSeek V4-Flash（默认，性价比高）
AI_MODEL = 'deepseek-v4-flash'

# DeepSeek V4-Pro（推理更深，贵约 12 倍）
# AI_MODEL = 'deepseek-v4-pro'
```

---

## 🧠 核心机制亮点

- **后端方向硬控制**：8 个访谈方向由后端队列管理，AI 偏离时自动检测并修正，确保访谈覆盖完整性
- **四段式输出解析**：AI 每轮回复强制分为「关键信号 / 天赋假设 / HUMAN 3.0 判断 / 下一题」，结构化提取信息
- **用户登录系统**：基于 Flask-Login 的认证体系，AI 访谈与报告生成需登录后使用
- **服务端会话持久化**：AI 访谈数据存储在 SQLite 中（对话历史、阶段、答案、报告），不依赖客户端 Cookie
- **对话式交互界面**：AI 提问在左、用户回答在右，左侧金色小球跳动动画模拟大模型思考过程
- **Sticky 进度条**：滚动对话时轮次徽章与进度条始终吸顶可见

---

## 👤 作者

毕业设计项目

---

*本项目仅用于学术研究目的。*
