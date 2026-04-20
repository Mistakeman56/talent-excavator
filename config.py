import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'YOUR_SECRET_KEY'
    
    # ============================================================
    # AI API 配置 - 支持一键切换
    # 改下面的 PROVIDER 即可切换模型，无需改其他代码
    # ============================================================
    
    PROVIDER = os.environ.get('PROVIDER') or 'kimi'  # 可选: 'kimi' | 'deepseek'
    
    # --- 方案1: Kimi (Moonshot) ---
    # 优点: 上下文窗口大(128k), 中文语料丰富
    # 缺点: 对长system prompt末尾指令遵循度一般, 容易"自主发挥"
    KIMI_API_KEY = 'YOUR_KIMI_API_KEY'
    KIMI_BASE_URL = 'https://api.moonshot.cn/v1'
    KIMI_MODEL = 'moonshot-v1-128k'
    
    # --- 方案2: DeepSeek ---
    # 优点: 指令遵循度更好, 价格便宜, 推理有深度, 更"听话"
    # 缺点: 需要单独申请API Key
    # 申请地址: https://platform.deepseek.com/
    DEEPSEEK_API_KEY = os.environ.get('DEEPSEEK_API_KEY') or 'your-deepseek-api-key-here'
    DEEPSEEK_BASE_URL = 'https://api.deepseek.com/v1'
    DEEPSEEK_MODEL = 'deepseek-chat'  # 也可换成 'deepseek-reasoner' (R1推理模型, 更深度但慢)
    
    # 自动根据 PROVIDER 选择配置
    @classmethod
    def get_ai_config(cls):
        if cls.PROVIDER == 'deepseek':
            return {
                'api_key': cls.DEEPSEEK_API_KEY,
                'base_url': cls.DEEPSEEK_BASE_URL,
                'model': cls.DEEPSEEK_MODEL
            }
        else:  # 默认 kimi
            return {
                'api_key': cls.KIMI_API_KEY,
                'base_url': cls.KIMI_BASE_URL,
                'model': cls.KIMI_MODEL
            }
    
    # 兼容旧配置名（直接读取）
    @property
    def AI_API_KEY(self):
        return self.get_ai_config()['api_key']
    
    @property
    def AI_BASE_URL(self):
        return self.get_ai_config()['base_url']
    
    @property
    def AI_MODEL(self):
        return self.get_ai_config()['model']
    
    # ============================================================
    # 测评流程配置
    # ============================================================
    MIN_QUESTIONS = 8          # 最少答题数才能生成报告
    SUGGEST_REPORT_AT = 12     # 建议生成报告的轮数
    MAX_QUESTIONS = 20         # 最大答题数，强制生成报告
    
    # 报告页面配置
    REPORT_TITLE = "个人天赋使用说明书 + 人类3.0发展诊断报告"
