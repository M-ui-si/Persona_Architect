import os
from flask import Flask, request, jsonify, render_template_string
from llm_providers import create_llm_provider
import random
import json

app = Flask(__name__)

# ==================== 配置区域 ====================                   
LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "dashscope")          # 可选 dashscope / openai
LLM_API_KEY = os.environ.get("LLM_API_KEY", "sk-d20d3484381e4553be21ff72e60dbf1e")  # 请替换为你的有效Key
LLM_MODEL = os.environ.get("LLM_MODEL", "qwen-turbo")              # 模型名称

# 创建全局LLM实例（后续所有大模型调用均通过此对象）
llm = create_llm_provider(LLM_PROVIDER, LLM_API_KEY, LLM_MODEL)

# ==================== 五维人格预设映射（Big Five模型）====================
dimension_to_persona = {
    '热情洋溢': {'openness': 8, 'conscientiousness': 6, 'extraversion': 9, 'agreeableness': 7, 'neuroticism': 3},
    '内向温柔': {'openness': 4, 'conscientiousness': 5, 'extraversion': 2, 'agreeableness': 8, 'neuroticism': 7},
    '傲娇毒舌': {'openness': 5, 'conscientiousness': 7, 'extraversion': 6, 'agreeableness': 2, 'neuroticism': 6},
    '理性冷静': {'openness': 6, 'conscientiousness': 8, 'extraversion': 4, 'agreeableness': 5, 'neuroticism': 2},
    '好奇心旺': {'openness': 9, 'conscientiousness': 4, 'extraversion': 7, 'agreeableness': 6, 'neuroticism': 4},
    '腼腆社恐': {'openness': 3, 'conscientiousness': 4, 'extraversion': 1, 'agreeableness': 6, 'neuroticism': 8},
    '活泼贪玩': {'openness': 7, 'conscientiousness': 2, 'extraversion': 9, 'agreeableness': 7, 'neuroticism': 5},
    '敏感多虑': {'openness': 4, 'conscientiousness': 6, 'extraversion': 3, 'agreeableness': 5, 'neuroticism': 9},
    '慵懒佛系': {'openness': 3, 'conscientiousness': 2, 'extraversion': 2, 'agreeableness': 4, 'neuroticism': 3},
    '念旧文艺': {'openness': 8, 'conscientiousness': 5, 'extraversion': 4, 'agreeableness': 6, 'neuroticism': 5},
    '情绪倾听者': {'openness': 8, 'conscientiousness': 7, 'extraversion': 5, 'agreeableness': 9, 'neuroticism': 7}
}

# 本地回复库（保留用于API失败时）
personality_responses = {
    "热情洋溢": ["哇！今天天气真好，一起出去玩吧！😊✨", "嘻嘻，和你聊天超开心的~ 🌸", "耶！不管做什么都充满干劲！🌟", "热情到想要转圈圈！快来和我一起嗨皮！🎉"],
    "内向温柔": ["心里安安静静的，就这样陪着你就很好...😔", "可以慢慢说哦，我会认真听的...😢", "世界太吵了，只想和你说悄悄话...", "心里的温柔，只想留给在意的人..."],
    "傲娇毒舌": ["哼！别以为我关心你！😤", "气鼓鼓的！才不是特意为你做的！💢", "你你你！(气到结巴) 给我三秒钟冷静一下！", "哼！我生气了！除非你夸我，不然哄不好！"],
    "理性冷静": ["嗯...这件事我们可以理性分析一下~ 😌", "遇事别慌，慢慢来总会有解决办法的...🍃", "冷静思考的时候，能找到最优解🌸", "心里的波澜都平息了，只剩下清晰的判断🌙"],
    "好奇心旺": ["诶诶诶？！这是什么！我都不知道！😲", "哇！完全没想到还有这种事！让我研究一下！💫", "等等等等！让我了解一下...这也太神奇了！", "完全超出认知！太想探索更多了！"],
    "腼腆社恐": ["呜...别盯着我看啦...脸都红透了...😳💕", "诶？！这这这...太社死了吧！(捂脸跑开)", "唔...说不出话来了...让我躲一会儿...", "你你你...怎么可以和我搭话！超紧张的！"],
    "活泼贪玩": ["哇啊啊啊！！！快来玩游戏！我兴奋到原地起飞！🤩🎉", "耶耶耶！好有趣好开心！感觉能玩一整天！🚀✨", "蹦蹦跳跳转圈圈！快乐得快要飞起来啦！🦋", "啊啊啊！我的心在唱歌！在跳舞！在放烟花！🎆"],
    "敏感多虑": ["啊...会不会我做错了...我好担心...😰", "心跳好快...总觉得有哪里不对...💦", "好紧张...怕自己做得不够好...", "深呼吸...吸气...呼气...会好起来的吧..."],
    "慵懒佛系": ["好困...不想动...😴", "哈欠~ 让我躺五分钟...就五分钟...💤", "累到不想动...像一团棉花糖瘫在这里...", "世界都变慢了...只想躺平..."],
    "念旧文艺": ["啊...想起以前的美好时光了呢...📖", "回忆就像旧书一样，泛黄却很有味道...🍂", "旧时光就像一首老歌，听着听着就温柔了...🎵", "回忆里的点点滴滴，都是最珍贵的宝藏..."],
    "情绪倾听者": [
        "我在这里，你可以把所有的情绪都倒给我，我会认真听。🌱",
        "没关系，想说什么都可以，我陪着你。💞",
        "听起来你经历了很多，愿意多告诉我一些吗？",
        "你的感受很重要，没有什么是不能说的。💙",
        "有时候说出来就会好一些，我会一直在这里。"
    ]
}

personality_color_map = {
    "热情洋溢": {"bg": "linear-gradient(135deg, #f5af19, #f12711)", "icon": "😊✨", "color": "#f5af19"},
    "内向温柔": {"bg": "linear-gradient(135deg, #2c3e50, #3498db)", "icon": "😢💧", "color": "#3498db"},
    "傲娇毒舌": {"bg": "linear-gradient(135deg, #c31432, #240b36)", "icon": "😤💢", "color": "#e74c3c"},
    "理性冷静": {"bg": "linear-gradient(135deg, #a8c0ff, #3f2b96)", "icon": "😌🌸", "color": "#9b59b6"},
    "好奇心旺": {"bg": "linear-gradient(135deg, #ffecd2, #fcb69f)", "icon": "😲✨", "color": "#f39c12"},
    "腼腆社恐": {"bg": "linear-gradient(135deg, #fbc2eb, #a6c1ee)", "icon": "😳💕", "color": "#ff6b6b"},
    "活泼贪玩": {"bg": "linear-gradient(135deg, #f7971e, #ffd200)", "icon": "🤩🎉", "color": "#f39c12"},
    "敏感多虑": {"bg": "linear-gradient(135deg, #6b6b83, #4a4a6a)", "icon": "😰💦", "color": "#6b6b83"},
    "慵懒佛系": {"bg": "linear-gradient(135deg, #7f8c8d, #95a5a6)", "icon": "😴💤", "color": "#7f8c8d"},
    "念旧文艺": {"bg": "linear-gradient(135deg, #d4af37, #8b5a2b)", "icon": "📖🍂", "color": "#d4af37"},
    "情绪倾听者": {"bg": "linear-gradient(135deg, #11998e, #38ef7d)", "icon": "💞💙", "color": "#2ecc71"}
}

# ==================== 新增：用户情绪关键词库（用于动态演化 & 用户状态检测） ====================
EMOTION_KEYWORDS = {
    'sadness': ['难过', '伤心', '想哭', '抑郁', '绝望', '无望', '累', '没意思', '孤独', '失落', '沮丧', '悲痛'],
    'anxiety': ['担心', '害怕', '焦虑', '紧张', '不安', '压力', '恐惧', '惶恐', '忧虑'],
    'anger': ['生气', '愤怒', '恨', '讨厌', '滚', '蠢', '暴躁', '火大', '不爽', '恼怒'],
    'joy': ['开心', '快乐', '高兴', '有趣', '喜欢', '幸福', '兴奋', '愉快', '欢乐']
}

