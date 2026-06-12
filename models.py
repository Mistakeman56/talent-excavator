"""
models.py — 数据库模型定义

本文件定义了系统中所有的数据库表结构，使用 SQLAlchemy ORM 将 Python 类映射为数据库表。
每个类对应一张数据库表，类的属性对应表的字段。

数据库：SQLite（文件存储在 instance/talent_assessment.db）

表结构概览：
┌─────────────────────┬───────────────────────────────────────────────┐
│ 表名                 │ 说明                                          │
├─────────────────────┼───────────────────────────────────────────────┤
│ users               │ 用户账户表（存储用户名、密码哈希、管理员标识）│
│ interview_sessions  │ AI访谈会话表（存储对话历史、阶段、报告）      │
│ scale_results       │ 量表测评结果表（存储答题、得分、天赋类型）    │
│ talent_type_results │ 天赋类型学测评结果表（存储类型代码、解读报告）│
│ human_dictionary    │ Human词典词条表（存储术语、定义、示例）       │
│ visit_logs          │ 访问日志表（存储页面访问记录，用于统计分析）  │
└─────────────────────┴───────────────────────────────────────────────┘

外键关系：
- users.id ← interview_sessions.user_id（一个用户可以有多次访谈）
- users.id ← scale_results.user_id（一个用户可以有多次量表测评）
- users.id ← talent_type_results.user_id（一个用户可以有多次类型学测评）
- users.id ← visit_logs.user_id（一个用户可以有多条访问记录）

级联删除规则：
- 删除用户时，自动删除该用户的所有测评记录和访问日志
"""

from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from datetime import datetime, timezone

# 创建 SQLAlchemy 数据库实例
# 这个实例是全局唯一的，所有模型类都继承自它
# 在 app.py 中通过 db.init_app(app) 绑定到 Flask 应用
db = SQLAlchemy()


# ============================================================
# 模型 1：天赋类型学测评结果
# ============================================================
# 对应天赋类型学测评（40道情境迫选题）的答题结果
# 每次完成测评会生成一条记录，包含：4字母类型代码、各维度得分、完整解读报告
class TalentTypeResult(db.Model):
    """
    天赋类型学测评结果表

    存储用户完成"40题情境迫选测评"后的结果。
    每条记录代表一次完整的测评，包含：
    - type_code: 4字母类型代码（如 "CDAM"），代表用户的天赋类型
    - answers: 用户的原始答题数据（JSON格式，如 {"t1": "a", "t2": "c", ...}）
    - scores: 各维度的原始得分（JSON格式）
    - dimensions: 四维度的详细信息（JSON格式）
    - report: 完整的解读报告（JSON格式，包含类型名称、标语、各维度解读）

    类型代码的4个字母分别代表：
    - 第1位：天赋形态（C=认知洞察型, R=关系创造型, B=身体实践型, S=系统引领型）
    - 第2位：能量模式（D=深度专注型, R=快速响应型, V=多元探索型）
    - 第3位：驱动来源（A=成就驱动型, H=和谐驱动型）
    - 第4位：兴趣指向（M=机械系统型, C=概念抽象型, P=人物关系型）
    """
    __tablename__ = 'talent_type_results'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, index=True)  # 关联用户
    session_id = db.Column(db.String(64), nullable=False, index=True)  # 测评会话标识（UUID），用于前端查询
    type_code = db.Column(db.String(4), nullable=False)   # 4字母类型代码，如 "CDAM"
    answers = db.Column(db.Text, nullable=False)           # JSON: 用户原始答题数据 {"t1": "a", "t2": "c", ...}
    scores = db.Column(db.Text, nullable=False)            # JSON: 各维度原始得分 {"dim1": 8, "dim2": 5, ...}
    dimensions = db.Column(db.Text, nullable=False)        # JSON: 四维度详情 {"dim1": {"code": "C", "name": "认知洞察型", "desc": "..."}, ...}
    report = db.Column(db.Text, nullable=False)            # JSON: 完整解读报告 {"name": "认知架构师", "tagline": "...", "sections": [...]}
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))  # 测评时间


