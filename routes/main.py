from flask import Blueprint, render_template, session, redirect, url_for
from flask_login import current_user
from datetime import datetime
from models import InterviewSession

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    return render_template('index.html', current_user=current_user)


@main_bp.route('/report')
def report():
    """报告展示页面"""
    interview = InterviewSession.query.filter_by(user_id=current_user.id).order_by(InterviewSession.id.desc()).first()
    report_content = interview.report_content if interview else ''
    if not report_content:
        return redirect(url_for('main.index'))
    return render_template('report.html', report=report_content,
                           now=datetime.now().strftime('%Y年%m月%d日 %H:%M'))
