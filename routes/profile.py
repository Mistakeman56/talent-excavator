"""
routes/profile.py — 个人天赋档案路由模块

本模块实现了个人天赋档案功能，整合三种测评结果，生成统一的个人天赋画像。

功能概览：
1. 档案页面 — 展示个人天赋档案的完整视图
2. 档案汇总 API — 汇总三种测评结果，进行跨测评交叉分析

核心价值：
┌─────────────────────────────────────────────────────────────┐
│  跨测评交叉验证                                               │
│                                                              │
│  AI访谈          量表测评          类型学测评                 │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐               │
│  │ 天赋假设 │    │ 五维度分 │    │ 4字母代码│               │
│  └────┬─────┘    └────┬─────┘    └────┬─────┘               │
│       │               │               │                      │
│       └───────────────┼───────────────┘                      │
│                       ↓                                      │
│              ┌─────────────────┐                             │
│              │   交叉分析      │                             │
│              │ - 互相验证的天赋│                             │
│              │ - 有分歧的维度  │                             │
│              └─────────────────┘                             │
│                       ↓                                      │
│              ┌─────────────────┐                             │
│              │  个人天赋档案   │                             │
│              │  - 天赋名片     │                             │
│              │  - 三栏展示     │                             │
│              │  - 交叉验证结果 │                             │
│              └─────────────────┘                             │
└─────────────────────────────────────────────────────────────┘

路由清单：
- GET /profile           — 个人天赋档案页面（需要登录）
- GET /api/profile/summary — 档案汇总API（需要登录）
"""

import json
import re
from flask import Blueprint, render_template, jsonify
from flask_login import login_required, current_user
from models import db, InterviewSession, ScaleResult, TalentTypeResult

# 创建个人档案模块的 Blueprint
profile_bp = Blueprint('profile', __name__)


def safe_json_loads(text, default=None):
    """
    安全的 JSON 反序列化函数

    参数:
        text: 要解析的JSON字符串
        default: 解析失败时返回的默认值
    返回:
        解析后的Python对象，或默认值

    说明:
        数据库中存储的JSON字符串可能格式不正确
        使用此函数可以避免因JSON解析错误导致整个请求失败
    """
    if default is None:
        default = {}
    try:
        return json.loads(text) if text else default
    except (json.JSONDecodeError, TypeError):
        return default


def extract_talent_keywords(report_content):
    """
    从AI访谈报告中提取天赋关键词

    参数:
        report_content: AI生成的Markdown格式报告
    返回:
        提取的关键词列表（最多10个）

    说明:
        使用正则表达式从报告中提取与天赋相关的关键词。
        匹配模式包括：
        - "底层天赋是..."
        - "核心天赋是..."
        - "天赋包括..."
        - "你的天赋是..."

        提取后去重并限制数量，用于展示和交叉验证。
    """
    if not report_content:
        return []

    keywords = []
    patterns = [
        r'底层天赋[是为：:]\s*(.+?)(?:\n|$)',
        r'核心天赋[是为：:]\s*(.+?)(?:\n|$)',
        r'天赋[包括有：:]\s*(.+?)(?:\n|$)',
        r'你的天赋[是为：:]\s*(.+?)(?:\n|$)',
    ]

    for pattern in patterns:
        matches = re.findall(pattern, report_content)
        for m in matches:
            # 按逗号、顿号分割
            parts = re.split(r'[、，,；;]', m)
            for p in parts:
                p = p.strip().strip('*').strip('。').strip()
                if 2 <= len(p) <= 20:
                    keywords.append(p)

    # 去重并限制数量
    return list(dict.fromkeys(keywords))[:10]


def cross_validate(interview_keywords, scale_dims, type_dims):
    """
    跨测评交叉分析

    参数:
        interview_keywords: AI访谈提取的天赋关键词
        scale_dims: 量表的Top维度列表
        type_dims: 类型学的维度信息
    返回:
        交叉验证结果：{confirmed: [...], conflicts: [...]}

    说明:
        将三种测评的结果进行交叉比对，找出：
        1. 互相验证的天赋 — 多种测评都指向同一方向
        2. 有分歧的维度 — 不同测评指向不同方向

        交叉验证可以帮助用户：
        - 确认天赋判断的可靠性
        - 发现需要进一步探索的领域
    """
    confirmed = []
    conflicts = []

    # 维度关键词映射
    dim_mapping = {
        '认知洞察型': ['认知运算', '逻辑分析', '模式识别', '系统思维', '抽象思考'],
        '创造表达型': ['创造', '表达', '创新', '原创', '想象力', '叙事'],
        '社交协同型': ['社交', '协同', '共情', '沟通', '关系', '连接', '同理'],
        '系统推动型': ['系统', '推动', '执行', '组织', '规划', '领导'],
        '身体感知型': ['身体', '感知', '直觉', '动手', '感官', '运动'],
    }

    # 获取量表Top维度
    scale_top = scale_dims[0]['name'] if scale_dims else ''

    # 获取类型学维度
    type_code = type_dims.get('code', '') if type_dims else ''
    type_to_dim = {
        'C': '认知洞察型',
        'R': '社交协同型',
        'B': '身体感知型',
        'S': '系统推动型',
    }
    type_dim_name = type_to_dim.get(type_code[0], '') if type_code else ''

    # 量表与类型学交叉验证
    if scale_top and type_dim_name:
        if scale_top == type_dim_name:
            confirmed.append(f'量表（{scale_top}）与类型学（{type_dim_name}）互相验证')
        else:
            conflicts.append(f'量表指向「{scale_top}」，类型学指向「{type_dim_name}」')

    # 访谈关键词与其他测评交叉验证
    for kw in interview_keywords:
        for dim_name, dim_keywords in dim_mapping.items():
            for dk in dim_keywords:
                if dk in kw:
                    if scale_top == dim_name or type_dim_name == dim_name:
                        confirmed.append(f'访谈关键词「{kw}」与{dim_name}维度吻合')
                    break

    return {
        'confirmed': list(dict.fromkeys(confirmed))[:5],
        'conflicts': list(dict.fromkeys(conflicts))[:3]
    }


