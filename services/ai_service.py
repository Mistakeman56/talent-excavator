"""
services/ai_service.py — AI 服务封装模块

本模块封装了与 AI API 的所有交互逻辑，包括：
1. 系统提示词（System Prompt）构建 — 定义 AI 的角色和行为规范
2. API 调用 — 通过 OpenAI 兼容接口调用 DeepSeek/Kimi 等模型
3. 响应解析 — 从 AI 输出中提取四段式结构化数据
4. 异常处理 — 检测 AI 是否违反规则（如讲故事）并自动重试

AI 访谈的核心机制：
┌─────────────────────────────────────────────────────────────┐
│  System Prompt 定义了 AI 的角色：                            │
│  - 深度天赋挖掘师                                           │
│  - HUMAN 3.0 发展诊断师                                     │
│  - 综合视角：生涯咨询师 + 组织发展专家 + 高管教练 + ...     │
│                                                              │
│  每轮对话 AI 必须输出四段式格式：                            │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ ---关键信号---                                        │   │
│  │ 刚听到的关键信息，简要提炼                            │   │
│  │                                                       │   │
│  │ ---天赋假设---                                        │   │
│  │ 当前初步天赋假设                                      │   │
│  │                                                       │   │
│  │ ---HUMAN 3.0 判断---                                  │   │
│  │ 四象限判断，可初步                                    │   │
│  │                                                       │   │
│  │ ---下一题---                                          │   │
│  │ 一次只问一个主问题                                    │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  后端控制访谈方向（A-H），AI 只负责在给定方向内提问          │
└─────────────────────────────────────────────────────────────┘

AI 提供商切换：
- 通过 config.py 中的 PROVIDER 环境变量切换
- deepseek: 使用 DeepSeek API（默认，指令遵循度好，价格便宜）
- kimi: 使用 Moonshot API（上下文窗口大，中文语料丰富）
"""

import re
import logging
from openai import OpenAI
from flask import current_app

logger = logging.getLogger(__name__)


