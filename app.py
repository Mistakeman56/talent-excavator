"""
app.py — Flask 应用主入口

本文件是整个"个人天赋发掘测评系统"的核心启动文件，负责：
1. 创建 Flask 应用实例并加载配置
2. 初始化数据库 ORM（SQLAlchemy）
3. 初始化用户认证系统（Flask-Login）
4. 注册所有路由模块（Blueprint）
5. 实现访问日志的批量写入优化
6. 定义全局错误处理器
7. 自动创建数据库表并执行兼容性迁移
8. 初始化管理员账号和词典数据

启动方式：python app.py
默认监听：http://0.0.0.0:5001
"""

# ============================================================
# 第一步：加载环境变量
# ============================================================
# 必须在导入 config 之前调用 load_dotenv()，否则 config.py 读不到 .env 中的密钥
from dotenv import load_dotenv
load_dotenv()

# ============================================================
# 第二步：导入基础依赖
# ============================================================
import os
import logging
from flask import Flask, jsonify, render_template
from config import Config          # 应用配置类（从环境变量读取）
from models import db              # SQLAlchemy 数据库实例
from flask_login import LoginManager

# ============================================================
# 第三步：配置日志系统
# ============================================================
# 使用 Python 标准 logging 模块，输出格式：时间 [级别] 消息
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

# ============================================================
# 第四步：创建 Flask 应用实例
# ============================================================
# Flask 应用是整个 Web 服务的核心对象，所有路由、中间件、配置都挂载在它上面
app = Flask(__name__)
app.config.from_object(Config)  # 从 Config 类加载所有配置项

# ============================================================
# 第五步：初始化数据库
# ============================================================
# SQLAlchemy 是 Python 最流行的 ORM 框架，将数据库表映射为 Python 类
# db.init_app(app) 将数据库实例绑定到 Flask 应用，之后可以通过 db.session 操作数据库
db.init_app(app)

# ============================================================
# 第六步：初始化用户认证系统（Flask-Login）
# ============================================================
# Flask-Login 提供用户登录/登出/session 管理功能
# 它会自动从 cookie 中读取用户 ID，并调用 user_loader 回调函数加载用户对象
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'       # 未登录时自动跳转到登录页
login_manager.login_message = '请先登录'        # 跳转时显示的提示消息

@login_manager.user_loader
def load_user(user_id):
    """
    Flask-Login 的用户加载回调函数

    当用户访问需要登录的页面时，Flask-Login 会从 session 中取出 user_id，
    然后调用此函数加载完整的用户对象。这个函数返回的对象会赋值给 current_user。

    参数:
        user_id: 用户ID（字符串形式的整数）
    返回:
        User 对象，如果用户不存在则返回 None
    """
    from models import User
    return db.session.get(User, int(user_id))

# ============================================================
# 第七步：注册所有路由模块（Blueprint）
# ============================================================
# Blueprint 是 Flask 的模块化路由机制，将不同功能的路由分组到不同文件中
# 这样可以避免所有路由都写在一个文件里，便于维护和扩展
#
# 本系统的路由模块：
# - main_bp:       主页、报告展示页、天赋类型学页面入口
# - interview_bp:  AI 访谈 API（开始、聊天、生成报告、重置）
# - scale_bp:      量表 API（获取题目、提交答案、二级量表、结果查询）
# - dictionary_bp: 词典 API（列表查询、分类筛选、单条详情）
# - talent_type_bp:天赋类型学 API（获取题目、提交答案、查询结果、图鉴）
# - auth_bp:       认证路由（注册、登录、登出、登录状态检查）
# - history_bp:    历史记录 API（汇总三种测评结果、详情查询）
# - admin_bp:      管理后台 API（统计数据、用户管理、记录管理）
# - profile_bp:    个人天赋档案（整合三种测评结果，跨测评交叉分析）
# - user_bp:       用户个人中心（修改密码、查看统计、账号注销）
from routes import main_bp, interview_bp, scale_bp, dictionary_bp, talent_type_bp, history_bp, admin_bp, profile_bp, user_bp
from routes.auth import auth_bp
from routes.admin import is_admin

