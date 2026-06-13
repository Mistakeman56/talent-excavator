"""
routes/talent_type.py — 天赋类型学测评路由模块

本模块实现了天赋类型学测评（类似MBTI）的完整功能，包括：
1. 获取题目 — 返回全部40道情境迫选题
2. 提交答案 — 计算4字母类型代码，生成解读报告
3. 查询结果 — 根据session_id查询历史测评结果
4. 72种人格图鉴 — 浏览所有72种天赋类型的详细信息
5. 类型对比 — 两种天赋类型的四维度并排对比

天赋类型学设计原理：
┌─────────────────────────────────────────────────────────────┐
│  40道题，分4个模组，每个模组决定1个字母                        │
│                                                              │
│  Module I (t1-t12) → 第1位字母：天赋形态                      │
│    C=认知洞察型  R=关系创造型  B=身体实践型  S=系统引领型      │
│                                                              │
│  Module II (t13-t22) → 第2位字母：能量模式                    │
│    D=深度专注型  R=快速响应型  V=多元探索型                    │
│                                                              │
│  Module III (t23-t30) → 第3位字母：驱动来源                   │
│    A=成就驱动型  H=和谐驱动型                                 │
│                                                              │
│  Module IV (t31-t40) → 第4位字母：兴趣指向                    │
│    M=机械系统型  C=概念抽象型  P=人物关系型                    │
│                                                              │
│  总组合 = 4 × 3 × 2 × 3 = 72种天赋类型                       │
│  每种类型配有专属中文名称、标语和详细解读报告                   │
└─────────────────────────────────────────────────────────────┘

计分逻辑：
- 每道题有2个选项，每个选项对应不同维度的得分
- 用户选择后，对应的维度累加得分
- 最终每个维度得分最高的选项即为该维度的字母
- 4个维度的字母组合成4位类型代码（如 "CDAM"）

平局检测：
- 如果某维度出现多个选项得分相同，返回 ties 字段标记歧义维度
- 前端会提示用户该维度存在平局，建议重新作答
"""

import json
import uuid
from flask import Blueprint, request, jsonify, render_template
from flask_login import current_user
from models import db, TalentTypeResult
from talent_type_data import ALL_QUESTIONS, calculate_type_code, TYPE_NAMES, DETAILED_REPORTS, TYPE_DIM1, TYPE_DIM2, TYPE_DIM3, TYPE_DIM4
from utils import api_error, ERR_NOT_LOGGED_IN

talent_type_bp = Blueprint('talent_type', __name__)


@talent_type_bp.route('/api/talent-type/catalog', methods=['GET'])
def get_catalog():
    """
    返回72种人格类型的完整数据

    路由: GET /api/talent-type/catalog
    需要登录: 否

    用途:
        用于72种人格图鉴页面，展示所有类型的列表和筛选

    返回数据:
    {
        "success": true,
        "types": [
            {
                "code": "CDAM",
                "name": "认知架构师",
                "tagline": "用系统思维重构世界的人",
                "dim1": {"code": "C", "name": "认知洞察型", "desc": "..."},
                "dim2": {"code": "D", "name": "深度专注型", "desc": "..."},
                "dim3": {"code": "A", "name": "成就驱动型", "desc": "..."},
                "dim4": {"code": "M", "name": "机械系统型", "desc": "..."},
                "has_detail": true,
                "report": { ... }  // 详细解读报告
            },
            ...  // 共72种
        ],
        "dimensions": {
            "dim1": {"C": {...}, "R": {...}, "B": {...}, "S": {...}},
            "dim2": {"D": {...}, "R": {...}, "V": {...}},
            "dim3": {"A": {...}, "H": {...}},
            "dim4": {"M": {...}, "C": {...}, "P": {...}}
        }
    }
    """
    # 四个维度的选项列表
    dim1_keys = ["C", "R", "B", "S"]  # 天赋形态
    dim2_keys = ["D", "R", "V"]        # 能量模式
    dim3_keys = ["A", "H"]             # 驱动来源
    dim4_keys = ["M", "C", "P"]        # 兴趣指向

    types = []
    # 遍历所有组合，生成72种类型
    for d1 in dim1_keys:
        for d2 in dim2_keys:
            for d3 in dim3_keys:
                for d4 in dim4_keys:
                    code = d1 + d2 + d3 + d4
                    name_info = TYPE_NAMES.get(code, {})
                    detail = DETAILED_REPORTS.get(code)

                    types.append({
                        "code": code,
                        "name": name_info.get("name", "未知类型"),
                        "tagline": name_info.get("tagline", ""),
                        "dim1": {"code": d1, "name": TYPE_DIM1[d1]["name"], "desc": TYPE_DIM1[d1]["desc"]},
                        "dim2": {"code": d2, "name": TYPE_DIM2[d2]["name"], "desc": TYPE_DIM2[d2]["desc"]},
                        "dim3": {"code": d3, "name": TYPE_DIM3[d3]["name"], "desc": TYPE_DIM3[d3]["desc"]},
                        "dim4": {"code": d4, "name": TYPE_DIM4[d4]["name"], "desc": TYPE_DIM4[d4]["desc"]},
                        "has_detail": detail is not None,
                        "report": detail if detail else None
                    })

    return jsonify({
        "success": True,
        "types": types,
        "dimensions": {
            "dim1": {k: v for k, v in TYPE_DIM1.items()},
            "dim2": {k: v for k, v in TYPE_DIM2.items()},
            "dim3": {k: v for k, v in TYPE_DIM3.items()},
            "dim4": {k: v for k, v in TYPE_DIM4.items()}
        }
    })


