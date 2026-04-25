"""天赋类型学测评路由 — 类似MBTI量表的固定选择题形式"""

import json
import uuid
from flask import Blueprint, request, jsonify, session
from models import db, TalentTypeResult
from talent_type_data import ALL_QUESTIONS, calculate_type_code

talent_type_bp = Blueprint('talent_type', __name__)


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
        'report': result['report']
    })


@talent_type_bp.route('/api/talent-type/result/<session_id>', methods=['GET'])
def get_result(session_id):
    """查询已保存的测评结果"""
    result = TalentTypeResult.query.filter_by(session_id=session_id).first()
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