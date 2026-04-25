# ============================================================
# 天赋类型学量表(融合Human 3.0框架)
# 40道情境迫选题,覆盖8个访谈方向(A-H)
# 输出4字母类型代码,类似MBTI
# ============================================================

# ============================================================
# 模组 I:天赋信号(12题,决定第1位:C/R/B/S)
# 对应方向:A(童年模式)、B(无意识胜任区)、E(社会可见优势)
# ============================================================
MODULE_1_QUESTIONS = [
    {
        "id": "t1",
        "direction": "A",
        "text": "16岁之前,没有人逼你,但你就是会自己沉进去做的事情,最接近以下哪项?",
        "options": [
            {"key": "a", "text": "把东西拆开研究内部结构,或者用纸笔推演各种逻辑问题", "score": {"cognitive": 2, "systemic": 0}},
            {"key": "b", "text": "写故事、画画、编歌,或者用任何方式创造自己的小世界", "score": {"relational": 2, "creative_add": 1}},
            {"key": "c", "text": "组织小伙伴一起玩、制定游戏规则、带头做点什么", "score": {"systemic": 2, "relational": 1}},
            {"key": "d", "text": "运动、手工、做模型,用身体和双手去感知和改变世界", "score": {"body": 2, "cognitive": 0}}
        ]
    },
    {
        "id": "t2",
        "direction": "A",
        "text": "小时候,你最常被大人说的一句话是什么?",
        "options": [
            {"key": "a", "text": "\u300c这孩子怎么这么多为什么\u300d", "score": {"cognitive": 2}},
            {"key": "b", "text": "\u300c这孩子真会说话/真会哄人开心\u300d", "score": {"relational": 2}},
            {"key": "c", "text": "\u300c这孩子坐不住/太能折腾了\u300d", "score": {"body": 2}},
            {"key": "d", "text": "\u300c这孩子特有主意,谁都说不过他\u300d", "score": {"systemic": 2}}
        ]
    },
    {
        "id": "t3",
        "direction": "B",
        "text": "别人觉得很难,但你觉得\u300c这不就是常识吗\u300d的事情,最接近哪类?",
        "options": [
            {"key": "a", "text": "一眼看出事情的关键矛盾或底层逻辑", "score": {"cognitive": 2}},
            {"key": "b", "text": "自然地让一群人玩到一起去、气氛变好", "score": {"relational": 2}},
            {"key": "c", "text": "快速学会一个动手技能,比如修东西、做饭、运动", "score": {"body": 2, "cognitive": 0}},
            {"key": "d", "text": "在混乱中理出头绪,把一堆人/事安排明白", "score": {"systemic": 2}}
        ]
    },
    {
        "id": "t4",
        "direction": "B",
        "text": "你帮朋友解决问题时,最常被夸的是什么?",
        "options": [
            {"key": "a", "text": "\u300c跟你聊完思路一下子清晰了\u300d", "score": {"cognitive": 2}},
            {"key": "b", "text": "\u300c跟你聊完心里舒服多了\u300d", "score": {"relational": 2}},
            {"key": "c", "text": "\u300c你怎么什么都能修/什么都会搞\u300d", "score": {"body": 2}},
            {"key": "d", "text": "\u300c谢谢你把事情安排得这么妥当\u300d", "score": {"systemic": 2}}
        ]
    },
    {
        "id": "t5",
        "direction": "E",
        "text": "在工作或学习中,别人最先注意到的你的特质是什么?",
        "options": [
            {"key": "a", "text": "分析能力很强,总能抓住重点", "score": {"cognitive": 2}},
            {"key": "b", "text": "很会照顾人/很擅长沟通", "score": {"relational": 2}},
            {"key": "c", "text": "动手能力很强,很靠谱", "score": {"body": 2}},
            {"key": "d", "text": "很有领导力/很擅长推动事情", "score": {"systemic": 2}}
        ]
    },
    {
        "id": "t6",
        "direction": "E",
        "text": "如果有人请你帮忙,最常是什么类型的求助?",
        "options": [
            {"key": "a", "text": "\u300c帮我分析一下这个问题/帮我看看这个方案有没有漏洞\u300d", "score": {"cognitive": 2}},
            {"key": "b", "text": "\u300c陪我说说话/我需要你的建议(关于人际关系)\u300d", "score": {"relational": 2}},
            {"key": "c", "text": "\u300c帮我修一下/帮我做一下这个\u300d", "score": {"body": 2}},
            {"key": "d", "text": "\u300c帮我把这个项目推进一下/帮我协调一下\u300d", "score": {"systemic": 2}}
        ]
    },
    {
        "id": "t7",
        "direction": "A",
        "text": "回想小时候,哪类游戏最能让你沉浸好几个小时忘记时间?",
        "options": [
            {"key": "a", "text": "棋类、解谜、看科普书、研究地图/百科", "score": {"cognitive": 2}},
            {"key": "b", "text": "过家家、角色扮演、编故事、画画", "score": {"relational": 2, "creative_add": 1}},
            {"key": "c", "text": "乐高、模型、做手工、户外到处跑", "score": {"body": 2}},
            {"key": "d", "text": "组织比赛、当队长、设计规则让大家玩", "score": {"systemic": 2, "relational": 1}}
        ]
    },
    {
        "id": "t8",
        "direction": "B",
        "text": "在你没刻意努力的情况下,以下哪种成就最接近你的\u300c无心插柳\u300d经历?",
        "options": [
            {"key": "a", "text": "写过的东西/分析的东西无意中被很多人认可", "score": {"cognitive": 2}},
            {"key": "b", "text": "莫名其妙成了朋友/同事之间的\u300c情感纽带\u300d人物", "score": {"relational": 2}},
            {"key": "c", "text": "随便做的东西/DIY的作品被人夸\u300c手真巧\u300d", "score": {"body": 2}},
            {"key": "d", "text": "无意中推动了一个项目/活动,大家说\u300c没你根本不行\u300d", "score": {"systemic": 2}}
        ]
    },
    {
        "id": "t9",
        "direction": "E",
        "text": "面试/自我介绍时,你最自然地强调自己哪方面?",
        "options": [
            {"key": "a", "text": "\u300c我擅长分析和思考复杂问题\u300d", "score": {"cognitive": 2}},
            {"key": "b", "text": "\u300c我擅长理解人、连接人\u300d", "score": {"relational": 2}},
            {"key": "c", "text": "\u300c我擅长动手实践,做出来的东西靠谱\u300d", "score": {"body": 2}},
            {"key": "d", "text": "\u300c我擅长推动事情落地、带领团队\u300d", "score": {"systemic": 2}}
        ]
    },
    {
        "id": "t10",
        "direction": "A",
        "text": "小时候遇到困难时,你的第一反应通常是?",
        "options": [
            {"key": "a", "text": "\u300c自己先琢磨、查资料,想通了再行动\u300d", "score": {"cognitive": 2}},
            {"key": "b", "text": "\u300c找大人或朋友倾诉,在聊天中获得方向\u300d", "score": {"relational": 2}},
            {"key": "c", "text": "\u300c直接上手试试,边做边调整\u300d", "score": {"body": 2}},
            {"key": "d", "text": "\u300c想办法调动身边资源,找人帮忙一起解决\u300d", "score": {"systemic": 2}}
        ]
    },
    {
        "id": "t11",
        "direction": "B",
        "text": "你在团队里,不自觉地就会扮演的角色是?",
        "options": [
            {"key": "a", "text": "\u300c分析者\u300d:理清逻辑、指出盲点", "score": {"cognitive": 2}},
            {"key": "b", "text": "\u300c粘合剂\u300d:凝聚人心、化解冲突", "score": {"relational": 2}},
            {"key": "c", "text": "\u300c实干家\u300d:默默把具体的事情做好", "score": {"body": 2, "systemic": 1}},
            {"key": "d", "text": "\u300c推动者\u300d:制定计划、推进进度、做决策", "score": {"systemic": 2}}
        ]
    },
    {
        "id": "t12",
        "direction": "E",
        "text": "如果你必须用一个超能力来形容自己,最接近的是?",
        "options": [
            {"key": "a", "text": "\u300c看透本质\u300d\u2014\u2014一眼看出事情/人背后的底层逻辑", "score": {"cognitive": 2}},
            {"key": "b", "text": "\u300c读心共情\u300d\u2014\u2014不需要说话就能感受到别人的情绪", "score": {"relational": 2}},
            {"key": "c", "text": "\u300c点石成金\u300d\u2014\u2014用双手把抽象想法变成实物", "score": {"body": 2, "relational": 0}},
            {"key": "d", "text": "\u300c运筹帷幄\u300d\u2014\u2014能把复杂的人和事安排得井井有条", "score": {"systemic": 2}}
        ]
    }
]