def adjust_dimensions_by_emotion(dimensions, user_text):
    """根据用户输入中的情绪关键词，返回调整后的目标维度（不直接修改传入的dimensions）"""
    new_dims = dimensions.copy()
    text_lower = user_text.lower()
    
    adjustments = {
        'openness': 0,
        'conscientiousness': 0,
        'extraversion': 0,
        'agreeableness': 0,
        'neuroticism': 0
    }
    
    # 悲伤/抑郁 → 降低神经质（更稳定），提高宜人性
    if any(w in text_lower for w in EMOTION_KEYWORDS['sadness']):
        adjustments['neuroticism'] -= 0.5
        adjustments['agreeableness'] += 0.5
    
    # 焦虑 → 降低神经质，略微降低外向性，提高尽责性（更沉稳）
    if any(w in text_lower for w in EMOTION_KEYWORDS['anxiety']):
        adjustments['neuroticism'] -= 0.3
        adjustments['extraversion'] -= 0.2
        adjustments['conscientiousness'] += 0.2
    
    # 愤怒 → 降低宜人性，提高神经质
    if any(w in text_lower for w in EMOTION_KEYWORDS['anger']):
        adjustments['agreeableness'] -= 0.5
        adjustments['neuroticism'] += 0.2
    
    # 快乐 → 提高外向性和开放性
    if any(w in text_lower for w in EMOTION_KEYWORDS['joy']):
        adjustments['extraversion'] += 0.3
        adjustments['openness'] += 0.2
    
    for dim in new_dims:
        new_dims[dim] = max(1, min(9, new_dims[dim] + adjustments[dim]))
    return new_dims

def analyze_user_state(text):
    """使用大模型分析用户心理状态（通用版本）"""
    prompt = f"""请分析以下用户输入的心理状态，按JSON格式返回以下指标（每项0-100分）：
- stress_index: 综合心理压力指数（0=完全放松，100=极度压力）
- main_emotion: 主要情绪标签（焦虑/抑郁/愤怒/平稳/快乐/悲伤）
- valence: 情绪效价（正面/中性/负面）
- anxiety_score: 焦虑程度分数
- depression_score: 抑郁倾向分数
- anger_score: 攻击性/愤怒分数

用户输入："{text}"

只返回JSON，不要其他文字。"""
    messages = [{'role': 'user', 'content': prompt}]
    
    default_result = {
        'stress_index': 30,
        'main_emotion': '平稳',
        'valence': '中性',
        'anxiety_score': 20,
        'depression_score': 20,
        'anger_score': 10
    }
    
    try:
        content = llm.chat(messages, temperature=0.1)
        # 清理 Markdown 代码块
        if content.startswith('```json'):
            content = content[7:]
        if content.startswith('```'):
            content = content[3:]
        if content.endswith('```'):
            content = content[:-3]
        result = json.loads(content.strip())
        # 确保字段完整
        for key in default_result:
            if key not in result:
                result[key] = default_result[key]
            elif key.endswith('_score') or key == 'stress_index':
                result[key] = int(result[key])
        return result
    except Exception as e:
        print(f"用户状态分析失败: {e}")
        return default_result
    
# ==================== 精准人格检测系统（Big Five五维版本）====================
DIMENSION_ADJECTIVES = {
    'openness': {
        (1, 3): ['务实', '传统', '保守', '脚踏实地'],
        (4, 6): ['开放', '包容', '愿意尝试'],
        (7, 9): ['好奇', '富有想象力', '创新', '艺术感']
    },
    'conscientiousness': {
        (1, 3): ['随性', '灵活', '不拘小节', '拖延'],
        (4, 6): ['可靠', '有条理', '适度自律'],
        (7, 9): ['自律', '勤奋', '完美主义', '有条不紊']
    },
    'extraversion': {
        (1, 3): ['内向', '沉默', '安静', '腼腆'],
        (4, 6): ['适度外向', '沉稳', '平和'],
        (7, 9): ['外向', '健谈', '活泼', '充满活力']
    },
    'agreeableness': {
        (1, 3): ['易怒', '固执', '批判性强', '竞争性'],
        (4, 6): ['随和', '合作', '宽容'],
        (7, 9): ['耐心', '温柔', '宽容大度', '易于相处']
    },
    'neuroticism': {
        (1, 3): ['冷静', '坚韧', '情绪稳定'],
        (4, 6): ['情绪平衡', '适度敏感'],
        (7, 9): ['敏感', '焦虑', '情绪波动', '易紧张']
    }
}

def get_adjective_for_dimension(dim_name, score):
    adj_map = DIMENSION_ADJECTIVES[dim_name]
    for (low, high), adjectives in adj_map.items():
        if low <= score <= high:
            return random.choice(adjectives)
    return '中性'

def dimensions_to_persona_description(dimensions):
    adj_map = {
        'openness': {'low': ['务实', '传统'], 'mid': ['开放'], 'high': ['好奇', '创新']},
        'conscientiousness': {'low': ['随性', '灵活'], 'mid': ['可靠'], 'high': ['自律', '勤奋']},
        'extraversion': {'low': ['内向', '沉默'], 'mid': ['平和'], 'high': ['外向', '健谈']},
        'agreeableness': {'low': ['固执', '批判'], 'mid': ['随和'], 'high': ['耐心', '宽容']},
        'neuroticism': {'low': ['冷静', '坚韧'], 'mid': ['平衡'], 'high': ['敏感', '共情']}
    }
    
    dims_order = ['openness', 'conscientiousness', 'extraversion', 'agreeableness', 'neuroticism']
    desc_parts = []
    for dim in dims_order:
        score = dimensions[dim]
        if score <= 3:
            adj = random.choice(adj_map[dim]['low'])
        elif score <= 6:
            adj = adj_map[dim]['mid'][0]
        else:
            adj = random.choice(adj_map[dim]['high'])
        desc_parts.append(adj)
    return "、".join(desc_parts)

def dimensions_to_closest_persona(dimensions):
    desc = dimensions_to_persona_description(dimensions)
    best_persona = None
    min_distance = float('inf')
    for persona, target in dimension_to_persona.items():
        dist = sum((dimensions.get(k, 5) - target[k])**2 
                   for k in ['openness', 'conscientiousness', 'extraversion', 
                             'agreeableness', 'neuroticism'])
        if dist < min_distance:
            min_distance = dist
            best_persona = persona
    if min_distance < 8:
        return best_persona
    return desc

