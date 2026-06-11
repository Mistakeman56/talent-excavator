from flask import Blueprint, render_template, jsonify, request, current_app
from flask_login import current_user, login_required
from functools import wraps
from datetime import datetime, timedelta, timezone
from models import db, User, InterviewSession, ScaleResult, TalentTypeResult, VisitLog
import json

admin_bp = Blueprint('admin', __name__)


def is_admin():
    """检查当前用户是否为管理员"""
    return (current_user.is_authenticated and
            getattr(current_user, 'is_admin', False))


def admin_required(f):
    """管理员权限装饰器"""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not is_admin():
            return jsonify({"success": False, "error": "无权限"}), 403
        return f(*args, **kwargs)
    return decorated


@admin_bp.route('/admin')
@login_required
@admin_required
def dashboard():
    return render_template('admin.html')


@admin_bp.route('/api/admin/stats')
@login_required
@admin_required
def stats():
    """管理后台统计数据"""
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)

    total_users = User.query.count()
    total_visits = VisitLog.query.count()
    today_new_users = User.query.filter(User.created_at >= today_start).count()
    today_visits = VisitLog.query.filter(VisitLog.created_at >= today_start).count()

    # 各模块访问量
    module_rows = db.session.query(
        VisitLog.module, db.func.count(VisitLog.id)
    ).group_by(VisitLog.module).all()
    module_counts = {row[0] or 'other': row[1] for row in module_rows}

    # 近7天趋势
    daily_trend = []
    for i in range(6, -1, -1):
        day = today_start - timedelta(days=i)
        next_day = day + timedelta(days=1)
        count = VisitLog.query.filter(
            VisitLog.created_at >= day,
            VisitLog.created_at < next_day
        ).count()
        daily_trend.append({
            'date': day.strftime('%m-%d'),
            'count': count
        })

    return jsonify({
        'total_users': total_users,
        'total_visits': total_visits,
        'today_new_users': today_new_users,
        'today_visits': today_visits,
        'module_counts': module_counts,
        'daily_trend': daily_trend
    })


