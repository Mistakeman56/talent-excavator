from dotenv import load_dotenv
# 必须在导入 config 之前加载环境变量
load_dotenv()

from flask import Flask
from config import Config
from models import db
from flask_login import LoginManager

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
    return User.query.get(int(user_id))

# 注册 Blueprint
from routes import main_bp, interview_bp, scale_bp, dictionary_bp, talent_type_bp
from routes.auth import auth_bp

app.register_blueprint(main_bp)
app.register_blueprint(interview_bp)
app.register_blueprint(scale_bp)
app.register_blueprint(dictionary_bp)
app.register_blueprint(talent_type_bp)
app.register_blueprint(auth_bp)

# 数据库初始化（创建表 + 导入词典数据）
with app.app_context():
    db.create_all()
    from routes.dictionary import init_dictionary
    init_dictionary()


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)