# ============================================================
# 模型 2：量表答题结果
# ============================================================
# 对应天赋维度筛查量表的答题结果
# 包括一级量表（20题，5维度）和二级量表（10题/维度，锁定具体天赋子类型）
class ScaleResult(db.Model):
    """
    量表答题结果表

    存储用户完成量表测评后的结果。支持两种类型的量表：
    1. 一级量表（scale_type='primary'）：
       - 20道题，覆盖5个天赋维度
       - 输出：各维度得分、Top维度排名
       - 用于初步筛查用户的天赋方向

    2. 二级量表（scale_type='secondary'）：
       - 10道题，针对某个天赋维度的子类型
       - 输出：具体的天赋子类型名称（如"系统架构师"、"模式侦探"等）
       - 用于在一级量表的基础上精准定位天赋

    字段说明：
    - session_id: 测评会话标识（UUID），前端通过这个ID查询结果
    - scale_type: 量表类型，'primary' 或 'secondary'
    - answers: 用户的原始答题数据
    - scores: 计算后的各维度得分
    - top_dimensions: 得分最高的前3个维度（仅一级量表有）
    - talent_type: 锁定的天赋类型名称（仅二级量表有）
    """
    __tablename__ = 'scale_results'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, index=True)  # 关联用户
    session_id = db.Column(db.String(64), nullable=False)      # 测评会话标识（UUID）
    scale_type = db.Column(db.String(20), nullable=False)      # 量表类型：'primary'（一级）或 'secondary'（二级）
    answers = db.Column(db.Text, nullable=False)               # JSON: 答题数据 {"q1": 4, "q2": 5, ...}
    scores = db.Column(db.Text, nullable=False)                # JSON: 各维度得分 {"cognitive": {"score": 4.2, ...}, ...}
    top_dimensions = db.Column(db.Text)                        # JSON: Top维度 [{"key": "cognitive", "name": "认知洞察型", "score": 4.2}, ...]
    talent_type = db.Column(db.String(100))                    # 二级量表锁定的天赋类型名称（如"系统架构师"）
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))  # 测评时间


# ============================================================
# 模型 3：用户账户
# ============================================================
# 继承 UserMixin 以获得 Flask-Login 所需的方法（is_authenticated, is_active 等）
class User(UserMixin, db.Model):
    """
    用户账户表

    存储用户的注册信息和认证数据。
    继承自 UserMixin，自动获得 Flask-Login 所需的接口方法。

    密码安全：
    - 密码不以明文存储，而是使用 werkzeug.security.generate_password_hash() 生成哈希值
    - 验证密码时使用 check_password_hash() 进行比较
    - 即使数据库泄露，攻击者也无法直接获取用户密码

    关联关系：
    - interviews: 该用户的所有AI访谈会话（一对多）
    - scale_results: 该用户的所有量表测评结果（一对多）
    - talent_type_results: 该用户的所有天赋类型学测评结果（一对多）
    - visit_logs: 该用户的所有访问日志（一对多）

    cascade='all, delete-orphan' 表示：
    - 删除用户时，自动删除所有关联的记录
    - 不会出现"孤儿记录"（即没有对应用户的测评结果）
    """
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)       # 用户名，唯一
    password_hash = db.Column(db.String(256), nullable=False)              # 密码哈希值（不是明文密码！）
    is_admin = db.Column(db.Boolean, default=False, nullable=False)        # 是否为管理员
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))  # 注册时间

    # 关联关系（级联删除）
    # lazy='dynamic' 表示返回的是查询对象而不是列表，可以进一步过滤和排序
    interviews = db.relationship('InterviewSession', backref='user', lazy='dynamic',
                                 cascade='all, delete-orphan')
    scale_results = db.relationship('ScaleResult', backref='user', lazy='dynamic',
                                    cascade='all, delete-orphan')
    talent_type_results = db.relationship('TalentTypeResult', backref='user', lazy='dynamic',
                                          cascade='all, delete-orphan')
    visit_logs = db.relationship('VisitLog', backref='user', lazy='dynamic',
                                 cascade='all, delete-orphan')

    def set_password(self, password):
        """
        设置用户密码（生成哈希值存储）

        参数:
            password: 明文密码字符串
        说明:
            使用 werkzeug 的 PBKDF2 算法生成密码哈希
            哈希值包含算法标识、盐值和哈希结果，格式类似：
            pbkdf2:sha256:260000$salt$hash
        """
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """
        验证用户密码

        参数:
            password: 用户输入的明文密码
        返回:
            True 如果密码正确，False 如果密码错误
        说明:
            从存储的哈希值中提取盐值，对输入密码进行同样的哈希运算，然后比较结果
        """
        return check_password_hash(self.password_hash, password)


