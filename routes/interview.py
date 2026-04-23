from flask import Blueprint, request, jsonify, session, current_app, url_for
from flask_login import current_user
from services.ai_service import AIService
from models import db, InterviewSession
import json

interview_bp = Blueprint('interview', __name__)
ai_service = AIService()


def _get_or_create_interview(user_id):
    """获取或创建用户的访谈会话"""
    interview = InterviewSession.query.filter_by(user_id=user_id).first()
    if not interview:
        interview = InterviewSession(
            user_id=user_id,
            messages=json.dumps([]),
            stage=0,
            answers=json.dumps({})
        )
        db.session.add(interview)
        db.session.commit()
    return interview


def _extract_question(text):
    """从AI输出中提取问题部分"""
    if not text:
        return ''
    if '---下一题---' in text:
        return text.split('---下一题---')[-1].strip()
    return text.strip()


def _is_repeat(new_q, messages):
    """检测新问题是否与最近3轮重复（前缀匹配，对中文高效）"""
    last_questions = []
    for msg in reversed(messages):
        if msg.get('role') == 'assistant':
            last_questions.append(_extract_question(msg.get('content', '')))
        if len(last_questions) >= 3:
            break
    for q in last_questions:
        if not q:
            continue
        prefix = new_q[:20]
        if prefix and (prefix in q or q[:20] in new_q):
            return True
    return False


@interview_bp.route('/api/start', methods=['POST'])
def start_assessment():
    """开始测评：初始化会话并获取AI开场白"""
    if not current_user.is_authenticated:
        return jsonify({"success": False, "error": "未登录", "need_login": True})

    # 清除旧会话（确保每次重新开始都是新局）
    InterviewSession.query.filter_by(user_id=current_user.id).delete()
    db.session.commit()
    session.clear()

    # 创建新会话
    interview = InterviewSession(
        user_id=current_user.id,
        messages=json.dumps([]),
        stage=0,
        answers=json.dumps({})
    )
    db.session.add(interview)
    db.session.commit()

    # 第一轮：获取AI开场白，方向固定为A
    result = ai_service.chat(
        [],
        round_num=0,
        current_direction='A',
        is_first_round=True
    )

    if result['type'] == 'error':
        db.session.delete(interview)
        db.session.commit()
        return jsonify({"success": False, "error": result.get('message', 'AI服务异常')})

    # 记录AI回复
    messages = [{"role": "assistant", "content": result['raw']}]
    interview.messages = json.dumps(messages)
    interview.stage = 1  # 已完成A方向，推进到B
    db.session.commit()

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

    interview = _get_or_create_interview(current_user.id)
    messages = json.loads(interview.messages)

    if not messages:
        return jsonify({"success": False, "error": "会话已过期，请重新开始"})

    # 添加用户消息
    messages.append({"role": "user", "content": user_answer})

    # 确定当前方向
    current_direction = ai_service.INTERVIEW_FLOW[interview.stage]

    # 计算轮数
    current_round = len([m for m in messages if m['role'] == 'assistant'])
    next_round = current_round + 1

    # 调用AI
    result = ai_service.chat(
        messages,
        round_num=next_round,
        current_direction=current_direction,
        is_first_round=False
    )

    if result['type'] == 'error':
        # 回滚用户消息
        messages.pop()
        return jsonify({"success": False, "error": result.get('message', 'AI服务异常')})

    # 记录AI回复
    messages.append({"role": "assistant", "content": result['raw']})

    # 防重复检测与重试
    new_q = _extract_question(result.get('question', result.get('raw', '')))
    if _is_repeat(new_q, messages):
        retry_messages = messages + [
            {"role": "system", "content": "你刚刚的问题与之前重复，请换一个全新的角度提问。"}
        ]
        retry_result = ai_service.chat(
            retry_messages,
            round_num=next_round,
            current_direction=current_direction,
            is_first_round=False
        )
        if retry_result['type'] != 'error':
            result = retry_result
            messages[-1] = {"role": "assistant", "content": result['raw']}

    # 推进阶段
    if interview.stage < 7:
        interview.stage += 1

    # 结构化存储当前方向的用户回答
    answers = json.loads(interview.answers or '{}')
    answers[current_direction] = user_answer
    interview.answers = json.dumps(answers)

    # 持久化对话历史
    interview.messages = json.dumps(messages)
    db.session.commit()

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

    interview = InterviewSession.query.filter_by(user_id=current_user.id).first()
    if not interview:
        return jsonify({"success": False, "error": "会话已过期"})

    messages = json.loads(interview.messages)
    current_round = len([m for m in messages if m['role'] == 'assistant'])

    if current_round < current_app.config['MIN_QUESTIONS']:
        return jsonify({
            "success": False,
            "error": f"至少完成{current_app.config['MIN_QUESTIONS']}轮对话才能生成报告"
        })

    # 添加生成报告的指令
    messages.append({
        "role": "user",
        "content": "访谈结束。请根据以上所有对话，生成最终的《个人天赋使用说明书+人类3.0发展诊断报告》。"
    })

    result = ai_service.chat(messages, round_num=current_round, is_report=True)

    if result['type'] == 'error':
        messages.pop()  # 回滚
        return jsonify({"success": False, "error": result.get('message', '报告生成失败')})

    # 保存报告到数据库
    interview.report_content = result['content']
    db.session.commit()

    return jsonify({
        "success": True,
        "redirect": url_for('main.report'),
        "report": result['content']
    })


@interview_bp.route('/api/reset', methods=['POST'])
def reset():
    """重置会话"""
    if current_user.is_authenticated:
        InterviewSession.query.filter_by(user_id=current_user.id).delete()
        db.session.commit()
    session.clear()
    return jsonify({"success": True})