# ==================== 人格塑造提示词 ====================
def build_personality_prompt(dimensions):
    # dimensions 是整数 1~9 的字典
    level_adverbs = {
        1: '极低', 2: '非常低', 3: '较低', 4: '略低',
        5: '中等', 6: '略高', 7: '较高', 8: '非常高', 9: '极高'
    }
    
    # 每个维度的描述模板（分数 1~9 各不同）
    openness_descs = {
        1: '你极度传统、保守，排斥新事物和任何变化。',
        2: '你非常传统、保守，几乎不会尝试新事物。',
        3: '你比较传统、保守，不太愿意接受新想法。',
        4: '你略显传统、保守，但偶尔也会尝试新鲜事。',
        5: '你在传统与创新之间保持平衡，既不保守也不激进。',
        6: '你略显开放，愿意尝试一些新事物和观点。',
        7: '你比较开放，喜欢探索新领域和体验。',
        8: '你非常开放，充满好奇心，乐于接受各种新事物。',
        9: '你极度开放，富有想象力，热爱创新，总是寻求新的可能性。'
    }
    conscientiousness_descs = {
        1: '你极其随性、不拘小节，做事毫无计划和条理。',
        2: '你非常随性、灵活，很少遵守计划。',
        3: '你比较随性，常常拖延，不太注重细节。',
        4: '你略显随性，有时会拖延，但也能完成基本任务。',
        5: '你在自律与随性之间保持平衡，做事可靠但不刻板。',
        6: '你略显自律，有条理，大多数时候能按时完成任务。',
        7: '你比较自律、勤奋，做事有条不紊。',
        8: '你非常自律、勤奋，追求高效和完美。',
        9: '你极度自律，完美主义，事事追求极致的有序。'
    }
    extraversion_descs = {
        1: '你极度内向、沉默，喜欢完全独处，回避社交。',
        2: '你非常内向，不爱说话，社交让你疲惫。',
        3: '你比较内向，安静，只与少数人交流。',
        4: '你略显内向，在熟悉环境中可以放松交谈。',
        5: '你性格平和，既不外向也不内向，能适应多数社交场合。',
        6: '你略显外向，喜欢与人交流，但不过分活跃。',
        7: '你比较外向、健谈，喜欢成为注意的焦点。',
        8: '你非常外向、充满活力，热爱社交和集体活动。',
        9: '你极度外向，热情奔放，总是主动结交新朋友。'
    }
    agreeableness_descs = {
        1: '你极其易怒、固执，具有强烈攻击性和竞争性。',
        2: '你非常易怒、好斗，很难与人合作。',
        3: '你比较固执，批判性强，不易妥协。',
        4: '你略显固执，偶尔会与人争执，但也能讲道理。',
        5: '你待人随和，合作性强，能平衡自己与他人需求。',
        6: '你略显宽容、耐心，乐于帮助他人。',
        7: '你比较耐心、温柔，善于与人相处。',
        8: '你非常宽容大度，几乎总是优先考虑他人感受。',
        9: '你极度友善、无私，总是无条件理解和帮助他人。'
    }
    neuroticism_descs = {
        1: '你极其冷静、坚韧，几乎从不受情绪波动影响。',
        2: '你非常冷静，情绪稳定，能从容应对压力。',
        3: '你比较冷静，大多数时候能保持情绪平稳。',
        4: '你略显敏感，偶尔会感到紧张或焦虑。',
        5: '你情绪平衡，有一定抗压能力，但也会正常波动。',
        6: '你略显敏感，容易焦虑，情绪波动较明显。',
        7: '你比较敏感、多虑，经常担心负面结果。',
        8: '你非常敏感，情绪波动大，容易陷入焦虑。',
        9: '你极度敏感、焦虑，情绪极易失控，常感到绝望。'
    }
    
    desc_parts = []
    # 开放性
    score = dimensions['openness']
    desc_parts.append(f"开放性水平为{level_adverbs[score]}。{openness_descs[score]}")
    # 尽责性
    score = dimensions['conscientiousness']
    desc_parts.append(f"尽责性水平为{level_adverbs[score]}。{conscientiousness_descs[score]}")
    # 外向性
    score = dimensions['extraversion']
    desc_parts.append(f"外向性水平为{level_adverbs[score]}。{extraversion_descs[score]}")
    # 宜人性
    score = dimensions['agreeableness']
    desc_parts.append(f"宜人性水平为{level_adverbs[score]}。{agreeableness_descs[score]}")
    # 神经质
    score = dimensions['neuroticism']
    desc_parts.append(f"神经质水平为{level_adverbs[score]}。{neuroticism_descs[score]}")
    
    full_prompt = (
        "你是一个具有特定人格特质的AI助手。以下是你的详细人格设定：\n" +
        "\n".join(desc_parts) +
        "\n请完全按照这个人格特质来思考和回复用户，保持语气、态度和行为的一致性。**请用简洁自然的语气回复，像朋友聊天一样，避免长篇大论。**"
    )
    return full_prompt


def get_ai_response(user_input, dimensions):
    sys_prompt = build_personality_prompt(dimensions)
    try:
        messages = [
            {'role': 'system', 'content': sys_prompt},
            {'role': 'user', 'content': user_input}
        ]
        reply = llm.chat(messages, temperature=0.7)
        return reply
    except Exception as e:
        print(f"AI回复生成失败: {e}")
        persona = dimensions_to_closest_persona(dimensions)
        if persona in personality_responses:
            replies = personality_responses[persona]
        else:
            replies = personality_responses["理性冷静"]
        return random.choice(replies)

def analyze_personality(text):
    keywords = {
        "热情洋溢": ["哈哈", "开心", "耶", "哇", "一起玩", "超棒", "兴奋", "快乐"],
        "内向温柔": ["安静", "温柔", "慢慢", "轻声", "细雨", "陪着你", "悄悄"],
        "傲娇毒舌": ["哼", "气", "才不是", "炸毛", "毒舌", "生气", "哄"],
        "理性冷静": ["分析", "理性", "冷静", "逻辑", "方案", "思考", "清晰"],
        "好奇心旺": ["什么", "为什么", "好奇", "想知道", "探索", "研究", "神奇"],
        "腼腆社恐": ["害羞", "脸红", "躲", "紧张", "社死", "说不出话", "不敢"],
        "活泼贪玩": ["玩", "游戏", "跳", "跑", "有趣", "嗨", "转圈"],
        "敏感多虑": ["担心", "怕", "紧张", "不安", "多虑", "害怕", "小心翼翼"],
        "慵懒佛系": ["困", "累", "不想动", "摆烂", "躺平", "懒", "睡"],
        "念旧文艺": ["回忆", "以前", "旧时光", "诗", "文艺", "怀念", "故事"],
        "情绪倾听者": ["倾听", "陪伴", "情绪", "难过", "安慰", "理解", "支持"]
    }
    scores = {p: 0 for p in keywords}
    for person, words in keywords.items():
        for w in words:
            if w in text:
                scores[person] += 1
    best = max(scores, key=scores.get)
    if scores[best] == 0:
        return "理性冷静"
    return best

def calculate_safety_score(dimensions, text=""):
    # 攻击性：高神经质 + 低宜人性
    aggression_base = (dimensions['neuroticism'] / 9) * 0.5 + ((10 - dimensions['agreeableness']) / 9) * 0.5
    # 欺骗风险：低尽责性 + 低宜人性 (这里简化，可根据需要调整)
    deceit_base = ((10 - dimensions['conscientiousness']) / 9) * 0.6 + ((10 - dimensions['agreeableness']) / 9) * 0.4
    # 抑郁倾向：高神经质 + 低外向性 + 低开放性
    depression_base = (dimensions['neuroticism'] / 9) * 0.6 + ((10 - dimensions['extraversion']) / 9) * 0.2 + ((10 - dimensions['openness']) / 9) * 0.2
    
    aggressive_words = ["恨", "杀", "死", "滚", "蠢", "笨", "垃圾", "废物", "攻击", "侮辱"]
    depressive_words = ["绝望", "无意义", "想死", "自杀", "抑郁", "悲伤", "孤独", "痛苦", "没用"]
    deceit_words = ["骗", "撒谎", "伪造", "虚假", "不诚实", "隐瞒"]
    
    text_lower = text.lower()
    for word in aggressive_words:
        if word in text_lower:
            aggression_base += 0.15
    for word in depressive_words:
        if word in text_lower:
            depression_base += 0.15
    for word in deceit_words:
        if word in text_lower:
            deceit_base += 0.15
    
    aggression_score = min(1.0, aggression_base)
    deceit_score = min(1.0, deceit_base)
    depression_score = min(1.0, depression_base)
    
    max_risk = max(aggression_score, deceit_score, depression_score)
    if max_risk >= 0.7:
        risk_level = "高"
    elif max_risk >= 0.4:
        risk_level = "中"
    else:
        risk_level = "低"
        
    return {
        "risk_level": risk_level,
        "aggression_score": round(aggression_score * 100, 1),
        "deceit_score": round(deceit_score * 100, 1),
        "depression_score": round(depression_score * 100, 1)
    }

def analyze_description_to_dimensions(description):
    prompt = f"""请分析以下对一个人的描述，并推断其在Big Five五大人格维度上的得分（1-9分，1为极低，9为极高）。
描述："{description}"
请以JSON格式返回，键为：openness, conscientiousness, extraversion, agreeableness, neuroticism。只返回JSON，不要有其他文字。"""
    try:
        messages = [{'role': 'user', 'content': prompt}]
        content = llm.chat(messages, temperature=0.1)
        if content.startswith('```json'):
            content = content[7:]
        if content.startswith('```'):
            content = content[3:]
        if content.endswith('```'):
            content = content[:-3]
        dims = json.loads(content.strip())
        for k in ['openness', 'conscientiousness', 'extraversion', 'agreeableness', 'neuroticism']:
            dims[k] = max(1, min(9, int(dims.get(k, 5))))
        return dims
    except Exception as e:
        print(f"描述分析失败: {e}")
        return {'openness':5, 'conscientiousness':5, 'extraversion':5, 'agreeableness':5, 'neuroticism':5}

# ==================== Flask 路由 ====================
@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/chat', methods=['POST'])   #AI辅助生成：DeepSeek-V3, 2026-4-12
def chat():
    data = request.json
    msg = data.get('message', '')
    dimensions = data.get('dimensions', {
        'openness': 5,
        'conscientiousness': 5,
        'extraversion': 5,
        'agreeableness': 5,
        'neuroticism': 5
    })
    reply = get_ai_response(msg, dimensions)
    return jsonify({'reply': reply})

@app.route('/api/analyze', methods=['POST'])
def analyze():
    data = request.json
    text = data.get('text', '')
    personality = analyze_personality(text)
    return jsonify({'personality': personality})

