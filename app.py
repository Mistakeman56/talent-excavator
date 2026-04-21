from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from config import Config
from services.ai_service import AIService
from models import db, ScaleResult, UserProfile, HumanDictionary
import uuid
import random
import json
from datetime import datetime

app = Flask(__name__)
app.config.from_object(Config)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///talent_assessment.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

ai_service = AIService()

with app.app_context():
    db.create_all()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/report')
def report():
    """报告展示页面"""
    report_content = session.get('report_content', '')
    if not report_content:
        return redirect(url_for('index'))
    return render_template('report.html', report=report_content, now=datetime.now().strftime('%Y年%m月%d日 %H:%M'))

@app.route('/api/start', methods=['POST'])
def start_assessment():
    """开始测评：初始化会话并获取AI开场白"""
    session.clear()
    session['session_id'] = str(uuid.uuid4())
    session['messages'] = []
    session['round'] = 0
    session['history'] = []
    session['asked_questions'] = []  # 记录AI已问过的问题
    session['covered_directions'] = []  # 记录已覆盖的方向(A-H)
    
    # 第一轮：获取AI开场白
    result = ai_service.chat([], round_num=0, asked_questions=[], covered_directions=[])
    
    if result['type'] == 'error':
        return jsonify({"success": False, "error": result.get('message', 'AI服务异常')})
    
    # 记录AI的回复到历史
    ai_msg = {
        "role": "assistant",
        "content": result['raw']
    }
    session['messages'].append(ai_msg)
    session['round'] = 1
    
    # 记录AI问的问题
    question_text = result.get('question', result.get('raw', ''))
    session['asked_questions'] = [question_text]
    
    # 检测第一轮实际方向并记录
    detected_dir = ai_service.detect_direction(question_text)
    if detected_dir:
        session['covered_directions'] = [detected_dir]
    
    session['history'].append({
        "round": 1,
        "role": "ai",
        **result
    })
    session.modified = True
    
    return jsonify({
        "success": True,
        "data": result,
        "round": 1,
        "can_report": False
    })

@app.route('/api/chat', methods=['POST'])
def chat():
    """用户提交回答，获取AI下一题"""
    data = request.get_json()
    user_answer = data.get('message', '').strip()
    
    if not user_answer:
        return jsonify({"success": False, "error": "请输入内容"})
    
    if 'messages' not in session:
        return jsonify({"success": False, "error": "会话已过期，请重新开始"})
    
    current_round = session.get('round', 0)
    messages = session['messages']
    
    # 添加用户消息
    messages.append({"role": "user", "content": user_answer})
    session['history'].append({
        "round": current_round,
        "role": "user",
        "content": user_answer
    })
    
    # 调用AI（后端不再干预方向选择）
    next_round = current_round + 1
    asked_questions = session.get('asked_questions', [])
    covered_directions = session.get('covered_directions', [])
    result = ai_service.chat(messages, round_num=next_round, asked_questions=asked_questions, covered_directions=covered_directions)
    
    if result['type'] == 'error':
        # 回滚用户消息
        messages.pop()
        session['history'].pop()
        return jsonify({"success": False, "error": result.get('message', 'AI服务异常')})
    
    # 记录AI回复
    messages.append({"role": "assistant", "content": result['raw']})
    session['round'] = next_round
    
    # 记录AI问的问题
    question_text = result.get('question', result.get('raw', ''))
    asked_questions.append(question_text)
    session['asked_questions'] = asked_questions
    
    # ========== 防重复兜底：如果问题与历史重复，重试一次 ==========
    is_duplicate = False
    for q in asked_questions[:-1]:  # 排除刚加入的当前问题
        if ai_service._is_similar_question(question_text, q):
            is_duplicate = True
            break
    
    if is_duplicate:
        # 添加提醒消息，使用临时消息列表重试（不污染session中的messages）
        retry_messages = messages + [{"role": "system", "content": "注意：你刚才的问题与之前重复。请换一个全新的问题，从未覆盖的方向中选择。"}]
        retry_result = ai_service.chat(retry_messages, round_num=next_round, asked_questions=asked_questions, covered_directions=covered_directions)
        
        if retry_result['type'] != 'error':
            # 用重试结果替换当前结果
            result = retry_result
            # 更新 messages 中最后一条AI消息
            messages[-1] = {"role": "assistant", "content": result['raw']}
            # 更新 asked_questions 中最后一条问题
            asked_questions[-1] = result.get('question', result.get('raw', ''))
            session['asked_questions'] = asked_questions
    
    # 检测AI实际方向并更新覆盖记录（被动记录，不干预）
    detected_dir = ai_service.detect_direction(question_text)
    if detected_dir and detected_dir not in covered_directions:
        covered_directions.append(detected_dir)
        session['covered_directions'] = covered_directions
    
    session['history'].append({
        "round": next_round,
        "role": "ai",
        **result
    })
    session.modified = True
    
    # 判断是否达到生成报告条件
    min_q = app.config['MIN_QUESTIONS']
    suggest_at = app.config['SUGGEST_REPORT_AT']
    max_q = app.config['MAX_QUESTIONS']
    
    can_report = next_round >= min_q
    suggest_report = next_round >= suggest_at
    force_report = next_round >= max_q
    
    return jsonify({
        "success": True,
        "data": result,
        "round": next_round,
        "can_report": can_report,
        "suggest_report": suggest_report,
        "force_report": force_report
    })

