"""
routes/history.py — 历史记录路由模块

本模块为登录用户提供统一的测评历史汇总功能，包括：
1. 历史记录页面 — 展示所有测评结果的时间线
2. 历史记录 API — 汇总三种测评结果（AI访谈、量表、天赋类型学）
3. 详情查询 API — 查询单条记录的详细信息
4. 访谈对话导出 — 将访谈对话导出为 Markdown 文件

三种测评类型：
- AI 深度访谈（interview）：8~20轮对话，生成14章节报告
- 天赋维度量表（scale）：20题标准化测评，输出五维度雷达图
- 天赋类型学（talent_type）：40题情境迫选，输出4字母类型代码

数据流向：
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│ InterviewSession │     │ ScaleResult │     │ TalentTypeResult│
│ (AI访谈)         │     │ (量表)       │     │ (类型学)         │
└────────┬────────┘     └──────┬──────┘     └───────┬───────┘
         │                     │                     │
         └─────────────────────┼─────────────────────┘
                               ↓
                    ┌─────────────────────┐
                    │   /api/history      │
                    │  (合并+排序)        │
                    └─────────────────────┘
                               ↓
                    ┌─────────────────────┐
                    │   history.html      │
                    │  (前端渲染展示)     │
                    └─────────────────────┘
"""

from flask import Blueprint, render_template, jsonify, make_response
from flask_login import login_required, current_user
from models import db, InterviewSession, ScaleResult, TalentTypeResult
import json


def safe_json_loads(text, default=None):
    """
    安全的 JSON 反序列化函数

    参数:
        text: 要解析的 JSON 字符串
        default: 解析失败时返回的默认值
    返回:
        解析后的 Python 对象，或默认值

    说明:
        数据库中存储的 JSON 字符串可能格式不正确（如手动修改导致）
        使用此函数可以避免因 JSON 解析错误导致整个请求失败
    """
    if default is None:
        default = {}
    try:
        return json.loads(text) if text else default
    except (json.JSONDecodeError, TypeError):
        return default

history_bp = Blueprint('history', __name__)


@history_bp.route('/history')
@login_required
def history_page():
    """
    历史记录页面

    路由: GET /history
    需要登录: 是

    说明:
        渲染历史记录页面模板，实际的数据通过 /api/history 接口异步加载
        这种"页面+API"的分离模式是现代 Web 应用的常见做法
    """
    return render_template('history.html')


