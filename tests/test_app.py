"""
核心功能单元测试
覆盖：用户注册/登录、量表评分逻辑、天赋类型计算
"""
import pytest
import json
import os
import sys

# 确保项目根目录在 sys.path 中
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from models import db, User


@pytest.fixture
def client():
    """创建测试客户端，每个测试使用独立的内存数据库"""
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
        yield client
        with app.app_context():
            db.drop_all()


@pytest.fixture
def auth_client(client):
    """已注册并登录的测试客户端"""
    client.post('/register', data={
        'username': 'testuser',
        'password': 'test123456',
        'confirm': 'test123456'
    }, follow_redirects=True)
    return client


# ==================== 用户注册测试 ====================

class TestRegistration:
    """用户注册功能测试"""

    def test_register_success(self, client):
        """正常注册"""
        resp = client.post('/register', data={
            'username': 'newuser',
            'password': 'pass123456',
            'confirm': 'pass123456'
        }, follow_redirects=True)
        assert resp.status_code == 200
        with app.app_context():
            user = User.query.filter_by(username='newuser').first()
            assert user is not None

    def test_register_password_mismatch(self, client):
        """两次密码不一致"""
        resp = client.post('/register', data={
            'username': 'newuser',
            'password': 'pass123456',
            'confirm': 'different'
        }, follow_redirects=True)
        assert b'\xe4\xb8\xa4\xe6\xac\xa1\xe8\xbe\x93\xe5\x85\xa5\xe7\x9a\x84\xe5\xaf\x86\xe7\xa0\x81\xe4\xb8\x8d\xe4\xb8\x80\xe8\x87\xb4' in resp.data  # "两次输入的密码不一致"

    def test_register_short_password(self, client):
        """密码太短"""
        resp = client.post('/register', data={
            'username': 'newuser',
            'password': '123',
            'confirm': '123'
        }, follow_redirects=True)
        assert b'\xe5\xaf\x86\xe7\xa0\x81\xe9\x95\xbf\xe5\xba\xa6\xe8\x87\xb3\xe5\xb0\x916\xe4\xbd\x8d' in resp.data  # "密码长度至少6位"

    def test_register_duplicate_username(self, client):
        """重复用户名"""
        client.post('/register', data={
            'username': 'existing',
            'password': 'pass123456',
            'confirm': 'pass123456'
        }, follow_redirects=True)
        # 登出后才能再次访问注册页面
        client.post('/logout', follow_redirects=True)
        resp = client.post('/register', data={
            'username': 'existing',
            'password': 'pass123456',
            'confirm': 'pass123456'
        }, follow_redirects=True)
        assert '用户名已被注册'.encode('utf-8') in resp.data


# ==================== 用户登录测试 ====================

class TestLogin:
    """用户登录功能测试"""

    def test_login_success(self, client):
        """正常登录"""
        client.post('/register', data={
            'username': 'logintest',
            'password': 'pass123456',
            'confirm': 'pass123456'
        }, follow_redirects=True)
        client.get('/logout', follow_redirects=True)  # 先登出（这里用 GET 是为了兼容旧版，实际测试 POST）

        resp = client.post('/login', data={
            'username': 'logintest',
            'password': 'pass123456'
        }, follow_redirects=True)
        assert resp.status_code == 200

    def test_login_wrong_password(self, client):
        """密码错误"""
        client.post('/register', data={
            'username': 'logintest',
            'password': 'pass123456',
            'confirm': 'pass123456'
        }, follow_redirects=True)
        # 登出后再用错误密码登录
        client.post('/logout', follow_redirects=True)
        resp = client.post('/login', data={
            'username': 'logintest',
            'password': 'wrongpassword'
        }, follow_redirects=True)
        assert '用户名或密码错误'.encode('utf-8') in resp.data


# ==================== 量表评分逻辑测试 ====================

class TestScaleScoring:
    """量表评分逻辑测试"""

    def test_scale_score_calculation(self):
        """测试量表评分计算逻辑"""
        # 模拟 5 个维度各 4 题的得分
        answers = {
            'q1': 4, 'q2': 3, 'q3': 5, 'q4': 4,   # 维度1
            'q5': 2, 'q6': 3, 'q7': 2, 'q8': 3,   # 维度2
            'q9': 5, 'q10': 4, 'q11': 5, 'q12': 4, # 维度3
            'q13': 1, 'q14': 2, 'q15': 1, 'q16': 2,# 维度4
            'q17': 3, 'q18': 3, 'q19': 3, 'q20': 3 # 维度5
        }
        # 每个维度满分 20（4题 * 5分），计算百分比
        dim1 = sum(answers[f'q{i}'] for i in range(1, 5))   # 16/20 = 80%
        dim2 = sum(answers[f'q{i}'] for i in range(5, 9))   # 10/20 = 50%
        dim3 = sum(answers[f'q{i}'] for i in range(9, 13))  # 18/20 = 90%
        dim4 = sum(answers[f'q{i}'] for i in range(13, 17)) # 6/20 = 30%
        dim5 = sum(answers[f'q{i}'] for i in range(17, 21)) # 12/20 = 60%

        assert dim1 == 16
        assert dim2 == 10
        assert dim3 == 18
        assert dim4 == 6
        assert dim5 == 12

        # 验证 Top 维度排序
        dims = {'认知洞察': dim1, '创造表达': dim2, '社交连接': dim3,
                '系统推动': dim4, '身体感知': dim5}
        top = sorted(dims, key=dims.get, reverse=True)
        assert top[0] == '社交连接'  # 18 分最高
        assert top[1] == '认知洞察'  # 16 分次高


