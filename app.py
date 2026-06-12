from dotenv import load_dotenv
# 必须在导入 config 之前加载环境变量
load_dotenv()

import os
import logging
from flask import Flask, jsonify, render_template
from config import Config
from models import db
from flask_login import LoginManager

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

# 创建 Flask 应用实例
app = Flask(__name__)
app.config.from_object(Config)

# 初始化数据库
db.init_app(app)

# 初始化 Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'
login_manager.login_message = '请先登录'

@login_manager.user_loader
def load_user(user_id):
    from models import User
    return db.session.get(User, int(user_id))

# 注册 Blueprint
from routes import main_bp, interview_bp, scale_bp, dictionary_bp, talent_type_bp, history_bp, admin_bp, profile_bp, user_bp
from routes.auth import auth_bp
from routes.admin import is_admin

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

# 注入 is_admin 到 Jinja2 模板
app.jinja_env.globals['is_admin'] = is_admin

# 访问日志缓冲区（批量写入优化，线程安全）
import threading
_visit_buffer = []
_visit_lock = threading.Lock()
_VISIT_FLUSH_SIZE = 50  # 累积 50 条后 flush


def _flush_visit_buffer():
    """将缓冲区的访问日志批量写入数据库"""
    with _visit_lock:
        if not _visit_buffer:
            return
        # 复制缓冲区并清空，避免长时间持锁
        batch = list(_visit_buffer)
        _visit_buffer.clear()

    from models import VisitLog, db
    try:
        with app.app_context():
            db.session.add_all([VisitLog(**v) for v in batch])
            db.session.commit()
    except Exception:
        db.session.rollback()
        # 失败时将数据放回缓冲区等待重试
        with _visit_lock:
            _visit_buffer.extend(batch)


# 应用关闭时 flush 缓冲区
import atexit
atexit.register(_flush_visit_buffer)


# 全局错误处理器
@app.errorhandler(404)
def not_found(error):
    from flask import request
    if request.path.startswith('/api/'):
        return jsonify({"success": False, "error": "资源不存在"}), 404
    return render_template('errors/404.html'), 404


@app.errorhandler(500)
def internal_error(error):
    from flask import request
    db.session.rollback()
    if request.path.startswith('/api/'):
        return jsonify({"success": False, "error": "服务器内部错误"}), 500
    return render_template('errors/500.html'), 500

# 访问追踪（仅记录页面访问，跳过 API/AJAX 请求，批量写入）
@app.before_request
def track_visit():
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

    _visit_buffer.append({
        'path': path,
        'module': module,
        'user_id': current_user.id if current_user.is_authenticated else None,
        'ip_address': request.remote_addr
    })

    # 累积到阈值后批量写入
    if len(_visit_buffer) >= _VISIT_FLUSH_SIZE:
        _flush_visit_buffer()

# 数据库初始化（创建表 + 导入词典数据）
with app.app_context():
    db.create_all()

    # 兼容性处理：为旧表添加 user_id 列
    from sqlalchemy import text
    from sqlalchemy.inspection import inspect
    inspector = inspect(db.engine)
    for tbl in ['scale_results', 'talent_type_results']:
        cols = [c['name'] for c in inspector.get_columns(tbl)]
        if 'user_id' not in cols:
            with db.engine.connect() as conn:
                conn.execute(text(f"ALTER TABLE {tbl} ADD COLUMN user_id INTEGER"))
                conn.commit()

    # 兼容性处理：为旧 interview_sessions 表添加 share_token 列
    iv_cols = [c['name'] for c in inspector.get_columns('interview_sessions')]
    if 'share_token' not in iv_cols:
        with db.engine.connect() as conn:
            conn.execute(text("ALTER TABLE interview_sessions ADD COLUMN share_token VARCHAR(64)"))
            conn.commit()

    # 兼容性处理：为旧 users 表添加 is_admin 列
    user_cols = [c['name'] for c in inspector.get_columns('users')]
    if 'is_admin' not in user_cols:
        with db.engine.connect() as conn:
            conn.execute(text("ALTER TABLE users ADD COLUMN is_admin BOOLEAN DEFAULT 0"))
            conn.commit()
        # 将 op 用户标记为管理员
        from models import User
        op_user = User.query.filter_by(username='op').first()
        if op_user:
            op_user.is_admin = True
            db.session.commit()

    # 确保 op 管理员账号存在
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

    from routes.dictionary import init_dictionary
    init_dictionary()


if __name__ == '__main__':
    app.run(debug=Config.DEBUG, host=Config.HOST, port=Config.PORT)