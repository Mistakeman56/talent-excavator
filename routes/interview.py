"""
routes/interview.py — AI 深度访谈路由模块

本模块实现了 AI 深度访谈的核心交互逻辑，包括：
1. 开始新访谈 — 初始化会话并获取 AI 开场白
2. 用户回答提交 — 将用户回答发送给 AI，获取下一个问题
3. 报告生成 — 根据完整对话历史生成天赋诊断报告
4. 会话重置 — 清除当前访谈，重新开始
5. 访谈状态检查 — 检测是否有未完成的访谈（用于中断恢复）
6. 访谈恢复 — 加载历史对话，从上次中断处继续

访谈流程：
┌─────────────────────────────────────────────────────────────┐
│  用户点击"开始访谈"                                          │
│       ↓                                                      │
│  创建 InterviewSession 记录                                  │
│       ↓                                                      │
│  AI 生成开场白（第1轮）                                       │
│       ↓                                                      │
│  ┌──────────────────────────────┐                           │
│  │  循环 8~20 轮                │                           │
│  │    ↓                         │                           │
│  │  用户输入回答                │                           │
│  │    ↓                         │                           │
│  │  AI 分析回答，生成下一个问题 │                           │
│  │    ↓                         │                           │
│  │  记录对话历史                │                           │
│  │    ↓                         │                           │
│  │  推进到下一个访谈方向        │                           │
│  └──────────────────────────────┘                           │
│       ↓                                                      │
│  用户点击"生成报告"                                          │
│       ↓                                                      │
│  AI 根据完整对话生成 14 章节 Markdown 报告                    │
│       ↓                                                      │
│  保存报告，跳转到报告展示页                                   │
└─────────────────────────────────────────────────────────────┘

8 个访谈方向（A-H）：
- A: 童年模式/顽固缺点 — 16岁之前没人逼你也会沉进去做的事
- B: 无意识胜任区 — 成年后别人觉得很难但你觉得很自然的事
- C: 能量审计 — 做完后身体累但精神极度亢奋、充满能量的事
- D: 嫉妒/压抑 — 强烈嫉妒过的人、能力、生活状态
- E: 社会可见优势 — 别人通常为什么来找你
- F: 深层痛苦 — 最反复痛苦/受伤/执著的主题
- G: 伪擅长区 — 做得不错但越做越空、没有成就感的事
- H: 真实兴趣 — 没赚到钱但一谈起来就眼睛发亮的事
"""

from flask import Blueprint, request, jsonify, current_app, url_for
from flask_login import current_user
from services.ai_service import AIService
from models import db, InterviewSession
import json

# 创建 Blueprint 实例
# Blueprint 是 Flask 的模块化路由机制，将不同功能的路由分组到不同文件
interview_bp = Blueprint('interview', __name__)

# 创建 AI 服务实例（全局复用）
ai_service = AIService()


# ============================================================
# 辅助函数
# ============================================================

def _create_interview(user_id):
    """
    创建新的访谈会话

    参数:
        user_id: 用户ID
    返回:
        新创建的 InterviewSession 对象

    说明:
        创建一个空的访谈会话，messages 为空数组，stage 为 0（从A方向开始）
    """
    interview = InterviewSession(
        user_id=user_id,
        messages=json.dumps([]),   # 空对话历史
        stage=0,                   # 从第0个方向（A=童年模式）开始
        answers=json.dumps({})     # 空的结构化回答
    )
    db.session.add(interview)
    db.session.commit()
    return interview


def _get_or_create_interview(user_id):
    """
    获取用户的访谈会话，如果不存在则创建新会话

    参数:
        user_id: 用户ID
    返回:
        InterviewSession 对象

    说明:
        用于聊天接口，确保用户始终有一个可用的访谈会话
    """
    interview = InterviewSession.query.filter_by(user_id=user_id).first()
    if not interview:
        interview = _create_interview(user_id)
    return interview


def _extract_question(text):
    """
    从 AI 输出中提取问题部分

    参数:
        text: AI 的完整输出文本
    返回:
        提取出的问题文本

    说明:
        AI 的输出格式为：
        ---关键信号---
        分析内容
        ---天赋假设---
        假设内容
        ---HUMAN 3.0 判断---
        判断内容
        ---下一题---
        这里是问题内容

        本函数提取 "---下一题---" 后面的问题内容
    """
    if not text:
        return ''
    if '---下一题---' in text:
        return text.split('---下一题---')[-1].strip()
    return text.strip()