# ============================================================
# 模组 II:能量审计(10题,决定第2位:D/R/V)
# 对应方向:C(能量审计)、G(伪擅长区)
# ============================================================
MODULE_2_QUESTIONS = [
    {
        "id": "t13",
        "direction": "C",
        "text": "以下哪种工作状态让你做完后**身体累但精神反而更亢奋**?",
        "options": [
            {"key": "a", "text": "连续几小时独自深度研究一个问题", "score": {"deep": 2}},
            {"key": "b", "text": "在紧迫的Deadline下快速高效地搞定一堆事情", "score": {"rapid": 2}},
            {"key": "c", "text": "上午做A项目,下午切到B项目,晚上又搞C", "score": {"varied": 2}}
        ]
    },
    {
        "id": "t14",
        "direction": "C",
        "text": "一个理想的休息天,以下哪种方式最让你\u300c回血\u300d?",
        "options": [
            {"key": "a", "text": "独处、看书、深入思考一个感兴趣的话题", "score": {"deep": 2}},
            {"key": "b", "text": "去参加各种活动、跟不同人见面聊天", "score": {"rapid": 1, "varied": 1}},
            {"key": "c", "text": "同时进行好几个小项目(看书、听播客、打扫、做饭轮着来)", "score": {"varied": 2}}
        ]
    },
    {
        "id": "t15",
        "direction": "C",
        "text": "面对一个需要花两周的大项目,你的理想工作节奏是?",
        "options": [
            {"key": "a", "text": "分成几个大块,每当沉浸进去就一口气干三四个小时", "score": {"deep": 2}},
            {"key": "b", "text": "每天快速推进一点点,喜欢每天都有可见的进展", "score": {"rapid": 2}},
            {"key": "c", "text": "同时在几个任务间切换,避免长时间做同一件事", "score": {"varied": 2}}
        ]
    },
    {
        "id": "t16",
        "direction": "G",
        "text": "以下哪种情形最让你觉得\u300c这是在工作,不是在活着\u300d?",
        "options": [
            {"key": "a", "text": "不停地被打断,刚进入状态就被人拉去开会/回消息", "score": {"deep": 2}},
            {"key": "b", "text": "事情推进太慢,反馈周期太长,看不到成果", "score": {"rapid": 2}},
            {"key": "c", "text": "每天重复做一模一样的事情,没有任何变化", "score": {"varied": 2}}
        ]
    },
    {
        "id": "t17",
        "direction": "C",
        "text": "你的最佳状态通常在什么时间出现?",
        "options": [
            {"key": "a", "text": "夜深人静,整个世界安静下来的时候", "score": {"deep": 2}},
            {"key": "b", "text": "早晨/上午,精力充沛地开足马力的时候", "score": {"rapid": 2}},
            {"key": "c", "text": "不一定,看心情和项目,随时可能进入状态", "score": {"varied": 2}}
        ]
    },
    {
        "id": "t18",
        "direction": "G",
        "text": "你做得很熟练、别人也认可,但你自己内心\u300c越做越空\u300d的事情,最接近哪类?",
        "options": [
            {"key": "a", "text": "需要长时间独自思考但思考内容却是重复套路的", "score": {"deep": 2}},
            {"key": "b", "text": "做完了马上就消失、留不下任何痕迹的短期任务", "score": {"rapid": 2}},
            {"key": "c", "text": "看似多样但本质都是同样套路、毫无新意的", "score": {"varied": 2}}
        ]
    },
    {
        "id": "t19",
        "direction": "C",
        "text": "开会时,你的状态通常是?",
        "options": [
            {"key": "a", "text": "觉得浪费时间,更喜欢会后自己消化信息", "score": {"deep": 2}},
            {"key": "b", "text": "积极参与快速讨论,喜欢当场碰撞出结果", "score": {"rapid": 2}},
            {"key": "c", "text": "取决于会议内容和自己的状态,有高有低", "score": {"varied": 2}}
        ]
    },
    {
        "id": "t20",
        "direction": "G",
        "text": "以下哪种情况最让你感到\u300c能量泄露\u300d?",
        "options": [
            {"key": "a", "text": "被要求快速切换任务、不断被打断", "score": {"deep": 2}},
            {"key": "b", "text": "被要求长时间做一件看不到进展的事情", "score": {"rapid": 2}},
            {"key": "c", "text": "被要求只做一件事,不能碰其他感兴趣的", "score": {"varied": 2}}
        ]
    },
    {
        "id": "t21",
        "direction": "C",
        "text": "你完成一项重要工作后,最自然的恢复方式是什么?",
        "options": [
            {"key": "a", "text": "一个人静静地复盘、消化,然后再开始新的", "score": {"deep": 2}},
            {"key": "b", "text": "马上找下一个事情做/找人分享成果,保持momentum", "score": {"rapid": 2}},
            {"key": "c", "text": "完全不同的事情切换一下,换个脑子", "score": {"varied": 2}}
        ]
    },
    {
        "id": "t22",
        "direction": "G",
        "text": "如果你发现自己在\u300c伪擅长\u300d(做得好但不喜欢),最可能是因为?",
        "options": [
            {"key": "a", "text": "做了太久太深,虽然擅长但已经没有任何新鲜感了", "score": {"deep": 2}},
            {"key": "b", "text": "回应得太快太多,但从来没有人问过你真正想做的是什么", "score": {"rapid": 2}},
            {"key": "c", "text": "在不同事情间跳来跳去,但始终没专注到一个方向上", "score": {"varied": 2}}
        ]
    }
]