@app.route('/api/report', methods=['POST'])
def generate_report():
    """生成最终报告"""
    if 'messages' not in session:
        return jsonify({"success": False, "error": "会话已过期"})
    
    current_round = session.get('round', 0)
    if current_round < app.config['MIN_QUESTIONS']:
        return jsonify({"success": False, "error": f"至少完成{app.config['MIN_QUESTIONS']}轮对话才能生成报告"})
    
    messages = session['messages']
    
    # 添加生成报告的指令
    messages.append({
        "role": "user",
        "content": "访谈结束。请根据以上所有对话，生成最终的《个人天赋使用说明书+人类3.0发展诊断报告》。"
    })
    
    result = ai_service.chat(messages, round_num=current_round, is_report=True)
    
    if result['type'] == 'error':
        messages.pop()  # 回滚
        return jsonify({"success": False, "error": result.get('message', '报告生成失败')})
    
    # 保存报告
    session['report_content'] = result['content']
    session.modified = True
    
    return jsonify({
        "success": True,
        "redirect": url_for('report'),
        "report": result['content']
    })

@app.route('/api/reset', methods=['POST'])
def reset():
    """重置会话"""
    session.clear()
    return jsonify({"success": True})


# ============================================================
# Human词典初始化
# ============================================================

def init_dictionary():
    """首次启动时导入词典数据"""
    from dictionary_data import DICTIONARY_ENTRIES
    if HumanDictionary.query.first() is None:
        for entry in DICTIONARY_ENTRIES:
            db.session.add(HumanDictionary(**entry))
        db.session.commit()
        print(f"[Dictionary] Imported {len(DICTIONARY_ENTRIES)} entries")

with app.app_context():
    db.create_all()
    init_dictionary()

# ============================================================
# 量表模块路由
# ============================================================

@app.route('/dictionary')
def dictionary():
    """Human词典页面"""
    return render_template('dictionary.html')

@app.route('/api/dictionary')
def get_dictionary():
    """获取词典词条（支持分类筛选和搜索）"""
    category = request.args.get('category', '')
    keyword = request.args.get('keyword', '')
    
    query = HumanDictionary.query
    
    if category:
        query = query.filter_by(category=category)
    
    if keyword:
        query = query.filter(
            db.or_(
                HumanDictionary.term.contains(keyword),
                HumanDictionary.definition.contains(keyword)
            )
        )
    
    entries = query.order_by(HumanDictionary.category, HumanDictionary.term).all()
    
    # 获取所有分类
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

@app.route('/api/dictionary/<int:entry_id>')
def get_dictionary_entry(entry_id):
    """获取单个词条详情"""
    entry = HumanDictionary.query.get_or_404(entry_id)
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

@app.route('/scale')
def scale_page():
    """量表测评页面"""
    return render_template('scale.html')

@app.route('/scale/result')
def scale_result_page():
    """量表结果页面"""
    return render_template('scale_result.html')

@app.route('/api/scale/questions')
def get_scale_questions():
    """获取一级量表题目"""
    from scale_data import PRIMARY_SCALE
    return jsonify({
        "success": True,
        "data": PRIMARY_SCALE
    })

@app.route('/api/scale/submit', methods=['POST'])
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

@app.route('/api/scale/secondary/questions', methods=['POST'])
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

@app.route('/api/scale/secondary/submit', methods=['POST'])
def submit_secondary_scale():
    """提交二级量表答案，计算天赋类型"""
    from scale_data import SECONDARY_SCALE
    
    data = request.get_json()
    dimension = data.get('dimension')
    answers = data.get('answers', {})
    primary_session_id = data.get('primary_session_id')
    
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


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
