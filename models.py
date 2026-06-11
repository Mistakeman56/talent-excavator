from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from datetime import datetime, timezone

db = SQLAlchemy()

class TalentTypeResult(db.Model):
    """天赋类型学测评结果（类似MBTI的4字母代码）"""
    __tablename__ = 'talent_type_results'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, index=True)
    session_id = db.Column(db.String(64), nullable=False, index=True)
    type_code = db.Column(db.String(4), nullable=False)  # 如 "CDAM"
    answers = db.Column(db.Text, nullable=False)  # JSON: {"t1": "a", ...}
    scores = db.Column(db.Text, nullable=False)   # JSON: 各维度原始得分
    dimensions = db.Column(db.Text, nullable=False)  # JSON: 四维度详情
    report = db.Column(db.Text, nullable=False)  # JSON: 完整解读报告
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))


class ScaleResult(db.Model):
    """量表答题结果"""
    __tablename__ = 'scale_results'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, index=True)
    session_id = db.Column(db.String(64), nullable=False)
    scale_type = db.Column(db.String(20), nullable=False)  # 'primary' 或 'secondary'
    answers = db.Column(db.Text, nullable=False)  # JSON格式存储答题结果
    scores = db.Column(db.Text, nullable=False)   # JSON格式存储各维度得分
    top_dimensions = db.Column(db.Text)  # JSON格式存储Top维度
    talent_type = db.Column(db.String(100))  # 二级量表锁定的天赋类型
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

class User(UserMixin, db.Model):
    """用户账户"""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # 关联关系（级联删除）
    interviews = db.relationship('InterviewSession', backref='user', lazy='dynamic',
                                 cascade='all, delete-orphan')
    scale_results = db.relationship('ScaleResult', backref='user', lazy='dynamic',
                                    cascade='all, delete-orphan')
    talent_type_results = db.relationship('TalentTypeResult', backref='user', lazy='dynamic',
                                          cascade='all, delete-orphan')
    visit_logs = db.relationship('VisitLog', backref='user', lazy='dynamic',
                                 cascade='all, delete-orphan')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class HumanDictionary(db.Model):
    """Human词典词条"""
    __tablename__ = 'human_dictionary'
    
    id = db.Column(db.Integer, primary_key=True)
    term = db.Column(db.String(100), nullable=False, unique=True)
    category = db.Column(db.String(50), nullable=False)
    definition = db.Column(db.Text, nullable=False)
    example = db.Column(db.Text)
    related_terms = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))


class InterviewSession(db.Model):
    """AI访谈会话（服务端持久化，替代session存messages）"""
    __tablename__ = 'interview_sessions'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    messages = db.Column(db.Text, default='[]')           # JSON序列化对话历史
    stage = db.Column(db.Integer, default=0)              # 当前方向索引 0-7（对应A-H）
    answers = db.Column(db.Text, default='{}')            # JSON，结构化存储各方向用户回答
    report_content = db.Column(db.Text)                   # 最终生成的报告Markdown
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class VisitLog(db.Model):
    """访问日志（用于管理后台统计）"""
    __tablename__ = 'visit_logs'

    id = db.Column(db.Integer, primary_key=True)
    path = db.Column(db.String(256), nullable=False)
    module = db.Column(db.String(32), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), index=True)