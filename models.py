from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

class ScaleResult(db.Model):
    """量表答题结果"""
    __tablename__ = 'scale_results'
    
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(64), nullable=False)
    scale_type = db.Column(db.String(20), nullable=False)  # 'primary' 或 'secondary'
    answers = db.Column(db.Text, nullable=False)  # JSON格式存储答题结果
    scores = db.Column(db.Text, nullable=False)   # JSON格式存储各维度得分
    top_dimensions = db.Column(db.Text)  # JSON格式存储Top维度
    talent_type = db.Column(db.String(100))  # 二级量表锁定的天赋类型
    created_at = db.Column(db.DateTime, default=datetime.now)

class User(UserMixin, db.Model):
    """用户账户"""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class UserProfile(db.Model):
    """用户背景信息（用于关联性分析）"""
    __tablename__ = 'user_profiles'
    
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(64), nullable=False, unique=True)
    age = db.Column(db.Integer)
    gender = db.Column(db.String(10))
    city_type = db.Column(db.String(20))  # 城市/农村/小镇
    education = db.Column(db.String(20))
    major = db.Column(db.String(50))
    parent_style = db.Column(db.String(20))  # 权威/放任/忽视
    only_child = db.Column(db.Boolean)
    mbti = db.Column(db.String(10))
    created_at = db.Column(db.DateTime, default=datetime.now)

class HumanDictionary(db.Model):
    """Human词典词条"""
    __tablename__ = 'human_dictionary'
    
    id = db.Column(db.Integer, primary_key=True)
    term = db.Column(db.String(100), nullable=False, unique=True)
    category = db.Column(db.String(50), nullable=False)
    definition = db.Column(db.Text, nullable=False)
    example = db.Column(db.Text)
    related_terms = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.now)


class InterviewSession(db.Model):
    """AI访谈会话（服务端持久化，替代session存messages）"""
    __tablename__ = 'interview_sessions'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    messages = db.Column(db.Text, default='[]')           # JSON序列化对话历史
    stage = db.Column(db.Integer, default=0)              # 当前方向索引 0-7（对应A-H）
    answers = db.Column(db.Text, default='{}')            # JSON，结构化存储各方向用户回答
    report_content = db.Column(db.Text)                   # 最终生成的报告Markdown
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
