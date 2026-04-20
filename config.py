import os

# ============================================================
# AI 提供商切换
# 改这一行即可切换模型: 'kimi' | 'deepseek'
# ============================================================
_PROVIDER = os.environ.get('PROVIDER', 'deepseek').lower()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'YOUR_SECRET_KEY'
    
    # 测评流程配置
    MIN_QUESTIONS = 8          # 最少答题数才能生成报告
    SUGGEST_REPORT_AT = 12     # 建议生成报告的轮数
    MAX_QUESTIONS = 20         # 最大答题数，强制生成报告
    REPORT_TITLE = "个人天赋使用说明书 + 人类3.0发展诊断报告"
    
    # ============================================================
    # AI API 配置（根据 PROVIDER 自动选择）
    # ============================================================
    if _PROVIDER == 'deepseek':
        # DeepSeek 配置
        # 优点: 指令遵循度更好, 价格便宜, 推理有深度, 更"听话"
        # 申请地址: https://platform.deepseek.com/
        AI_API_KEY = os.environ.get('DEEPSEEK_API_KEY') or 'YOUR_DEEPSEEK_API_KEY'
        AI_BASE_URL = 'https://api.deepseek.com/v1'
        AI_MODEL = 'deepseek-chat'  # 可换 'deepseek-reasoner' (R1推理模型, 更深度但慢)
    else:
        # Kimi (Moonshot) 配置
        # 优点: 上下文窗口大(128k), 中文语料丰富
        # 缺点: 对长system prompt末尾指令遵循度一般, 容易"自主发挥"
        AI_API_KEY = 'YOUR_KIMI_API_KEY'
        AI_BASE_URL = 'https://api.moonshot.cn/v1'
        AI_MODEL = 'moonshot-v1-128k'
