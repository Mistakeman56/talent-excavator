import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'YOUR_SECRET_KEY'
    
    # Kimi (Moonshot) API 配置
    AI_API_KEY = os.environ.get('AI_API_KEY') or 'YOUR_KIMI_API_KEY'
    AI_BASE_URL = os.environ.get('AI_BASE_URL') or 'https://api.moonshot.cn/v1'
    AI_MODEL = os.environ.get('AI_MODEL') or 'moonshot-v1-128k'
    
    # 测评流程配置
    MIN_QUESTIONS = 8          # 最少答题数才能生成报告
    SUGGEST_REPORT_AT = 12     # 建议生成报告的轮数
    MAX_QUESTIONS = 20         # 最大答题数，强制生成报告
    
    # 报告页面配置
    REPORT_TITLE = "个人天赋使用说明书 + 人类3.0发展诊断报告"
