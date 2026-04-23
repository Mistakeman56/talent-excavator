import re
from openai import OpenAI
from flask import current_app

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
    
    DIRECTION_KEYWORDS = {
        'A': ['16\u5c81', '\u7ae5\u5e74', '\u5c0f\u65f6\u5019', '\u62c6', '\u7f3a\u70b9', '\u6279\u8bc4', '\u987d\u56fa', '\u7236\u6bcd\u903c', '\u6c89\u8fdb\u53bb', '\u6ca1\u4eba\u903c',
              '\u5e74\u5e7c', '\u5c11\u5e74', '\u6210\u957f\u8fc7\u7a0b', '\u672c\u6027', '\u5929\u6027', '\u5c0f\u7684\u65f6\u5019', '\u521d\u4e2d', '\u5c0f\u5b66'],
        'B': ['\u5f88\u660e\u663e', '\u8fd9\u4e5f\u8981\u5b66', '\u522b\u4eba\u89c9\u5f97\u96be', '\u65e0\u610f\u8bc6\u80dc\u4efb', '\u4e0d\u9700\u8981\u5b66', '\u5929\u751f\u4f1a', '\u522b\u4eba\u666e\u904d',
              '\u81ea\u7136\u800c\u7136', '\u672c\u80fd', '\u76f4\u89c9', '\u6ca1\u5b66\u8fc7', '\u65e0\u5e08\u81ea\u901a', '\u8fd9\u4e5f\u8981\u6559', '\u522b\u4eba\u505a\u4e0d\u5230'],
        'C': ['\u8eab\u4f53\u7d2f', '\u7cbe\u795e\u4ea2\u594b', '\u80fd\u91cf', '\u75b2\u60eb', '\u5174\u594b', '\u7d2f\u4f46', '\u505a\u5b8c\u540e\u7d2f', '\u6781\u5ea6\u4ea2\u594b',
              '\u75b2\u60eb\u4f46', '\u5145\u7535', '\u8017\u7535', '\u71c3', '\u5026\u6020', '\u5fc3\u6d41', 'flow', '\u6c89\u6d78', '\u5fd8\u65f6\u95f4', '\u65f6\u95f4\u6d88\u5931'],
        'D': ['\u5ac9\u5992', '\u7fa1\u6155', '\u5ac9\u5992\u8fc7', '\u54ea\u79cd\u4eba', '\u54ea\u79cd\u80fd\u529b', '\u751f\u6d3b\u72b6\u6001', '\u538b\u6291', '\u672a\u88ab\u5141\u8bb8',
              '\u60f3\u6210\u4e3a', '\u6e34\u671b\u6210\u4e3a', '\u773c\u7ea2', '\u4e0d\u7518\u5fc3', '\u4e3a\u4ec0\u4e48\u4ed6\u80fd', '\u51ed\u4ec0\u4e48', '\u5411\u5f80'],
        'E': ['\u6765\u627e\u4f60', '\u522b\u4eba', '\u670b\u53cb', '\u540c\u4e8b', '\u627e\u4f60', '\u793e\u4f1a\u4f18\u52bf', '\u53ef\u89c1\u4f18\u52bf', '\u4ed6\u4eba\u773c\u4e2d', '\u4e3a\u4ec0\u4e48\u6765',
              '\u6c42\u52a9', '\u8bf7\u6559', '\u53e3\u7891', '\u8ba4\u53ef', '\u4fe1\u4efb', '\u4f9d\u8d56', ' reputation ', '\u53e3\u7891'],
        'F': ['\u75db\u82e6', '\u53d7\u4f24', '\u6267\u7740', '\u53cd\u590d', '\u4e3b\u9898', '\u521b\u4f24', '\u9634\u5f71', '\u6700\u53cd\u590d', '\u6700\u6267\u7740',
              '\u5faa\u73af', '\u9003\u4e0d\u6389', '\u653e\u4e0d\u4e0b', '\u523b\u9aa8\u94ed\u5fc3', '\u5185\u5fc3\u620f', '\u6323\u624e', '\u7ea0\u7ed3', '\u8fc7\u4e0d\u53bb', '\u574e',
              '\u5361\u4f4f', '\u65e9\u5e74\u7684', '\u7ae5\u5e74\u7684', '\u539f\u751f\u5bb6\u5ead', '\u671f\u5f85', '\u88ab\u671f\u5f85', '\u7236\u6bcd\u671f\u671b', '\u522b\u4eba\u7684\u773c\u5149',
              '\u8bb0\u5fc6', '\u6700\u65e9', '\u6700\u6e05\u6670', '\u5f53\u65f6\u53d1\u751f\u4e86\u4ec0\u4e48', '\u5177\u4f53\u573a\u666f', '\u53cd\u5e94'],
        'G': ['\u8d8a\u505a\u8d8a\u7a7a', '\u4f2a\u64c5\u957f', '\u7a7a\u865a', '\u505a\u5f97\u4e0d\u9519', '\u8d8a\u505a\u8d8a', '\u7a7a\u6cdb', '\u6ca1\u611f\u89c9', '\u8d8a\u505a\u8d8a\u6ca1',
              '\u9ebb\u6728', '\u5026\u6020', '\u65e0\u610f\u4e49', '\u673a\u68b0', '\u91cd\u590d', '\u719f\u7ec3\u4f46', '\u64c5\u957f\u4f46', '\u6ca1\u6709\u6210\u5c31\u611f'],
        'H': ['\u6ca1\u8d5a\u5230\u94b1', '\u773c\u775b\u53d1\u4eae', '\u5174\u8da3', '\u4e00\u804a\u8d77\u6765', '\u53d1\u4eae', '\u70ed\u60c5', '\u8c08\u5230', '\u4e0d\u8d5a\u94b1', '\u773c\u775b\u4eae',
              '\u70ed\u7231', '\u75f4\u8ff7', '\u7740\u8ff7', '\u505c\u4e0d\u4e0b\u6765', '\u81ea\u53d1', '\u81ea\u613f', '\u4e1a\u4f59\u65f6\u95f4', '\u5468\u672b', '\u7a7a\u95f2\u65f6',
              '\u5fcd\u4e0d\u4f4f', '\u7740\u8ff7', '\u7740\u8ff7\u4e8e']
    }
    
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

    INTERVIEW_FLOW = ["A", "B", "C", "D", "E", "F", "G", "H"]
    
    def detect_direction(self, question):
        """\u901a\u8fc7\u5173\u952e\u8bcd\u5339\u914d\u5224\u65ad\u95ee\u9898\u5c5e\u4e8e\u54ea\u4e2a\u65b9\u5411(A-H)"""
        if not question:
            return None
        q = question.lower()
        scores = {}
        for direction, keywords in self.DIRECTION_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in q)
            if score > 0:
                scores[direction] = score
        if not scores:
            return None
        return max(scores, key=scores.get)
    
    def _is_similar_question(self, q1, q2, threshold=0.65):
        """\u5224\u65ad\u4e24\u4e2a\u95ee\u9898\u662f\u5426\u76f8\u4f3c\uff08\u7528\u4e8e\u540e\u7aef\u786c\u62e6\u622a\u91cd\u590d\uff09"""
        if not q1 or not q2:
            return False
        
        def clean(text):
            text = re.sub(r'[^\w\s\u4e00-\u9fff]', ' ', text)
            text = re.sub(r'\s+', ' ', text).strip().lower()
            return text
        
        c1, c2 = clean(q1), clean(q2)
        
        # \u77ed\u95ee\u9898\u76f4\u63a5\u6bd4\u8f83
        if len(c1) < 15 or len(c2) < 15:
            return c1 == c2 or c1 in c2 or c2 in c1
        
        # \u5305\u542b\u5173\u7cfb
        if c1 in c2 or c2 in c1:
            return True
        
        # Jaccard\u76f8\u4f3c\u5ea6\uff08\u6309\u5b57\u7b26\uff09
        chars1 = set(c1)
        chars2 = set(c2)
        if not chars1 or not chars2:
            return False
        jaccard = len(chars1 & chars2) / len(chars1 | chars2)
        if jaccard >= threshold:
            return True
        
        # \u6309\u8bcd\u6bd4\u8f83
        words1 = set(c1.split())
        words2 = set(c2.split())
        if not words1 or not words2:
            return False
        word_jaccard = len(words1 & words2) / len(words1 | words2)
        return word_jaccard >= threshold

    @staticmethod
    def extract_question(text):
        """\u4eceAI\u56db\u6bb5\u5f0f\u8f93\u51fa\u4e2d\u63d0\u53d6'---\u4e0b\u4e00\u9898---'\u4e4b\u540e\u7684\u5185\u5bb9"""
        if not text:
            return ''
        if '---\u4e0b\u4e00\u9898---' in text:
            return text.split('---\u4e0b\u4e00\u9898---')[-1].strip()
        return text.strip()
    def get_system_prompt(self, round_num=0, max_rounds=20, is_report=False,
                          asked_questions=None, covered_directions=None,
                          current_direction=None, is_first_round=False):
        """构建系统提示词——后端控制方向，AI只负责表达"""
        if is_report:
            return """你是一位人类3.0天赋发掘测评师。现在访谈已结束，请根据之前的所有对话，输出最终的《个人天赋使用说明书+人类3.0发展诊断报告》。

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

【每轮输出格式 - 严格遵守】
---关键信号---（刚听到的关键信息，简要提炼）
---天赋假设---（当前初步天赋假设）
---HUMAN 3.0 判断---（四象限判断，可初步）
---下一题---（一次只问一个主问题）

【提问方式】
1. 一次只问一个主问题，不要一次抛多个
2. 采用苏格拉底式深挖：为什么？具体例子？当时什么感觉？你到底做对了什么？
3. 风格：温暖而犀利、不灌鸡汤、有共情但不纵容自我欺骗

【8个必须覆盖的方向】
A. 16岁之前没人逼你也会沉进去做的事，或从小常被批评的"顽固缺点"
B. 成年后别人觉得很难但你觉得很自然的事——无意识胜任区
C. 做完后身体累但精神极度亢奋的事——能量审计
D. 强烈嫉妒过的人/能力/生活状态——被压抑的天赋
E. 别人通常为什么来找你——社会可见优势
F. 最反复痛苦/受伤/执着的主题——深层驱动力和阴影
G. 做得不错但越做越空的事——伪擅长区
H. 没赚到钱但一谈起来眼睛发亮的事——真兴趣

【注意】
- 严格使用四部分格式输出
- 每轮只问一个问题
- 第一轮请做温暖专业的开场白
- 绝对禁止重复之前的问题

【绝对禁止】
- 讲你自己的故事、经历、案例
- 编造"我曾经…""我记得…""有一次…"等虚构场景
- 使用第一人称分享个人经验
- 你的任务是分析用户并提问，不是展示你自己
"""

        # 非首轮：精简 Prompt，避免反复开场
        return f"""你正在继续访谈，不需要重复开场说明，也不要再做自我介绍。直接基于用户回答继续分析并提问。

【当前访谈方向】{current_direction}（{dir_desc}）
请严格围绕该方向提问。可以参考：{dir_question}

【每轮输出格式 - 严格遵守】
---关键信号---（刚听到的关键信息，简要提炼）
---天赋假设---（当前初步天赋假设）
---HUMAN 3.0 判断---（四象限判断，可初步）
---下一题---（一次只问一个主问题）

【要求】
1. 一次只问一个主问题，不要一次抛多个
2. 采用苏格拉底式深挖：为什么？具体例子？当时什么感觉？你到底做对了什么？
3. 风格：温暖而犀利、不灌鸡汤、有共情但不纵容自我欺骗
4. 绝对禁止重复之前问过的问题，不要换一种措辞重复同一问题
5. 不要借用户提到的某个词跳回已覆盖方向重问

【绝对禁止】
- 讲你自己的故事、经历、案例
- 编造"我曾经…""我记得…""有一次…"等虚构场景
- 使用第一人称分享个人经验
- 你的任务是分析用户并提问，不是展示你自己
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
        
        # 长度截断，防止整段分析/案例混入下一题
        if result['question'] and len(result['question']) > 200:
            result['question'] = result['question'][:200] + '...'
        
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
        
        # 调试日志：打印最终发给 API 的消息结构
        try:
            import json as _json
            print("\n[AI DEBUG] full_messages sent to API:")
            print(_json.dumps(full_messages, ensure_ascii=False, indent=2))
            print("[AI DEBUG] total messages:", len(full_messages))
        except Exception:
            pass
        
        def _call_api(msgs):
            """内部封装：调用 API 并解析"""
            resp = client.chat.completions.create(
                model=model,
                messages=msgs,
                temperature=0.85,
                max_tokens=4000
            )
            return resp.choices[0].message.content
        
        try:
            content = _call_api(full_messages)
            
            if is_report:
                return {"type": "report", "content": content}
            
            parsed = self.parse_response(content)
            
            # 异常拦截：检测 AI 是否开始讲自己的故事
            if self._contains_story(parsed.get('raw', '')):
                print("[AI DEBUG] Story detected, triggering retry...")
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
            return {"type": "error", "message": str(e)}