@talent_type_bp.route('/api/talent-type/questions', methods=['GET'])
def get_questions():
    """
    返回全部40道题目（不包含答案key，前端做选项映射）

    路由: GET /api/talent-type/questions
    需要登录: 否

    说明:
        返回的题目不包含正确答案（因为是迫选题，没有对错之分）
        每道题有2个选项，每个选项对应不同维度的得分权重

    返回数据:
    {
        "success": true,
        "questions": [
            {
                "id": "t1",
                "dimension": "dim1",
                "text": "面对一个复杂问题时，你通常会...",
                "options": [
                    {
                        "key": "a",
                        "text": "先拆解成小问题，逐一分析",
                        "scores": {"C": 2, "R": 0, "B": 0, "S": 1}
                    },
                    {
                        "key": "b",
                        "text": "先找有经验的人讨论",
                        "scores": {"C": 0, "R": 2, "B": 0, "S": 1}
                    }
                ]
            },
            ...
        ]
    }
    """
    sanitized = []
    for q in ALL_QUESTIONS:
        sanitized.append({
            'id': q['id'],
            'dimension': q.get('dimension', ''),
            'text': q['text'],
            'options': [{'key': o['key'], 'text': o['text']} for o in q['options']]
        })
    return jsonify({
        'success': True,
        'questions': sanitized
    })


@talent_type_bp.route('/api/talent-type/submit', methods=['POST'])
def submit_answers():
    """
    提交答题结果，计算类型并保存

    路由: POST /api/talent-type/submit
    需要登录: 是
    请求体: {"answers": {"t1": "a", "t2": "c", "t3": "b", ...}}

    处理流程:
    1. 校验是否回答了全部40道题
    2. 调用 calculate_type_code() 计算4字母类型代码
    3. 保存结果到数据库
    4. 返回类型代码、维度详情和解读报告

    返回数据:
    {
        "success": true,
        "session_id": "uuid-string",
        "type_code": "CDAM",
        "dimensions": {
            "dim1": {"code": "C", "name": "认知洞察型", "desc": "...", "score": 18},
            "dim2": {"code": "D", "name": "深度专注型", "desc": "...", "score": 12},
            "dim3": {"code": "A", "name": "成就驱动型", "desc": "...", "score": 8},
            "dim4": {"code": "M", "name": "机械系统型", "desc": "...", "score": 15}
        },
        "scores": {"dim1": {"C": 18, "R": 8, "B": 4, "S": 10}, ...},
        "ties": {},  // 平局检测（如果有维度出现平局，会在这里标记）
        "report": {
            "name": "认知架构师",
            "tagline": "用系统思维重构世界的人",
            "sections": [...]
        }
    }
    """
    if not current_user.is_authenticated:
        return api_error(ERR_NOT_LOGGED_IN, "请先登录")

    data = request.get_json(silent=True)
    if not data or 'answers' not in data:
        return jsonify({'success': False, 'error': '缺少答题数据'}), 400

    answers = data['answers']  # {"t1": "a", "t2": "c", ...}

    # 校验是否回答了全部题目
    if len(answers) != len(ALL_QUESTIONS):
        return jsonify({
            'success': False,
            'error': f'需要回答全部 {len(ALL_QUESTIONS)} 题，当前仅回答了 {len(answers)} 题'
        }), 400

    # 计算类型代码
    result = calculate_type_code(answers)
    session_id = str(uuid.uuid4())

    # 保存到数据库
    record = TalentTypeResult(
        user_id=current_user.id,
        session_id=session_id,
        type_code=result['code'],
        answers=json.dumps(answers, ensure_ascii=False),
        scores=json.dumps(result['scores'], ensure_ascii=False),
        dimensions=json.dumps(result['dimensions'], ensure_ascii=False),
        report=json.dumps(result['report'], ensure_ascii=False)
    )
    db.session.add(record)
    db.session.commit()

    return jsonify({
        'success': True,
        'session_id': session_id,
        'type_code': result['code'],
        'dimensions': result['dimensions'],
        'scores': result['scores'],
        'ties': result.get('ties', {}),
        'report': result['report']
    })


