from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from config import Config
from services.ai_service import AIService
import uuid
import random
from datetime import datetime

app = Flask(__name__)
app.config.from_object(Config)

ai_service = AIService()

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
    session['history'] = []  # 存储解析后的结构化历史
    session['asked_questions'] = []  # 记录AI已问过的问题
    session['covered_directions'] = []  # 记录已覆盖的方向(A-H)
    
    # 初始化方向队列：随机打乱A-H，后端硬控制每轮方向
    directions = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']
    random.shuffle(directions)
    session['remaining_directions'] = directions
    
    # 第一轮：取出第一个方向
    assigned = directions.pop(0) if directions else None
    session['remaining_directions'] = directions
    
    # 第一轮：获取AI开场白（围绕指定方向）
    result = ai_service.chat([], round_num=0, asked_questions=[], covered_directions=[], assigned_direction=assigned)
    
    if result['type'] == 'error':
        return jsonify({"success": False, "error": result.get('message', 'AI服务异常')})
    
    # 记录AI的回复到历史
    ai_msg = {
        "role": "assistant",
        "content": result['raw']
    }
    session['messages'].append(ai_msg)
    session['round'] = 1
    # 记录第一轮方向为已覆盖
    if assigned:
        session['covered_directions'] = [assigned]
    
    # 记录AI问的问题
    question_text = result.get('question', result.get('raw', ''))
    session['asked_questions'] = [question_text]
    
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
        "can_report": False,
        "assigned_direction": assigned
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
    
    # 取出本轮指定方向
    remaining_directions = session.get('remaining_directions', [])
    assigned = remaining_directions.pop(0) if remaining_directions else None
    session['remaining_directions'] = remaining_directions
    
    # 调用AI（传入指定方向）
    next_round = current_round + 1
    asked_questions = session.get('asked_questions', [])
    covered_directions = session.get('covered_directions', [])
    result = ai_service.chat(messages, round_num=next_round, asked_questions=asked_questions, covered_directions=covered_directions, assigned_direction=assigned)
    
    if result['type'] == 'error':
        # 回滚用户消息和方向
        messages.pop()
        session['history'].pop()
        if assigned:
            remaining_directions.insert(0, assigned)
            session['remaining_directions'] = remaining_directions
        return jsonify({"success": False, "error": result.get('message', 'AI服务异常')})
    
    # 记录AI回复
    messages.append({"role": "assistant", "content": result['raw']})
    session['round'] = next_round
    
    # 记录AI问的问题（防止重复）
    question_text = result.get('question', result.get('raw', ''))
    asked_questions.append(question_text)
    session['asked_questions'] = asked_questions
    
    # 更新方向覆盖状态（以指定方向为准，确保准确）
    if assigned and assigned not in covered_directions:
        covered_directions.append(assigned)
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
        "force_report": force_report,
        "assigned_direction": assigned
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

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