@profile_bp.route('/profile')
@login_required
def profile_page():
    """
    个人天赋档案页面

    路由: GET /profile
    需要登录: 是

    说明:
        渲染个人天赋档案页面，展示用户的完整天赋画像。
        页面加载后通过 /api/profile/summary 接口异步获取数据。

    页面布局：
        1. 天赋名片：类型代码、核心天赋、量表Top维度
        2. 三栏展示：AI访谈摘要 | 量表雷达图 | 类型学维度
        3. 交叉验证：互相验证的天赋和有分歧的维度
    """
    return render_template('profile.html')


@profile_bp.route('/api/profile/summary')
@login_required
def get_profile_summary():
    """
    获取个人天赋档案汇总数据

    路由: GET /api/profile/summary
    需要登录: 是

    说明:
        汇总当前用户的所有测评结果，并进行跨测评交叉分析。

    返回数据:
    {
        "success": true,
        "has_data": true,
        "interview": {
            "has": true,
            "keywords": ["系统思维", "逻辑分析", ...],
            "report_preview": "报告前500字...",
            "created_at": "2024-01-01T00:00:00"
        },
        "scale": {
            "primary": {
                "scores": {...},
                "top_dimensions": [...],
                "created_at": "..."
            },
            "secondary": {
                "talent_type": "系统架构师",
                "scores": {...},
                "created_at": "..."
            }
        },
        "talent_type": {
            "has": true,
            "type_code": "CDAM",
            "name": "认知架构师",
            "tagline": "用系统思维重构世界的人",
            "dimensions": {...},
            "scores": {...},
            "created_at": "..."
        },
        "cross_validation": {
            "confirmed": ["量表与类型学互相验证", ...],
            "conflicts": []
        }
    }
    """
    user_id = current_user.id

    # ----------------------------------------------------------
    # 查询AI访谈结果
    # ----------------------------------------------------------
    interview = InterviewSession.query.filter(
        InterviewSession.user_id == user_id,
        InterviewSession.report_content.isnot(None)
    ).order_by(InterviewSession.created_at.desc()).first()

    interview_data = None
    interview_keywords = []
    if interview:
        interview_keywords = extract_talent_keywords(interview.report_content)
        interview_data = {
            'has': True,
            'keywords': interview_keywords,
            'report_preview': interview.report_content[:500] + '...' if len(interview.report_content) > 500 else interview.report_content,
            'created_at': interview.created_at.isoformat() if interview.created_at else None
        }
    else:
        interview_data = {'has': False}

    # ----------------------------------------------------------
    # 查询量表结果
    # ----------------------------------------------------------
    primary_scale = ScaleResult.query.filter_by(
        user_id=user_id, scale_type='primary'
    ).order_by(ScaleResult.created_at.desc()).first()

    secondary_scale = ScaleResult.query.filter_by(
        user_id=user_id, scale_type='secondary'
    ).order_by(ScaleResult.created_at.desc()).first()

    scale_data = {'primary': None, 'secondary': None}
    scale_top_dims = []

    if primary_scale:
        scores = safe_json_loads(primary_scale.scores)
        top_dims = safe_json_loads(primary_scale.top_dimensions, [])
        scale_top_dims = top_dims
        scale_data['primary'] = {
            'scores': scores,
            'top_dimensions': top_dims,
            'created_at': primary_scale.created_at.isoformat() if primary_scale.created_at else None
        }

    if secondary_scale:
        scale_data['secondary'] = {
            'talent_type': secondary_scale.talent_type,
            'scores': safe_json_loads(secondary_scale.scores),
            'created_at': secondary_scale.created_at.isoformat() if secondary_scale.created_at else None
        }

    # ----------------------------------------------------------
    # 查询天赋类型学结果
    # ----------------------------------------------------------
    talent_type = TalentTypeResult.query.filter_by(
        user_id=user_id
    ).order_by(TalentTypeResult.created_at.desc()).first()

    tt_data = None
    tt_dims = {}
    if talent_type:
        report = safe_json_loads(talent_type.report)
        tt_dims = {
            'code': talent_type.type_code,
            'name': report.get('name', ''),
            'tagline': report.get('tagline', ''),
            'dimensions': safe_json_loads(talent_type.dimensions),
            'scores': safe_json_loads(talent_type.scores)
        }
        tt_data = {
            'has': True,
            'type_code': talent_type.type_code,
            'name': report.get('name', ''),
            'tagline': report.get('tagline', ''),
            'dimensions': safe_json_loads(talent_type.dimensions),
            'scores': safe_json_loads(talent_type.scores),
            'created_at': talent_type.created_at.isoformat() if talent_type.created_at else None
        }
    else:
        tt_data = {'has': False}

    # ----------------------------------------------------------
    # 跨测评交叉分析
    # ----------------------------------------------------------
    validation = cross_validate(interview_keywords, scale_top_dims, tt_dims)

    # 判断是否有任何测评数据
    has_any = interview_data['has'] or scale_data['primary'] or tt_data['has']

    return jsonify({
        'success': True,
        'has_data': has_any,
        'interview': interview_data,
        'scale': scale_data,
        'talent_type': tt_data,
        'cross_validation': validation
    })