# ============================================================
# 模组 III:驱动力(8题,决定第3位:A/H)
# 对应方向:D(嫉妒与压抑)、F(深层痛苦)
# ============================================================
MODULE_3_QUESTIONS = [
    {
        "id": "t23",
        "direction": "D",
        "text": "看到以下哪种人,你内心会升起一丝嫉妒/不平?",
        "options": [
            {"key": "a", "text": "那些很早就知道自己热爱什么、并且一直做下去的人", "score": {"aspiration": 2}},
            {"key": "b", "text": "那些经历了痛苦但把痛苦转化成了某种美好作品的人", "score": {"healing": 2}}
        ]
    },
    {
        "id": "t24",
        "direction": "D",
        "text": "你在社交媒体上最容易\u300c眼红\u300d的,是别人的什么?",
        "options": [
            {"key": "a", "text": "对自己在做的事情充满热情,眼睛里有光", "score": {"aspiration": 2}},
            {"key": "b", "text": "经历了挫折/低谷后反而更强大、更清晰了", "score": {"healing": 2}}
        ]
    },
    {
        "id": "t25",
        "direction": "F",
        "text": "以下哪种描述最接近你内心深处反复出现的痛?",
        "options": [
            {"key": "a", "text": "感觉自己还没有找到真正让自己发光的方向", "score": {"aspiration": 2}},
            {"key": "b", "text": "感觉自己经历过某些伤害/误解/不被看见,但不知道如何转化它", "score": {"healing": 2}}
        ]
    },
    {
        "id": "t26",
        "direction": "F",
        "text": "如果用一个词形容你最大的内在驱动,最接近的是?",
        "options": [
            {"key": "a", "text": "\u300c好奇/热爱\u300d\u2014\u2014我想探索、我想创造、我想成为某个样子", "score": {"aspiration": 2}},
            {"key": "b", "text": "\u300c证明/治愈\u300d\u2014\u2014我想证明自己、我想治愈过去的某种不够好", "score": {"healing": 2}}
        ]
    },
    {
        "id": "t27",
        "direction": "D",
        "text": "当别人做了你想做但没做的事情,你的情绪是?",
        "options": [
            {"key": "a", "text": "激励\u2014\u2014\u300c原来真的可以这样,我也想要\u300d", "score": {"aspiration": 2}},
            {"key": "b", "text": "复杂\u2014\u2014\u300c为什么不是我?我是不是错过了什么?\u300d", "score": {"healing": 2}}
        ]
    },
    {
        "id": "t28",
        "direction": "F",
        "text": "你最怕自己的人生变成以下哪种样子?",
        "options": [
            {"key": "a", "text": "从来没真正热爱过什么,浑浑噩噩过完一生", "score": {"aspiration": 2}},
            {"key": "b", "text": "一直被过去的伤痛/模式困住,重复同样的遗憾", "score": {"healing": 2}}
        ]
    },
    {
        "id": "t29",
        "direction": "D",
        "text": "夜深人静时,你最常思考的问题是?",
        "options": [
            {"key": "a", "text": "\u300c我真正想要的是什么?什么让我真正快乐?\u300d", "score": {"aspiration": 2}},
            {"key": "b", "text": "\u300c我为什么会成为现在的我?过去哪些事塑造了我?\u300d", "score": {"healing": 2}}
        ]
    },
    {
        "id": "t30",
        "direction": "F",
        "text": "如果有一天你可以对过去的自己说一句话,你会说?",
        "options": [
            {"key": "a", "text": "\u300c别怕,去试试,你真正喜欢的事情终会找到你\u300d", "score": {"aspiration": 2}},
            {"key": "b", "text": "\u300c你已经做得很好了,那些伤痛会变成你的力量\u300d", "score": {"healing": 2}}
        ]
    }
]

