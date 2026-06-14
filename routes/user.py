"""
routes/user.py — 用户个人中心路由模块

本模块实现了用户的个人设置功能，包括：
1. 设置页面 — 展示用户信息和设置选项
2. 修改用户名 — 更新用户名（唯一性校验）
3. 修改密码 — 验证旧密码后更新为新密码
4. 账号注销 — 删除用户账号和所有相关数据
5. 个人统计 — 查询用户的测评统计数据

路由清单：
- GET  /user/settings              — 个人设置页面（需要登录）
- GET  /api/user/stats             — 个人统计数据（需要登录）
- POST /api/user/change-username   — 修改用户名（需要登录）
- POST /api/user/change-password   — 修改密码（需要登录）
- DELETE /api/user/delete-account  — 注销账号（需要登录）

安全设计：
- 修改密码需要验证旧密码
- 管理员账号不能注销
- 用户名修改需要检查唯一性
"""

from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required, current_user
from models import db, User, InterviewSession, ScaleResult, TalentTypeResult

# 创建用户模块的 Blueprint
user_bp = Blueprint('user', __name__)


@user_bp.route('/user/settings')
@login_required
def user_settings():
    """
    个人设置页面

    路由: GET /user/settings
    需要登录: 是

    说明:
        渲染用户个人设置页面，包含：
        1. 个人统计：AI访谈次数、量表次数、类型学次数
        2. 修改用户名：输入新用户名并提交
        3. 修改密码：输入旧密码和新密码并提交
        4. 账号注销：删除账号（危险操作）

    页面交互：
        - 统计数据通过 /api/user/stats 接口异步加载
        - 修改操作通过对应的API接口提交
        - 危险操作（注销）需要二次确认
    """
    return render_template('user_settings.html')


@user_bp.route('/api/user/stats')
@login_required
def get_user_stats():
    """
    获取用户个人统计数据

    路由: GET /api/user/stats
    需要登录: 是

    返回数据:
    {
        "success": true,
        "username": "testuser",
        "created_at": "2024-01-01",
        "stats": {
            "interview": 3,     // AI访谈完成次数
            "scale": 5,         // 量表测评次数
            "talent_type": 2,   // 类型学测评次数
            "total": 10         // 总测评次数
        }
    }

    说明:
        统计数据包括：
        - AI访谈：report_content 不为空的记录数
        - 量表：所有 scale_results 记录数
        - 类型学：所有 talent_type_results 记录数
    """
    user_id = current_user.id

    # 统计各种测评的完成次数
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
    """
    修改密码

    路由: POST /api/user/change-password
    需要登录: 是
    请求体: {"old_password": "...", "new_password": "...", "confirm_password": "..."}

    处理流程:
    1. 验证所有字段不为空
    2. 验证旧密码是否正确
    3. 验证新密码长度（至少6位）
    4. 验证两次新密码输入一致
    5. 更新密码（哈希存储）

    返回数据:
    成功: {"success": true, "message": "密码修改成功"}
    失败: {"success": false, "error": "错误信息"}

    安全设计:
    - 必须验证旧密码才能修改
    - 新密码需要长度校验
    - 新密码需要二次确认
    """
    data = request.get_json(silent=True)
    if not data:
        return jsonify({'success': False, 'error': '请求格式错误'}), 400
    old_password = data.get('old_password', '')
    new_password = data.get('new_password', '')
    confirm_password = data.get('confirm_password', '')

    # 参数校验
    if not old_password or not new_password:
        return jsonify({'success': False, 'error': '请填写完整'})

    # 验证旧密码
    if not current_user.check_password(old_password):
        return jsonify({'success': False, 'error': '当前密码错误'})

    # 新密码长度校验
    if len(new_password) < 6:
        return jsonify({'success': False, 'error': '新密码至少6位'})

    # 新密码一致性校验
    if new_password != confirm_password:
        return jsonify({'success': False, 'error': '两次输入的密码不一致'})

    # 更新密码
    current_user.set_password(new_password)
    db.session.commit()
    return jsonify({'success': True, 'message': '密码修改成功'})


@user_bp.route('/api/user/change-username', methods=['POST'])
@login_required
def change_username():
    """
    修改用户名

    路由: POST /api/user/change-username
    需要登录: 是
    请求体: {"username": "new_username"}

    处理流程:
    1. 验证用户名不为空
    2. 验证用户名长度（3-20个字符）
    3. 验证新用户名与当前用户名不同
    4. 验证新用户名未被占用
    5. 更新用户名

    返回数据:
    成功: {"success": true, "message": "用户名修改成功", "username": "new_username"}
    失败: {"success": false, "error": "错误信息"}

    安全设计:
    - 用户名需要唯一性校验
    - 不能修改为与当前用户名相同的值
    """
    data = request.get_json(silent=True)
    if not data:
        return jsonify({'success': False, 'error': '请求格式错误'}), 400
    new_username = data.get('username', '').strip()

    # 参数校验
    if not new_username:
        return jsonify({'success': False, 'error': '用户名不能为空'})

    if len(new_username) < 3 or len(new_username) > 20:
        return jsonify({'success': False, 'error': '用户名长度为3-20个字符'})

    # 检查是否与当前用户名相同
    if new_username == current_user.username:
        return jsonify({'success': False, 'error': '新用户名与当前相同'})

    # 检查用户名是否已被占用
    existing = User.query.filter_by(username=new_username).first()
    if existing:
        return jsonify({'success': False, 'error': '用户名已被占用'})

    # 更新用户名
    current_user.username = new_username
    db.session.commit()
    return jsonify({'success': True, 'message': '用户名修改成功', 'username': new_username})


@user_bp.route('/api/user/delete-account', methods=['DELETE'])
@login_required
def delete_account():
    """
    注销账号

    路由: DELETE /api/user/delete-account
    需要登录: 是

    处理流程:
    1. 检查是否为管理员（管理员不能注销）
    2. 删除用户账号
    3. ORM级联删除所有关联数据（访谈、量表、类型学、访问日志）

    返回数据:
    成功: {"success": true, "message": "账号已注销"}
    失败: {"success": false, "error": "错误信息"}

    安全设计:
    - 管理员账号不能注销，防止误操作
    - 前端需要二次确认才能执行注销
    - 删除操作不可逆，所有数据将被永久删除

    级联删除:
    - interview_sessions: 用户的所有访谈记录
    - scale_results: 用户的所有量表结果
    - talent_type_results: 用户的所有类型学结果
    - visit_logs: 用户的所有访问日志
    """
    # 管理员不能注销
    if current_user.is_admin:
        return jsonify({'success': False, 'error': '管理员账号不能注销'}), 400

    # 删除用户（ORM级联删除所有关联数据）
    db.session.delete(current_user)
    db.session.commit()
    return jsonify({'success': True, 'message': '账号已注销'})
