from flask import Blueprint, request, jsonify, session, current_app, url_for
from flask_login import current_user
from services.ai_service import AIService
import uuid

interview_bp = Blueprint('interview', __name__)
ai_service = AIService()


@interview_bp.route('/api/start', methods=['POST'])
def start_assessment():
    """开始测评：初始化会话并获取AI开场白"""
    if not current_user.is_authenticated:
        return jsonify({"success": False, "error": "未登录", "need_login": True})
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


@interview_bp.route('/api/chat', methods=['POST'])
def chat():
    """用户提交回答，获取AI下一题"""
    if not current_user.is_authenticated:
        return jsonify({"success": False, "error": "未登录", "need_login": True})
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
    result = ai_service.chat(
        messages, round_num=next_round,
        asked_questions=asked_questions,
        covered_directions=covered_directions
    )

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
        retry_messages = messages + [
            {"role": "system",
             "content": "注意：你刚才的问题与之前重复。请换一个全新的问题，从未覆盖的方向中选择。"}
        ]
        retry_result = ai_service.chat(
            retry_messages, round_num=next_round,
            asked_questions=asked_questions,
            covered_directions=covered_directions
        )

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
    min_q = current_app.config['MIN_QUESTIONS']
    suggest_at = current_app.config['SUGGEST_REPORT_AT']
    max_q = current_app.config['MAX_QUESTIONS']

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


@interview_bp.route('/api/report', methods=['POST'])
def generate_report():
    """生成最终报告"""
    if not current_user.is_authenticated:
        return jsonify({"success": False, "error": "未登录", "need_login": True})
    if 'messages' not in session:
        return jsonify({"success": False, "error": "会话已过期"})

    current_round = session.get('round', 0)
    if current_round < current_app.config['MIN_QUESTIONS']:
        return jsonify({
            "success": False,
            "error": f"至少完成{current_app.config['MIN_QUESTIONS']}轮对话才能生成报告"
        })

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
        "redirect": url_for('main.report'),
        "report": result['content']
    })


@interview_bp.route('/api/reset', methods=['POST'])
def reset():
    """重置会话"""
    session.clear()
    return jsonify({"success": True})