@admin_bp.route('/api/admin/users')
@login_required
@admin_required
def get_users():
    """用户列表（分页）"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    pagination = User.query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    # 使用子查询一次性获取每个用户的测评计数
    interview_subq = db.session.query(
        InterviewSession.user_id,
        db.func.count(InterviewSession.id).label('count')
    ).group_by(InterviewSession.user_id).subquery()

    scale_subq = db.session.query(
        ScaleResult.user_id,
        db.func.count(ScaleResult.id).label('count')
    ).group_by(ScaleResult.user_id).subquery()

    tt_subq = db.session.query(
        TalentTypeResult.user_id,
        db.func.count(TalentTypeResult.id).label('count')
    ).group_by(TalentTypeResult.user_id).subquery()

    users_query = db.session.query(
        User,
        db.func.coalesce(interview_subq.c.count, 0).label('interview_count'),
        db.func.coalesce(scale_subq.c.count, 0).label('scale_count'),
        db.func.coalesce(tt_subq.c.count, 0).label('tt_count')
    ).outerjoin(
        interview_subq, User.id == interview_subq.c.user_id
    ).outerjoin(
        scale_subq, User.id == scale_subq.c.user_id
    ).outerjoin(
        tt_subq, User.id == tt_subq.c.user_id
    ).order_by(User.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    users = []
    for u, interview_count, scale_count, tt_count in users_query.items:
        users.append({
            'id': u.id,
            'username': u.username,
            'created_at': u.created_at.strftime('%Y-%m-%d %H:%M'),
            'assessment_count': interview_count + scale_count + tt_count
        })

    return jsonify({
        'data': users,
        'total': pagination.total,
        'page': page,
        'per_page': per_page,
        'pages': pagination.pages
    })


@admin_bp.route('/api/admin/users/<int:user_id>', methods=['DELETE'])
@login_required
@admin_required
def delete_user(user_id):
    """删除用户（通过 ORM 级联自动删除关联记录）"""
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"success": False, "error": "用户不存在"}), 404
    if user.is_admin:
        return jsonify({"success": False, "error": "不能删除管理员账号"}), 400

    # ORM cascade 会自动删除关联的 interviews、scale_results、talent_type_results、visit_logs
    db.session.delete(user)
    db.session.commit()

    return jsonify({"success": True})


@admin_bp.route('/api/admin/records')
@login_required
@admin_required
def get_records():
    """测评记录列表（分页+类型筛选）"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    record_type = request.args.get('type', '')

    # 收集所有记录（使用 JOIN 避免 N+1 查询）
    items = []

    if not record_type or record_type == 'interview':
        interviews = db.session.query(InterviewSession, User).join(
            User, InterviewSession.user_id == User.id
        ).filter(
            InterviewSession.report_content.isnot(None)
        ).order_by(InterviewSession.created_at.desc()).all()
        for r, user in interviews:
            items.append({
                'id': r.id,
                'type': 'interview',
                'type_label': 'AI 访谈',
                'username': user.username,
                'user_id': r.user_id,
                'title': f'访谈报告',
                'created_at': r.created_at.strftime('%Y-%m-%d %H:%M')
            })

    if not record_type or record_type == 'scale':
        scales = db.session.query(ScaleResult, User).outerjoin(
            User, ScaleResult.user_id == User.id
        ).order_by(ScaleResult.created_at.desc()).all()
        for s, user in scales:
            scores = json.loads(s.scores) if s.scores else {}
            top = json.loads(s.top_dimensions) if s.top_dimensions else []
            title = f'量表 ({s.scale_type})'
            if top:
                title = f'量表 Top: {", ".join(top[:2])}'
            items.append({
                'id': s.id,
                'type': 'scale',
                'type_label': '量表',
                'session_id': s.session_id,
                'username': user.username if user else '未知',
                'user_id': s.user_id,
                'title': title,
                'created_at': s.created_at.strftime('%Y-%m-%d %H:%M')
            })

    if not record_type or record_type == 'talent_type':
        tts = db.session.query(TalentTypeResult, User).outerjoin(
            User, TalentTypeResult.user_id == User.id
        ).order_by(TalentTypeResult.created_at.desc()).all()
        for t, user in tts:
            report = json.loads(t.report) if t.report else {}
            name = report.get('name', '')
            title = f'{t.type_code}' + (f' · {name}' if name else '')
            items.append({
                'id': t.id,
                'type': 'talent_type',
                'type_label': '类型学',
                'session_id': t.session_id,
                'username': user.username if user else '未知',
                'user_id': t.user_id,
                'title': title,
                'created_at': t.created_at.strftime('%Y-%m-%d %H:%M')
            })

    # 按时间排序
    items.sort(key=lambda x: x['created_at'], reverse=True)

    total = len(items)
    start = (page - 1) * per_page
    end = start + per_page
    paged = items[start:end]

    return jsonify({
        'data': paged,
        'total': total,
        'page': page,
        'per_page': per_page,
        'pages': (total + per_page - 1) // per_page
    })


@admin_bp.route('/api/admin/records/<record_type>/<int:record_id>', methods=['DELETE'])
@login_required
@admin_required
def delete_record(record_type, record_id):
    """删除单条测评记录"""
    if record_type == 'interview':
        record = db.session.get(InterviewSession, record_id)
    elif record_type == 'scale':
        record = db.session.get(ScaleResult, record_id)
    elif record_type == 'talent_type':
        record = db.session.get(TalentTypeResult, record_id)
    else:
        return jsonify({"success": False, "error": "无效的记录类型"}), 400

    if not record:
        return jsonify({"success": False, "error": "记录不存在"}), 404

    db.session.delete(record)
    db.session.commit()
    return jsonify({"success": True})