@talent_type_bp.route('/api/talent-type/result/<session_id>', methods=['GET'])
def get_result(session_id):
    """
    查询已保存的测评结果（仅限本人）

    路由: GET /api/talent-type/result/<session_id>
    需要登录: 是

    说明:
        根据session_id查询测评结果
        只能查询自己的结果，不能查询其他用户的

    返回数据:
    {
        "success": true,
        "type_code": "CDAM",
        "answers": {"t1": "a", "t2": "c", ...},
        "scores": {...},
        "dimensions": {...},
        "report": {...},
        "created_at": "2024-01-01T00:00:00"
    }
    """
    if not current_user.is_authenticated:
        return api_error(ERR_NOT_LOGGED_IN, "请先登录")

    result = TalentTypeResult.query.filter_by(
        session_id=session_id,
        user_id=current_user.id
    ).first()
    if not result:
        return jsonify({'success': False, 'error': '结果不存在'}), 404

    return jsonify({
        'success': True,
        'type_code': result.type_code,
        'answers': json.loads(result.answers),
        'scores': json.loads(result.scores),
        'dimensions': json.loads(result.dimensions),
        'report': json.loads(result.report),
        'created_at': result.created_at.isoformat()
    })


@talent_type_bp.route('/type-catalog/cognitive')
def type_catalog_cognitive():
    """认知洞察型图鉴页面 — 展示所有C开头的18种类型"""
    return render_template('type_catalog_group.html', group_type='C')

@talent_type_bp.route('/type-catalog/relational')
def type_catalog_relational():
    """关系创造型图鉴页面 — 展示所有R开头的18种类型"""
    return render_template('type_catalog_group.html', group_type='R')

@talent_type_bp.route('/type-catalog/body')
def type_catalog_body():
    """身体实践型图鉴页面 — 展示所有B开头的18种类型"""
    return render_template('type_catalog_group.html', group_type='B')

@talent_type_bp.route('/type-catalog/systemic')
def type_catalog_systemic():
    """系统引领型图鉴页面 — 展示所有S开头的18种类型"""
    return render_template('type_catalog_group.html', group_type='S')


@talent_type_bp.route('/type-compare')
def type_compare_page():
    """
    天赋类型对比页面

    路由: GET /type-compare
    需要登录: 否

    说明:
        用户选择两种天赋类型，四维度并排对比
        展示两种类型的异同点
    """
    return render_template('type_compare.html')


@talent_type_bp.route('/api/talent-type/compare')
def compare_types():
    """
    对比两种天赋类型

    路由: GET /api/talent-type/compare?code1=CDAM&code2=RBAM
    需要登录: 否
    参数:
        code1: 第一种类型的4字母代码
        code2: 第二种类型的4字母代码

    返回数据:
    {
        "success": true,
        "type1": {
            "code": "CDAM",
            "name": "认知架构师",
            "tagline": "...",
            "dim1": {"code": "C", "name": "认知洞察型", "desc": "..."},
            "dim2": {"code": "D", "name": "深度专注型", "desc": "..."},
            "dim3": {"code": "A", "name": "成就驱动型", "desc": "..."},
            "dim4": {"code": "M", "name": "机械系统型", "desc": "..."}
        },
        "type2": { ... }
    }
    """
    code1 = request.args.get('code1', '').upper()
    code2 = request.args.get('code2', '').upper()

    # 校验类型代码是否有效
    valid_codes = set(TYPE_NAMES.keys())
    if code1 not in valid_codes:
        return jsonify({'success': False, 'error': f'无效的类型代码: {code1}'}), 400
    if code2 not in valid_codes:
        return jsonify({'success': False, 'error': f'无效的类型代码: {code2}'}), 400

    def get_type_info(code):
        """获取单个类型的完整信息"""
        name_info = TYPE_NAMES.get(code, {})
        detail = DETAILED_REPORTS.get(code)
        return {
            'code': code,
            'name': name_info.get('name', '未知类型'),
            'tagline': name_info.get('tagline', ''),
            'dim1': {'code': code[0], 'name': TYPE_DIM1[code[0]]['name'], 'desc': TYPE_DIM1[code[0]]['desc']},
            'dim2': {'code': code[1], 'name': TYPE_DIM2[code[1]]['name'], 'desc': TYPE_DIM2[code[1]]['desc']},
            'dim3': {'code': code[2], 'name': TYPE_DIM3[code[2]]['name'], 'desc': TYPE_DIM3[code[2]]['desc']},
            'dim4': {'code': code[3], 'name': TYPE_DIM4[code[3]]['name'], 'desc': TYPE_DIM4[code[3]]['desc']},
            'has_detail': detail is not None
        }

    return jsonify({
        'success': True,
        'type1': get_type_info(code1),
        'type2': get_type_info(code2)
    })
