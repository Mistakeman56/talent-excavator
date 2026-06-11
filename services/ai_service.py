import re
import logging
from openai import OpenAI
from flask import current_app

logger = logging.getLogger(__name__)

class AIService:
    def __init__(self):
        self.client = None

    def _get_client(self):
        if self.client is None:
            self.client = OpenAI(
                api_key=current_app.config['AI_API_KEY'],
                base_url=current_app.config['AI_BASE_URL']
            )
        return self.client

    DIRECTION_DESCRIPTIONS = {
        'A': '\u3010A-\u7ae5\u5e74/\u987d\u56fa\u7f3a\u70b9\u301116\u5c81\u4e4b\u524d\u6ca1\u4eba\u903c\u4f60\u4e5f\u4f1a\u6c89\u8fdb\u53bb\u505a\u7684\u4e8b\uff0c\u6216\u4ece\u5c0f\u5e38\u88ab\u6279\u8bc4\u7684"\u987d\u56fa\u7f3a\u70b9"',
        'B': '\u3010B-\u65e0\u610f\u8bc6\u80dc\u4efb\u533a\u3011\u6210\u5e74\u540e\u522b\u4eba\u89c9\u5f97\u5f88\u96be\u4f46\u4f60\u89c9\u5f97\u5f88\u81ea\u7136\u3001"\u8fd9\u4e0d\u662f\u5f88\u660e\u663e\u5417"\u7684\u4e8b',
        'C': '\u3010C-\u80fd\u91cf\u5ba1\u8ba1\u3011\u505a\u5b8c\u540e\u8eab\u4f53\u7d2f\u4f46\u7cbe\u795e\u6781\u5ea6\u4ea2\u594b\u3001\u5145\u6ee1\u80fd\u91cf\u7684\u4e8b',
        'D': '\u3010D-\u5ac9\u5992/\u538b\u6291\u3011\u5f3a\u70c8\u5ac9\u5992\u8fc7\u7684\u4eba\u3001\u80fd\u529b\u3001\u751f\u6d3b\u72b6\u6001\u2014\u2014\u8bc6\u522b\u88ab\u538b\u6291\u7684\u5929\u8d4b',
        'E': '\u3010E-\u793e\u4f1a\u53ef\u89c1\u4f18\u52bf\u3011\u522b\u4eba\u901a\u5e38\u4e3a\u4ec0\u4e48\u6765\u627e\u4f60\u2014\u2014\u4ed6\u4eba\u773c\u4e2d\u7684\u4f60',
        'F': '\u3010F-\u6df1\u5c42\u75db\u82e6\u3011\u6700\u53cd\u590d\u75db\u82e6/\u53d7\u4f24/\u6267\u7740\u7684\u4e3b\u9898\u2014\u2014\u6df1\u5c42\u9a71\u52a8\u529b\u548c\u9634\u5f71',
        'G': '\u3010G-\u4f2a\u64c5\u957f\u533a\u3011\u505a\u5f97\u4e0d\u9519\u4f46\u8d8a\u505a\u8d8a\u7a7a\u3001\u6ca1\u6709\u6210\u5c31\u611f\u7684\u4e8b',
        'H': '\u3010H-\u771f\u5174\u8da3\u3011\u6ca1\u8d5a\u5230\u94b1\u4f46\u4e00\u8c08\u8d77\u6765\u773c\u775b\u53d1\u4eae\u3001\u5145\u6ee1\u751f\u547d\u529b\u7684\u4e8b'
    }
    
    DIRECTION_QUESTIONS = {
        'A': '16\u5c81\u4e4b\u524d\uff0c\u6ca1\u4eba\u903c\u4f60\u4e5f\u4f1a\u6c89\u8fdb\u53bb\u505a\u7684\u4e8b\u662f\u4ec0\u4e48\uff1f\u6216\u8005\u4f60\u4ece\u5c0f\u5e38\u88ab\u6279\u8bc4\u7684"\u987d\u56fa\u7f3a\u70b9"\u662f\u4ec0\u4e48\uff1f',
        'B': '\u6210\u5e74\u540e\uff0c\u4ec0\u4e48\u4e8b\u60c5\u4f60\u4f1a\u89c9\u5f97\uff1a"\u8fd9\u4e0d\u662f\u5f88\u660e\u663e\u5417\uff1f\u8fd9\u4e5f\u8981\u5b66\uff1f"\u4f46\u522b\u4eba\u666e\u904d\u89c9\u5f97\u5f88\u96be\uff1f',
        'C': '\u4ec0\u4e48\u4e8b\u60c5\u505a\u5b8c\u540e\u8eab\u4f53\u7d2f\uff0c\u4f46\u7cbe\u795e\u6781\u5ea6\u4ea2\u594b\uff1f',
        'D': '\u4f60\u5f3a\u70c8\u5ac9\u5992\u8fc7\u54ea\u79cd\u4eba\u3001\u54ea\u79cd\u80fd\u529b\u3001\u54ea\u79cd\u751f\u6d3b\u72b6\u6001\uff1f',
        'E': '\u522b\u4eba\u901a\u5e38\u4e3a\u4ec0\u4e48\u6765\u627e\u4f60\uff1f',
        'F': '\u4f60\u6700\u53cd\u590d\u75db\u82e6/\u53d7\u4f24/\u6267\u7740\u7684\u4e3b\u9898\u662f\u4ec0\u4e48\uff1f',
        'G': '\u54ea\u4e9b\u4e8b\u60c5\u4f60\u505a\u5f97\u4e0d\u9519\uff0c\u4f46\u8d8a\u505a\u8d8a\u7a7a\uff1f',
        'H': '\u54ea\u4e9b\u4e8b\u60c5\u4f60\u6ca1\u8d5a\u5230\u94b1\uff0c\u4f46\u4e00\u8c08\u8d77\u6765\u5c31\u773c\u775b\u53d1\u4eae\uff1f'
    }

    # 公共 prompt 片段
    _OUTPUT_FORMAT = """【每轮输出格式 - 严格遵守】
---关键信号---（刚听到的关键信息，简要提炼）
---天赋假设---（当前初步天赋假设）
---HUMAN 3.0 判断---（四象限判断，可初步）
---下一题---（一次只问一个主问题）"""

    _QUESTION_STYLE = """【提问方式】
1. 一次只问一个主问题，不要一次抛多个
2. 采用苏格拉底式深挖：为什么？具体例子？当时什么感觉？你到底做对了什么？
3. 风格：温暖而犀利、不灌鸡汤、有共情但不纵容自我欺骗"""

    _PROHIBITED = """【绝对禁止】
- 讲你自己的故事、经历、案例
- 编造"我曾经…""我记得…""有一次…"等虚构场景
- 使用第一人称分享个人经验
- 你的任务是分析用户并提问，不是展示你自己"""

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
        """构建系统提示词——后端控制方向，AI只负责表达"""
        if is_report:
            return self._REPORT_PROMPT

        dir_desc = self.DIRECTION_DESCRIPTIONS.get(current_direction, '')
        dir_question = self.DIRECTION_QUESTIONS.get(current_direction, '')

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
        """解析AI返回的四部分结构"""
        result = {
            'signal': '',
            'hypothesis': '',
            'judgment': '',
            'question': '',
            'raw': content
        }
        
        patterns = {
            'signal': r'---关键信号---\s*\n?(.*?)(?=---天赋假设---|$)',
            'hypothesis': r'---天赋假设---\s*\n?(.*?)(?=---HUMAN 3\.0 判断---|$)',
            'judgment': r'---HUMAN 3\.0 判断---\s*\n?(.*?)(?=---下一题---|$)',
            'question': r'---下一题---\s*\n?(.*?)(?=$)'
        }
        
        for key, pattern in patterns.items():
            match = re.search(pattern, content, re.DOTALL)
            if match:
                result[key] = match.group(1).strip()
        
        # 如果没有解析到格式，把全部内容作为 question
        if not result['question']:
            result['question'] = content.strip()
        
        return result
    
    # 讲故事/编造经历的关键词拦截列表
    STORY_KEYWORDS = ['我记得', '当时我', '我曾经', '有一次']

    def _contains_story(self, text):
        """检测 AI 输出是否开始讲自己的故事/案例"""
        if not text:
            return False
        return any(kw in text for kw in self.STORY_KEYWORDS)

    def chat(self, messages, round_num=0, is_report=False, asked_questions=None,
             covered_directions=None, current_direction=None, is_first_round=False):
        """调用AI API进行对话——后端控制方向"""
        client = self._get_client()
        model = current_app.config['AI_MODEL']
        max_rounds = current_app.config['MAX_QUESTIONS']
        
        covered_directions = covered_directions or []
        
        system_prompt = self.get_system_prompt(
            round_num, max_rounds, is_report, asked_questions, covered_directions,
            current_direction=current_direction, is_first_round=is_first_round
        )
        
        full_messages = [{"role": "system", "content": system_prompt}] + messages

        logger.info("AI API 调用: %d 条消息, direction=%s, round=%d",
                     len(full_messages), current_direction, round_num)

        def _call_api(msgs, is_report=False):
            """内部封装：调用 API 并解析"""
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
            
            if is_report:
                return {"type": "report", "content": content}
            
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