# ============================================================
# 模型 4：Human 词典词条
# ============================================================
# 存储项目核心概念的解释，如"天赋类型"、"HUMAN 3.0"、"评估术语"等
# 首次启动时从 dictionary_data.py 自动导入
class HumanDictionary(db.Model):
    """
    Human词典词条表

    存储项目中使用的核心概念和术语解释。
    词典分为以下几个类别：
    - 天赋类型：认知运算型、创造表达型、社交协同型、系统驱动型、身体感知型
    - HUMAN 3.0：四象限模型、认知象限、身体象限、精神象限、职业象限等
    - 评估术语：无意识胜任区、伪擅长区、血氧区、纯粹兴趣等
    - 心理学概念：心流、盖洛普优势识别器、苏格拉底式提问等
    - 天赋应用：天赋映射、价值场景、高光时刻分析等
    - 成长方法：发展性反馈、最小可行验证、环境重设计等
    - AI相关：思维外包、假知道、Glitch、AI增强型天赋等

    首次启动时，app.py 会调用 init_dictionary() 从 dictionary_data.py 导入数据。
    如需更新词条，修改 dictionary_data.py 后删除数据库文件或清空表，重启即可。
    """
    __tablename__ = 'human_dictionary'

    id = db.Column(db.Integer, primary_key=True)
    term = db.Column(db.String(100), nullable=False, unique=True)   # 术语名称（如"心流"、"无意识胜任区"）
    category = db.Column(db.String(50), nullable=False)              # 所属类别（如"心理学概念"、"评估术语"）
    definition = db.Column(db.Text, nullable=False)                  # 术语定义（详细的解释说明）
    example = db.Column(db.Text)                                     # 示例说明（帮助理解的具体场景）
    related_terms = db.Column(db.String(255))                        # 相关术语（逗号分隔，如"系统思维,模式识别,元认知"）
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))  # 创建时间


# ============================================================
# 模型 5：AI 访谈会话
# ============================================================
# 存储用户与 AI 的完整对话历史，支持中断恢复
# 每个用户同时只有一条活跃的访谈记录
class InterviewSession(db.Model):
    """
    AI访谈会话表

    存储用户与 AI 的完整对话过程和最终报告。
    设计要点：
    1. 服务端持久化：对话历史存在服务器端（而非 Cookie），避免数据丢失
    2. 单会话模式：每个用户同时只有一条活跃记录，开始新访谈时删除旧记录
    3. 中断恢复：用户关闭浏览器后可以从上次中断处继续

    字段说明：
    - messages: 完整对话历史（JSON格式），结构如下：
      [
        {"role": "user", "content": "开始访谈"},
        {"role": "assistant", "content": "---关键信号---\n...---下一题---\n问题内容"},
        {"role": "user", "content": "用户的回答"},
        ...
      ]
    - stage: 当前访谈方向索引（0-7），对应 A-H 八个方向
      0=A(童年模式), 1=B(无意识胜任区), 2=C(能量审计), 3=D(嫉妒与压抑),
      4=E(社会可见优势), 5=F(深层痛苦), 6=G(伪擅长区), 7=H(真实兴趣)
    - answers: 按方向结构化存储的用户回答（JSON格式）
      {"A": "用户的回答...", "B": "用户的回答...", ...}
    - report_content: 最终生成的 Markdown 格式报告
    - share_token: 分享链接的唯一标识（用于生成无需登录即可查看的分享链接）
    """
    __tablename__ = 'interview_sessions'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)  # 关联用户
    messages = db.Column(db.Text, default='[]')           # JSON序列化对话历史
    stage = db.Column(db.Integer, default=0)              # 当前方向索引 0-7（对应A-H八个访谈方向）
    answers = db.Column(db.Text, default='{}')            # JSON，结构化存储各方向用户回答
    report_content = db.Column(db.Text)                   # 最终生成的 Markdown 格式报告
    share_token = db.Column(db.String(64), unique=True, nullable=True)  # 分享链接 token（用于生成公开链接）
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))  # 会话创建时间
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))  # 最后更新时间


# ============================================================
# 模型 6：访问日志
# ============================================================
# 记录用户的页面访问行为，用于管理后台的统计分析
# 使用批量写入优化（见 app.py 中的 _visit_buffer）
class VisitLog(db.Model):
    """
    访问日志表

    记录用户的页面访问行为，用于管理后台的统计分析。
    数据来源：app.py 中的 @app.before_request 中间件

    记录的信息：
    - path: 访问的页面路径（如 "/", "/scale", "/talent-type"）
    - module: 所属模块（如 "main", "scale", "talent_type"），用于分类统计
    - user_id: 用户ID（未登录时为 None），用于统计登录/未登录用户的访问比例
    - ip_address: 用户的IP地址（IPv4或IPv6）

    写入策略：
    - 不是每次访问都写数据库，而是先存在内存缓冲区
    - 累积到 50 条后批量写入，减少数据库 I/O 次数
    - 应用关闭时自动 flush 缓冲区，确保不丢失数据
    """
    __tablename__ = 'visit_logs'

    id = db.Column(db.Integer, primary_key=True)
    path = db.Column(db.String(256), nullable=False)          # 访问路径
    module = db.Column(db.String(32), nullable=True)           # 所属模块
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # 用户ID（可为空）
    ip_address = db.Column(db.String(45), nullable=True)       # IP地址（支持IPv6）
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), index=True)  # 访问时间（带索引，便于按时间查询）
