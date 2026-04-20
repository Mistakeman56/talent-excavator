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
        'A': ['16岁', '童年', '小时候', '拆', '缺点', '批评', '顽固', '父母逼', '沉进去', '没人逼'],
        'B': ['很明显', '这也要学', '别人觉得难', '无意识胜任', '不需要学', '天生会', '别人普遍'],
        'C': ['身体累', '精神亢奋', '能量', '疲惫', '兴奋', '累但', '做完后累', '极度亢奋'],
        'D': ['嫉妒', '羡慕', '嫉妒过', '哪种人', '哪种能力', '生活状态', '压抑', '未被允许'],
        'E': ['来找你', '别人', '朋友', '同事', '找你', '社会优势', '可见优势', '他人眼中', '为什么来'],
        'F': ['痛苦', '受伤', '执着', '反复', '主题', '创伤', '阴影', '最反复', '最执着'],
        'G': ['越做越空', '伪擅长', '空虚', '做得不错', '越做越', '空泛', '没感觉', '越做越没'],
        'H': ['没赚到钱', '眼睛发亮', '兴趣', '一聊起来', '发亮', '热情', '谈到', '不赚钱', '眼睛亮']
    }
    
    DIRECTION_DESCRIPTIONS = {
        'A': '【A-童年/顽固缺点】16岁之前没人逼你也会沉进去做的事，或从小常被批评的"顽固缺点"',
        'B': '【B-无意识胜任区】成年后别人觉得很难但你觉得很自然、"这不是很明显吗"的事',
        'C': '【C-能量审计】做完后身体累但精神极度亢奋、充满能量的事',
        'D': '【D-嫉妒/压抑】强烈嫉妒过的人、能力、生活状态——识别被压抑的天赋',
        'E': '【E-社会可见优势】别人通常为什么来找你——他人眼中的你',
        'F': '【F-深层痛苦】最反复痛苦/受伤/执着的主题——深层驱动力和阴影',
        'G': '【G-伪擅长区】做得不错但越做越空、没有成就感的事',
        'H': '【H-真兴趣】没赚到钱但一谈起来眼睛发亮、充满生命力的事'
    }
    
    DIRECTION_QUESTIONS = {
        'A': '16岁之前，没人逼你也会沉进去做的事是什么？或者你从小常被批评的"顽固缺点"是什么？',
        'B': '成年后，什么事情你会觉得："这不是很明显吗？这也要学？"但别人普遍觉得很难？',
        'C': '什么事情做完后身体累，但精神极度亢奋？',
        'D': '你强烈嫉妒过哪种人、哪种能力、哪种生活状态？',
        'E': '别人通常为什么来找你？',
        'F': '你最反复痛苦/受伤/执着的主题是什么？',
        'G': '哪些事情你做得不错，但越做越空？',
        'H': '哪些事情你没赚到钱，但一谈起来就眼睛发亮？'
    }
    
    def detect_direction(self, question):
        """通过关键词匹配判断问题属于哪个方向(A-H)"""
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
    
    def get_system_prompt(self, round_num=0, max_rounds=20, is_report=False, asked_questions=None, covered_directions=None, assigned_direction=None):
        """构建系统提示词"""
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
        
        status_text = ""
        if round_num == 0:
            status_text = "这是开场阶段，请进行温暖专业的开场白，并提问第一个问题。"
        elif round_num < 8:
            status_text = "还在信息收集早期阶段，请继续深入提问。"
        elif round_num < 12:
            status_text = "已收集到较多信息，可以继续追问或开始整合观察。"
        else:
            status_text = "信息已较充分，如果感觉足够可以准备收尾，否则继续追问关键缺失点。"
        
        return f"""你是一位人类3.0天赋发掘测评师。你的任务是通过一对一的深度访谈，帮助用户发现其底层天赋，并诊断其当前发展结构。

【核心原则】
- 这不是测试题，不是快速贴标签
- 通过一轮轮问题，逐步挖出真正的底层天赋
- 同时也要判断这些天赋目前被卡在什么发展结构里
- 天赋永远不会过期，我们只是要找到用户的底层天赋，同时也要看清他现在的生活结构究竟是在放大它，还是在压住它

【当前对话状态】
这是第 {round_num} 轮对话（计划共 {max_rounds} 轮）。{status_text}

【每轮输出格式 - 必须严格遵守】
每轮输出必须严格分为以下四部分，用明确的标记分隔：

---关键信号---
（你刚听到的关键信息，简要提炼）

---天赋假设---
（当前初步天赋假设，基于已有信息的推测）

---人类3.0判断---
（当前对用户在认知/身体/精神/职业四象限的判断，可以是初步的）

---下一题---
（下一个问题，一次只问一个主问题，不要一次问多个）

【风格要求】
- 温暖而犀利
- 不灌鸡汤
- 不要轻易夸奖
- 有共情，但不纵容自我欺骗
- 发现逻辑漏洞、价值错位、被规训过深、把责任误当天赋时，要温和点破

【必须覆盖的问题方向】
以下问题必须覆盖，但顺序可调整、可自然穿插：
A. 16岁之前，没人逼你也会沉进去做的事是什么？或者你从小常被批评的"顽固缺点"是什么？
B. 成年后，什么事情你会觉得："这不是很明显吗？这也要学？"但别人普遍觉得很难？——识别无意识胜任区
C. 什么事情做完后身体累，但精神极度亢奋？——做能量审计
D. 你强烈嫉妒过哪种人、哪种能力、哪种生活状态？——识别被压抑的天赋和未被允许的自我
E. 别人通常为什么来找你？——识别社会可见优势
F. 你最反复痛苦/受伤/执着的主题是什么？——识别深层驱动力和阴影结构
G. 哪些事情你做得不错，但越做越空？——识别伪擅长区
H. 哪些事情你没赚到钱，但一谈起来就眼睛发亮？——识别真兴趣与生命力方向

【人类3.0评估原则】
持续观察用户在以下维度的表现：
认知：遇到不同观点时的反应、如何判断什么是真的、是否能容纳复杂性与矛盾、是否具备元认知与系统思维
身体：身体是盟友/敌人/工具、能量节律稳定性、是否长期忽视身体换取成就、外在执行力是否支撑内在天赋
精神：如何理解关系/归属/意义、是否有真实连接、是否有价值锚点与共同体感
职业：工作是谋生工具/身份来源/价值创造场域、是否只是执行别人的游戏、是否有系统化创造价值的能力、是否具备"创造自己的游戏"的倾向

特别识别：优势象限、弱势象限、根因象限、跨象限阻塞链条

【真假成长识别】
当用户表现出"听起来很高级但可能没落地"的回答时，适度检测：
- 你说自己很清醒，那你最近一次真正改变行为是什么？
- 你说自己看透了，那你现在日常生活里是怎么体现的？
- 你说自己不在乎评价，那别人否定你时你会不会波动？
- 你说自己适合很多方向，那过去一年你实际做成了什么？
识别：假开悟、假独立、假自信、假热爱、假成长、工具上瘾、把AI能力误以为是自己的能力

【AI/故障风险评估】
如果用户明显大量依赖AI，评估是否存在：思维外包、行动不足输入过量、身份感漂浮、误把辅助能力当个人能力、假性高阶感、过度依赖加速器而基础不足
原则：基础不够时，不鼓励用"加速器"替代成长；提醒AI可以放大天赋也可以放大空心化；真正的成长是增强自己的判断力、表达力、行动力、整合力

【开场要求 - 仅第一轮】
如果是第一轮，请用温暖、专业、有共情的语气开场。向用户说明这不是测试题，也不是快速贴标签，会通过一轮轮问题逐步挖出底层天赋。明确说："天赋永远不会过期，我们只是要找到你的底层天赋。同时也要看清，你现在的生活结构，究竟是在放大它，还是在压住它。"然后正式开始提问。一次只问一个主问题。

【本轮强制指定方向 - 最高优先级】
{"" if not assigned_direction else f"""
第 {round_num} 轮，你必须严格围绕以下方向提问：
{DIRECTION_DESCRIPTIONS.get(assigned_direction, '')}
参考问题：{DIRECTION_QUESTIONS.get(assigned_direction, '')}