# ============================================================
# 模组 IV:兴趣指向(10题,决定第4位:M/C/P)
# 对应方向:H(真兴趣)
# ============================================================
MODULE_4_QUESTIONS = [
    {
        "id": "t31",
        "direction": "H",
        "text": "如果不考虑钱和时间,你最愿意花一年时间去做什么?",
        "options": [
            {"key": "a", "text": "深入研究某个领域/问题,写一本书或形成一套理论", "score": {"meaning": 2}},
            {"key": "b", "text": "创造一件作品(小说/电影/专辑/产品),让世界看到", "score": {"creation": 2}},
            {"key": "c", "text": "去不同的地方和不同的人深入相处,建立有意义的连接", "score": {"people": 2}}
        ]
    },
    {
        "id": "t32",
        "direction": "H",
        "text": "聊天时,哪个话题最让你眼睛发光、滔滔不绝?",
        "options": [
            {"key": "a", "text": "某个领域的深层规律、哲学问题、人性的本质", "score": {"meaning": 2}},
            {"key": "b", "text": "你的创意/正在做的作品/想创造的东西", "score": {"creation": 2}},
            {"key": "c", "text": "关于人的故事、关系、成长经历", "score": {"people": 2}}
        ]
    },
    {
        "id": "t33",
        "direction": "H",
        "text": "以下哪种成就感对你最有吸引力?",
        "options": [
            {"key": "a", "text": "\u300c我终于想通了这个问题/这个体系\u300d", "score": {"meaning": 2}},
            {"key": "b", "text": "\u300c我终于把脑中那个东西做出来了/表达出来了\u300d", "score": {"creation": 2}},
            {"key": "c", "text": "\u300c我帮到了一个人/影响了某些人\u300d", "score": {"people": 2}}
        ]
    },
    {
        "id": "t34",
        "direction": "H",
        "text": "如果有闲暇时间,你最容易被哪种内容吸引?",
        "options": [
            {"key": "a", "text": "深度解析、知识科普、哲学/科学类内容", "score": {"meaning": 2}},
            {"key": "b", "text": "创作过程分享、设计/艺术/科技产品", "score": {"creation": 2}},
            {"key": "c", "text": "人物访谈、真人故事、关系/心理类内容", "score": {"people": 2}}
        ]
    },
    {
        "id": "t35",
        "direction": "H",
        "text": "你学习新东西时,最自然的方式是?",
        "options": [
            {"key": "a", "text": "先把理论框架搞清楚,理解底层原理", "score": {"meaning": 2}},
            {"key": "b", "text": "边做边学,做出一个东西来比什么都重要", "score": {"creation": 2}},
            {"key": "c", "text": "找到懂的人聊天/请教,在交流中理解", "score": {"people": 2}}
        ]
    },
    {
        "id": "t36",
        "direction": "H",
        "text": "你觉得有意义的工作最核心的标准是?",
        "options": [
            {"key": "a", "text": "让我能不断深入地理解和思考世界", "score": {"meaning": 2}},
            {"key": "b", "text": "让我能亲手创造出一些东西", "score": {"creation": 2}},
            {"key": "c", "text": "让我能和人有深度的互动和连接", "score": {"people": 2}}
        ]
    },
    {
        "id": "t37",
        "direction": "H",
        "text": "如果参加一个工作坊/课程,你最可能选择的是?",
        "options": [
            {"key": "a", "text": "某个领域的深度研讨会/哲学读书会", "score": {"meaning": 2}},
            {"key": "b", "text": "创意工作坊/动手造物/艺术创作", "score": {"creation": 2}},
            {"key": "c", "text": "人际关系/心理学/教练技术", "score": {"people": 2}}
        ]
    },
    {
        "id": "t38",
        "direction": "H",
        "text": "你对一个好故事的定义是?",
        "options": [
            {"key": "a", "text": "有深刻的洞察,让人觉得\u300c原来如此\u300d", "score": {"meaning": 2}},
            {"key": "b", "text": "有独特的美感/创意,让人觉得\u300c还能这样\u300d", "score": {"creation": 2}},
            {"key": "c", "text": "有人物的温度,让人觉得\u300c我懂你\u300d", "score": {"people": 2}}
        ]
    },
    {
        "id": "t39",
        "direction": "H",
        "text": "你在心流状态中,最常在做的事情是?",
        "options": [
            {"key": "a", "text": "思考/阅读/分析/推理", "score": {"meaning": 2}},
            {"key": "b", "text": "创作/设计/建造/表达", "score": {"creation": 2}},
            {"key": "c", "text": "对话/倾听/帮助/连接", "score": {"people": 2}}
        ]
    },
    {
        "id": "t40",
        "direction": "H",
        "text": "10年后,你希望别人怎么评价你?",
        "options": [
            {"key": "a", "text": "\u300c他/她对很多问题有深刻的洞见\u300d", "score": {"meaning": 2}},
            {"key": "b", "text": "\u300c他/她创造出了真正独特的东西\u300d", "score": {"creation": 2}},
            {"key": "c", "text": "\u300c他/她影响和帮助了很多人\u300d", "score": {"people": 2}}
        ]
    }
]

