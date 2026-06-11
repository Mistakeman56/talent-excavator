from dotenv import load_dotenv
# 必须在导入 config 之前加载环境变量
load_dotenv()

import os
import logging
from flask import Flask
from config import Config
from models import db
from flask_login import LoginManager

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

# 创建 Flask 应用实例
app = Flask(__name__)
app.config.from_object(Config)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///talent_assessment.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

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
from routes import main_bp, interview_bp, scale_bp, dictionary_bp, talent_type_bp, history_bp, admin_bp
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

# 注入 is_admin 到 Jinja2 模板
app.jinja_env.globals['is_admin'] = is_admin

# 访问追踪（仅记录页面访问，跳过 API/AJAX 请求）
@app.before_request
def track_visit():
    from flask import request
    from flask_login import current_user
    from models import VisitLog

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

    visit = VisitLog(
        path=path,
        module=module,
        user_id=current_user.id if current_user.is_authenticated else None,
        ip_address=request.remote_addr
    )
    db.session.add(visit)
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()

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

    # 兼容性处理：为旧 users 表添加 is_admin 列
    user_cols = [c['name'] for c in inspector.get_columns('users')]
    if 'is_admin' not in user_cols:
        with db.engine.connect() as conn:
            conn.execute(text("ALTER TABLE users ADD COLUMN is_admin BOOLEAN DEFAULT 0"))
            conn.commit()
        # 将原 admin 用户标记为管理员
        from models import User
        admin_user = User.query.filter_by(username='admin').first()
        if admin_user:
            admin_user.is_admin = True
            db.session.commit()

    from routes.dictionary import init_dictionary
    init_dictionary()


if __name__ == '__main__':
    debug = os.getenv('FLASK_DEBUG', 'false').lower() == 'true'
    app.run(debug=debug, host='0.0.0.0', port=5001)