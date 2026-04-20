# 一级量表：天赋维度筛查（20题，5维度，每维度4题）
# 评分：1=完全不像我 2=不太像 3=一般 4=比较像 5=非常像我

PRIMARY_SCALE = {
    "title": "天赋维度筛查量表",
    "description": "通过20道标准化题目，快速识别你的天赋倾向维度。每题请根据'有多像我'选择1-5分。",
    "dimensions": {
        "cognitive": {
            "name": "认知洞察型",
            "description": "擅长逻辑分析、模式识别、抽象思考",
            "questions": [
                {
                    "id": "c1",
                    "text": "看到复杂信息时，我会本能地想要拆解它的底层结构",
                    "reverse": False
                },
                {
                    "id": "c2",
                    "text": "我能很快发现两件事物之间的隐藏关联或规律",
                    "reverse": False
                },
                {
                    "id": "c3",
                    "text": "别人还在描述现象，我已经在思考背后的原因和机制",
                    "reverse": False
                },
                {
                    "id": "c4",
                    "text": "我擅长用框架、模型或分类法来整理混乱的信息",
                    "reverse": False
                }
            ]
        },
        "creative": {
            "name": "创造表达型",
            "description": "擅长原创想法、内容创作、艺术表达",
            "questions": [
                {
                    "id": "cr1",
                    "text": "我经常有'如果换个方式会怎样'的想法冒出来",
                    "reverse": False
                },
                {
                    "id": "cr2",
                    "text": "我享受把抽象概念转化为具体作品或内容的过程",
                    "reverse": False
                },
                {
                    "id": "cr3",
                    "text": "我善于用比喻、故事或视觉化方式表达想法",
                    "reverse": False
                },
                {
                    "id": "cr4",
                    "text": "限制和规则常常激发我找到别出心裁的解决方案",
                    "reverse": False
                }
            ]
        },
        "social": {
            "name": "社交连接型",
            "description": "擅长共情理解、人际沟通、关系构建",
            "questions": [
                {
                    "id": "s1",
                    "text": "我能敏锐察觉对话中对方没直接说出来的情绪和需要",
                    "reverse": False
                },
                {
                    "id": "s2",
                    "text": "我在群体中常常自然成为协调矛盾、照顾各方感受的人",
                    "reverse": False
                },
                {
                    "id": "s3",
                    "text": "一对一深度交流比大规模社交更让我有能量",
                    "reverse": False
                },
                {
                    "id": "s4",
                    "text": "我擅长把不同背景的人连接起来，促成合作",
                    "reverse": False
                }
            ]
        },
        "systemic": {
            "name": "系统推动型",
            "description": "擅长战略规划、组织协调、目标驱动",
            "questions": [
                {
                    "id": "sy1",
                    "text": "面对模糊目标时，我会本能地把它拆解成可执行的步骤",
                    "reverse": False
                },
                {
                    "id": "sy2",
                    "text": "我享受带领团队或项目从0到1推进的过程",
                    "reverse": False
                },
                {
                    "id": "sy3",
                    "text": "我擅长识别系统中的瓶颈，并推动关键节点改变",
                    "reverse": False
                },
                {
                    "id": "sy4",
                    "text": "别人还在犹豫时，我已经做出了判断并开始行动",
                    "reverse": False
                }
            ]
        },
        "physical": {
            "name": "身体感知型",
            "description": "擅长动手操作、身体协调、感官敏锐",
            "questions": [
                {
                    "id": "p1",
                    "text": "我擅长通过身体动作或动手操作来理解和解决问题",
                    "reverse": False
                },
                {
                    "id": "p2",
                    "text": "我对环境中的细微变化（声音、气味、触感）很敏感",
                    "reverse": False
                },
                {
                    "id": "p3",
                    "text": "学习新技能时，'做一遍'比'听十遍'更有效",
                    "reverse": False
                },
                {
                    "id": "p4",
                    "text": "我在体育、手工、烹饪或类似需要身体协调的活动中有优势",
                    "reverse": False
                }
            ]
        }
    },
    "scoring": {
        "options": [
            {"value": 1, "label": "完全不像我"},
            {"value": 2, "label": "不太像"},
            {"value": 3, "label": "一般"},
            {"value": 4, "label": "比较像"},
            {"value": 5, "label": "非常像我"}
        ]
    }
}

