# routes 包：导出所有 Blueprint，方便 app.py 统一注册

from .main import main_bp
from .interview import interview_bp
from .scale import scale_bp
from .dictionary import dictionary_bp
from .auth import auth_bp
from .talent_type import talent_type_bp

__all__ = ['main_bp', 'interview_bp', 'scale_bp', 'dictionary_bp', 'auth_bp', 'talent_type_bp']