def _is_repeat(new_q, messages):
    """
    检测新问题是否与最近 3 轮的问题重复

    参数:
        new_q: 新生成的问题文本
        messages: 完整的对话历史
    返回:
        True 如果检测到重复，False 如果没有重复

    说明:
        使用前缀匹配算法：取新问题的前20个字符，检查是否与最近3个问题重复
        这种方法对中文效果很好，因为中文信息密度高，前20个字符通常足以判断是否重复
    """
    last_questions = []
    # 从最新的消息开始，收集最近3个AI问题
    for msg in reversed(messages):
        if msg.get('role') == 'assistant':
            last_questions.append(_extract_question(msg.get('content', '')))
        if len(last_questions) >= 3:
            break
    # 检查新问题是否与任何一个旧问题重复
    for q in last_questions:
        if not q:
            continue
        prefix = new_q[:20]
        if prefix and (prefix in q or q[:20] in new_q):
            return True
    return False


# ============================================================
# API 端点
# ============================================================

@interview_bp.route('/api/start', methods=['POST'])
def start_assessment():
    """
    开始测评 — 初始化会话并获取 AI 开场白

    请求方式: POST
    需要登录: 是

    处理流程:
    1. 检查用户是否已登录
    2. 删除该用户之前的访谈记录（确保每次都是全新开始）
    3. 创建新的 InterviewSession
    4. 调用 AI 服务生成开场白（方向固定为 A=童年模式）
    5. 将对话记录保存到数据库
    6. 返回 AI 的开场白和当前轮数

    返回数据:
    {
        "success": true,
        "data": {  // AI 解析后的结构化数据
            "type": "parsed",
            "signal": "关键信号内容",
            "hypothesis": "天赋假设内容",
            "judgment": "HUMAN 3.0 判断内容",
            "question": "问题内容",
            "raw": "AI 原始输出"
        },
        "round": 1,         // 当前轮数
        "can_report": false  // 是否可以生成报告
    }
    """
    # 检查登录状态
    if not current_user.is_authenticated:
        return jsonify({"success": False, "error": "未登录", "need_login": True})

    # 清除旧访谈记录（确保每次重新开始都是新局）
    InterviewSession.query.filter_by(user_id=current_user.id).delete()
    db.session.commit()

    # 创建新会话
    interview = _create_interview(current_user.id)

    # 第一轮：获取AI开场白，方向固定为A（童年模式）
    result = ai_service.chat(
        [],                           # 空的对话历史
        round_num=0,                  // 第0轮
        current_direction='A',        // 方向A=童年模式
        is_first_round=True           // 标记为第一轮
    )

    # 如果 AI 服务返回错误，删除刚创建的会话
    if result['type'] == 'error':
        db.session.delete(interview)
        db.session.commit()
        return jsonify({"success": False, "error": result.get('message', 'AI服务异常')})

    # 记录AI回复
    # 注意：为了保持 user->assistant 的交替模式，先添加一个虚拟的 user 消息
    messages = [
        {"role": "user", "content": "开始访谈"},
        {"role": "assistant", "content": result['raw']}
    ]
    interview.messages = json.dumps(messages)
    interview.stage = 1  # 已完成A方向，推进到B方向
    db.session.commit()

    return jsonify({
        "success": True,
        "data": result,          # AI 解析后的结构化数据
        "round": 1,              // 当前轮数
        "can_report": False      // 至少需要 MIN_QUESTIONS 轮才能生成报告
    })


