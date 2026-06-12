"""用户历史记录路由 — 汇总 AI 访谈、量表、天赋类型学三种测评结果"""

from flask import Blueprint, render_template, jsonify
from flask_login import login_required, current_user
from models import db, InterviewSession, ScaleResult, TalentTypeResult
import json


def safe_json_loads(text, default=None):
    """安全的 JSON 反序列化，失败返回默认值"""
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
    """历史记录页面"""
    return render_template('history.html')


@history_bp.route('/api/history')
@login_required
def get_history():
    """获取当前用户的所有测评历史"""
    user_id = current_user.id

    # AI 访谈（有报告才算完成）
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
            'subtitle': f'{len(messages) // 2} 轮对话',
            'created_at': iv.created_at.isoformat() if iv.created_at else None,
            'has_report': True
        })

    # 量表
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

    # 天赋类型学
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

    # 合并按时间倒序
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
    """获取 AI 访谈报告详情"""
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
    """获取量表结果详情（用于 localStorage 回填）"""
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
    """导出访谈对话为 Markdown"""
    from flask import make_response

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
            if msg.get('content') != '开始访谈':
                lines.append(f'## 你的回答\n{msg["content"]}\n')
        elif msg.get('role') == 'assistant':
            round_num += 1
            content = msg.get('content', '')
            parts = {}
            for label in ['关键信号', '天赋假设', 'HUMAN 3.0 判断']:
                marker = f'---{label}---'
                if marker in content:
                    start = content.index(marker) + len(marker)
                    end_marker = '---'
                    next_marker = content.find('---', start)
                    if next_marker != -1:
                        parts[label] = content[start:next_marker].strip()

            question = content
            if '---下一题---' in content:
                question = content.split('---下一题---')[-1].strip()

            lines.append(f'## 第 {round_num} 轮\n')
            for label, text in parts.items():
                lines.append(f'**{label}**：{text}\n')
            lines.append(f'**AI 提问**：{question}\n')

    md_content = '\n'.join(lines)
    response = make_response(md_content)
    response.headers['Content-Type'] = 'text/markdown; charset=utf-8'
    response.headers['Content-Disposition'] = f'attachment; filename=interview_{interview_id}.md'
    return response