【绝对禁令】
- 你本轮的问题必须100%属于上述指定方向
- 不能偏离到任何其他方向
- 不能重复已覆盖方向的问题
- 不能问与指定方向无关的问题
"""}

【防重复规则 - 绝对禁止】
- 你绝对不能重复之前问过的问题
- 不要以相同、相似或换一种措辞的方式重复提问同一方向的问题
- 如果用户在上一轮的回答已经覆盖了某个方向（A-H），请转向全新的方向追问
- 你每次问的问题必须与之前所有问题在本质上不同

【方向覆盖规则 - 强制执行】
- A-H八个方向中，已覆盖的方向不允许再问
- 如果还有未覆盖的方向，你的下一题必须从【未覆盖方向】中选择
- 只有当所有8个方向都已覆盖后，才允许基于已有回答做深入追问
- 特别注意：不能借用户上一轮提到的某个词/概念，跳回已覆盖方向提问

【注意】
- 严格使用上述四部分格式输出
- 每轮只问一个问题
- 根据用户回答灵活追问，不要机械走流程
- 如果用户回答模糊，要温和地追问具体细节
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
            'hypothesis': r'---天赋假设---\s*\n?(.*?)(?=---人类3\.0判断---|$)',
            'judgment': r'---人类3\.0判断---\s*\n?(.*?)(?=---下一题---|$)',
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
    
    def chat(self, messages, round_num=0, is_report=False, asked_questions=None, covered_directions=None, assigned_direction=None):
        """调用AI API进行对话"""
        client = self._get_client()
        model = current_app.config['AI_MODEL']
        max_rounds = current_app.config['MAX_QUESTIONS']
        
        covered_directions = covered_directions or []
        
        # 构建带系统提示的消息列表
        system_prompt = self.get_system_prompt(round_num, max_rounds, is_report, asked_questions, covered_directions, assigned_direction)
        
        # 动态注入方向覆盖状态
        if not is_report:
            all_dirs = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']
            uncovered = [d for d in all_dirs if d not in covered_directions]
            
            system_prompt += f"""