class AIService:
    """
    AI 服务类 — 封装所有与 AI API 的交互

    设计思路：
    - 使用 OpenAI Python SDK 的兼容接口，可以无缝切换不同的 AI 提供商
    - 延迟初始化客户端（首次调用时才创建），避免在模块导入时就需要 Flask 应用上下文
    - 全局复用同一个客户端实例，减少连接开销
    """

    def __init__(self):
        """初始化 AI 服务（客户端延迟创建）"""
        self.client = None  # OpenAI 客户端实例，首次调用时创建

    def _get_client(self):
        """
        获取 OpenAI 客户端实例（延迟初始化）

        返回:
            OpenAI 客户端实例

        说明:
            使用延迟初始化模式，避免在模块导入时就需要 Flask 应用上下文
            首次调用时从 config 读取 API 密钥和基础 URL 创建客户端
        """
        if self.client is None:
            self.client = OpenAI(
                api_key=current_app.config['AI_API_KEY'],
                base_url=current_app.config['AI_BASE_URL']
            )
        return self.client

    # ============================================================
    # 访谈方向定义（8个方向 A-H）
    # ============================================================
    # 每个方向有三个组成部分：
    # 1. DIRECTION_DESCRIPTIONS: 方向描述（注入到 System Prompt）
    # 2. DIRECTION_QUESTIONS: 参考问题（引导 AI 在该方向内提问）
    # 3. INTERVIEW_FLOW: 方向遍历顺序（定义在 route 中）

    DIRECTION_DESCRIPTIONS = {
        'A': '【A-童年/顽固缺点】16岁之前没人逼你也会沉进去做的事，或从小常被批评的"顽固缺点"',
        'B': '【B-无意识胜任区】成年后别人觉得很难但你觉得很自然、"这不是很明显吗"的事',
        'C': '【C-能量审计】做完后身体累但精神极度亢奋、充满能量的事',
        'D': '【D-嫉妒/压抑】强烈嫉妒过的人、能力、生活状态——识别被压抑的天赋',
        'E': '【E-社会可见优势】别人通常为什么来找你——他人眼中的你',
        'F': '【F-深层痛苦】最反复痛苦/受伤/执著的主题——深层驱动力和阴影',
        'G': '【G-伪擅长区】做得不错但越做越空、没有成就感的事',
        'H': '【H-真兴趣】没赚到钱但一谈起来眼睛发亮、充满生命力的事'
    }

    DIRECTION_QUESTIONS = {
        'A': '16岁之前，没人逼你也会沉进去做的事是什么？或者你从小常被批评的"顽固缺点"是什么？',
        'B': '成年后，什么事情你会觉得："这不是很明显吗？这也也要学？"但别人普遍觉得很难？',
        'C': '什么事情做完后身体累，但精神极度亢奋？',
        'D': '你强烈嫉妒过哪种人、哪种能力、哪种生活状态？',
        'E': '别人通常为什么来找你？',
        'F': '你最反复痛苦/受伤/执著的主题是什么？',
        'G': '哪些事情你做得不错，但越做越空？',
        'H': '哪些事情你没赚到钱，但一谈起来就眼睛发亮？'
    }

    # ============================================================
    # System Prompt 模板
    # ============================================================
    # 这些模板定义了 AI 的行为规范，包括输出格式、提问风格、禁止事项等

    # 四段式输出格式要求
    _OUTPUT_FORMAT = """【每轮输出格式 - 严格遵守】
---关键信号---（刚听到的关键信息，简要提炼）
---天赋假设---（当前初步天赋假设）
---HUMAN 3.0 判断---（四象限判断，可初步）
---下一题---（一次只问一个主问题）"""

    # 提问风格要求
    _QUESTION_STYLE = """【提问方式】
1. 一次只问一个主问题，不要一次抛多个
2. 采用苏格拉底式深挖：为什么？具体例子？当时什么感觉？你到底做对了什么？
3. 风格：温暖而犀利、不灌鸡汤、有共情但不纵容自我欺骗"""

    # 禁止事项（防止 AI 偏离角色）
    _PROHIBITED = """【绝对禁止】
- 讲你自己的故事、经历、案例
- 编造"我曾经…""我记得…""有一次…"等虚构场景
- 使用第一人称分享个人经验
- 你的任务是分析用户并提问，不是展示你自己"""

    # 报告生成的 Prompt
    _REPORT_PROMPT = """你是一位人类3.0天赋发掘测评师。现在访谈已结束，请根据之前的所有对话，输出最终的《个人天赋使用说明书+人类3.0发展诊断报告》。

要求：
- 篇幅要足够长，内容要深，不走模板感
- 用温暖而犀利、不灌鸡汤、有共情但不纵容自我欺骗的语气
- 报告必须自然覆盖以下14个方面：

1. 用户真正的底层天赋是什么
2. 为什么这些天赋过去被遮蔽了
3. 用户的缺点、怪癖、嫉妒、痛苦分别透露了什么
4. 用户的能量来源与能量黑洞
5. 用户的高能场景与伪擅长场景
6. 用户最适合的角色类型
7. 用户最不该再走的路
8. 用户如何把天赋映射到职业、事业、产品、内容表达、服务模式、商业路径
9. 用户在认知/身体/精神/职业四象限的现状判断
10. 用户当前更像哪种生活方式原型
11. 当前最核心的问题是什么
12. 未来30天 / 90天 / 6-12个月的演进建议
13. AI使用建议：如何让AI成为放大器，而不是拐杖
14. 一段真正打到用户心里的、诚实但有力量的结语

请用Markdown格式输出，层次清晰。"""

    # 8个方向的简要说明（注入到 System Prompt）
    _DIRECTIONS_GUIDE = """【8个必须覆盖的方向】
A. 16岁之前没人逼你也会沉进去做的事，或从小常被批评的"顽固缺点"
B. 成年后别人觉得很难但你觉得很自然的事——无意识胜任区
C. 做完后身体累但精神极度亢奋的事——能量审计
D. 强烈嫉妒过的人/能力/生活状态——被压抑的天赋
E. 别人通常为什么来找你——社会可见优势
F. 最反复痛苦/受伤/执着的主题——深层驱动力和阴影
G. 做得不错但越做越空的事——伪擅长区
H. 没赚到钱但一谈起来眼睛发亮的事——真兴趣"""

    def get_system_prompt(self, round_num=0, max_rounds=20, is_report=False,
                          asked_questions=None, covered_directions=None,
                          current_direction=None, is_first_round=False):
        """
        构建系统提示词（System Prompt）

        参数:
            round_num: 当前轮数
            max_rounds: 最大轮数
            is_report: 是否是报告生成模式
            asked_questions: 已问过的问题列表（防重复）
            covered_directions: 已覆盖的方向列表
            current_direction: 当前访谈方向（A-H）
            is_first_round: 是否是第一轮

        返回:
            系统提示词字符串

        说明:
            System Prompt 是 AI 行为的核心控制机制
            不同阶段（首轮/非首轮/报告）使用不同的 Prompt 模板
            当前方向的描述和参考问题会动态注入到 Prompt 中
        """
        # 报告生成模式：使用专用的报告 Prompt
        if is_report:
            return self._REPORT_PROMPT

        # 获取当前方向的描述和参考问题
        dir_desc = self.DIRECTION_DESCRIPTIONS.get(current_direction, '')
        dir_question = self.DIRECTION_QUESTIONS.get(current_direction, '')

        # 首轮：完整的 Prompt，包含角色定义、核心理念、输出格式等
        if is_first_round:
            return f"""你现在不是普通聊天助手。
你要扮演一位"深度天赋挖掘师 + HUMAN 3.0 发展诊断师"，综合以下视角：
1. 30年经验的资深生涯咨询师
2. 30年经验的组织发展专家
3. 30年经验的高管教练
4. 30年经验的心理咨询师
5. 30年经验的人才测评专家
6. 熟悉盖洛普优势理论、心流理论、荣格心理学、关键事件访谈法、苏格拉底式提问法的深度访谈研究者
7. 熟悉 HUMAN 3.0 模型的多维发展评估者

你的真正任务：通过多轮深度访谈，挖掘用户被遮蔽的底层天赋，同时评估这些天赋目前卡在哪个发展象限、哪种生活方式中，最终输出《个人天赋使用说明书 + HUMAN 3.0 发展诊断报告》。

【当前对话状态】第 {round_num} 轮（计划共 {max_rounds} 轮）。这是开场阶段，请进行温暖专业的开场白，并提问第一个问题。

【当前访谈方向】{current_direction}（{dir_desc}）
参考问题：{dir_question}

【核心理念】
1. 反宿命论：天赋不是固定标签，是可迁移的底层能力结构
2. 天赋不是具体技能："会写PPT"不是天赋；"复杂信息结构化表达"才是
3. 能量审计：真正的天赋让人做完后"回血"，即便辛苦也更兴奋
4. 阴影即宝藏：缺点、嫉妒、执念、反复受伤的主题，往往是被压抑天赋的背面
5. 区分底层天赋、后天技能、家庭责任、创伤补偿、误以为的"热爱"
6. HUMAN 3.0 四象限：认知 / Body / Spirit / Vocation，找到根问题让其余象限自然联动

{self._OUTPUT_FORMAT}

{self._QUESTION_STYLE}

{self._DIRECTIONS_GUIDE}

【注意】
- 严格使用四部分格式输出
- 每轮只问一个问题
- 第一轮请做温暖专业的开场白
- 绝对禁止重复之前的问题

{self._PROHIBITED}
"""

        # 非首轮：精简 Prompt，避免反复开场
        return f"""你正在继续访谈，不需要重复开场说明，也不要再做自我介绍。直接基于用户回答继续分析并提问。

【当前访谈方向】{current_direction}（{dir_desc}）
请严格围绕该方向提问。可以参考：{dir_question}

{self._OUTPUT_FORMAT}

【要求】
1. 一次只问一个主问题，不要一次抛多个
2. 采用苏格拉底式深挖：为什么？具体例子？当时什么感觉？你到底做对了什么？
3. 风格：温暖而犀利、不灌鸡汤、有共情但不纵容自我欺骗
4. 绝对禁止重复之前问过的问题，不要换一种措辞重复同一问题
5. 不要借用户提到的某个词跳回已覆盖方向重问

{self._PROHIBITED}
"""

    def parse_response(self, content):
        """
        解析 AI 返回的四段式结构

        参数:
            content: AI 的原始输出文本
        返回:
            解析后的结构化字典：
            {
                'signal': '关键信号内容',
                'hypothesis': '天赋假设内容',
                'judgment': 'HUMAN 3.0 判断内容',
                'question': '问题内容',
                'raw': 'AI 原始输出'
            }

        说明:
            AI 的输出格式为：
            ---关键信号---
            分析内容
            ---天赋假设---
            假设内容
            ---HUMAN 3.0 判断---
            判断内容
            ---下一题---
            问题内容

            使用正则表达式提取每个部分的内容
            如果解析失败，将全部内容作为 question 返回
        """
        result = {
            'signal': '',
            'hypothesis': '',
            'judgment': '',
            'question': '',
            'raw': content
        }

        # 定义四个部分的正则表达式模式
        patterns = {
            'signal': r'---关键信号---\s*\n?(.*?)(?=---天赋假设---|$)',
            'hypothesis': r'---天赋假设---\s*\n?(.*?)(?=---HUMAN 3\.0 判断---|$)',
            'judgment': r'---HUMAN 3\.0 判断---\s*\n?(.*?)(?=---下一题---|$)',
            'question': r'---下一题---\s*\n?(.*?)(?=$)'
        }

        # 逐个提取
        for key, pattern in patterns.items():
            match = re.search(pattern, content, re.DOTALL)
            if match:
                result[key] = match.group(1).strip()

        # 如果没有解析到问题部分，把全部内容作为 question
        if not result['question']:
            result['question'] = content.strip()

        return result

    # 讲故事/编造经历的关键词拦截列表
    # 如果 AI 输出中包含这些关键词，说明它开始讲自己的故事了，需要重试
    STORY_KEYWORDS = ['我记得', '当时我', '我曾经', '有一次']

    def _contains_story(self, text):
        """
        检测 AI 输出是否开始讲自己的故事/案例

        参数:
            text: AI 的输出文本
        返回:
            True 如果检测到讲故事的关键词

        说明:
            这是一个安全机制，防止 AI 偏离"分析用户并提问"的角色
            如果检测到 AI 开始讲故事，会触发重试
        """
        if not text:
            return False
        return any(kw in text for kw in self.STORY_KEYWORDS)

    def chat(self, messages, round_num=0, is_report=False, asked_questions=None,
             covered_directions=None, current_direction=None, is_first_round=False):
        """
        调用 AI API 进行对话

        参数:
            messages: 对话历史列表 [{"role": "user", "content": "..."}, ...]
            round_num: 当前轮数
            is_report: 是否是报告生成模式
            asked_questions: 已问过的问题列表
            covered_directions: 已覆盖的方向列表
            current_direction: 当前访谈方向（A-H）
            is_first_round: 是否是第一轮

        返回:
            成功时: {"type": "chat", "signal": "...", "hypothesis": "...", "judgment": "...", "question": "...", "raw": "..."}
            报告时: {"type": "report", "content": "..."}
            失败时: {"type": "error", "message": "..."}

        处理流程:
        1. 构建 System Prompt（根据当前轮数和方向）
        2. 调用 AI API
        3. 如果是报告模式，直接返回原始内容
        4. 如果是对话模式，解析四段式结构
        5. 检测是否讲故事，如果是则重试一次
        6. 返回解析后的结构化数据
        """
        client = self._get_client()
        model = current_app.config['AI_MODEL']
        max_rounds = current_app.config['MAX_QUESTIONS']

        covered_directions = covered_directions or []

        # 构建 System Prompt
        system_prompt = self.get_system_prompt(
            round_num, max_rounds, is_report, asked_questions, covered_directions,
            current_direction=current_direction, is_first_round=is_first_round
        )

        # 组装完整的消息列表（System Prompt + 对话历史）
        full_messages = [{"role": "system", "content": system_prompt}] + messages

        logger.info("AI API 调用: %d 条消息, direction=%s, round=%d",
                     len(full_messages), current_direction, round_num)

        def _call_api(msgs, is_report=False):
            """
            内部封装：调用 API 并处理响应

            参数:
                msgs: 完整的消息列表
                is_report: 是否是报告模式
            返回:
                AI 的原始输出文本

            说明:
                - temperature=0.85: 适度的创造性，既不呆板也不太发散
                - max_tokens: 报告模式用 8192，对话模式用 4000
                - 检测 finish_reason: 如果报告被截断，添加警告信息
            """
            resp = client.chat.completions.create(
                model=model,
                messages=msgs,
                temperature=0.85,
                max_tokens=8192 if is_report else 4000
            )
            content = resp.choices[0].message.content
            # 报告生成时检测输出是否被截断
            if is_report and resp.choices[0].finish_reason != 'stop':
                content += '\n\n---\n\n> ⚠️ 报告内容较长，可能未完全生成。如需更完整的报告，建议重新测评或联系管理员。'
            return content

        try:
            content = _call_api(full_messages, is_report=is_report)

            # 报告模式：直接返回原始内容
            if is_report:
                return {"type": "report", "content": content}

            # 对话模式：解析四段式结构
            parsed = self.parse_response(content)

            # 异常拦截：检测 AI 是否开始讲自己的故事
            if self._contains_story(parsed.get('raw', '')):
                logger.warning("检测到 AI 讲故事，触发重试")
                retry_messages = full_messages + [
                    {"role": "system", "content": "你刚才开始讲自己的案例或经历，这是绝对不允许的。你的任务是分析用户并提问，不是展示你自己。请重新输出。"}
                ]
                content = _call_api(retry_messages)
                parsed = self.parse_response(content)

            return {
                "type": "chat",
                **parsed
            }
        except Exception as e:
            logger.error("AI API 调用失败: %s", str(e))
            return {"type": "error", "message": "AI 服务暂时不可用，请稍后重试"}
