"""
routes/scale.py — 天赋维度量表路由模块

本模块实现了天赋维度筛查量表的完整功能，包括：
1. 量表页面入口 — 渲染量表测评页面
2. 获取一级量表题目 — 返回20道标准化测评题
3. 提交一级量表答案 — 计算五维度得分，找出Top维度
4. 获取二级量表题目 — 基于一级量表Top维度，返回针对性的10道题
5. 提交二级量表答案 — 精准锁定天赋子类型
6. 查询量表结果 — 根据session_id查询历史结果

量表体系设计：
┌─────────────────────────────────────────────────────────────┐
│  一级量表（20题，5维度）                                      │
│  ┌─────────────┬─────────────┬─────────────┬─────────────┐  │
│  │ 认知洞察型 │ 创造表达型 │ 社交协同型 │ 系统推动型 │  │
│  │ 4题         │ 4题         │ 4题         │ 4题         │  │
│  └─────────────┴─────────────┴─────────────┴─────────────┘  │
│  │ 身体感知型 │                                             │
│  │ 4题（含反向计分题）                                      │
│  └─────────────┘                                             │
│       ↓ Top维度                                              │
│  二级量表（10题/维度）                                        │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ 针对Top维度的3个子类型，精准定位天赋subtype            │  │
│  │ 例如：认知洞察型 → 系统架构师/模式侦探/本质追问者      │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘

计分规则：
- 正向题：直接计分（1-5分）
- 反向题：反向计分（6-原始分）
- 维度得分 = 该维度所有题目的平均分
- Top维度 = 得分最高的前3个维度
"""

from flask import Blueprint, render_template, request, jsonify
from flask_login import current_user
from models import db, ScaleResult
import uuid
import json

scale_bp = Blueprint('scale', __name__)


@scale_bp.route('/scale')
def scale_page():
    """
    量表测评页面

    路由: GET /scale
    需要登录: 否（但提交答案需要登录）

    说明:
        渲染量表测评页面模板
        页面加载后会通过 API 获取题目并展示给用户
    """
    return render_template('scale.html')


@scale_bp.route('/scale/result')
def scale_result_page():
    """
    量表结果页面

    路由: GET /scale/result?session_id=xxx
    需要登录: 否

    说明:
        渲染量表结果页面模板
        页面加载后会通过 API 获取测评结果并展示雷达图和详情
    """
    return render_template('scale_result.html')


@scale_bp.route('/api/scale/questions')
def get_scale_questions():
    """
    获取一级量表题目

    路由: GET /api/scale/questions
    需要登录: 否

    返回数据:
    {
        "success": true,
        "data": {
            "scoring": {
                "options": [
                    {"value": 1, "label": "完全不符合"},
                    {"value": 2, "label": "比较不符合"},
                    {"value": 3, "label": "一般"},
                    {"value": 4, "label": "比较符合"},
                    {"value": 5, "label": "完全符合"}
                ]
            },
            "dimensions": {
                "cognitive": {
                    "name": "认知洞察型",
                    "description": "...",
                    "questions": [
                        {"id": "q1", "text": "题目内容", "reverse": false},
                        {"id": "q2", "text": "反向题内容", "reverse": true},
                        ...
                    ]
                },
                "creative": { ... },
                "social": { ... },
                "system": { ... },
                "body": { ... }
            }
        }
    }

    说明:
        题目数据来自 scale_data.py 中的 PRIMARY_SCALE 常量
        reverse=true 表示反向计分题（得分 = 6 - 原始分）
    """
    from scale_data import PRIMARY_SCALE
    return jsonify({
        "success": True,
        "data": PRIMARY_SCALE
    })


