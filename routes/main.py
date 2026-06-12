from flask import Blueprint, render_template, redirect, url_for, jsonify, request, make_response
from flask_login import current_user, login_required
from datetime import datetime
from models import db, InterviewSession
import uuid

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    return render_template('index.html', current_user=current_user)


@main_bp.route('/report')
@login_required
def report():
    """报告展示页面"""
    interview = InterviewSession.query.filter_by(user_id=current_user.id).order_by(InterviewSession.id.desc()).first()
    report_content = interview.report_content if interview else ''
    if not report_content:
        return redirect(url_for('main.index'))
    return render_template('report.html', report=report_content,
                           now=datetime.now().strftime('%Y年%m月%d日 %H:%M'))


@main_bp.route('/api/report/share', methods=['POST'])
@login_required
def share_report():
    """生成报告分享链接"""
    interview = InterviewSession.query.filter_by(
        user_id=current_user.id
    ).filter(
        InterviewSession.report_content.isnot(None)
    ).order_by(InterviewSession.id.desc()).first()

    if not interview:
        return jsonify({"success": False, "error": "没有可分享的报告"})

    if not interview.share_token:
        interview.share_token = uuid.uuid4().hex[:16]
        db.session.commit()

    share_url = url_for('main.shared_report', token=interview.share_token, _external=True)
    return jsonify({"success": True, "url": share_url, "token": interview.share_token})


@main_bp.route('/report/shared/<token>')
def shared_report(token):
    """通过分享链接查看报告（无需登录）"""
    interview = InterviewSession.query.filter_by(share_token=token).first()
    if not interview or not interview.report_content:
        return render_template('errors/404.html'), 404
    return render_template('report.html', report=interview.report_content,
                           now=interview.created_at.strftime('%Y年%m月%d日 %H:%M') if interview.created_at else '',
                           is_shared=True)


@main_bp.route('/api/report/export-markdown')
@login_required
def export_markdown():
    """导出报告为 Markdown 文件"""
    interview = InterviewSession.query.filter_by(
        user_id=current_user.id
    ).filter(
        InterviewSession.report_content.isnot(None)
    ).order_by(InterviewSession.id.desc()).first()

    if not interview:
        return jsonify({"success": False, "error": "没有可导出的报告"})

    response = make_response(interview.report_content)
    response.headers['Content-Type'] = 'text/markdown; charset=utf-8'
    response.headers['Content-Disposition'] = 'attachment; filename=talent_report.md'
    return response


@main_bp.route('/talent-type')
def talent_type():
    """天赋类型学测评页面（无需登录）"""
    return render_template('talent_type.html')


@main_bp.route('/talent-type/result/<session_id>')
def talent_type_result(session_id):
    """天赋类型学测评结果页"""
    return render_template('talent_type_result.html', session_id=session_id)