# ============================================================
# 全部40道题目合并
# ============================================================
ALL_QUESTIONS = MODULE_1_QUESTIONS + MODULE_2_QUESTIONS + MODULE_3_QUESTIONS + MODULE_4_QUESTIONS

# ============================================================
# 类型代码映射表(4字母代码 -> 类型名称 + 完整解读)
# ============================================================

# 第1位:天赋形态
TYPE_DIM1 = {
    "C": {"name": "认知洞察型", "desc": "你的天赋核心在于\u300c想\u300d\u2014\u2014理解复杂系统、发现底层模式、追问本质"},
    "R": {"name": "关系创造型", "desc": "你的天赋核心在于\u300c连接\u300d\u2014\u2014深度共情、网络编织、关系创造"},
    "B": {"name": "身体实践型", "desc": "你的天赋核心在于\u300c做\u300d\u2014\u2014用双手和身体去感知世界、改变世界"},
    "S": {"name": "系统引领型", "desc": "你的天赋核心在于\u300c推动\u300d\u2014\u2014在混乱中建立秩序、带领大家往前走"}
}

# 第2位:能量模式
TYPE_DIM2 = {
    "D": {"name": "深度沉浸", "desc": "你需要长时间不受打扰地专注在一件事上,才能进入最佳状态。你的能量像深潜,越往下越有惊喜。"},
    "R": {"name": "快速响应", "desc": "你在紧迫、多变、高反馈的环境中反而被激活。你的能量像短跑,爆发力强、越有挑战越兴奋。"},
    "V": {"name": "多元切换", "desc": "你在多个项目/领域间自由切换时能量最高。你的能量像万花筒,变化本身就是滋养。"}
}

# 第3位:驱动来源
TYPE_DIM3 = {
    "A": {"name": "热爱牵引型", "desc": "你被\u300c想成为什么样的人\u300d驱动。你的动力来自于对美好未来的向往、对热爱的追寻。"},
    "H": {"name": "痛苦驱动型", "desc": "你被\u300c不想再重复什么\u300d驱动。你的动力来自于对过去的反思、对伤痛的意义转化。"}
}

# 第4位:兴趣指向
TYPE_DIM4 = {
    "M": {"name": "意义建构", "desc": "你最在意的是理解世界的规律、追问人生的本质。知识、洞察、哲学是你灵魂的燃料。"},
    "C": {"name": "创造产出", "desc": "你最在意的是把脑中的东西变成现实。表达、建造、设计是你与世界的对话方式。"},
    "P": {"name": "与人连接", "desc": "你最在意的是人与人之间的深度连接。倾听、影响、联结是你生命的核心动力。"}
}