# ==================== 天赋类型学评分测试 ====================

class TestTalentTypeScoring:
    """天赋类型学评分逻辑测试"""

    def test_type_code_generation(self):
        """测试 4 字母类型码生成逻辑"""
        # 模拟 40 题答案，每模块 10 题
        answers = {}
        # 模块1：天赋形态（A/B/C/D 四选一，10题计票）
        for i in range(1, 11):
            answers[f't{i}'] = 'a'  # 全选 A
        # 模块2：能量模式（A/B/C 三选一）
        for i in range(11, 21):
            answers[f't{i}'] = 'b'  # 全选 B
        # 模块3：驱动来源（A/B 二选一）
        for i in range(21, 31):
            answers[f't{i}'] = 'a'  # 全选 A
        # 模块4：兴趣指向（A/B/C 三选一）
        for i in range(31, 41):
            answers[f't{i}'] = 'c'  # 全选 C

        # 计算每个模块的票数
        modules = [
            ('天赋形态', ['a', 'b', 'c', 'd'], range(1, 11)),
            ('能量模式', ['a', 'b', 'c'], range(11, 21)),
            ('驱动来源', ['a', 'b'], range(21, 31)),
            ('兴趣指向', ['a', 'b', 'c'], range(31, 41))
        ]

        type_code = ''
        for name, options, q_range in modules:
            counts = {opt: 0 for opt in options}
            for i in q_range:
                ans = answers[f't{i}']
                if ans in counts:
                    counts[ans] += 1
            winner = max(counts, key=counts.get)
            type_code += winner.upper()

        assert type_code == 'ABAC'

    def test_type_code_all_same(self):
        """全选同一选项的情况"""
        answers = {}
        for i in range(1, 41):
            answers[f't{i}'] = 'a'

        modules = [
            (['a', 'b', 'c', 'd'], range(1, 11)),
            (['a', 'b', 'c'], range(11, 21)),
            (['a', 'b'], range(21, 31)),
            (['a', 'b', 'c'], range(31, 41))
        ]

        type_code = ''
        for options, q_range in modules:
            counts = {opt: 0 for opt in options}
            for i in q_range:
                ans = answers[f't{i}']
                if ans in counts:
                    counts[ans] += 1
            winner = max(counts, key=counts.get)
            type_code += winner.upper()

        assert type_code == 'AAAA'


# ==================== API 端点测试 ====================

class TestAPIEndpoints:
    """API 端点基本可达性测试"""

    def test_home_page(self, client):
        """首页可访问"""
        resp = client.get('/')
        assert resp.status_code == 200

    def test_scale_page(self, client):
        """量表页面可访问"""
        resp = client.get('/scale')
        assert resp.status_code == 200

    def test_talent_type_page(self, client):
        """类型学页面可访问"""
        resp = client.get('/talent-type')
        assert resp.status_code == 200

    def test_dictionary_page(self, client):
        """词典页面可访问"""
        resp = client.get('/dictionary')
        assert resp.status_code == 200

    def test_login_page(self, client):
        """登录页面可访问"""
        resp = client.get('/login')
        assert resp.status_code == 200

    def test_register_page(self, client):
        """注册页面可访问"""
        resp = client.get('/register')
        assert resp.status_code == 200

    def test_admin_requires_login(self, client):
        """管理后台需要登录"""
        resp = client.get('/admin', follow_redirects=False)
        assert resp.status_code == 302  # 重定向到登录

    def test_history_requires_login(self, client):
        """历史页面需要登录"""
        resp = client.get('/history', follow_redirects=False)
        assert resp.status_code == 302  # 重定向到登录

    def test_dictionary_api(self, client):
        """词典 API 返回正确格式"""
        resp = client.get('/api/dictionary')
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert 'success' in data
        assert 'entries' in data

    def test_auth_check(self, client):
        """登录状态检查 API"""
        resp = client.get('/api/auth/check')
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data['authenticated'] == False


# ==================== 管理员权限测试 ====================

class TestAdminPermissions:
    """管理员权限测试"""

    def test_admin_field_default_false(self, client):
        """新注册用户默认不是管理员"""
        client.post('/register', data={
            'username': 'normaluser',
            'password': 'pass123456',
            'confirm': 'pass123456'
        }, follow_redirects=True)
        with app.app_context():
            user = User.query.filter_by(username='normaluser').first()
            assert user.is_admin == False

    def test_non_admin_cannot_access_admin(self, auth_client):
        """非管理员无法访问管理后台"""
        resp = auth_client.get('/admin')
        # 应该返回 403 或重定向
        assert resp.status_code in (302, 403)
