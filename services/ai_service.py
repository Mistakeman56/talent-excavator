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
        'A': ['16岁', '童年', '小时候', '拆', '缺点', '批评', '顽固', '父母逼', '沉进去', '没人逼',
              '年幼', '少年', '成长过程', '本性', '天性', '小的时候', '初中', '小学'],
        'B': ['很明显', '这也要学', '别人觉得难', '无意识胜任', '不需要学', '天生会', '别人普遍',
              '自然而然', '本能', '直觉', '没学过', '无师自通', '这也要教', '别人做不到'],
        'C': ['身体累', '精神亢奋', '能量', '疲惫', '兴奋', '累但', '做完后累', '极度亢奋',
              '疲惫但', '充电', '耗电', '燃', '倦怠', '心流', 'flow', '沉浸', '忘时间', '时间消失'],
        'D': ['嫉妒', '羡慕', '嫉妒过', '哪种人', '哪种能力', '生活状态', '压抑', '未被允许',
              '想成为', '渴望成为', '眼红', '不甘心', '为什么他能', '凭什么', '向往'],
        'E': ['来找你', '别人', '朋友', '同事', '找你', '社会优势', '可见优势', '他人眼中', '为什么来',
              '求助', '请教', '口碑', '认可', '信任', '依赖', ' reputation ', '口碑'],
        'F': ['痛苦', '受伤', '执着', '反复', '主题', '创伤', '阴影', '最反复', '最执着',
              '循环', '逃不掉', '放不下', '刻骨铭心', '内心戏', '挣扎', '纠结', '过不去', '坎',
              '卡住', '早年的', '童年的', '原生家庭', '期待', '被期待', '父母期望', '别人的眼光',
              '记忆', '最早', '最清晰', '当时发生了什么', '具体场景', '反应'],
        'G': ['越做越空', '伪擅长', '空虚', '做得不错', '越做越', '空泛', '没感觉', '越做越没',
              '麻木', '倦怠', '无意义', '机械', '重复', '熟练但', '擅长但', '没有成就感'],
        'H': ['没赚到钱', '眼睛发亮', '兴趣', '一聊起来', '发亮', '热情', '谈到', '不赚钱', '眼睛亮',
              '热爱', '痴迷', '着迷', '停不下来', '自发', '自愿', '业余时间', '周末', '空闲时',
              '忍不住', '着迷', '着迷于']
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
    
    def _is_similar_question(self, q1, q2, threshold=0.65):
        """判断两个问题是否相似（用于后端硬拦截重复）"""
        if not q1 or not q2:
            return False
        
        def clean(text):
            text = re.sub(r'[^\w\s\u4e00-\u9fff]', ' ', text)
            text = re.sub(r'\s+', ' ', text).strip().lower()
            return text
        
        c1, c2 = clean(q1), clean(q2)
        
        # 短问题直接比较
        if len(c1) < 15 or len(c2) < 15:
            return c1 == c2 or c1 in c2 or c2 in c1
        
        # 包含关系
        if c1 in c2 or c2 in c1:
            return True
        
        # Jaccard相似度（按字符）
        chars1 = set(c1)
        chars2 = set(c2)
        if not chars1 or not chars2:
            return False
        jaccard = len(chars1 & chars2) / len(chars1 | chars2)
        if jaccard >= threshold:
            return True
        
        # 按词比较
        words1 = set(c1.split())
        words2 = set(c2.split())
        if not words1 or not words2:
            return False
        word_jaccard = len(words1 & words2) / len(words1 | words2)
        return word_jaccard >= threshold
    
    def get_system_prompt(self, round_num=0, max_rounds=20, is_report=False, asked_questions=None, covered_directions=None):
        """构建精简版系统提示词——后端不再干预方向，完全交给AI自主选择"""
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
        
        # 构建方向覆盖状态文本
        all_dirs = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']
        covered = covered_directions or []
        uncovered = [d for d in all_dirs if d not in covered]
        
        coverage_text = ""
        if covered:
            coverage_text += f"已覆盖方向：{', '.join(covered)}\n"
        if uncovered:
            coverage_text += f"未覆盖方向：{', '.join(uncovered)}"
        else:
            coverage_text += "所有8个方向均已覆盖，现在可以做深入追问或整合观察。"
        
        # 已提问记录（简短列出最近5个）
        asked_text = ""
        if asked_questions:
            recent = asked_questions[-5:]
            asked_text = "\n\n【你已问过的问题 - 禁止重复】\n" + "\n".join(f"{i+1}. {q[:60]}..." if len(q) > 60 else f"{i+1}. {q}" for i, q in enumerate(recent))
        
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

【当前对话状态】第 {round_num} 轮（计划共 {max_rounds} 轮）。{status_text}

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

【8个必须覆盖的方向 - 全部覆盖前不要重复问同一方向的初始问题】
A. 16岁之前没人逼你也会沉进去做的事，或从小常被批评的"顽固缺点"
B. 成年后别人觉得很难但你觉得很自然的事——无意识胜任区
C. 做完后身体累但精神极度亢奋的事——能量审计
D. 强烈嫉妒过的人/能力/生活状态——被压抑的天赋
E. 别人通常为什么来找你——社会可见优势
F. 最反复痛苦/受伤/执着的主题——深层驱动力和阴影
G. 做得不错但越做越空的事——伪擅长区
H. 没赚到钱但一谈起来眼睛发亮的事——真兴趣

【方向覆盖状态 - 参考】
{coverage_text}{asked_text}

【防重复规则 - 绝对禁止】
- 绝对不能重复之前问过的问题，不要换一种措辞重复同一问题
- 8个方向全部覆盖前，不要重复问同一方向的"初始问题"
- 如果还有未覆盖方向，优先从未覆盖方向中选择下一个问题
- 你可以根据对话节奏自然追问，但不要借用户提到的某个词跳回已覆盖方向重问

【注意】
- 严格使用四部分格式输出
- 每轮只问一个问题
- 根据用户回答灵活追问，不要机械走流程
- 第一轮请做温暖专业的开场白
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
    
    def chat(self, messages, round_num=0, is_report=False, asked_questions=None, covered_directions=None):
        """调用AI API进行对话——后端不再干预方向选择"""
        client = self._get_client()
        model = current_app.config['AI_MODEL']
        max_rounds = current_app.config['MAX_QUESTIONS']
        
        covered_directions = covered_directions or []
        
        # 构建精简版系统提示词
        system_prompt = self.get_system_prompt(round_num, max_rounds, is_report, asked_questions, covered_directions)
        
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
