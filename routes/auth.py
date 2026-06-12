"""
routes/auth.py — 用户认证路由模块

本模块实现了用户的注册、登录、登出和登录状态检查功能，是系统安全的基础模块。

功能概览：
1. 用户注册 — 创建新用户账号，密码哈希存储，自动登录
2. 用户登录 — 验证用户名密码，创建用户会话，区分普通用户和管理员
3. 用户登出 — 清除用户会话，仅接受 POST 请求防止 CSRF 攻击
4. 登录状态检查 — 供前端异步检查当前用户的登录状态

安全设计：
┌─────────────────────────────────────────────────────────────┐
│  密码安全                                                     │
│  - 使用 werkzeug.security.generate_password_hash() 生成哈希   │
│  - 哈希算法：PBKDF2-SHA256，包含随机盐值                      │
│  - 即使数据库泄露，攻击者也无法直接获取明文密码                │
├─────────────────────────────────────────────────────────────┤
│  开放重定向防护                                               │
│  - _safe_redirect() 函数验证重定向目标                        │
│  - 只允许相对路径（同源重定向），拒绝绝对URL                   │
│  - 防止攻击者通过 ?next=evil.com 窃取用户凭证                 │
├─────────────────────────────────────────────────────────────┤
│  CSRF 防护                                                    │
│  - 登出接口仅接受 POST 请求                                   │
│  - 防止通过 GET 请求触发登出的 CSRF 攻击                      │
├─────────────────────────────────────────────────────────────┤
│  输入验证                                                     │
│  - 用户名：3-20个字符，唯一性检查                             │
│  - 密码：至少6位                                              │
│  - 前后端双重验证                                             │
└─────────────────────────────────────────────────────────────┘

路由清单：
- GET  /register      — 注册页面
- POST /register      — 提交注册
- GET  /login         — 登录页面
- POST /login         — 提交登录
- POST /logout        — 登出
- GET  /api/auth/check — 检查登录状态（JSON）

依赖：
- flask_login: 提供 login_user, logout_user, login_required, current_user
- werkzeug.security: 提供密码哈希功能（在 models.py 中使用）
"""

from urllib.parse import urlparse
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from models import db, User

# 创建认证模块的 Blueprint
# 所有认证相关的路由都挂载在这个 Blueprint 下
auth_bp = Blueprint('auth', __name__)


