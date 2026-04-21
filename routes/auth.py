from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from models import db, User

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """用户注册"""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        confirm = request.form.get('confirm', '')

        # 简单校验
        if not username or not password:
            flash('用户名和密码不能为空', 'error')
            return redirect(url_for('auth.register'))

        if len(username) < 3 or len(username) > 20:
            flash('用户名长度为3-20个字符', 'error')
            return redirect(url_for('auth.register'))

        if len(password) < 6:
            flash('密码长度至少6位', 'error')
            return redirect(url_for('auth.register'))

        if password != confirm:
            flash('两次输入的密码不一致', 'error')
            return redirect(url_for('auth.register'))

        # 检查用户名是否已存在
        if User.query.filter_by(username=username).first():
            flash('用户名已被注册', 'error')
            return redirect(url_for('auth.register'))

        # 创建用户
        user = User(username=username)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        # 自动登录
        login_user(user)
        next_page = request.args.get('next') or url_for('main.index')
        return redirect(next_page)

    return render_template('register.html')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """用户登录"""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        if not username or not password:
            flash('请输入用户名和密码', 'error')
            return redirect(url_for('auth.login'))

        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            next_page = request.args.get('next') or url_for('main.index')
            return redirect(next_page)
        else:
            flash('用户名或密码错误', 'error')
            return redirect(url_for('auth.login'))

    return render_template('login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    """用户登出"""
    logout_user()
    return redirect(url_for('main.index'))


@auth_bp.route('/api/auth/check')
def auth_check():
    """前端检查当前登录状态"""
    return jsonify({
        "authenticated": current_user.is_authenticated,
        "username": current_user.username if current_user.is_authenticated else None
    })
