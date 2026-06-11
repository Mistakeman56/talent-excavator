"""天赋类型学测评路由 — 类似MBTI量表的固定选择题形式"""

import json
import uuid
from flask import Blueprint, request, jsonify, render_template
from flask_login import current_user
from models import db, TalentTypeResult
from talent_type_data import ALL_QUESTIONS, calculate_type_code, TYPE_NAMES, DETAILED_REPORTS, TYPE_DIM1, TYPE_DIM2, TYPE_DIM3, TYPE_DIM4

talent_type_bp = Blueprint('talent_type', __name__)


@talent_type_bp.route('/api/talent-type/catalog', methods=['GET'])
def get_catalog():
    """返回72种人格类型的完整数据"""
    dim1_keys = ["C", "R", "B", "S"]
    dim2_keys = ["D", "R", "V"]
    dim3_keys = ["A", "H"]
    dim4_keys = ["M", "C", "P"]

    types = []
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
    """返回全部40道题目（不包含答案key，前端做选项映射）"""
    return jsonify({
        'success': True,
        'questions': ALL_QUESTIONS
    })


@talent_type_bp.route('/api/talent-type/submit', methods=['POST'])
def submit_answers():
    """提交答题结果，计算类型并保存"""
    if not current_user.is_authenticated:
        return jsonify({"success": False, "error": "未登录", "need_login": True})

    data = request.get_json()
    if not data or 'answers' not in data:
        return jsonify({'success': False, 'error': '缺少答题数据'}), 400

    answers = data['answers']  # {"t1": "a", "t2": "c", ...}

    if len(answers) != len(ALL_QUESTIONS):
        return jsonify({
            'success': False,
            'error': f'需要回答全部 {len(ALL_QUESTIONS)} 题，当前仅回答了 {len(answers)} 题'
        }), 400

    result = calculate_type_code(answers)
    session_id = str(uuid.uuid4())

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
    """查询已保存的测评结果（仅限本人）"""
    if not current_user.is_authenticated:
        return jsonify({"success": False, "error": "未登录", "need_login": True})

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
    """认知洞察型图鉴页面"""
    return render_template('type_catalog_group.html', group_type='C')

@talent_type_bp.route('/type-catalog/relational')
def type_catalog_relational():
    """关系创造型图鉴页面"""
    return render_template('type_catalog_group.html', group_type='R')

@talent_type_bp.route('/type-catalog/body')
def type_catalog_body():
    """身体实践型图鉴页面"""
    return render_template('type_catalog_group.html', group_type='B')

@talent_type_bp.route('/type-catalog/systemic')
def type_catalog_systemic():
    """系统引领型图鉴页面"""
    return render_template('type_catalog_group.html', group_type='S')