@history_bp.route('/api/history')
@login_required
def get_history():
    """
    获取当前用户的所有测评历史

    路由: GET /api/history
    需要登录: 是

    处理逻辑:
    1. 查询该用户所有已完成的 AI 访谈（report_content 不为空）
    2. 查询该用户所有的量表测评结果
    3. 查询该用户所有的天赋类型学测评结果
    4. 将三种结果合并，按创建时间倒序排列

    返回数据结构:
    {
        "success": true,
        "data": [
            {
                "id": 1,
                "type": "interview",           // 测评类型
                "type_label": "AI 深度访谈",   // 显示标签
                "title": "AI 天赋诊断报告",    // 标题
                "subtitle": "12 轮对话",       // 副标题
                "created_at": "2024-01-01T00:00:00",
                "has_report": true
            },
            {
                "id": 1,
                "type": "scale",
                "type_label": "天赋维度量表",
                "title": "一级量表 · 五维筛查",
                "subtitle": "Top: 认知洞察型, 创造表达型",
                "created_at": "...",
                "scale_type": "primary",
                "dimensions": {...},
                "top_dimensions": [...]
            },
            {
                "id": 1,
                "type": "talent_type",
                "type_label": "天赋类型学",
                "title": "CDAM · 认知架构师",
                "subtitle": "用系统思维重构世界的人",
                "created_at": "...",
                "type_code": "CDAM",
                "dimensions": {...},
                "scores": {...}
            },
            ...
        ],
        "counts": {
            "interview": 3,
            "scale": 5,
            "talent_type": 2,
            "total": 10
        }
    }
    """
    user_id = current_user.id

    # ----------------------------------------------------------
    # 查询 AI 访谈记录（只有生成了报告的才算完成）
    # ----------------------------------------------------------
    interviews = InterviewSession.query.filter(
        InterviewSession.user_id == user_id,
        InterviewSession.report_content.isnot(None)
    ).order_by(InterviewSession.created_at.desc()).all()

    interview_items = []
    for iv in interviews:
        messages = safe_json_loads(iv.messages, [])
        interview_items.append({
            'id': iv.id,
            'type': 'interview',
            'type_label': 'AI 深度访谈',
            'title': 'AI 天赋诊断报告',
            'subtitle': f'{len(messages) // 2} 轮对话',  # 每轮包含 user+assistant 两条消息
            'created_at': iv.created_at.isoformat() if iv.created_at else None,
            'has_report': True
        })

    # ----------------------------------------------------------
    # 查询量表测评记录
    # ----------------------------------------------------------
    scales = ScaleResult.query.filter_by(user_id=user_id).order_by(ScaleResult.created_at.desc()).all()

    scale_items = []
    for sc in scales:
        scores = safe_json_loads(sc.scores)
        top_dims = safe_json_loads(sc.top_dimensions, [])
        if sc.scale_type == 'primary':
            title = '一级量表 · 五维筛查'
            subtitle = f'Top: {", ".join([d["name"] for d in top_dims[:2]])}' if top_dims else ''
        else:
            title = '二级量表 · 精准锁定'
            subtitle = sc.talent_type or ''
        scale_items.append({
            'id': sc.id,
            'session_id': sc.session_id,
            'type': 'scale',
            'type_label': '天赋维度量表',
            'title': title,
            'subtitle': subtitle,
            'created_at': sc.created_at.isoformat() if sc.created_at else None,
            'scale_type': sc.scale_type,
            'dimensions': scores,
            'top_dimensions': top_dims
        })

    # ----------------------------------------------------------
    # 查询天赋类型学测评记录
    # ----------------------------------------------------------
    tts = TalentTypeResult.query.filter_by(user_id=user_id).order_by(TalentTypeResult.created_at.desc()).all()

    tt_items = []
    for tt in tts:
        report = safe_json_loads(tt.report)
        tt_items.append({
            'id': tt.id,
            'session_id': tt.session_id,
            'type': 'talent_type',
            'type_label': '天赋类型学',
            'title': f'{tt.type_code} · {report.get("name", "")}',
            'subtitle': report.get('tagline', ''),
            'created_at': tt.created_at.isoformat() if tt.created_at else None,
            'type_code': tt.type_code,
            'dimensions': safe_json_loads(tt.dimensions),
            'scores': safe_json_loads(tt.scores)
        })

    # ----------------------------------------------------------
    # 合并三种结果，按创建时间倒序排列
    # ----------------------------------------------------------
    all_items = interview_items + scale_items + tt_items
    all_items.sort(key=lambda x: x['created_at'] or '', reverse=True)

    return jsonify({
        'success': True,
        'data': all_items,
        'counts': {
            'interview': len(interview_items),
            'scale': len(scale_items),
            'talent_type': len(tt_items),
            'total': len(all_items)
        }
    })


@history_bp.route('/api/history/interview/<int:interview_id>')
@login_required
def get_interview_detail(interview_id):
    """
    获取 AI 访谈报告详情

    路由: GET /api/history/interview/<interview_id>
    需要登录: 是
    参数: interview_id — 访谈记录的ID

    说明:
        返回访谈的完整报告内容和对话历史
        用于在历史记录页面点击"查看结果"时展示报告弹窗
    """
    iv = InterviewSession.query.filter_by(id=interview_id, user_id=current_user.id).first()
    if not iv:
        return jsonify({'success': False, 'error': '记录不存在'}), 404

    return jsonify({
        'success': True,
        'type': 'interview',
        'report': iv.report_content,
        'messages': safe_json_loads(iv.messages, []),
        'created_at': iv.created_at.isoformat() if iv.created_at else None
    })


