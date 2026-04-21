from flask import Blueprint, render_template, request, jsonify
from models import db, ScaleResult
import uuid
import json

scale_bp = Blueprint('scale', __name__)


@scale_bp.route('/scale')
def scale_page():
    """量表测评页面"""
    return render_template('scale.html')


@scale_bp.route('/scale/result')
def scale_result_page():
    """量表结果页面"""
    return render_template('scale_result.html')


@scale_bp.route('/api/scale/questions')
def get_scale_questions():
    """获取一级量表题目"""
    from scale_data import PRIMARY_SCALE
    return jsonify({
        "success": True,
        "data": PRIMARY_SCALE
    })


@scale_bp.route('/api/scale/submit', methods=['POST'])
def submit_scale():
    """提交一级量表答案，计算得分"""
    from scale_data import PRIMARY_SCALE

    data = request.get_json()
    answers = data.get('answers', {})

    if not answers:
        return jsonify({"success": False, "error": "没有提交答案"})

    # 计算各维度得分
    scores = {}
    for dim_key, dim_data in PRIMARY_SCALE['dimensions'].items():
        total = 0
        count = 0
        for q in dim_data['questions']:
            qid = q['id']
            if qid in answers:
                score = answers[qid]
                if q.get('reverse'):
                    score = 6 - score  # 反向计分
                total += score
                count += 1
        scores[dim_key] = {
            "name": dim_data['name'],
            "description": dim_data['description'],
            "score": round(total / count, 1) if count > 0 else 0,
            "max_score": 5,
            "raw_total": total
        }

    # 排序找出Top维度
    sorted_dims = sorted(scores.items(), key=lambda x: x[1]['score'], reverse=True)
    top_dimensions = [
        {"key": k, "name": v["name"], "score": v["score"]}
        for k, v in sorted_dims[:3]
    ]

    # 保存到数据库
    session_id = str(uuid.uuid4())
    result = ScaleResult(
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
    """获取二级量表题目（基于一级量表Top维度）"""
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


@scale_bp.route('/api/scale/secondary/submit', methods=['POST'])
def submit_secondary_scale():
    """提交二级量表答案，计算天赋类型"""
    from scale_data import SECONDARY_SCALE

    data = request.get_json()
    dimension = data.get('dimension')
    answers = data.get('answers', {})

    if not dimension or dimension not in SECONDARY_SCALE:
        return jsonify({"success": False, "error": "无效维度"})

    scale_data = SECONDARY_SCALE[dimension]

    # 计算各类型得分
    type_scores = {t: 0 for t in scale_data['types'].keys()}

    for q in scale_data['questions']:
        qid = q['id']
        if qid in answers:
            score = answers[qid]
            for t, weight in q['mapping'].items():
                type_scores[t] += score * weight

    # 找出最高分的类型
    best_type = max(type_scores, key=type_scores.get)
    talent_info = scale_data['types'][best_type]

    # 保存到数据库
    session_id = str(uuid.uuid4())
    result = ScaleResult(
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