@interview_bp.route('/api/chat', methods=['POST'])
def chat():
    """
    用户提交回答，获取 AI 下一个问题

    请求方式: POST
    需要登录: 是
    请求体: {"message": "用户的回答内容"}

    处理流程:
    1. 获取用户的访谈会话
    2. 将用户回答添加到对话历史
    3. 根据当前 stage 确定访谈方向
    4. 调用 AI 服务生成下一个问题
    5. 检测是否与最近问题重复，如果重复则重试一次
    6. 将 AI 回复保存到数据库
    7. 推进 stage 到下一个方向
    8. 检查是否达到生成报告的条件

    返回数据:
    {
        "success": true,
        "data": { ... },           // AI 解析后的结构化数据
        "round": 5,                // 当前轮数
        "can_report": true,        // 是否可以生成报告（>= MIN_QUESTIONS）
        "suggest_report": false,   // 是否建议生成报告（>= SUGGEST_REPORT_AT）
        "force_report": false      // 是否强制生成报告（>= MAX_QUESTIONS）
    }
    """
    # 检查登录状态
    if not current_user.is_authenticated:
        return jsonify({"success": False, "error": "未登录", "need_login": True})

    # 获取用户输入
    data = request.get_json()
    user_answer = data.get('message', '').strip()

    if not user_answer:
        return jsonify({"success": False, "error": "请输入内容"})

    # 获取或创建访谈会话
    interview = _get_or_create_interview(current_user.id)
    messages = json.loads(interview.messages)

    if not messages:
        return jsonify({"success": False, "error": "会话已过期，请重新开始"})

    # 添加用户消息到对话历史
    messages.append({"role": "user", "content": user_answer})

    # 确定当前访谈方向（根据 stage 从 INTERVIEW_FLOW 中查找）
    current_direction = ai_service.INTERVIEW_FLOW[interview.stage]

    # 计算轮数（统计 assistant 消息的数量）
    current_round = len([m for m in messages if m['role'] == 'assistant'])
    next_round = current_round + 1

    # 调用 AI 服务生成下一个问题
    result = ai_service.chat(
        messages,
        round_num=next_round,
        current_direction=current_direction,
        is_first_round=False
    )

    # 如果 AI 服务返回错误，回滚用户消息
    if result['type'] == 'error':
        messages.pop()
        return jsonify({"success": False, "error": result.get('message', 'AI服务异常')})

    # 防重复检测与重试
    new_q = _extract_question(result.get('question', result.get('raw', '')))
    if _is_repeat(new_q, messages):
        # 构造临时重试消息列表
        # 注意：system 消息只存在于本次调用，绝不写回数据库
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

    # 将最终确认的 AI 回复写入数据库历史
    messages.append({"role": "assistant", "content": result['raw']})

    # 推进阶段（循环遍历8个方向）
    interview.stage = (interview.stage + 1) % 8

    # 结构化存储当前方向的用户回答
    answers = json.loads(interview.answers or '{}')
    answers[current_direction] = user_answer
    interview.answers = json.dumps(answers)

    # 持久化对话历史
    interview.messages = json.dumps(messages)
    db.session.commit()

    # 判断是否达到生成报告条件
    min_q = current_app.config['MIN_QUESTIONS']        # 最少8轮
    suggest_at = current_app.config['SUGGEST_REPORT_AT']  # 建议12轮
    max_q = current_app.config['MAX_QUESTIONS']          # 最多20轮

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
    """
    生成最终报告

    请求方式: POST
    需要登录: 是

    处理流程:
    1. 检查是否已完成足够轮数（至少 MIN_QUESTIONS 轮）
    2. 在对话历史后追加一条触发报告生成的用户消息
    3. 调用 AI 服务生成报告（is_report=True）
    4. 将报告保存到数据库的 report_content 字段
    5. 返回报告内容和跳转地址

    AI 生成的报告要求覆盖 14 个章节：
    1. 用户真正的底层天赋是什么
    2. 为什么这些天赋过去被遮蔽了
    3. 用户的缺点、怪癖、嫉妒、痛苦分别透露了什么
    4. 用户的能量来源与能量黑洞
    5. 用户的高能场景与伪擅长场景
    6. 用户最适合的角色类型
    7. 用户最不该再走的路
    8. 用户如何把天赋映射到职业/事业/产品
    9. 用户在认知/身体/精神/职业四象限的现状判断
    10. 用户当前更像哪种生活方式原型
    11. 当前最核心的问题是什么
    12. 未来30天/90天/6-12个月的演进建议
    13. AI使用建议
    14. 一段真正打到用户心里的结语
    """
    # 检查登录状态
    if not current_user.is_authenticated:
        return jsonify({"success": False, "error": "未登录", "need_login": True})

    # 获取访谈会话
    interview = InterviewSession.query.filter_by(user_id=current_user.id).first()
    if not interview:
        return jsonify({"success": False, "error": "会话已过期"})

    messages = json.loads(interview.messages)
    current_round = len([m for m in messages if m['role'] == 'assistant'])

    # 检查是否完成足够轮数
    if current_round < current_app.config['MIN_QUESTIONS']:
        return jsonify({
            "success": False,
            "error": f"至少完成{current_app.config['MIN_QUESTIONS']}轮对话才能生成报告"
        })

    # 添加生成报告的指令到对话历史
    messages.append({
        "role": "user",
        "content": "访谈结束。请根据以上所有对话，生成最终的《个人天赋使用说明书+人类3.0发展诊断报告》。"
    })

    # 调用 AI 生成报告
    result = ai_service.chat(messages, round_num=current_round, is_report=True)

    if result['type'] == 'error':
        messages.pop()  # 回滚
        return jsonify({"success": False, "error": result.get('message', '报告生成失败')})

    # 保存报告到数据库
    interview.report_content = result['content']
    db.session.commit()

    return jsonify({
        "success": True,
        "redirect": url_for('main.report'),  # 报告页面的URL
        "report": result['content']            # 报告的 Markdown 内容
    })