@history_bp.route('/api/history/scale/<session_id>')
@login_required
def get_scale_detail(session_id):
    """
    获取量表结果详情

    路由: GET /api/history/scale/<session_id>
    需要登录: 是
    参数: session_id — 测评会话的UUID标识

    说明:
        返回量表的得分数据和Top维度
        用于跳转到量表结果页时回填数据
    """
    sc = ScaleResult.query.filter_by(session_id=session_id, user_id=current_user.id).first()
    if not sc:
        return jsonify({'success': False, 'error': '记录不存在'}), 404

    return jsonify({
        'success': True,
        'type': 'scale',
        'session_id': sc.session_id,
        'scale_type': sc.scale_type,
        'scores': safe_json_loads(sc.scores),
        'top_dimensions': safe_json_loads(sc.top_dimensions, []),
        'talent_type': sc.talent_type,
        'created_at': sc.created_at.isoformat() if sc.created_at else None
    })


@history_bp.route('/api/history/interview/<int:interview_id>/export')
@login_required
def export_interview(interview_id):
    """
    导出访谈对话为 Markdown 文件

    路由: GET /api/history/interview/<interview_id>/export
    需要登录: 是
    参数: interview_id — 访谈记录的ID

    说明:
        将完整的访谈对话导出为格式化的 Markdown 文件
        包含每轮的AI分析（关键信号、天赋假设、HUMAN 3.0判断）和问题

    导出格式示例:
        # AI 深度访谈对话记录

        生成时间：2024年01月01日 12:00

        ---

        ## 你的回答
        用户的回答内容...

        ## 第 1 轮
        **关键信号**：分析内容...
        **天赋假设**：假设内容...
        **HUMAN 3.0 判断**：判断内容...
        **AI 提问**：问题内容...
    """
    iv = InterviewSession.query.filter_by(id=interview_id, user_id=current_user.id).first()
    if not iv:
        return jsonify({'success': False, 'error': '记录不存在'}), 404

    messages = safe_json_loads(iv.messages, [])
    lines = ['# AI 深度访谈对话记录\n']
    lines.append(f'生成时间：{iv.created_at.strftime("%Y年%m月%d日 %H:%M") if iv.created_at else "未知"}\n')
    lines.append('---\n')

    round_num = 0
    for msg in messages:
        if msg.get('role') == 'user':
            # 跳过虚拟的"开始访谈"消息
            if msg.get('content') != '开始访谈':
                lines.append(f'## 你的回答\n{msg["content"]}\n')
        elif msg.get('role') == 'assistant':
            round_num += 1
            content = msg.get('content', '')

            # 解析 AI 输出的四个部分
            parts = {}
            for label in ['关键信号', '天赋假设', 'HUMAN 3.0 判断']:
                marker = f'---{label}---'
                if marker in content:
                    start = content.index(marker) + len(marker)
                    next_marker = content.find('---', start)
                    if next_marker != -1:
                        parts[label] = content[start:next_marker].strip()

            # 提取问题部分
            question = content
            if '---下一题---' in content:
                question = content.split('---下一题---')[-1].strip()

            lines.append(f'## 第 {round_num} 轮\n')
            for label, text in parts.items():
                lines.append(f'**{label}**：{text}\n')
            lines.append(f'**AI 提问**：{question}\n')

    # 生成 Markdown 文件并返回
    md_content = '\n'.join(lines)
    response = make_response(md_content)
    response.headers['Content-Type'] = 'text/markdown; charset=utf-8'
    response.headers['Content-Disposition'] = f'attachment; filename=interview_{interview_id}.md'
    return response