# ============================================================
# 完整解读库:15个最具代表性的类型画像
# 其余组合根据维度描述自动合成解读
# ============================================================
DETAILED_REPORTS = {
    "CDAM": {
        "name": "深度思想者",
        "tagline": "在独处的深渊里,打捞那些所有人都看不见的真相。",
        "strength": "你天生具备独立、深度思考的能力。你不需要外界刺激就能沉浸到一个问题中,享受思维本身的乐趣。你的天赋在于\u300c看透\u300d\u2014\u2014看到别人看不到的底层逻辑和系统关联。",
        "watch_out": "警惕过于沉浸在自己的思维中而脱离现实。注意区分\u300c真知\u300d和\u300c思维反刍\u300d。",
        "best_environment": "需要大块不受打扰的时间、容忍长时间沉默的工作环境、对深度而非速度的认可。",
        "human30_insight": "你的童年(A)就显现了认知倾向,无意识胜任区(B)在分析和洞察,他人(E)也认可你的思考力。你的能量(C)来自深度沉浸,而非表面的快速响应。你的驱动来自对真理的热爱(A),而非过去的伤痛。你的兴趣(H)直指意义本身。",
        "development_advice": "不要浪费时间去模仿那些\u300c快速行动者\u300d。你的优势在于想清楚再走,每一步都很扎实。找到需要深度思考的领域,你就是不可替代的。"
    },
    "CDAC": {
        "name": "哲思创造者",
        "tagline": "想得很深,做得很美。思想是你的土壤,创造是你的果实。",
        "strength": "你兼具深度思考的能力和创造表达的冲动。你不会止步于\u300c想通\u300d,而是想把\u300c想通的东西\u300d变成某种可见的成果。",
        "watch_out": "小心陷入\u300c追求完美作品\u300d而迟迟不行动的陷阱。完成比完美更重要。",
        "best_environment": "需要独立思考的空间,也需要输出和展示的渠道。适合研究+创作结合的工作。",
        "human30_insight": "你的认知天赋(A/B/E)与创造指向(H)结合,形成\u300c思而后作\u300d的独特路径。",
        "development_advice": "把思想产品化。不要只是思考,把思考变成文章、课程、作品。你的思想值得被更多人看到。"
    },
    "CDAP": {
        "name": "思想传道者",
        "tagline": "当你想通了一件事,你最大的快乐是把它讲给所有人听。",
        "strength": "你的深度思考最终指向的是人\u2014\u2014你想用你的洞察去启发、影响、帮助别人。",
        "watch_out": "注意区分\u300c别人需要被启发\u300d和\u300c你想启发别人\u300d。不是所有人都准备好了接受你的深度洞察。",
        "best_environment": "需要独处思考的时间+与他人的深度交流机会。适合教育、咨询、教练等角色。",
        "human30_insight": "你的认知天赋和人际指向形成互补,让你成为一个\u300c有深度的连接者\u300d。",
        "development_advice": "学会\u300c降维沟通\u300d\u2014\u2014把你的深度思考用别人能懂的语言表达出来。这是你最大的杠杆。"
    },
    "CDHM": {
        "name": "伤痛哲人",
        "tagline": "你思考的深度,来自于你曾经在黑暗中的凝视。",
        "strength": "你的深度思考并非凭空而来,而是被某种深层痛苦驱动。这使得你的洞察有一种\u300c过来人\u300d的力量\u2014\u2014你不是在讲理论,你是在总结自己走过的路。",
        "watch_out": "警惕用思考来代替面对情绪。有时候你不是在\u300c想\u300d,你是在\u300c躲\u300d。",
        "best_environment": "需要一个允许被脆弱、允许慢慢来的环境。你的节奏和别人不一样。",
        "human30_insight": "你的痛苦(F)转化为了追问意义的动力(M),这是\u300c创伤后成长\u300d的典型路径。",
        "development_advice": "把伤痛写成作品。你的经历是别人无法复制的\u300c独家内容\u300d。你是苦难的意义制造者。"
    },
    "CDHC": {
        "name": "火焰转化者",
        "tagline": "那些没有把你打倒的,正在变成你手中最独特的作品。",
        "strength": "痛苦驱动+创造指向,这是最强大的创作动力组合。很多伟大的艺术家和创造者都是这个类型\u2014\u2014他们把痛苦炼成了光。",
        "watch_out": "防止把创作变成痛苦的循环。你需要学会在创作中疗愈,而非在创作中反复撕裂伤口。",
        "best_environment": "允许情绪起伏、允许不完美的创作空间。你需要被理解和被接纳。",
        "human30_insight": "你的嫉妒(D)指向的是那些把痛苦转化成了作品的人\u2014\u2014因为你知道你也可以。",
        "development_advice": "创作就是你的疗愈。不要等\u300c准备好\u300d才创作,创作本身就是整理自己的过程。"
    },
    "CDHP": {
        "name": "共情疗愈者",
        "tagline": "因为你痛过,所以你能真正理解别人的痛。",
        "strength": "你的痛苦不仅变成了觉察,还变成了对他人的理解和关爱。你是天生的\u300c疗愈型人物\u300d\u2014\u2014无论是作为朋友、伴侣还是专业人士。",
        "watch_out": "小心共情耗竭。别人的痛苦可能触发你自己的伤痛。设置边界是对所有人的保护。",
        "best_environment": "需要有意义的人际连接,也需要独处来消化和恢复。",
        "human30_insight": "你的深层痛苦(F)让你天然地理解他人的痛苦,这是你与人连接(P)的独特深度。",
        "development_advice": "你在助人中也在助己。找到那些和你有相似经历的人,你的存在就是他们的希望。"
    },
    "RDAC": {
        "name": "故事建筑家",
        "tagline": "你用关系编织的网,比任何架构都结实。而你会把它写成故事。",
        "strength": "关系天赋+深度沉浸+热爱牵引+创造产出:你在关系中汲取能量和素材,然后用深度专注把它转化成作品。你的关系不是消耗,而是养料。",
        "watch_out": "不要让创作占据了关系本身。别忘了享受关系本身,而不只是把它们当成素材。",
        "best_environment": "需要深度的人际关系和不受打扰的创作时间。",
        "human30_insight": "你的无意识胜任区(B)在关系,能量(C)在沉浸,兴趣(H)在创造\u2014\u2014三位一体。",
        "development_advice": "你的关系就是你的作品。写下来、拍下来、画下来。你有能力把人与人的故事变成艺术。"
    },
    "RDAP": {
        "name": "灵魂连接者",
        "tagline": "你对人的深度理解,是你送给这个世界最好的礼物。",
        "strength": "关系天赋+深度沉浸+热爱牵引+与人连接:你不是泛泛的社交,而是深度的、一个对一个的连接。你享受和人慢慢变熟、慢慢变深的过程。",
        "watch_out": "可能因为过度投入少数关系而忽视更广阔的社交网络。偶尔也要打开天线。",
        "best_environment": "小规模、高质量的人际互动环境。",
        "human30_insight": "你的能量来自深度而非广度,在关系中也是如此。",
        "development_advice": "不用强迫自己做\u300c外向者\u300d。深度连接本身就是稀缺能力。做好一个\u300c值得深交的人\u300d。"
    },
    "SRAC": {
        "name": "战略实干家",
        "tagline": "你有运筹帷幄的脑,也有让事情落地的脚。",
        "strength": "系统天赋+快速响应+热爱牵引+创造产出:你能看大局、推执行、出成果,是典型的\u300c做成事的人\u300d。",
        "watch_out": "小心变成\u300c无情的结果机器\u300d。关注人的感受和执行效率同样重要。",
        "best_environment": "需要明确目标、快速反馈、可见进展的工作环境。",
        "human30_insight": "你的他人反馈(E)在推动力,能量(C)在快速响应\u2014\u2014你是天生的项目推动者。",
        "development_advice": "找到能让你\u300c指点江山\u300d又能\u300c落地执行\u300d的舞台。创业、项目管理、总导演\u2014\u2014都是你的主场。"
    },
    "SVAP": {
        "name": "社群编织者",
        "tagline": "你能在人群中发现秩序,在秩序中创造温度。",
        "strength": "系统天赋+多元切换+热爱牵引+与人连接:你擅长把人组织起来,但同时切换多个社群/项目能让你保持能量。",
        "watch_out": "注意别变成\u300c救火队长\u300d。建立规则和流程,别什么事都自己顶上。",
        "best_environment": "需要多样性、人际互动和可见的影响力。",
        "human30_insight": "你的能量(V)来自多样切换,如果整天做一件事,你会枯萎。",
        "development_advice": "你的天赋在于\u300c编织\u300d\u2014\u2014把人、资源、想法连接成网。社群运营、社区建设是你的天然舞台。"
    },
    "BDAC": {
        "name": "身体诗人",
        "tagline": "你的身体知道大脑不知道的事。把它表达出来。",
        "strength": "身体天赋+深度沉浸+热爱牵引+创造产出:你的身体不仅是工具,更是你与世界对话的方式。你通过身体来理解和创造。",
        "watch_out": "身体能力会随年龄变化。尽早把身体经验转化为可传承的体系或作品。",
        "best_environment": "需要有动手空间、允许长时间专注实践的环境。",
        "human30_insight": "你的童年(A)就在动手,能量(C)源自沉浸式操作\u2014\u2014你的身体就是你的第一语言。",
        "development_advice": "记录你的身体经验。不论通过视频、教学还是产品,把\u300c只可意会\u300d变成\u300c可以言传\u300d。"
    },
    "BVHC": {
        "name": "野火手艺人",
        "tagline": "你的不安来自于停滞。你的安全来自于一直动、一直变、一直做。",
        "strength": "身体天赋+多元切换+痛苦驱动+创造产出:你对停滞有极大的恐惧,这反而让你不断尝试新领域、新技能、新作品。你是一个动态创造者。",
        "watch_out": "注意不要因为恐惧停滞而跳过深耕。有时候慢下来是为了走更远。",
        "best_environment": "需要变化、挑战和创作空间。固定重复的工作会让你枯竭。",
        "human30_insight": "你的痛苦(F)来自\u300c被束缚感\u300d,这解释了你为什么如此需要多元切换(V)。",
        "development_advice": "你的力量在于\u300c跨界\u300d。把不同领域的身体经验融合起来,你会找到独特的生态位。"
    },
    "CHAM": {
        "name": "灯塔思考者",
        "tagline": "你的头脑是你的灯塔,指引你自己也照亮别人。",
        "strength": "认知天赋+痛苦驱动+热爱牵引+意义建构:你既有理性的深度,又有情感的厚度。你思考不是为了炫耀,而是为了理解自己的人生和他人的处境。",
        "watch_out": "在\u300c热爱牵引\u300d和\u300c痛苦驱动\u300d之间可能有内在拉扯。允许自己两者都拥有。",
        "best_environment": "需要能同时容纳思考深度和情感温度的领域。",
        "human30_insight": "你罕见地同时拥有热爱(A)和痛苦(H)两种驱动\u2014\u2014这意味着你既有理想主义的向上力,也有现实主义的向内力。",
        "development_advice": "拥抱你的复杂性。你不是简单的\u300c思考者\u300d或\u300c感受者\u300d,你是两者的辩证统一体。"
    },
    "SHAC": {
        "name": "风暴引领者",
        "tagline": "越是混乱的局面,你越是能站出来。因为你心里有一张别人看不到的地图。",
        "strength": "系统天赋+痛苦驱动+热爱牵引+创造产出:你有在混乱中建立秩序的天赋,而且这种天赋可能是从曾经的失控经历中生长出来的。",
        "watch_out": "不要变成\u300c控制狂\u300d。有些混乱需要被容忍,而非被整理。",
        "best_environment": "需要有挑战性、需要推动力的环境。创业团队、转型期的组织是你的舞台。",
        "human30_insight": "你的痛苦(F)可能来自曾经的\u300c失控感\u300d,这让你现在极度擅长\u300c掌控\u300d\u2014\u2014这是一种积极的转化。",
        "development_advice": "你就是那个在暴风雨中别人会看向的人。接受这个角色,发展与之匹配的能力。"
    }
}

