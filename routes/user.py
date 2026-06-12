"""用户个人中心 — 修改密码、查看统计、账号注销"""

from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required, current_user
from models import db, User, InterviewSession, ScaleResult, TalentTypeResult

user_bp = Blueprint('user', __name__)


@user_bp.route('/user/settings')
@login_required
def user_settings():
    return render_template('user_settings.html')


@user_bp.route('/api/user/stats')
@login_required
def get_user_stats():
    user_id = current_user.id
    interview_count = InterviewSession.query.filter_by(user_id=user_id).filter(
        InterviewSession.report_content.isnot(None)
    ).count()
    scale_count = ScaleResult.query.filter_by(user_id=user_id).count()
    tt_count = TalentTypeResult.query.filter_by(user_id=user_id).count()

    return jsonify({
        'success': True,
        'username': current_user.username,
        'created_at': current_user.created_at.strftime('%Y-%m-%d') if current_user.created_at else '',
        'stats': {
            'interview': interview_count,
            'scale': scale_count,
            'talent_type': tt_count,
            'total': interview_count + scale_count + tt_count
        }
    })


@user_bp.route('/api/user/change-password', methods=['POST'])
@login_required
def change_password():
    data = request.get_json()
    old_password = data.get('old_password', '')
    new_password = data.get('new_password', '')
    confirm_password = data.get('confirm_password', '')

    if not old_password or not new_password:
        return jsonify({'success': False, 'error': '请填写完整'})

    if not current_user.check_password(old_password):
        return jsonify({'success': False, 'error': '当前密码错误'})

    if len(new_password) < 6:
        return jsonify({'success': False, 'error': '新密码至少6位'})

    if new_password != confirm_password:
        return jsonify({'success': False, 'error': '两次输入的密码不一致'})

    current_user.set_password(new_password)
    db.session.commit()
    return jsonify({'success': True, 'message': '密码修改成功'})


@user_bp.route('/api/user/change-username', methods=['POST'])
@login_required
def change_username():
    data = request.get_json()
    new_username = data.get('username', '').strip()

    if not new_username:
        return jsonify({'success': False, 'error': '用户名不能为空'})

    if len(new_username) < 3 or len(new_username) > 20:
        return jsonify({'success': False, 'error': '用户名长度为3-20个字符'})

    if new_username == current_user.username:
        return jsonify({'success': False, 'error': '新用户名与当前相同'})

    existing = User.query.filter_by(username=new_username).first()
    if existing:
        return jsonify({'success': False, 'error': '用户名已被占用'})

    current_user.username = new_username
    db.session.commit()
    return jsonify({'success': True, 'message': '用户名修改成功', 'username': new_username})


@user_bp.route('/api/user/delete-account', methods=['DELETE'])
@login_required
def delete_account():
    if current_user.is_admin:
        return jsonify({'success': False, 'error': '管理员账号不能注销'}), 400

    db.session.delete(current_user)
    db.session.commit()
    return jsonify({'success': True, 'message': '账号已注销'})