def _safe_redirect(target):
    """
    验证重定向目标，防止开放重定向攻击

    参数:
        target: 用户请求的重定向目标URL
    返回:
        验证通过的重定向URL，或首页URL

    安全说明:
        开放重定向是一种常见的Web安全漏洞。攻击者构造如下链接：
        https://example.com/login?next=https://evil.com
        用户登录后会被重定向到恶意网站，可能泄露凭证。

        本函数通过 urlparse 解析目标URL，只允许相对路径（同源重定向），
        拒绝包含 netloc（域名）或 scheme（协议）的绝对URL。
    """
    if not target:
        return url_for('main.index')
    parsed = urlparse(target)
    # 仅允许相对路径（同源重定向）
    if parsed.netloc or parsed.scheme:
        return url_for('main.index')
    return target


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """
    用户注册

    路由: GET/POST /register
    需要登录: 否（已登录用户自动跳转到首页）

    GET 请求:
        渲染注册页面模板

    POST 请求:
        处理注册表单提交，流程如下：
        1. 验证用户名和密码不为空
        2. 验证用户名长度（3-20个字符）
        3. 验证密码长度（至少6位）
        4. 验证两次密码输入一致
        5. 检查用户名是否已被注册
        6. 创建用户（密码哈希存储）
        7. 自动登录新用户
        8. 跳转到首页或之前的页面

    表单字段:
        - username: 用户名（3-20个字符）
        - password: 密码（至少6位）
        - confirm: 确认密码

    Flash 消息:
        - 'error': 各种验证失败的错误提示
    """
    # 已登录用户自动跳转到首页
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        # 获取表单数据
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        confirm = request.form.get('confirm', '')

        # 参数校验：用户名和密码不能为空
        if not username or not password:
            flash('用户名和密码不能为空', 'error')
            return redirect(url_for('auth.register'))

        # 参数校验：用户名长度
        if len(username) < 3 or len(username) > 20:
            flash('用户名长度为3-20个字符', 'error')
            return redirect(url_for('auth.register'))

        # 参数校验：密码长度
        if len(password) < 6:
            flash('密码长度至少6位', 'error')
            return redirect(url_for('auth.register'))

        # 参数校验：密码一致性
        if password != confirm:
            flash('两次输入的密码不一致', 'error')
            return redirect(url_for('auth.register'))

        # 业务校验：用户名唯一性
        if User.query.filter_by(username=username).first():
            flash('用户名已被注册', 'error')
            return redirect(url_for('auth.register'))

        # 创建用户账号
        # set_password() 方法使用 werkzeug 生成密码哈希
        user = User(username=username)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        # 注册成功后自动登录
        login_user(user)

        # 跳转到登录前的页面（如果有）或首页
        # 使用 _safe_redirect 防止开放重定向
        next_page = _safe_redirect(request.args.get('next'))
        return redirect(next_page)

    # GET 请求：渲染注册页面
    return render_template('register.html')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """
    用户登录

    路由: GET/POST /login
    需要登录: 否（已登录用户自动跳转到首页）

    GET 请求:
        渲染登录页面模板

    POST 请求:
        处理登录表单提交，流程如下：
        1. 验证用户名和密码不为空
        2. 查询用户是否存在
        3. 验证密码是否正确
        4. 创建用户会话
        5. 管理员跳转到管理后台，普通用户跳转到首页

    表单字段:
        - username: 用户名
        - password: 密码

    安全设计:
        - 登录失败时提示"用户名或密码错误"，不区分具体原因
        - 防止攻击者通过错误提示枚举有效用户名
    """
    # 已登录用户自动跳转到首页
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        # 获取表单数据
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        # 参数校验
        if not username or not password:
            flash('请输入用户名和密码', 'error')
            return redirect(url_for('auth.login'))

        # 查询用户并验证密码
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            # 登录成功
            login_user(user)

            # 管理员直接跳转到管理后台
            if user.is_admin:
                return redirect(url_for('admin.dashboard'))

            # 普通用户跳转到之前的页面或首页
            next_page = _safe_redirect(request.args.get('next'))
            return redirect(next_page)
        else:
            # 登录失败：统一提示，不区分用户名不存在还是密码错误
            flash('用户名或密码错误', 'error')
            return redirect(url_for('auth.login'))

    # GET 请求：渲染登录页面
    return render_template('login.html')


@auth_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    """
    用户登出

    路由: POST /logout
    需要登录: 是

    说明:
        清除用户的登录会话，跳转到首页。
        仅接受 POST 请求，防止通过 GET 请求触发登出的 CSRF 攻击。

        前端通过表单提交实现登出：
        <form method="POST" action="/logout">
            <button type="submit">退出</button>
        </form>
    """
    logout_user()
    return redirect(url_for('main.index'))


@auth_bp.route('/api/auth/check')
def auth_check():
    """
    前端检查当前登录状态

    路由: GET /api/auth/check
    需要登录: 否

    用途:
        前端JavaScript通过此接口异步检查用户的登录状态，
        用于实现：
        - 开始访谈前检查是否已登录
        - 导航栏显示用户名或登录按钮
        - 权限控制（如显示/隐藏管理后台入口）

    返回数据:
    {
        "authenticated": true,   // 是否已登录
        "username": "testuser"   // 用户名（未登录时为 null）
    }
    """
    return jsonify({
        "authenticated": current_user.is_authenticated,
        "username": current_user.username if current_user.is_authenticated else None
    })