@scale_bp.route('/api/scale/submit', methods=['POST'])
def submit_scale():
    """
    提交一级量表答案，计算得分

    路由: POST /api/scale/submit
    需要登录: 是
    请求体: {"answers": {"q1": 4, "q2": 5, "q3": 3, ...}}

    处理流程:
    1. 校验答案数据（题目ID是否有效、分数是否在1-5范围内）
    2. 按维度分组计算得分（反向题使用 6-原始分）
    3. 计算每个维度的平均分
    4. 排序找出Top维度（得分最高的前3个）
    5. 保存结果到数据库
    6. 返回session_id供前端跳转到结果页

    计分公式:
    - 正向题：score = 原始分
    - 反向题：score = 6 - 原始分
    - 维度得分 = 该维度所有题目的平均分（保留1位小数）

    返回数据:
    {
        "success": true,
        "session_id": "uuid-string",
        "scores": {
            "cognitive": {
                "name": "认知洞察型",
                "description": "...",
                "score": 4.2,
                "max_score": 5,
                "raw_total": 17
            },
            ...
        },
        "top_dimensions": [
            {"key": "cognitive", "name": "认知洞察型", "score": 4.2},
            {"key": "creative", "name": "创造表达型", "score": 3.8},
            {"key": "social", "name": "社交协同型", "score": 3.5}
        ]
    }
    """
    # 检查登录状态
    if not current_user.is_authenticated:
        return jsonify({"success": False, "error": "未登录", "need_login": True})

    from scale_data import PRIMARY_SCALE

    # 获取用户提交的答案
    data = request.get_json()
    answers = data.get('answers', {})

    if not answers:
        return jsonify({"success": False, "error": "没有提交答案"})

    # ----------------------------------------------------------
    # 校验答案数据
    # ----------------------------------------------------------
    # 收集所有有效的题目ID
    valid_question_ids = set()
    for dim_data in PRIMARY_SCALE['dimensions'].values():
        for q in dim_data['questions']:
            valid_question_ids.add(q['id'])

    # 逐个校验
    for qid, score in answers.items():
        if qid not in valid_question_ids:
            return jsonify({"success": False, "error": f"无效的题目ID: {qid}"}), 400
        if not isinstance(score, (int, float)) or score < 1 or score > 5:
            return jsonify({"success": False, "error": f"无效的分数值: {qid}={score}，应为1-5"}), 400

    # ----------------------------------------------------------
    # 计算各维度得分
    # ----------------------------------------------------------
    scores = {}
    for dim_key, dim_data in PRIMARY_SCALE['dimensions'].items():
        total = 0
        count = 0
        for q in dim_data['questions']:
            qid = q['id']
            if qid in answers:
                score = answers[qid]
                # 反向计分题：得分 = 6 - 原始分
                if q.get('reverse'):
                    score = 6 - score
                total += score
                count += 1
        scores[dim_key] = {
            "name": dim_data['name'],
            "description": dim_data['description'],
            "score": round(total / count, 1) if count > 0 else 0,  # 平均分，保留1位小数
            "max_score": 5,
            "raw_total": total
        }

    # ----------------------------------------------------------
    # 排序找出Top维度（得分最高的前3个）
    # ----------------------------------------------------------
    sorted_dims = sorted(scores.items(), key=lambda x: x[1]['score'], reverse=True)
    top_dimensions = [
        {"key": k, "name": v["name"], "score": v["score"]}
        for k, v in sorted_dims[:3]
    ]

    # ----------------------------------------------------------
    # 保存到数据库
    # ----------------------------------------------------------
    session_id = str(uuid.uuid4())
    result = ScaleResult(
        user_id=current_user.id,
        session_id=session_id,
        scale_type='primary',
        answers=json.dumps(answers),
        scores=json.dumps(scores),
        top_dimensions=json.dumps(top_dimensions)
    )
    db.session.add(result)
    db.session.commit()

    return jsonify({
        "success": True,
        "session_id": session_id,
        "scores": scores,
        "top_dimensions": top_dimensions
    })


@scale_bp.route('/api/scale/secondary/questions', methods=['POST'])
def get_secondary_questions():
    """
    获取二级量表题目（基于一级量表Top维度）

    路由: POST /api/scale/secondary/questions
    需要登录: 否
    请求体: {"dimension": "cognitive"}

    说明:
        根据一级量表的Top维度，返回该维度的二级量表题目
        二级量表有10道题，用于在3个子类型中精准定位天赋

    返回数据:
    {
        "success": true,
        "dimension_name": "认知洞察型",
        "types": {
            "architect": {
                "name": "系统架构师",
                "description": "擅长构建复杂系统..."
            },
            "detective": {
                "name": "模式侦探",
                "description": "擅长发现隐藏规律..."
            },
            "seeker": {
                "name": "本质追问者",
                "description": "擅长追问事物本质..."
            }
        },
        "questions": [
            {
                "id": "sq1",
                "text": "题目内容",
                "mapping": {
                    "architect": 2,
                    "detective": 1,
                    "seeker": 0
                }
            },
            ...
        ]
    }

    mapping 说明:
        每个选项对应不同子类型的权重分
        用户选择后，各子类型累加对应的权重分
        最终得分最高的子类型即为用户的天赋类型
    """
    from scale_data import SECONDARY_SCALE

    data = request.get_json()
    dimension = data.get('dimension')

    if not dimension or dimension not in SECONDARY_SCALE:
        return jsonify({"success": False, "error": "无效维度"})

    scale_data = SECONDARY_SCALE[dimension]
    return jsonify({
        "success": True,
        "dimension_name": scale_data['name'],
        "types": {k: v for k, v in scale_data['types'].items()},
        "questions": scale_data['questions']
    })