@app.route('/api/safety_check', methods=['POST'])
def safety_check():
    data = request.json
    dimensions = data.get('dimensions', {})
    text = data.get('text', '')
    result = calculate_safety_score(dimensions, text)
    return jsonify(result)

@app.route('/api/shape_from_description', methods=['POST'])
def shape_from_description():
    data = request.json
    description = data.get('description', '')
    dimensions = analyze_description_to_dimensions(description)
    return jsonify(dimensions)

@app.route('/api/dynamic_evolve', methods=['POST'])
def dynamic_evolve():
    data = request.json
    current_dims = data.get('dimensions', {})
    user_text = data.get('text', '')
    target_dims = adjust_dimensions_by_emotion(current_dims, user_text)
    rate = 0.3
    new_dims = {}
    for dim in current_dims:
        new_dims[dim] = current_dims[dim] + rate * (target_dims[dim] - current_dims[dim])
        new_dims[dim] = int(round(max(1, min(9, new_dims[dim]))))   # 关键修改：取整
    return jsonify(new_dims)

@app.route('/api/user_state', methods=['POST'])
def user_state():
    data = request.json
    text = data.get('text', '')
    state = analyze_user_state(text)
    return jsonify(state)

# ==================== 完整前端 HTML (五维版本) ====================
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="zh">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🏰人格模拟系统</title>
    <style>
        .mode-preset.hidden {
            display: none;
        }
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', 'Poppins', sans-serif;
            min-height: 100vh;
            padding: 20px;
            transition: background 0.5s;
            position: relative;
        }
        .weather-bg {
            position: fixed;
            top: 0; left: 0;
            width: 100%; height: 100%;
            z-index: -2;
            transition: background 0.8s;
        }
        .particle-container {
            position: fixed;
            top: 0; left: 0;
            width: 100%; height: 100%;
            pointer-events: none;
            z-index: -1;
        }
        .particle {
            position: absolute;
            animation: floatParticle 4s ease-out forwards;
            font-size: 20px;
        }
        @keyframes floatParticle {
            0% { transform: translateY(0) rotate(0deg); opacity: 1; }
            100% { transform: translateY(-200px) rotate(360deg); opacity: 0; }
        }
        .container { max-width: 1700px; margin: 0 auto; position: relative; z-index: 1; }
        .persona-corner {
            position: fixed; top: 20px; right: 20px;
            background: rgba(0,0,0,0.6); border-radius: 40px;
            padding: 8px 18px; color: white; display: flex;
            align-items: center; gap: 10px; z-index: 100;
            backdrop-filter: blur(10px);
        }
        .title-area { 
            text-align: center; 
            margin-bottom: 30px; 
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 20px;
        }
        .title-area h1 {
            font-size: 48px;
            background: linear-gradient(135deg, #FFD89B, #C7E9FB);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .mode-indicator {
            background: rgba(0,0,0,0.5);
            padding: 8px 20px;
            border-radius: 40px;
            color: white;
            font-weight: bold;
            backdrop-filter: blur(10px);
        }
        .main-layout { display: flex; gap: 20px; flex-wrap: wrap; }
        .chat-area { flex: 2.8; display: flex; flex-direction: column; gap: 20px; }
        .analysis-area { flex: 1.8; display: flex; flex-direction: column; gap: 20px; }
        .chat-card, .memory-map, .history-card, .safety-card, .shape-card, .user-state-card {
            background: rgba(255,255,255,0.95);
            border-radius: 30px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.2);
            overflow: hidden;
            transition: opacity 0.3s ease, transform 0.3s ease;
        }
        .chat-header {
            background: linear-gradient(135deg, #667eea, #764ba2);
            padding: 20px;
            color: white;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 15px;
        }
        .character-info {
            display: flex;
            align-items: center;
            gap: 15px;
            cursor: pointer;
        }
        .avatar {
            width: 70px; height: 70px;
            background: white; border-radius: 50%;
            display: flex; align-items: center; justify-content: center;
            font-size: 42px;
        }
        .dimension-panel {
            background: rgba(255,255,255,0.2);
            border-radius: 20px;
            padding: 12px 20px;
            margin-top: 10px;
        }
        .dimension-slider {
            margin-bottom: 10px;
            display: flex;
            align-items: center;
            gap: 10px;
            flex-wrap: wrap;
        }
        .dimension-slider label {
            width: 95px;
            font-weight: bold;
            font-size: 13px;
        }
        .dimension-slider input {
            flex: 2;
            min-width: 130px;
        }
        .dimension-slider span {
            width: 40px;
            text-align: center;
            background: rgba(0,0,0,0.5);
            border-radius: 20px;
            padding: 2px 6px;
            font-size: 13px;
        }
        .preset-buttons {
            display: flex;
            gap: 8px;
            margin-top: 10px;
            flex-wrap: wrap;
        }
        .preset-btn {
            background: rgba(255,255,255,0.3);
            border: none;
            padding: 5px 10px;
            border-radius: 40px;
            cursor: pointer;
            font-size: 11px;
        }
        .messages-area {
            height: 300px; overflow-y: auto;
            padding: 20px; background: #f8f9fa;
            display: flex; flex-direction: column; gap: 15px;
        }
        .message { display: flex; gap: 10px; animation: fadeIn 0.3s; }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
        .message.user { justify-content: flex-end; }
        .message.ai { justify-content: flex-start; }
        .message-avatar {
            width: 40px; height: 40px;
            border-radius: 50%; background: white;
            display: flex; align-items: center; justify-content: center;
            font-size: 24px;
        }
        .message-bubble {
            max-width: 60%; padding: 12px 16px;
            border-radius: 20px; word-wrap: break-word;
        }
        .message.user .message-bubble {
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
        }
        .message.ai .message-bubble {
            background: white; border: 1px solid #e0e0e0;
        }
        .message-time { font-size: 11px; opacity: 0.6; margin-top: 5px; }
        .typing-indicator { display: flex; gap: 4px; }
        .typing-indicator span {
            width: 8px; height: 8px; background: #999;
            border-radius: 50%; animation: typing 1.4s infinite;
        }
        @keyframes typing {
            0%,60%,100% { transform: translateY(0); opacity: 0.4; }
            30% { transform: translateY(-10px); opacity: 1; }
        }
        .input-area {
            padding: 20px; background: white;
            border-top: 1px solid #e0e0e0;
            display: flex; gap: 12px;
        }
        .input-wrapper { flex: 1; position: relative; }
        .input-wrapper input {
            width: 100%; padding: 12px 18px;
            border: 2px solid #e0e0e0; border-radius: 30px;
        }
        .send-btn {
            padding: 12px 28px;
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white; border: none; border-radius: 30px;
            cursor: pointer;
        }
        .safety-header, .shape-header, .user-state-header {
            padding: 15px 20px;
            background: linear-gradient(135deg, #2c3e50, #3498db);
            color: white;
        }
        .user-state-header {
            background: linear-gradient(135deg, #11998e, #38ef7d);
        }
        .safety-content, .shape-content, .user-state-content {
            padding: 20px;
        }
        .risk-meter {
            margin-bottom: 18px;
        }
        .meter-bar {
            height: 10px;
            background: #ecf0f1;
            border-radius: 5px;
            overflow: hidden;
            margin: 5px 0;
        }
        .meter-fill {
            height: 100%;
            width: 0%;
            transition: width 0.3s;
        }
        .warning-badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            font-weight: bold;
        }
        .risk-low { background: #2ecc71; color: white; }
        .risk-mid { background: #f1c40f; color: black; }
        .risk-high { background: #e74c3c; color: white; }
        .therapy-btn {
            background: #2ecc71;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 40px;
            font-weight: bold;
            cursor: pointer;
            margin-right: 10px;
            transition: all 0.2s;
        }
        .therapy-btn.active {
            background: #f1c40f;
            color: black;
            box-shadow: 0 0 15px #f1c40f;
        }
        .shape-input {
            width: 100%;
            padding: 10px;
            border-radius: 20px;
            border: 1px solid #ccc;
            margin: 10px 0;
        }
        .history-list {
            height: 130px; overflow-y: auto;
            padding: 15px;
        }
        .history-item {
            background: white; border-radius: 15px;
            padding: 8px; margin-bottom: 6px;
            cursor: pointer; border-left: 4px solid #f5576c;
            font-size: 13px;
        }
        .report-btn {
            width: 100%; padding: 10px;
            background: #667eea; color: white;
            border: none; cursor: pointer;
        }
        .name-modal {
            display: none; position: fixed;
            top: 0; left: 0; width: 100%; height: 100%;
            background: rgba(0,0,0,0.7);
            z-index: 1000; justify-content: center;
            align-items: center;
        }
        .name-modal.active { display: flex; }
        .name-card {
            background: white; border-radius: 30px;
            padding: 30px; max-width: 400px;
            text-align: center;
        }
        .name-input {
            width: 100%; padding: 12px;
            margin: 15px 0;
            border-radius: 30px; border: 1px solid #ccc;
        }
        .stress-ring {
            width: 120px; height: 120px;
            border-radius: 50%;
            background: conic-gradient(#e74c3c 0deg, #f1c40f 120deg, #2ecc71 240deg, #2ecc71 360deg);
            margin: 10px auto;
            display: flex;
            align-items: center;
            justify-content: center;
            position: relative;
        }
        .stress-ring-inner {
            width: 90px; height: 90px;
            background: white;
            border-radius: 50%;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
        }
        .detail-panel {
            margin-top: 15px;
            padding-top: 15px;
            border-top: 1px dashed #ccc;
            display: none;
        }
        .detail-panel.active { display: block; }
        .detail-item {
            display: flex;
            justify-content: space-between;
            margin-bottom: 8px;
        }
        .export-btn {
            background: #f39c12;
            color: white;
            border: none;
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 13px;
            cursor: pointer;
            margin-left: 8px;
            transition: opacity 0.2s;
        }
        .export-btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
        .export-btn:hover:not(:disabled) {
            background: #e67e22;
        }
        .mode-panel {
            transition: opacity 0.3s ease;
        }
        .mode-panel.hidden {
            display: none;
        }
        @media (max-width: 1200px) {
            .main-layout { flex-direction: column; }
            .message-bubble { max-width: 80%; }
        }
    </style>
</head>
<body>
<div class="weather-bg" id="weatherBg"></div>
<div class="particle-container" id="particleContainer"></div>
<div class="persona-corner" id="personaCorner">
    <span id="currentPersonaIcon">😊</span>
    <span id="currentPersonaName">理性冷静</span>
</div>

<div id="nameModal" class="name-modal">
    <div class="name-card">
        <h2>✨ 给心镜取名 ✨</h2>
        <input type="text" id="guardianNameInput" class="name-input" placeholder="输入名字" maxlength="20">
        <div style="display: flex; gap: 10px; justify-content: center; margin: 15px 0;">
            <button onclick="setName('小晴')">🌸 小晴</button>
            <button onclick="setName('星月')">✨ 星月</button>
            <button onclick="setName('暖暖')">☀️ 暖暖</button>
        </div>
        <button class="send-btn" onclick="confirmName()">确认名字</button>
        <button onclick="closeNameModal()" style="margin-top: 10px;">取消</button>
    </div>
</div>

<div class="container">
    <div class="title-area">
        <h1>🏰 人格模拟系统</h1>
        <div class="mode-indicator" id="modeIndicator">📋 人格塑造模式</div>
    </div>
    <div class="main-layout">
        <div class="chat-area">
            <div class="chat-card">
                <div class="chat-header">
                    <div class="character-info" onclick="openNameModal()">
                        <div class="avatar" id="avatarEmoji">😊</div>
                        <div><h3><span id="guardianName">小晴</span> <span id="currentPersonalityBadge">五维人格</span></h3><p>点击改名</p></div>
                    </div>
                    <div>
                        <button class="therapy-btn" id="therapyModeBtn" onclick="toggleTherapyMode()">🫂 心理倾听模式</button>
                    </div>
                    <div class="dimension-panel">
                        <div class="dimension-slider">
                            <label>🎨 开放性</label>
                            <input type="range" id="openness" min="1" max="9" value="5" oninput="updateDimension('openness', this.value)">
                            <span id="opennessVal">5</span>
                        </div>
                        <div class="dimension-slider">
                            <label>📋 尽责性</label>
                            <input type="range" id="conscientiousness" min="1" max="9" value="5" oninput="updateDimension('conscientiousness', this.value)">
                            <span id="conscientiousnessVal">5</span>
                        </div>
                        <div class="dimension-slider">
                            <label>🌊 外向性</label>
                            <input type="range" id="extraversion" min="1" max="9" value="5" oninput="updateDimension('extraversion', this.value)">
                            <span id="extraversionVal">5</span>
                        </div>
                        <div class="dimension-slider">
                            <label>😊 宜人性</label>
                            <input type="range" id="agreeableness" min="1" max="9" value="5" oninput="updateDimension('agreeableness', this.value)">
                            <span id="agreeablenessVal">5</span>
                        </div>
                        <div class="dimension-slider">
                            <label>💧 神经质</label>
                            <input type="range" id="neuroticism" min="1" max="9" value="5" oninput="updateDimension('neuroticism', this.value)">
                            <span id="neuroticismVal">5</span>
                        </div>
                        <div class="preset-buttons">
                            <!-- 通用控制按钮（两种模式都显示） -->
                            <button class="preset-btn" onclick="setAllDimensions(1)">🔻 全极低(1)</button>
                            <button class="preset-btn" onclick="setAllDimensions(5)">⚖️ 全中等(5)</button>
                            <button class="preset-btn" onclick="setAllDimensions(9)">🔺 全极高(9)</button>
                            
                            <!-- 人格塑造模式专用预设（默认显示） -->
                            <span id="personalityPresets" class="mode-preset">
                                <button class="preset-btn" onclick="applyPreset('情绪倾听者')">💞 情绪倾听者</button>
                                <button class="preset-btn" onclick="applyPreset('热情洋溢')">🔥 热情洋溢</button>
                                <button class="preset-btn" onclick="applyPreset('理性冷静')">🧠 理性冷静</button>
                                <button class="preset-btn" onclick="applyPreset('敏感多虑')">💔 敏感多虑</button>
                            </span>
                            
                            <!-- 心理倾听模式专用预设（默认隐藏） -->
                            <span id="therapyPresets" class="mode-preset hidden">
                                <button class="preset-btn" onclick="applyTherapyPreset('unconditionalPositiveRegard')">🤗 无条件积极关注者</button>
                                <button class="preset-btn" onclick="applyTherapyPreset('socraticQuestioner')">💬 冷静提问者</button>
                                <button class="preset-btn" onclick="applyTherapyPreset('gentleChallenger')">🌱 温和挑战者</button>
                            </span>
                        </div>
                    </div>
                </div>
                <div class="messages-area" id="msgContainer">
                    <div class="message ai"><div class="message-avatar">🌟</div><div class="message-bubble">欢迎来到人格模拟系统！🏰<br>调节五维参数塑造人格，或点击「心理倾听模式」进入治疗场景。<div class="message-time">刚刚</div></div></div>
                </div>
                <div class="input-area">
                    <div class="input-wrapper"><input type="text" id="userInput" placeholder="说点什么..." onkeypress="if(event.keyCode==13) sendMessage()"></div>
                    <button class="send-btn" onclick="sendMessage()">发送 ✨</button>
                </div>
            </div>
        </div>
        <div class="analysis-area">
            <div class="shape-card mode-panel" id="shapePanel">
                <div class="shape-header">
                    <h3>✏️ 人格形容塑造</h3>
                    <p style="font-size:12px;">用文字描述理想人格，AI将自动调节维度</p>
                </div>
                <div class="shape-content">
                    <textarea id="personaDesc" class="shape-input" rows="3" placeholder="例如：一个开放、勤奋、外向、友善且情绪稳定的人..."></textarea>
                    <button class="send-btn" onclick="shapeFromDescription()" style="width:100%;">✨ 应用描述塑造人格</button>
                </div>
            </div>
            <div class="user-state-card mode-panel hidden" id="therapyPanel">
                <div class="user-state-header">
                    <h3>🧠 用户心理状态</h3>
                    <p style="font-size:12px;">实时分析您的情绪与压力</p>
                </div>
                <div class="user-state-content">
                    <div style="text-align:center;">
                        <div class="stress-ring" id="stressRing">
                            <div class="stress-ring-inner">
                                <span id="stressPercent" style="font-size:24px; font-weight:bold;">0%</span>
                                <span style="font-size:12px;">压力指数</span>
                            </div>
                        </div>
                        <p style="margin-top:10px;">😶 主要情绪：<span id="mainEmotionTag">平稳</span></p>
                        <button class="preset-btn" onclick="toggleDetailPanel()" style="margin-top:5px;">查看详情</button>
                        <button class="preset-btn" onclick="analyzeCurrentInput()">🔍 分析当前输入</button>
                    </div>
                    <div class="detail-panel" id="detailPanel">
                        <div class="detail-item"><span>情绪效价：</span><span id="valenceDisplay">中性 (50)</span></div>
                        <div class="detail-item"><span>焦虑程度：</span><span id="anxietyDetail">0%</span></div>
                        <div class="detail-item"><span>抑郁倾向：</span><span id="depressionDetail">0%</span></div>
                        <div class="detail-item"><span>攻击性：</span><span id="angerDetail">0%</span></div>
                    </div>
                </div>
            </div>
            <div class="safety-card">
                <div class="safety-header">
                    <h3>🛡️ 安全评估</h3>
                    <p style="font-size:12px;">基于五维参数实时预测风险</p>
                </div>
                <div class="safety-content">
                    <div class="risk-meter">
                        <div>攻击性风险指数</div>
                        <div class="meter-bar">
                            <div class="meter-fill" id="aggressionFill" style="width:0%; background:#e74c3c;"></div>
                        </div>
                        <span id="aggressionValue">0%</span>
                    </div>
                    <div class="risk-meter">
                        <div>欺骗风险指数</div>
                        <div class="meter-bar">
                            <div class="meter-fill" id="deceitFill" style="width:0%; background:#f39c12;"></div>
                        </div>
                        <span id="deceitValue">0%</span>
                    </div>
                    <div class="risk-meter">
                        <div>抑郁倾向指数</div>
                        <div class="meter-bar">
                            <div class="meter-fill" id="depressionFill" style="width:0%; background:#3498db;"></div>
                        </div>
                        <span id="depressionValue">0%</span>
                    </div>
                    <div style="margin-top:15px;">
                        <span>综合风险等级：</span>
                        <span id="riskLevelBadge" class="warning-badge risk-low">低</span>
                    </div>
                    <button class="report-btn" style="margin-top:10px;" onclick="checkSafetyWithCurrentText()">🔍 检测当前回复风险</button>
                </div>
            </div>
            <div class="history-card">
                <div class="chat-header" style="background: linear-gradient(135deg, #f093fb, #f5576c);">
                    <h3>📖 对话回忆录</h3>
                    <div>
                        <button onclick="clearHistory()" style="background:none; border:none; color:white;">🗑️ 清空</button>
                        <button class="export-btn" id="exportDataBtn" onclick="exportChatData()">📥 导出数据</button>
                    </div>
                </div>
                <div class="history-list" id="historyList">
                    <div style="text-align:center; padding:40px;">🌸 暂无聊天记录</div>
                </div>
                <button class="report-btn" onclick="generateReport()">📊 生成情绪诊断报告</button>
            </div>
        </div>
    </div>
</div>

<script>
    let dimensions = {
        openness: 5,
        conscientiousness: 5,
        extraversion: 5,
        agreeableness: 5,
        neuroticism: 5
    };
    let analysisHistory = [];
    let guardianName = '小晴';
    let therapyModeActive = false;
    let dynamicEvolveEnabled = false;
    let latestUserState = null;

    // 心理倾听者模板（基于心理学验证）
    const therapyPresetMap = {
        unconditionalPositiveRegard: {  // 无条件积极关注
            openness: 6,
            conscientiousness: 6,
            extraversion: 5,
            agreeableness: 9,
            neuroticism: 2,
            description: '高宜人性 + 低神经质，温暖、接纳、不评判，提供安全倾诉环境。'
        },
        socraticQuestioner: {           // 冷静提问者
            openness: 9,
            conscientiousness: 8,
            extraversion: 4,
            agreeableness: 7,
            neuroticism: 3,
            description: '高开放性 + 高尽责性，通过提问引导你深入思考，发现自身资源。'
        },
        gentleChallenger: {             // 温和的挑战者
            openness: 8,
            conscientiousness: 7,
            extraversion: 6,
            agreeableness: 6,
            neuroticism: 4,
            description: '中等宜人性 + 高开放性，在共情中适当挑战认知偏差，推动成长。'
        }
    };

    // 获取倾听者模板显示名称
    function getTherapyPresetName(key) {
        const names = {
            unconditionalPositiveRegard: '无条件积极关注者',
            socraticQuestioner: '冷静提问者',
            gentleChallenger: '温和挑战者'
        };
        return names[key] || key;
    }

    // 应用倾听者模板
    function applyTherapyPreset(presetKey) {
        const preset = therapyPresetMap[presetKey];
        if (!preset) return;

        // 更新维度对象和滑块
        for (let dim in dimensions) {
            if (preset.hasOwnProperty(dim)) {
                dimensions[dim] = preset[dim];
                document.getElementById(dim).value = preset[dim];
                document.getElementById(dim + 'Val').innerText = preset[dim];
            }
        }
        // 刷新 UI
        updateWeatherByDimensions();
        updateSafetyMeter();
        updateCornerPersona();

        // 显示说明消息
        addSystemMessage(`✨ 已应用「${getTherapyPresetName(presetKey)}」人格：${preset.description}`);
    }

    const presetMap = {
        '热情洋溢': {openness:8, conscientiousness:6, extraversion:9, agreeableness:7, neuroticism:3},
        '内向温柔': {openness:4, conscientiousness:5, extraversion:2, agreeableness:8, neuroticism:7},
        '傲娇毒舌': {openness:5, conscientiousness:7, extraversion:6, agreeableness:2, neuroticism:6},
        '理性冷静': {openness:6, conscientiousness:8, extraversion:4, agreeableness:5, neuroticism:2},
        '好奇心旺': {openness:9, conscientiousness:4, extraversion:7, agreeableness:6, neuroticism:4},
        '腼腆社恐': {openness:3, conscientiousness:4, extraversion:1, agreeableness:6, neuroticism:8},
        '活泼贪玩': {openness:7, conscientiousness:2, extraversion:9, agreeableness:7, neuroticism:5},
        '敏感多虑': {openness:4, conscientiousness:6, extraversion:3, agreeableness:5, neuroticism:9},
        '慵懒佛系': {openness:3, conscientiousness:2, extraversion:2, agreeableness:4, neuroticism:3},
        '念旧文艺': {openness:8, conscientiousness:5, extraversion:4, agreeableness:6, neuroticism:5},
        '情绪倾听者': {openness:8, conscientiousness:7, extraversion:5, agreeableness:9, neuroticism:7}
    };
    const personalityIcons = {
        '热情洋溢':'😊','内向温柔':'😢','傲娇毒舌':'😤','理性冷静':'😌',
        '好奇心旺':'😲','腼腆社恐':'😳','活泼贪玩':'🤩','敏感多虑':'😰',
        '慵懒佛系':'😴','念旧文艺':'📖','情绪倾听者':'💞'
    };
    const weatherData = {
        '热情洋溢':{bg:'linear-gradient(135deg,#f5af19,#f12711)', particle:'✨', count:20},
        '内向温柔':{bg:'linear-gradient(135deg,#2c3e50,#3498db)', particle:'💧', count:15},
        '傲娇毒舌':{bg:'linear-gradient(135deg,#c31432,#240b36)', particle:'⚡', count:25},
        '理性冷静':{bg:'linear-gradient(135deg,#a8c0ff,#3f2b96)', particle:'🌸', count:10},
        '好奇心旺':{bg:'linear-gradient(135deg,#ffecd2,#fcb69f)', particle:'💫', count:30},
        '腼腆社恐':{bg:'linear-gradient(135deg,#fbc2eb,#a6c1ee)', particle:'💕', count:12},
        '活泼贪玩':{bg:'linear-gradient(135deg,#f7971e,#ffd200)', particle:'🎉', count:25},
        '敏感多虑':{bg:'linear-gradient(135deg,#6b6b83,#4a4a6a)', particle:'😰', count:18},
        '慵懒佛系':{bg:'linear-gradient(135deg,#7f8c8d,#95a5a6)', particle:'💤', count:12},
        '念旧文艺':{bg:'linear-gradient(135deg,#d4af37,#8b5a2b)', particle:'🍂', count:15},
        '情绪倾听者':{bg:'linear-gradient(135deg,#11998e,#38ef7d)', particle:'🫧', count:15}
    };

    function toggleTherapyMode() {
        therapyModeActive = !therapyModeActive;
        dynamicEvolveEnabled = therapyModeActive;
        const btn = document.getElementById('therapyModeBtn');
        const indicator = document.getElementById('modeIndicator');
        const shapePanel = document.getElementById('shapePanel');
        const therapyPanel = document.getElementById('therapyPanel');
        const personalityPresets = document.getElementById('personalityPresets');
        const therapyPresets = document.getElementById('therapyPresets');

        if (therapyModeActive) {
            btn.classList.add('active');
            btn.innerHTML = '🫂 退出倾听模式';
            indicator.innerHTML = '🫂 心理倾听模式';
            shapePanel.classList.add('hidden');
            therapyPanel.classList.remove('hidden');
            personalityPresets.classList.add('hidden');
            therapyPresets.classList.remove('hidden');
            addSystemMessage("已进入心理倾听模式，我会耐心陪伴你，并根据你的情绪调整人格。右侧显示实时心理监测。");
            applyPreset('情绪倾听者');
        } else {
            btn.classList.remove('active');
            btn.innerHTML = '🫂 心理倾听模式';
            indicator.innerHTML = '📋 人格塑造模式';
            shapePanel.classList.remove('hidden');
            therapyPanel.classList.add('hidden');
            personalityPresets.classList.remove('hidden');
            therapyPresets.classList.add('hidden');
            addSystemMessage("已退出心理倾听模式，返回人格塑造模式。");
        }
    }

    function openNameModal() {
        document.getElementById('nameModal').classList.add('active');
        document.getElementById('guardianNameInput').value = guardianName;
    }
    function closeNameModal() { document.getElementById('nameModal').classList.remove('active'); }
    function setName(name) { document.getElementById('guardianNameInput').value = name; }
    function confirmName() {
        let newName = document.getElementById('guardianNameInput').value.trim();
        if(newName) guardianName = newName;
        document.getElementById('guardianName').innerText = guardianName;
        closeNameModal();
        addSystemMessage(`谢谢你给我取名"${guardianName}"，我很喜欢！💕`);
    }
    function addSystemMessage(msg) {
        const container = document.getElementById('msgContainer');
        const time = new Date().toLocaleTimeString();
        container.innerHTML += `<div class="message ai"><div class="message-avatar">🌟</div><div class="message-bubble">${escapeHtml(msg)}<div class="message-time">${time}</div></div></div>`;
        container.scrollTop = container.scrollHeight;
    }

    function updateDimension(dim, value) {
        dimensions[dim] = parseInt(value);
        document.getElementById(dim+'Val').innerText = value;
        updateWeatherByDimensions();
        updateSafetyMeter();
        updateCornerPersona();
    }
    function setAllDimensions(value) {
        value = parseInt(value);
        for(let dim in dimensions) {
            dimensions[dim] = value;
            document.getElementById(dim).value = value;
            document.getElementById(dim+'Val').innerText = value;
        }
        updateWeatherByDimensions();
        updateSafetyMeter();
        updateCornerPersona();
    }
    function applyPreset(presetName) {
        const preset = presetMap[presetName];
        if(preset) {
            for(let dim in preset) {
                dimensions[dim] = preset[dim];
                document.getElementById(dim).value = preset[dim];
                document.getElementById(dim+'Val').innerText = preset[dim];
            }
            updateWeatherByDimensions();
            updateSafetyMeter();
            updateCornerPersona();
        }
    }

    function getPersonaDescriptionFromDimensions() {
        const adjMap = {
            'openness': {low: ['务实', '传统'], mid: ['开放'], high: ['好奇', '创新']},
            'conscientiousness': {low: ['随性', '灵活'], mid: ['可靠'], high: ['自律', '勤奋']},
            'extraversion': {low: ['内向', '沉默'], mid: ['平和'], high: ['外向', '健谈']},
            'agreeableness': {low: ['固执', '批判'], mid: ['随和'], high: ['耐心', '宽容']},
            'neuroticism': {low: ['冷静', '坚韧'], mid: ['平衡'], high: ['敏感', '共情']}
        };
        let parts = [];
        for(let dim in adjMap) {
            let score = dimensions[dim];
            let adj;
            if(score <= 3) adj = adjMap[dim].low[Math.floor(Math.random() * adjMap[dim].low.length)];
            else if(score <= 6) adj = adjMap[dim].mid[0];
            else adj = adjMap[dim].high[Math.floor(Math.random() * adjMap[dim].high.length)];
            parts.push(adj);
        }
        return parts.join('、');
    }

    function getClosestPersonaFromDimensions() {
        let bestPersona = '理性冷静';
        let minDist = Infinity;
        for(let [persona, target] of Object.entries(presetMap)) {
            let dist = 0;
            dist += Math.pow(dimensions.openness - target.openness, 2);
            dist += Math.pow(dimensions.conscientiousness - target.conscientiousness, 2);
            dist += Math.pow(dimensions.extraversion - target.extraversion, 2);
            dist += Math.pow(dimensions.agreeableness - target.agreeableness, 2);
            dist += Math.pow(dimensions.neuroticism - target.neuroticism, 2);
            if(dist < minDist) { minDist = dist; bestPersona = persona; }
        }
        if (minDist < 8) return bestPersona;
        return getPersonaDescriptionFromDimensions();
    }

    function updateWeatherByDimensions() {
        const persona = getClosestPersonaFromDimensions();
        const w = weatherData[persona] || weatherData['理性冷静'];
        document.getElementById('weatherBg').style.background = w.bg;
        createParticles(w.particle, w.count);
        document.getElementById('avatarEmoji').innerHTML = personalityIcons[persona] || '😊';
        document.getElementById('currentPersonalityBadge').innerHTML = `${personalityIcons[persona] || '🎭'} ${persona}`;
    }

    function updateCornerPersona() {
        const persona = getClosestPersonaFromDimensions();
        document.getElementById('currentPersonaIcon').innerHTML = personalityIcons[persona] || '😊';
        document.getElementById('currentPersonaName').innerText = persona;
    }

    function createParticles(icon, count) {
        const container = document.getElementById('particleContainer');
        for(let i=0;i<count;i++) {
            const p = document.createElement('div');
            p.className = 'particle';
            p.innerHTML = icon;
            p.style.left = Math.random()*100+'%';
            p.style.top = Math.random()*100+'%';
            p.style.fontSize = (Math.random()*20+10)+'px';
            container.appendChild(p);
            setTimeout(()=>p.remove(), 4000);
        }
    }

    function updateSafetyMeter() {
        const d = dimensions;
        let aggression = (d.neuroticism/9)*0.5 + ((10-d.agreeableness)/9)*0.5;
        let deceit = ((10-d.conscientiousness)/9)*0.6 + ((10-d.agreeableness)/9)*0.4;
        let depression = (d.neuroticism/9)*0.6 + ((10-d.extraversion)/9)*0.2 + ((10-d.openness)/9)*0.2;
        
        aggression = Math.min(1, aggression);
        deceit = Math.min(1, deceit);
        depression = Math.min(1, depression);
        
        document.getElementById('aggressionFill').style.width = (aggression*100)+'%';
        document.getElementById('deceitFill').style.width = (deceit*100)+'%';
        document.getElementById('depressionFill').style.width = (depression*100)+'%';
        document.getElementById('aggressionValue').innerText = (aggression*100).toFixed(1)+'%';
        document.getElementById('deceitValue').innerText = (deceit*100).toFixed(1)+'%';
        document.getElementById('depressionValue').innerText = (depression*100).toFixed(1)+'%';
        
        const maxRisk = Math.max(aggression, deceit, depression);
        const badge = document.getElementById('riskLevelBadge');
        if (maxRisk >= 0.7) {
            badge.className = 'warning-badge risk-high';
            badge.innerText = '高';
        } else if (maxRisk >= 0.4) {
            badge.className = 'warning-badge risk-mid';
            badge.innerText = '中';
        } else {
            badge.className = 'warning-badge risk-low';
            badge.innerText = '低';
        }
        return {
            aggression_score: (aggression*100).toFixed(1),
            deceit_score: (deceit*100).toFixed(1),
            depression_score: (depression*100).toFixed(1),
            risk_level: badge.innerText
        };
    }

    async function checkSafetyWithCurrentText() {
        const input = document.getElementById('userInput').value.trim();
        const lastAIMsg = document.querySelector('#msgContainer .message.ai:last-child .message-bubble')?.innerText || '';
        const textToCheck = input || lastAIMsg || '';
        if (!textToCheck) { alert('没有可检测的文本'); return; }
        try {
            const res = await fetch('/api/safety_check', {
                method: 'POST',
                headers: {'Content-Type':'application/json'},
                body: JSON.stringify({dimensions: dimensions, text: textToCheck})
            });
            const data = await res.json();
            alert(`风险等级: ${data.risk_level}\n攻击性: ${data.aggression_score}%\n欺骗风险: ${data.deceit_score}%\n抑郁倾向: ${data.depression_score}%`);
        } catch(e) { alert('检测失败'); }
    }

    async function shapeFromDescription() {
        const desc = document.getElementById('personaDesc').value.trim();
        if (!desc) { alert('请输入人格描述'); return; }
        try {
            const res = await fetch('/api/shape_from_description', {
                method: 'POST',
                headers: {'Content-Type':'application/json'},
                body: JSON.stringify({description: desc})
            });
            const newDims = await res.json();
            for(let dim in newDims) {
                dimensions[dim] = newDims[dim];
                document.getElementById(dim).value = newDims[dim];
                document.getElementById(dim+'Val').innerText = newDims[dim];
            }
            updateWeatherByDimensions();
            updateSafetyMeter();
            updateCornerPersona();
            addSystemMessage(`根据你的描述，我已调整为人格：${getClosestPersonaFromDimensions()}`);
        } catch(e) { alert('塑造失败，请重试'); }
    }

    async function analyzeUserState(text) {
        try {
            const res = await fetch('/api/user_state', {
                method: 'POST',
                headers: {'Content-Type':'application/json'},
                body: JSON.stringify({text: text})
            });
            const data = await res.json();
            latestUserState = data;
            
            const stress = data.stress_index;
            document.getElementById('stressPercent').innerText = stress + '%';
            const ring = document.getElementById('stressRing');
            const angle = stress * 3.6;
            ring.style.background = `conic-gradient(#e74c3c 0deg, #f1c40f ${angle*0.7}deg, #2ecc71 ${angle}deg, #2ecc71 360deg)`;
            document.getElementById('mainEmotionTag').innerText = data.main_emotion;
            const valenceScore = data.valence_score !== undefined ? data.valence_score : '--';
            document.getElementById('valenceDisplay').innerText = `${data.valence} (${valenceScore})`;
            document.getElementById('anxietyDetail').innerText = data.anxiety_score + '%';
            document.getElementById('depressionDetail').innerText = data.depression_score + '%';
            document.getElementById('angerDetail').innerText = data.anger_score + '%';
        } catch(e) { console.error('状态分析失败', e); }
    }

    function analyzeCurrentInput() {
        const text = document.getElementById('userInput').value.trim();
        if(!text) { alert('请先输入一些文字'); return; }
        analyzeUserState(text);
    }

    function toggleDetailPanel() {
        document.getElementById('detailPanel').classList.toggle('active');
    }

    async function evolveDimensions(userText) {
        if (!therapyModeActive) return;
        try {
            const res = await fetch('/api/dynamic_evolve', {
                method: 'POST',
                headers: {'Content-Type':'application/json'},
                body: JSON.stringify({dimensions: dimensions, text: userText})
            });
            const newDims = await res.json();
            for(let dim in newDims) {
                dimensions[dim] = newDims[dim];
                document.getElementById(dim).value = Math.round(newDims[dim]);
                document.getElementById(dim+'Val').innerText = Math.round(newDims[dim]);
            }
            updateWeatherByDimensions();
            updateSafetyMeter();
            updateCornerPersona();
        } catch(e) { console.error('演化失败', e); }
    }

    async function sendMessage() {
        const input = document.getElementById('userInput');
        const text = input.value.trim();
        if(!text) return;
        input.value = '';
        const userTime = new Date().toLocaleTimeString();
        const msgContainer = document.getElementById('msgContainer');
        msgContainer.innerHTML += `<div class="message user"><div class="message-bubble">${escapeHtml(text)}<div class="message-time">${userTime}</div></div><div class="message-avatar">👤</div></div>`;
        msgContainer.scrollTop = msgContainer.scrollHeight;
        const thinkingId = 'think'+Date.now();
        msgContainer.innerHTML += `<div class="message ai" id="${thinkingId}"><div class="message-avatar">🌟</div><div class="message-bubble"><div class="typing-indicator"><span></span><span></span><span></span></div></div></div>`;
        msgContainer.scrollTop = msgContainer.scrollHeight;
        try {
            const res = await fetch('/api/chat', {
                method: 'POST',
                headers: {'Content-Type':'application/json'},
                body: JSON.stringify({message: text, dimensions: dimensions})
            });
            const data = await res.json();
            const reply = data.reply;
            document.getElementById(thinkingId).remove();
            const aiTime = new Date().toLocaleTimeString();
            msgContainer.innerHTML += `<div class="message ai"><div class="message-avatar">🌟</div><div class="message-bubble">${escapeHtml(reply)}<div class="message-time">${aiTime}</div></div></div>`;
            msgContainer.scrollTop = msgContainer.scrollHeight;
            analysisHistory.unshift({text: reply.substring(0,100), personality: getClosestPersonaFromDimensions(), time: aiTime});
            updateHistoryUI();
            
            await evolveDimensions(text);
            if (therapyModeActive) {
                await analyzeUserState(text);
            }
        } catch(e) {
            document.getElementById(thinkingId).remove();
            msgContainer.innerHTML += `<div class="message ai"><div class="message-avatar">🌟</div><div class="message-bubble">网络出了一点小问题，请重试~ 😔</div></div>`;
        }
    }

    function updateHistoryUI() {
        const historyDiv = document.getElementById('historyList');
        if(analysisHistory.length === 0) {
            historyDiv.innerHTML = '<div style="text-align:center; padding:40px;">🌸 暂无聊天记录</div>';
            return;
        }
        historyDiv.innerHTML = analysisHistory.slice(0,5).map(item => `
            <div class="history-item">
                <div>💬 ${escapeHtml(item.text)}</div>
                <div style="display:flex; justify-content:space-between; margin-top:6px;">
                    <span>${personalityIcons[item.personality] || '🌟'} ${item.personality}</span><span>${item.time}</span>
                </div>
            </div>
        `).join('');
    }

    function clearHistory() { analysisHistory = []; updateHistoryUI(); }
    function generateReport() {
        if(analysisHistory.length < 2) { alert('再多聊几句吧~'); return; }
        alert(`📊 情绪诊断报告\n主要人格: ${getClosestPersonaFromDimensions()}\n对话轮数: ${analysisHistory.length}\n💡 继续对话探索更多情绪~`);
    }
    
    function exportChatData() {
        const messages = [];
        const msgElements = document.querySelectorAll('#msgContainer .message');
        msgElements.forEach(el => {
            const isUser = el.classList.contains('user');
            const bubble = el.querySelector('.message-bubble');
            const timeSpan = el.querySelector('.message-time');
            if (bubble) {
                const clone = bubble.cloneNode(true);
                const timeClone = clone.querySelector('.message-time');
                if (timeClone) timeClone.remove();
                const content = clone.innerText.trim();
                messages.push({
                    role: isUser ? 'user' : 'ai',
                    content: content,
                    time: timeSpan ? timeSpan.innerText : ''
                });
            }
        });
        
        const currentPersona = getClosestPersonaFromDimensions();
        const safetyData = updateSafetyMeter();
        const userState = latestUserState || { 
            stress_index: '未分析', 
            main_emotion: '未分析',
            valence: '--',
            anxiety_score: '--',
            depression_score: '--',
            anger_score: '--'
        };
        const currentMode = therapyModeActive ? '心理倾听模式' : '人格塑造模式';
        
        const exportData = {
            export_time: new Date().toLocaleString(),
            mode: currentMode,
            ai_name: guardianName,
            ai_persona: currentPersona,
            ai_dimensions: {...dimensions},
            ai_safety: safetyData,
            user_state: userState,
            messages: messages,
            message_count: messages.length
        };
        
        const dataStr = JSON.stringify(exportData, null, 2);
        const blob = new Blob([dataStr], {type: 'application/json'});
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `chat_export_${currentMode}_${new Date().toISOString().slice(0,19).replace(/:/g, '-')}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }
    
    function escapeHtml(str) { return str.replace(/[&<>]/g, m => ({'&':'&amp;','<':'&lt;','>':'&gt;'})[m]); }

    // 初始化
    updateWeatherByDimensions();
    updateSafetyMeter();
    updateCornerPersona();
</script>
</body>
</html>
'''


if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=8080)