@interview_bp.route('/api/reset', methods=['POST'])
def reset():
    """
    重置会话 — 清除当前用户的访谈记录

    请求方式: POST
    需要登录: 是

    说明:
        删除该用户的所有访谈记录，下次点击"开始访谈"时会创建新会话
    """
    if current_user.is_authenticated:
        InterviewSession.query.filter_by(user_id=current_user.id).delete()
        db.session.commit()
    return jsonify({"success": True})


@interview_bp.route('/api/interview/status')
def interview_status():
    """
    检查当前用户是否有未完成的访谈会话

    请求方式: GET
    需要登录: 否（未登录时返回 has_active: false）

    用途:
        首页加载时调用，如果用户有未完成的访谈，显示"继续上次访谈"按钮

    返回数据:
    {
        "success": true,
        "has_active": true,        // 是否有未完成的访谈
        "round": 5,                // 已完成的轮数
        "can_report": true,        // 是否可以生成报告
        "updated_at": "..."        // 最后更新时间
    }
    """
    if not current_user.is_authenticated:
        return jsonify({"success": True, "has_active": False})

    # 查询未完成的访谈（report_content 为空说明还没生成报告）
    interview = InterviewSession.query.filter_by(
        user_id=current_user.id
    ).filter(
        InterviewSession.report_content.is_(None)
    ).first()

    if not interview:
        return jsonify({"success": True, "has_active": False})

    messages = json.loads(interview.messages or '[]')
    round_count = len([m for m in messages if m['role'] == 'assistant'])

    # 如果轮数为0，说明还没有开始对话，不算活跃会话
    if round_count == 0:
        return jsonify({"success": True, "has_active": False})

    min_q = current_app.config['MIN_QUESTIONS']
    return jsonify({
        "success": True,
        "has_active": True,
        "round": round_count,
        "can_report": round_count >= min_q,
        "updated_at": interview.updated_at.isoformat() if interview.updated_at else None
    })


@interview_bp.route('/api/interview/resume')
def resume_interview():
    """
    恢复未完成的访谈会话，返回完整对话历史

    请求方式: GET
    需要登录: 是

    用途:
        用户点击"继续上次访谈"按钮时调用，加载历史对话并恢复聊天界面

    返回数据:
    {
        "success": true,
        "messages": [              // 解析后的对话历史
            {
                "role": "assistant",
                "data": {          // AI 解析后的结构化数据
                    "signal": "...",
                    "hypothesis": "...",
                    "judgment": "...",
                    "question": "..."
                },
                "raw": "..."       // AI 原始输出
            },
            {
                "role": "user",
                "content": "用户的回答"
            },
            ...
        ],
        "round": 5,                // 已完成的轮数
        "can_report": true,        // 是否可以生成报告
        "suggest_report": false,   // 是否建议生成报告
        "force_report": false      // 是否强制生成报告
    }
    """
    if not current_user.is_authenticated:
        return jsonify({"success": False, "error": "未登录", "need_login": True})

    # 查询未完成的访谈
    interview = InterviewSession.query.filter_by(
        user_id=current_user.id
    ).filter(
        InterviewSession.report_content.is_(None)
    ).first()

    if not interview:
        return jsonify({"success": False, "error": "没有未完成的访谈"})

    messages = json.loads(interview.messages or '[]')
    round_count = len([m for m in messages if m['role'] == 'assistant'])

    # 读取配置参数
    min_q = current_app.config['MIN_QUESTIONS']
    suggest_at = current_app.config['SUGGEST_REPORT_AT']
    max_q = current_app.config['MAX_QUESTIONS']

    # 解析每条 AI 消息，提取结构化数据
    parsed_messages = []
    for msg in messages:
        if msg['role'] == 'assistant':
            parsed = ai_service.parse_response(msg['content'])
            parsed_messages.append({
                'role': 'assistant',
                'data': parsed,
                'raw': msg['content']
            })
        elif msg['role'] == 'user':
            parsed_messages.append({
                'role': 'user',
                'content': msg['content']
            })

    return jsonify({
        "success": True,
        "messages": parsed_messages,
        "round": round_count,
        "can_report": round_count >= min_q,
        "suggest_report": round_count >= suggest_at,
        "force_report": round_count >= max_q
    })