@scale_bp.route('/api/scale/result/<session_id>')
def get_scale_result(session_id):
    """
    获取量表结果

    路由: GET /api/scale/result/<session_id>
    需要登录: 否

    说明:
        根据session_id查询量表结果
        用于结果页面加载时获取数据

    返回数据:
    {
        "success": true,
        "session_id": "uuid-string",
        "scale_type": "primary",
        "scores": {...},
        "top_dimensions": [...],
        "talent_type": null  // 一级量表没有talent_type
    }
    """
    result = ScaleResult.query.filter_by(session_id=session_id).first()
    if not result:
        return jsonify({"success": False, "error": "结果不存在"}), 404

    return jsonify({
        "success": True,
        "session_id": result.session_id,
        "scale_type": result.scale_type,
        "scores": json.loads(result.scores or '{}'),
        "top_dimensions": json.loads(result.top_dimensions or '[]'),
        "talent_type": result.talent_type
    })


@scale_bp.route('/api/scale/secondary/submit', methods=['POST'])
def submit_secondary_scale():
    """
    提交二级量表答案，计算天赋类型

    路由: POST /api/scale/secondary/submit
    需要登录: 是
    请求体: {"dimension": "cognitive", "answers": {"sq1": 4, "sq2": 5, ...}}

    处理流程:
    1. 获取二级量表题目数据
    2. 根据每道题的 mapping 权重，累加各子类型的得分
    3. 找出得分最高的子类型
    4. 保存结果到数据库

    计分示例:
        假设题目 sq1 的 mapping 为 {"architect": 2, "detective": 1, "seeker": 0}
        用户选择了分数 4（比较符合）
        则 architect += 4*2 = 8, detect += 4*1 = 4, seek += 4*0 = 0

    返回数据:
    {
        "success": true,
        "session_id": "uuid-string",
        "talent_type": "系统架构师",
        "talent_description": "擅长构建复杂系统...",
        "type_scores": {
            "architect": 35,
            "detective": 28,
            "seeker": 22
        },
        "dimension": "认知洞察型"
    }
    """
    # 检查登录状态
    if not current_user.is_authenticated:
        return jsonify({"success": False, "error": "未登录", "need_login": True})

    from scale_data import SECONDARY_SCALE

    # 获取请求数据
    data = request.get_json()
    dimension = data.get('dimension')
    answers = data.get('answers', {})

    if not dimension or dimension not in SECONDARY_SCALE:
        return jsonify({"success": False, "error": "无效维度"})

    scale_data = SECONDARY_SCALE[dimension]

    # ----------------------------------------------------------
    # 计算各类型得分
    # ----------------------------------------------------------
    # 初始化各子类型的得分为0
    type_scores = {t: 0 for t in scale_data['types'].keys()}

    # 遍历每道题，根据 mapping 权重累加得分
    for q in scale_data['questions']:
        qid = q['id']
        if qid in answers:
            score = answers[qid]
            for t, weight in q['mapping'].items():
                type_scores[t] += score * weight

    # ----------------------------------------------------------
    # 找出最高分的类型
    # ----------------------------------------------------------
    best_type = max(type_scores, key=type_scores.get)
    talent_info = scale_data['types'][best_type]

    # ----------------------------------------------------------
    # 保存到数据库
    # ----------------------------------------------------------
    session_id = str(uuid.uuid4())
    result = ScaleResult(
        user_id=current_user.id,
        session_id=session_id,
        scale_type='secondary',
        answers=json.dumps(answers),
        scores=json.dumps(type_scores),
        talent_type=talent_info['name']
    )
    db.session.add(result)
    db.session.commit()

    return jsonify({
        "success": True,
        "session_id": session_id,
        "talent_type": talent_info['name'],
        "talent_description": talent_info['description'],
        "type_scores": type_scores,
        "dimension": scale_data['name']
    })