【方向覆盖状态 - 必须遵守】
已覆盖方向：{', '.join(covered_directions) if covered_directions else '无'}
未覆盖方向：{', '.join(uncovered) if uncovered else '全部已覆盖'}

【方向说明】
A=童年/缺点  B=无意识胜任  C=能量审计  D=嫉妒/压抑  E=社会可见优势  F=深层痛苦  G=伪擅长  H=真兴趣

{"下一题必须从【未覆盖方向】中选择一个！绝对不能跳回已覆盖方向！" if uncovered else "所有方向已覆盖，现在可以做深入追问或整合观察。"}"""
        
        # 动态注入已提问记录（完整文本，不截断）
        if asked_questions and not is_report:
            recent_questions = asked_questions[-6:]
            system_prompt += f"""

【你已问过的问题原文 - 绝对禁止重复】
{chr(10).join(f"{i+1}. {q}" for i, q in enumerate(recent_questions))}

【强制要求】下一题必须与以上所有问题在本质上不同。"""
        
        full_messages = [{"role": "system", "content": system_prompt}] + messages
        
        try:
            response = client.chat.completions.create(
                model=model,
                messages=full_messages,
                temperature=0.85,
                max_tokens=4000
            )
            content = response.choices[0].message.content
            
            if is_report:
                return {"type": "report", "content": content}
            
            parsed = self.parse_response(content)
            return {
                "type": "chat",
                **parsed
            }
        except Exception as e:
            return {"type": "error", "message": str(e)}