# 二级量表：天赋类型锁定（每个一级维度下有3个细化类型）
SECONDARY_SCALE = {
    "cognitive": {
        "name": "认知洞察型",
        "types": {
            "architect": {
                "name": "系统架构师",
                "description": "擅长搭建复杂系统的整体框架，看到各部分如何联动"
            },
            "detective": {
                "name": "模式侦探",
                "description": "擅长从数据和信息中发现隐藏规律，做预测和归因"
            },
            "philosopher": {
                "name": "本质追问者",
                "description": "擅长追问底层逻辑和第一原理，重新定义问题"
            }
        },
        "questions": [
            {"id": "cog_1", "text": "比起解决具体问题，我更享受设计解决问题的整体框架", "mapping": {"architect": 2, "detective": 0, "philosopher": 1}},
            {"id": "cog_2", "text": "我经常在杂乱的数据中一眼看出别人看不到的趋势", "mapping": {"architect": 0, "detective": 2, "philosopher": 1}},
            {"id": "cog_3", "text": "别人问我'怎么做'时，我第一反应是追问'为什么要做'", "mapping": {"architect": 0, "detective": 0, "philosopher": 2}},
            {"id": "cog_4", "text": "我擅长把一个复杂项目拆解成清晰的模块和接口", "mapping": {"architect": 2, "detective": 1, "philosopher": 0}},
            {"id": "cog_5", "text": "我享受验证假设、排除干扰变量的过程", "mapping": {"architect": 0, "detective": 2, "philosopher": 1}},
            {"id": "cog_6", "text": "同一个问题，我倾向于从多个根本不同的角度重新审视", "mapping": {"architect": 1, "detective": 0, "philosopher": 2}},
            {"id": "cog_7", "text": "我擅长设计流程和规则，让系统自动运转", "mapping": {"architect": 2, "detective": 1, "philosopher": 0}},
            {"id": "cog_8", "text": "我能在信息不完整时做出合理的推断", "mapping": {"architect": 1, "detective": 2, "philosopher": 0}},
            {"id": "cog_9", "text": "我常常会质疑公认的'常识'和前提假设", "mapping": {"architect": 0, "detective": 1, "philosopher": 2}},
            {"id": "cog_10", "text": "比起追求完美答案，我更想找到问题的正确定义方式", "mapping": {"architect": 1, "detective": 0, "philosopher": 2}},
        ]
    },
    "creative": {
        "name": "创造表达型",
        "types": {
            "storyteller": {
                "name": "故事编织者",
                "description": "擅长用叙事和情感打动人，把复杂概念变生动"
            },
            "visionary": {
                "name": "视觉构想家",
                "description": "擅长在脑海中构建画面，把抽象想法可视化"
            },
            "inventor": {
                "name": "组合创新者",
                "description": "擅长把看似无关的元素组合成新事物"
            }
        },
        "questions": [
            {"id": "cre_1", "text": "我习惯用故事、案例或场景来表达观点", "mapping": {"storyteller": 2, "visionary": 1, "inventor": 0}},
            {"id": "cre_2", "text": "我的创意常常以画面、色彩或空间形式先出现", "mapping": {"storyteller": 0, "visionary": 2, "inventor": 1}},
            {"id": "cre_3", "text": "我喜欢把不同领域的概念混搭，产生新的东西", "mapping": {"storyteller": 0, "visionary": 1, "inventor": 2}},
            {"id": "cre_4", "text": "别人说我讲事情很有感染力，能让人产生共鸣", "mapping": {"storyteller": 2, "visionary": 0, "inventor": 1}},
            {"id": "cre_5", "text": "我能闭着眼睛在脑海中'看到'一个设计的全貌", "mapping": {"storyteller": 1, "visionary": 2, "inventor": 0}},
            {"id": "cre_6", "text": "我享受'无中生有'的过程，从0创造一个东西", "mapping": {"storyteller": 1, "visionary": 0, "inventor": 2}},
            {"id": "cre_7", "text": "我擅长把握节奏和情绪曲线，知道什么时候该铺垫、什么时候该高潮", "mapping": {"storyteller": 2, "visionary": 1, "inventor": 0}},
            {"id": "cre_8", "text": "我对颜色、排版、空间布局有直觉般的敏感", "mapping": {"storyteller": 0, "visionary": 2, "inventor": 1}},
            {"id": "cre_9", "text": "我经常在完全不同的东西之间发现可以连接的桥梁", "mapping": {"storyteller": 1, "visionary": 0, "inventor": 2}},
            {"id": "cre_10", "text": "如果让我选择，我更愿意做一个'开创者'而不是'优化者'", "mapping": {"storyteller": 1, "visionary": 1, "inventor": 2}},
        ]
    },
    "social": {
        "name": "社交连接型",
        "types": {
            "empath": {
                "name": "深度共情者",
                "description": "擅长感知他人情绪，做心灵的翻译和容器"
            },
            "connector": {
                "name": "网络编织者",
                "description": "擅长连接人和资源，构建关系网络"
            },
            "mediator": {
                "name": "冲突调解者",
                "description": "擅长在分歧中找到共识，平衡多方利益"
            }
        },
        "questions": [
            {"id": "soc_1", "text": "我常常能感知到别人没说出口的情绪和需要", "mapping": {"empath": 2, "connector": 1, "mediator": 0}},
            {"id": "soc_2", "text": "我擅长把不同背景、不同圈子的人介绍给彼此", "mapping": {"empath": 0, "connector": 2, "mediator": 1}},
            {"id": "soc_3", "text": "在冲突中，我能理解各方立场并找到中间地带", "mapping": {"empath": 1, "connector": 0, "mediator": 2}},
            {"id": "soc_4", "text": "别人愿意向我倾诉心事，即使我们关系不算特别近", "mapping": {"empath": 2, "connector": 0, "mediator": 1}},
            {"id": "soc_5", "text": "我的通讯录/社交圈里横跨很多不同领域", "mapping": {"empath": 0, "connector": 2, "mediator": 1}},
            {"id": "soc_6", "text": "我能让原本对立的两方坐下来谈，并达成妥协", "mapping": {"empath": 1, "connector": 0, "mediator": 2}},
            {"id": "soc_7", "text": "我在倾听时，常常能说出对方心里想说但说不出来的感受", "mapping": {"empath": 2, "connector": 1, "mediator": 0}},
            {"id": "soc_8", "text": "我喜欢组织聚会、活动或项目，把人聚起来", "mapping": {"empath": 0, "connector": 2, "mediator": 1}},
            {"id": "soc_9", "text": "在团队中，我往往是那个安抚情绪、恢复信任的人", "mapping": {"empath": 1, "connector": 0, "mediator": 2}},
            {"id": "soc_10", "text": "比起一对一，我更享受把一群人凝聚成共同体", "mapping": {"empath": 0, "connector": 2, "mediator": 1}},
        ]
    },
    "systemic": {
        "name": "系统推动型",
        "types": {
            "strategist": {
                "name": "战略制定者",
                "description": "擅长看全局、定方向、规划长期路径"
            },
            "executor": {
                "name": "落地执行者",
                "description": "擅长把计划变成结果，克服阻力推进"
            },
            "leader": {
                "name": "团队引领者",
                "description": "擅长激励他人、建立文化、放大团队能力"
            }
        },
        "questions": [
            {"id": "sys_1", "text": "我习惯先看清全局和长期趋势，再决定当下行动", "mapping": {"strategist": 2, "executor": 0, "leader": 1}},
            {"id": "sys_2", "text": "我擅长把模糊的目标变成清晰的任务清单并推动完成", "mapping": {"strategist": 0, "executor": 2, "leader": 1}},
            {"id": "sys_3", "text": "我能让团队成员发挥出比平时更高的水平", "mapping": {"strategist": 1, "executor": 0, "leader": 2}},
            {"id": "sys_4", "text": "面对不确定性，我能快速做出判断并承担决策后果", "mapping": {"strategist": 2, "executor": 1, "leader": 0}},
            {"id": "sys_5", "text": "我擅长识别障碍并找到绕过或击破它的方法", "mapping": {"strategist": 1, "executor": 2, "leader": 0}},
            {"id": "sys_6", "text": "我更看重团队的氛围和凝聚力，而不仅仅是任务完成", "mapping": {"strategist": 0, "executor": 0, "leader": 2}},
            {"id": "sys_7", "text": "我善于权衡利弊，在复杂局面中找到最优路径", "mapping": {"strategist": 2, "executor": 1, "leader": 0}},
            {"id": "sys_8", "text": "我有一种'必须把事情做成'的内在驱动力", "mapping": {"strategist": 0, "executor": 2, "leader": 1}},
            {"id": "sys_9", "text": "我擅长识别每个人的优势并安排到合适的位置", "mapping": {"strategist": 1, "executor": 0, "leader": 2}},
            {"id": "sys_10", "text": "当别人还在讨论时，我已经开始验证可行性了", "mapping": {"strategist": 1, "executor": 2, "leader": 0}},
        ]
    },
    "physical": {
        "name": "身体感知型",
        "types": {
            "craftsman": {
                "name": "精细工匠",
                "description": "擅长精确操作、细节打磨、手眼协调"
            },
            "athlete": {
                "name": "身体艺术家",
                "description": "擅长身体表达、运动协调、空间感知"
            },
            "sensory": {
                "name": "感官探索者",
                "description": "擅长通过感官获取信息，对细微差异极度敏感"
            }
        },
        "questions": [
            {"id": "phy_1", "text": "我擅长需要精细操作和耐心的手工或技术活", "mapping": {"craftsman": 2, "athlete": 0, "sensory": 1}},
            {"id": "phy_2", "text": "我在运动、舞蹈或肢体表达方面有天赋或热情", "mapping": {"craftsman": 0, "athlete": 2, "sensory": 1}},
            {"id": "phy_3", "text": "我能分辨出极其细微的声音、气味、味道或触感差异", "mapping": {"craftsman": 1, "athlete": 0, "sensory": 2}},
            {"id": "phy_4", "text": "我享受亲手把一个东西从粗糙打磨到完美的过程", "mapping": {"craftsman": 2, "athlete": 0, "sensory": 1}},
            {"id": "phy_5", "text": "我对身体在空间中的位置和运动轨迹有清晰感知", "mapping": {"craftsman": 0, "athlete": 2, "sensory": 1}},
            {"id": "phy_6", "text": "别人觉得相似的东西，我能感受到它们之间微妙的不同", "mapping": {"craftsman": 1, "athlete": 0, "sensory": 2}},
            {"id": "phy_7", "text": "我擅长修理、组装、制作等需要动手能力的活动", "mapping": {"craftsman": 2, "athlete": 1, "sensory": 0}},
            {"id": "phy_8", "text": "在压力大时，身体活动（运动、散步等）比思考更能让我恢复", "mapping": {"craftsman": 0, "athlete": 2, "sensory": 1}},
            {"id": "phy_9", "text": "我能通过触摸或观察质地来判断材料的质量", "mapping": {"craftsman": 1, "athlete": 0, "sensory": 2}},
            {"id": "phy_10", "text": "我倾向于'先做了再说'，在实践中学习和调整", "mapping": {"craftsman": 1, "athlete": 2, "sensory": 0}},
        ]
    }
}