# 将所有 Blueprint 注册到 Flask 应用
# 注册后，这些路由才会生效，用户才能通过 URL 访问对应的页面和 API
app.register_blueprint(main_bp)
app.register_blueprint(interview_bp)
app.register_blueprint(scale_bp)
app.register_blueprint(dictionary_bp)
app.register_blueprint(talent_type_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(history_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(profile_bp)
app.register_blueprint(user_bp)

# ============================================================
# 第八步：注入模板全局变量
# ============================================================
# 将 is_admin 函数注入到 Jinja2 模板引擎中
# 这样在 HTML 模板中可以直接调用 is_admin() 来判断当前用户是否为管理员
# 例如：{% if is_admin() %}显示管理后台链接{% endif %}
app.jinja_env.globals['is_admin'] = is_admin

# ============================================================
# 第九步：访问日志批量写入机制
# ============================================================
# 设计思路：
# - 每次页面访问都写数据库会造成频繁的磁盘 I/O，影响性能
# - 因此使用"内存缓冲 + 批量写入"的策略：先将访问记录存在内存列表中
# - 当累积到 50 条时，一次性写入数据库
# - 使用 threading.Lock 保证多线程安全
#
# 缓冲区数据结构示例：
# [
#     {'path': '/', 'module': 'main', 'user_id': 1, 'ip_address': '127.0.0.1'},
#     {'path': '/scale', 'module': 'scale', 'user_id': None, 'ip_address': '192.168.1.1'},
#     ...
# ]
import threading
_visit_buffer = []           # 内存缓冲区，存储待写入的访问记录
_visit_lock = threading.Lock()  # 线程锁，防止多线程同时修改缓冲区导致数据错乱
_VISIT_FLUSH_SIZE = 50       # 批量写入阈值：累积 50 条后 flush 到数据库


def _flush_visit_buffer():
    """
    将缓冲区的访问日志批量写入数据库

    工作流程：
    1. 加锁，复制缓冲区内容，然后清空缓冲区（避免长时间持锁）
    2. 解锁后，将复制的数据批量插入数据库
    3. 如果插入失败，将数据放回缓冲区等待下次重试

    这种"复制-清空-写入"的模式可以最小化锁的持有时间，提高并发性能
    """
    with _visit_lock:
        if not _visit_buffer:
            return
        # 复制缓冲区并清空，避免长时间持锁
        batch = list(_visit_buffer)
        _visit_buffer.clear()

    from models import VisitLog, db
    try:
        with app.app_context():
            # 使用 add_all 批量插入，比逐条 insert 高效得多
            db.session.add_all([VisitLog(**v) for v in batch])
            db.session.commit()
    except Exception:
        db.session.rollback()
        # 失败时将数据放回缓冲区等待重试
        with _visit_lock:
            _visit_buffer.extend(batch)


# 应用关闭时 flush 缓冲区，确保不丢失数据
# atexit.register() 注册的函数会在 Python 进程正常退出时调用
import atexit
atexit.register(_flush_visit_buffer)


# ============================================================
# 第十步：全局错误处理器
# ============================================================
# Flask 允许自定义错误页面，提升用户体验
# API 请求返回 JSON 格式的错误信息，页面请求返回友好的错误页面
@app.errorhandler(404)
def not_found(error):
    """
    404 错误处理器 — 资源不存在

    判断逻辑：
    - 如果请求路径以 /api/ 开头，说明是 API 请求，返回 JSON 格式的错误
    - 否则说明是页面请求，返回友好的 404 错误页面
    """
    from flask import request
    if request.path.startswith('/api/'):
        return jsonify({"success": False, "error": "资源不存在"}), 404
    return render_template('errors/404.html'), 404


@app.errorhandler(500)
def internal_error(error):
    """
    500 错误处理器 — 服务器内部错误

    注意：500 错误通常是数据库异常导致的，所以先调用 db.session.rollback()
    回滚当前事务，否则后续的数据库操作会继续失败
    """
    from flask import request
    db.session.rollback()  # 回滚失败的数据库事务
    if request.path.startswith('/api/'):
        return jsonify({"success": False, "error": "服务器内部错误"}), 500
    return render_template('errors/500.html'), 500

# ============================================================
# 第十一步：访问追踪中间件
# ============================================================
# @app.before_request 装饰器注册的函数会在每次请求前自动执行
# 用于记录用户的页面访问行为，供管理后台统计分析
@app.before_request
def track_visit():
    """
    访问追踪中间件 — 记录用户的页面访问行为

    过滤规则（只记录有价值的访问）：
    - 跳过静态资源（CSS/JS/图片）和 favicon
    - 跳过所有 /api/ 接口请求（避免记录 AJAX 轮询）
    - 跳过管理后台 API
    - 只记录 GET 请求（页面访问），跳过 POST/PUT/DELETE 等操作请求

    记录的信息：
    - path: 访问的页面路径
    - module: 所属模块（main/scale/talent_type/dictionary/profile/other）
    - user_id: 用户ID（未登录为 None）
    - ip_address: 用户IP地址
    """
    from flask import request
    from flask_login import current_user

    path = request.path
    # 跳过静态资源、favicon、管理后台 API、以及所有 /api/ 接口请求
    if (path.startswith('/static') or path == '/favicon.ico'
            or path.startswith('/admin/api') or path.startswith('/api/')):
        return

    # 仅记录页面级别的 GET 请求（排除 AJAX 轮询）
    if request.method != 'GET':
        return

    # 根据路径判断所属模块
    module = 'other'
    if path in ('/', '/report'):
        module = 'main'
    elif path.startswith('/interview'):
        module = 'interview'
    elif path.startswith('/scale'):
        module = 'scale'
    elif path.startswith('/talent-type'):
        module = 'talent_type'
    elif path.startswith('/dictionary'):
        module = 'dictionary'
    elif path.startswith('/profile'):
        module = 'profile'

    # 将访问记录添加到缓冲区
    _visit_buffer.append({
        'path': path,
        'module': module,
        'user_id': current_user.id if current_user.is_authenticated else None,
        'ip_address': request.remote_addr
    })

    # 累积到阈值后批量写入
    if len(_visit_buffer) >= _VISIT_FLUSH_SIZE:
        _flush_visit_buffer()

# ============================================================
# 第十二步：数据库初始化
# ============================================================
# 这段代码在应用启动时自动执行，完成以下工作：
# 1. 创建所有数据库表（如果不存在）
# 2. 执行兼容性迁移（为旧表添加新字段）
# 3. 创建默认管理员账号
# 4. 导入 Human 词典数据
with app.app_context():
    # 创建所有表（根据 models.py 中定义的模型类）
    db.create_all()

    # ----------------------------------------------------------
    # 兼容性处理：为旧表添加新字段
    # ----------------------------------------------------------
    # 这些 ALTER TABLE 语句用于在不丢失数据的情况下为旧数据库表添加新字段
    # 只有当字段不存在时才会执行，所以重复运行是安全的
    # 注意：这不是正式的数据库迁移方案（如 Alembic），只是轻量级兼容处理
    from sqlalchemy import text
    from sqlalchemy.inspection import inspect
    inspector = inspect(db.engine)

    # 为量表结果表和天赋类型学结果表添加 user_id 外键字段
    # 这个字段用于关联到 users 表，实现"每个用户只能看到自己的测评结果"
    for tbl in ['scale_results', 'talent_type_results']:
        cols = [c['name'] for c in inspector.get_columns(tbl)]
        if 'user_id' not in cols:
            with db.engine.connect() as conn:
                conn.execute(text(f"ALTER TABLE {tbl} ADD COLUMN user_id INTEGER"))
                conn.commit()

    # 为访谈会话表添加 share_token 字段（用于生成分享链接）
    iv_cols = [c['name'] for c in inspector.get_columns('interview_sessions')]
    if 'share_token' not in iv_cols:
        with db.engine.connect() as conn:
            conn.execute(text("ALTER TABLE interview_sessions ADD COLUMN share_token VARCHAR(64)"))
            conn.commit()

    # 为用户表添加 is_admin 管理员标识字段
    user_cols = [c['name'] for c in inspector.get_columns('users')]
    if 'is_admin' not in user_cols:
        with db.engine.connect() as conn:
            conn.execute(text("ALTER TABLE users ADD COLUMN is_admin BOOLEAN DEFAULT 0"))
            conn.commit()
        # 将 op 用户标记为管理员（兼容旧数据）
        from models import User
        op_user = User.query.filter_by(username='op').first()
        if op_user:
            op_user.is_admin = True
            db.session.commit()

    # ----------------------------------------------------------
    # 确保默认管理员账号存在
    # ----------------------------------------------------------
    # 管理员账号：op，密码：323328
    # 如果账号不存在则创建，如果存在但不是管理员则升级为管理员
    from models import User
    from werkzeug.security import generate_password_hash
    op_user = User.query.filter_by(username='op').first()
    if not op_user:
        op_user = User(
            username='op',
            password_hash=generate_password_hash('323328'),
            is_admin=True
        )
        db.session.add(op_user)
        db.session.commit()
        logging.info('已创建管理员账号: op')
    elif not op_user.is_admin:
        op_user.is_admin = True
        db.session.commit()

    # ----------------------------------------------------------
    # 导入 Human 词典数据
    # ----------------------------------------------------------
    # 首次启动时自动从 dictionary_data.py 导入词典词条到数据库
    # 如果表中已有数据则跳过，不会重复导入
    from routes.dictionary import init_dictionary
    init_dictionary()


# ============================================================
# 第十三步：启动开发服务器
# ============================================================
# 只有直接运行 python app.py 时才会启动服务器
# 如果是被其他模块导入（如 gunicorn），则不会执行这段代码
if __name__ == '__main__':
    app.run(debug=Config.DEBUG, host=Config.HOST, port=Config.PORT)
