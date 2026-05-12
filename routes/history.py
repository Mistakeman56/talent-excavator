"""用户历史记录路由 — 汇总 AI 访谈、量表、天赋类型学三种测评结果"""

from flask import Blueprint, render_template, jsonify
from flask_login import login_required, current_user
from models import db, InterviewSession, ScaleResult, TalentTypeResult
import json

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
        interview_items.append({
            'id': iv.id,
            'type': 'interview',
            'type_label': 'AI 深度访谈',
            'title': 'AI 天赋诊断报告',
            'subtitle': f'{len(json.loads(iv.messages or "[]")) // 2} 轮对话',
            'created_at': iv.created_at.isoformat() if iv.created_at else None
        })

    # 量表
    scales = ScaleResult.query.filter_by(user_id=user_id).order_by(ScaleResult.created_at.desc()).all()

    scale_items = []
    for sc in scales:
        scores = json.loads(sc.scores) if sc.scores else {}
        top_dims = json.loads(sc.top_dimensions) if sc.top_dimensions else []
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
            'created_at': sc.created_at.isoformat() if sc.created_at else None
        })

    # 天赋类型学
    tts = TalentTypeResult.query.filter_by(user_id=user_id).order_by(TalentTypeResult.created_at.desc()).all()

    tt_items = []
    for tt in tts:
        report = json.loads(tt.report) if tt.report else {}
        tt_items.append({
            'id': tt.id,
            'session_id': tt.session_id,
            'type': 'talent_type',
            'type_label': '天赋类型学',
            'title': f'{tt.type_code} · {report.get("name", "")}',
            'subtitle': report.get('tagline', ''),
            'created_at': tt.created_at.isoformat() if tt.created_at else None
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
        'messages': json.loads(iv.messages or '[]'),
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
        'scores': json.loads(sc.scores) if sc.scores else {},
        'top_dimensions': json.loads(sc.top_dimensions) if sc.top_dimensions else [],
        'talent_type': sc.talent_type,
        'created_at': sc.created_at.isoformat() if sc.created_at else None
    })