# ============================================================
# 评分辅助函数
# ============================================================
def calculate_type_code(answers):
    """
    根据40道题的答案计算4字母类型代码
    输入:answers = {"t1": "a", "t2": "c", ...}
    输出:{"code": "CDAM", "dimensions": {...}, "scores": {...}}
    """
    # 初始化各维度分数
    dim1_scores = {"cognitive": 0, "relational": 0, "body": 0, "systemic": 0}
    dim2_scores = {"deep": 0, "rapid": 0, "varied": 0}
    dim3_scores = {"aspiration": 0, "healing": 0}
    dim4_scores = {"meaning": 0, "creation": 0, "people": 0}

    # 计分:模组 I(t1-t12)-> 第1位
    for q in MODULE_1_QUESTIONS:
        choice = answers.get(q["id"])
        if not choice:
            continue
        for opt in q["options"]:
            if opt["key"] == choice:
                for dim, score in opt["score"].items():
                    if dim == "creative_add":
                        dim1_scores["relational"] += score
                    else:
                        dim1_scores[dim] = dim1_scores.get(dim, 0) + score
                break

    # 计分:模组 II(t13-t22)-> 第2位
    for q in MODULE_2_QUESTIONS:
        choice = answers.get(q["id"])
        if not choice:
            continue
        for opt in q["options"]:
            if opt["key"] == choice:
                for dim, score in opt["score"].items():
                    dim2_scores[dim] = dim2_scores.get(dim, 0) + score
                break

    # 计分:模组 III(t23-t30)-> 第3位
    for q in MODULE_3_QUESTIONS:
        choice = answers.get(q["id"])
        if not choice:
            continue
        for opt in q["options"]:
            if opt["key"] == choice:
                for dim, score in opt["score"].items():
                    dim3_scores[dim] = dim3_scores.get(dim, 0) + score
                break

    # 计分:模组 IV(t31-t40)-> 第4位
    for q in MODULE_4_QUESTIONS:
        choice = answers.get(q["id"])
        if not choice:
            continue
        for opt in q["options"]:
            if opt["key"] == choice:
                for dim, score in opt["score"].items():
                    dim4_scores[dim] = dim4_scores.get(dim, 0) + score
                break

    # 找出各维度最高分
    code_1 = max(dim1_scores, key=dim1_scores.get)
    code_2 = max(dim2_scores, key=dim2_scores.get)
    code_3 = max(dim3_scores, key=dim3_scores.get)
    code_4 = max(dim4_scores, key=dim4_scores.get)

    # 映射到缩写字母
    map1 = {"cognitive": "C", "relational": "R", "body": "B", "systemic": "S"}
    map2 = {"deep": "D", "rapid": "R", "varied": "V"}
    map3 = {"aspiration": "A", "healing": "H"}
    map4 = {"meaning": "M", "creation": "C", "people": "P"}

    code = map1[code_1] + map2[code_2] + map3[code_3] + map4[code_4]

    # 查找详细报告
    report = DETAILED_REPORTS.get(code)

    # 如果没有精确匹配,生成默认报告
    if not report:
        d1 = TYPE_DIM1[map1[code_1]]
        d2 = TYPE_DIM2[map2[code_2]]
        d3 = TYPE_DIM3[map3[code_3]]
        d4 = TYPE_DIM4[map4[code_4]]
        report = {
            "name": f"{d1['name']}·{d2['name']}型",
            "tagline": f"你的天赋在于{d1['desc']}。",
            "strength": f"你天生具备{d1['name']}的天赋,能量来自{d2['name']}模式,由{d3['name']}驱动,兴趣指向{d4['name']}。",
            "watch_out": "注意平衡各维度的发展,避免单一维度的过度使用。",
            "best_environment": f"最适合你的环境是能发挥{d1['name']}能力、匹配{d2['name']}节奏的地方。",
            "human30_insight": f"Human 3.0框架分析:你的童年(A)和他人反馈(E)指向{d1['name']},能量审计(C)显示{d2['name']}模式,嫉妒/痛苦(D/F)揭示{d3['name']}驱动,真兴趣(H)指向{d4['name']}。",
            "development_advice": f"在{d1['name']}和{d4['name']}的交汇处找到你的独特生态位。"
        }

    return {
        "code": code,
        "dimensions": {
            "dim1": {"key": code_1, "code": map1[code_1], "info": TYPE_DIM1[map1[code_1]]},
            "dim2": {"key": code_2, "code": map2[code_2], "info": TYPE_DIM2[map2[code_2]]},
            "dim3": {"key": code_3, "code": map3[code_3], "info": TYPE_DIM3[map3[code_3]]},
            "dim4": {"key": code_4, "code": map4[code_4], "info": TYPE_DIM4[map4[code_4]]}
        },
        "scores": {
            "dim1": dim1_scores,
            "dim2": dim2_scores,
            "dim3": dim3_scores,
            "dim4": dim4_scores
        },
        "report": report
    }