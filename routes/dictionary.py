"""
routes/dictionary.py — Human 词典路由模块

本模块实现了 Human 词典的查询和管理功能，为用户提供项目核心概念的速查手册。

功能概览：
1. 词典页面 — 渲染词典浏览页面
2. 词条列表查询 — 支持分类筛选和关键词搜索
3. 单条词条详情 — 查询单个词条的完整信息
4. 首次数据导入 — 系统启动时自动导入词典种子数据

词典内容分类：
┌─────────────────────────────────────────────────────────────┐
│  天赋类型                                                     │
│  - 认知运算型、创造表达型、社交协同型、系统驱动型、身体感知型 │
├─────────────────────────────────────────────────────────────┤
│  HUMAN 3.0                                                   │
│  - 四象限模型、认知象限、身体象限、精神象限、职业象限等       │
├─────────────────────────────────────────────────────────────┤
│  评估术语                                                     │
│  - 无意识胜任区、伪擅长区、血氧区、纯粹兴趣、阴影功能区等     │
├─────────────────────────────────────────────────────────────┤
│  心理学概念                                                   │
│  - 心流、盖洛普优势识别器、苏格拉底式提问等                   │
├─────────────────────────────────────────────────────────────┤
│  天赋应用                                                     │
│  - 天赋映射、价值场景、高光时刻分析等                         │
├─────────────────────────────────────────────────────────────┤
│  成长方法                                                     │
│  - 发展性反馈、最小可行验证、环境重设计等                     │
├─────────────────────────────────────────────────────────────┤
│  AI相关                                                       │
│  - 思维外包、假知道、Glitch、AI增强型天赋、数字断食等         │
└─────────────────────────────────────────────────────────────┘

数据来源：
- 种子数据存储在 dictionary_data.py 中，以 Python 列表常量形式存在
- 首次启动时自动导入到 SQLite 数据库的 human_dictionary 表
- 如需更新词条，修改 dictionary_data.py 后删除数据库或清空表，重启即可

路由清单：
- GET /dictionary              — 词典浏览页面
- GET /api/dictionary          — 词条列表查询（支持筛选和搜索）
- GET /api/dictionary/<id>     — 单条词条详情
"""

import logging
from flask import Blueprint, render_template, request, jsonify
from models import db, HumanDictionary

logger = logging.getLogger(__name__)

# 创建词典模块的 Blueprint
dictionary_bp = Blueprint('dictionary', __name__)


@dictionary_bp.route('/dictionary')
def dictionary():
    """
    Human 词典浏览页面

    路由: GET /dictionary
    需要登录: 否

    说明:
        渲染词典浏览页面模板，页面加载后通过 /api/dictionary 接口
        异步获取词条数据并渲染。

    页面功能：
        - 搜索框：按关键词搜索词条
        - 分类标签：按类别筛选词条
        - 词条列表：展示词条卡片（名称、分类、定义摘要）
        - 详情弹窗：点击查看完整定义、示例和相关术语
    """
    return render_template('dictionary.html')


@dictionary_bp.route('/api/dictionary')
def get_dictionary():
    """
    获取词典词条列表（支持分类筛选和关键词搜索）

    路由: GET /api/dictionary
    需要登录: 否

    查询参数:
        - category (str, 可选): 按分类筛选，如 "天赋类型"、"HUMAN 3.0"
        - keyword (str, 可选): 按关键词搜索，匹配术语名称和定义

    返回数据:
    {
        "success": true,
        "categories": ["天赋类型", "HUMAN 3.0", "评估术语", ...],  // 所有分类
        "entries": [
            {
                "id": 1,
                "term": "认知运算型天赋",
                "category": "天赋类型",
                "definition": "擅长逻辑分析、模式识别...",
                "example": "看到别人觉得混乱的数据...",
                "related_terms": "系统思维,模式识别,元认知"
            },
            ...
        ]
    }

    查询逻辑:
        1. 如果指定了 category，按分类精确筛选
        2. 如果指定了 keyword，在术语名称和定义中模糊搜索
        3. 两个条件可以组合使用
        4. 结果按分类和术语名称排序
    """
    category = request.args.get('category', '')
    keyword = request.args.get('keyword', '')

    # 构建查询
    query = HumanDictionary.query

    # 按分类筛选
    if category:
        query = query.filter_by(category=category)

    # 按关键词搜索（匹配术语名称或定义）
    if keyword:
        query = query.filter(
            db.or_(
                HumanDictionary.term.contains(keyword),
                HumanDictionary.definition.contains(keyword)
            )
        )

    # 执行查询，按分类和术语排序
    entries = query.order_by(HumanDictionary.category, HumanDictionary.term).all()

    # 获取所有分类（用于前端渲染分类标签）
    categories = db.session.query(HumanDictionary.category).distinct().all()
    categories = [c[0] for c in categories]

    return jsonify({
        "success": True,
        "categories": categories,
        "entries": [
            {
                "id": e.id,
                "term": e.term,
                "category": e.category,
                "definition": e.definition,
                "example": e.example,
                "related_terms": e.related_terms
            }
            for e in entries
        ]
    })


@dictionary_bp.route('/api/dictionary/<int:entry_id>')
def get_dictionary_entry(entry_id):
    """
    获取单个词条详情

    路由: GET /api/dictionary/<entry_id>
    需要登录: 否
    参数: entry_id — 词条ID

    返回数据:
    {
        "success": true,
        "entry": {
            "id": 1,
            "term": "心流(Flow)",
            "category": "心理学概念",
            "definition": "心理学家米哈里·契克森米哈伊提出的概念...",
            "example": "写作/编程/竞技时，突然抬头发现3小时过去了...",
            "related_terms": "专注状态,最优体验,内在动机"
        }
    }

    错误情况:
        - 词条不存在时返回 404 错误
    """
    entry = db.session.get(HumanDictionary, entry_id)
    if not entry:
        return jsonify({"success": False, "error": "词条不存在"}), 404
    return jsonify({
        "success": True,
        "entry": {
            "id": entry.id,
            "term": entry.term,
            "category": entry.category,
            "definition": entry.definition,
            "example": entry.example,
            "related_terms": entry.related_terms
        }
    })


def init_dictionary():
    """
    首次启动时导入词典数据

    说明:
        此函数在 app.py 的数据库初始化阶段调用。
        如果 human_dictionary 表为空，则从 dictionary_data.py
        导入所有词条数据。

        导入逻辑：
        1. 检查表中是否已有数据
        2. 如果为空，遍历 DICTIONARY_ENTRIES 列表
        3. 将每条数据创建为 HumanDictionary 对象并添加到数据库
        4. 提交事务并记录日志

        更新词条的方法：
        1. 修改 dictionary_data.py 中的 DICTIONARY_ENTRIES
        2. 删除 instance/talent_assessment.db 文件
        3. 重启应用，系统会自动重新导入
    """
    from dictionary_data import DICTIONARY_ENTRIES

    # 只在表为空时导入（避免重复导入）
    if HumanDictionary.query.first() is None:
        for entry in DICTIONARY_ENTRIES:
            db.session.add(HumanDictionary(**entry))
        db.session.commit()
        logger.info("导入词典数据: %d 条", len(DICTIONARY_ENTRIES))
