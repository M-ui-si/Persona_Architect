import streamlit as st
import random
import json
import time
from datetime import datetime
from llm_providers import create_llm_provider

# -------------------- 页面配置 --------------------
st.set_page_config(
    page_title="🏰 人格模拟系统",
    page_icon="🏰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -------------------- 初始化 Session State --------------------
if "dimensions" not in st.session_state:
    st.session_state.dimensions = {
        "openness": 5,
        "conscientiousness": 5,
        "extraversion": 5,
        "agreeableness": 5,
        "neuroticism": 5
    }

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "ai", "content": "欢迎来到人格模拟系统！🏰\n调节五维参数塑造人格，或点击「心理倾听模式」进入治疗场景。", "time": datetime.now().strftime("%H:%M")}
    ]

if "therapy_mode" not in st.session_state:
    st.session_state.therapy_mode = False

if "guardian_name" not in st.session_state:
    st.session_state.guardian_name = "小晴"

if "latest_user_state" not in st.session_state:
    st.session_state.latest_user_state = None

if "analysis_history" not in st.session_state:
    st.session_state.analysis_history = []

# -------------------- 常量与配置 --------------------
# 从环境变量读取 LLM 配置（与原来一致）
import os
LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "dashscope")
LLM_API_KEY = os.environ.get("LLM_API_KEY", "sk-d20d3484381e4553be21ff72e60dbf1e")  # 请替换
LLM_MODEL = os.environ.get("LLM_MODEL", "qwen-turbo")

# 创建 LLM 实例
llm = create_llm_provider(LLM_PROVIDER, LLM_API_KEY, LLM_MODEL)

# 五维人格预设（与之前一致）
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

personality_icons = {
    '热情洋溢':'😊','内向温柔':'😢','傲娇毒舌':'😤','理性冷静':'😌',
    '好奇心旺':'😲','腼腆社恐':'😳','活泼贪玩':'🤩','敏感多虑':'😰',
    '慵懒佛系':'😴','念旧文艺':'📖','情绪倾听者':'💞'
}

# 心理倾听模式专用预设
therapy_preset_map = {
    "unconditionalPositiveRegard": {
        "openness": 6, "conscientiousness": 6, "extraversion": 5,
        "agreeableness": 9, "neuroticism": 2,
        "description": "高宜人性 + 低神经质，温暖、接纳、不评判，提供安全倾诉环境。"
    },
    "socraticQuestioner": {
        "openness": 9, "conscientiousness": 8, "extraversion": 4,
        "agreeableness": 7, "neuroticism": 3,
        "description": "高开放性 + 高尽责性，通过提问引导你深入思考，发现自身资源。"
    },
    "gentleChallenger": {
        "openness": 8, "conscientiousness": 7, "extraversion": 6,
        "agreeableness": 6, "neuroticism": 4,
        "description": "中等宜人性 + 高开放性，在共情中适当挑战认知偏差，推动成长。"
    }
}

# 情绪关键词（用于动态演化）
EMOTION_KEYWORDS = {
    'sadness': ['难过', '伤心', '想哭', '抑郁', '绝望', '无望', '累', '没意思', '孤独', '失落', '沮丧', '悲痛'],
    'anxiety': ['担心', '害怕', '焦虑', '紧张', '不安', '压力', '恐惧', '惶恐', '忧虑'],
    'anger': ['生气', '愤怒', '恨', '讨厌', '滚', '蠢', '暴躁', '火大', '不爽', '恼怒'],
    'joy': ['开心', '快乐', '高兴', '有趣', '喜欢', '幸福', '兴奋', '愉快', '欢乐']
}

# -------------------- 辅助函数 --------------------
def get_closest_persona(dimensions):
    """根据五维分数返回最接近的人格名称"""
    best_persona = "理性冷静"
    min_dist = float('inf')
    for persona, target in dimension_to_persona.items():
        dist = sum((dimensions.get(k, 5) - target[k]) ** 2
                   for k in ['openness', 'conscientiousness', 'extraversion',
                             'agreeableness', 'neuroticism'])
        if dist < min_dist:
            min_dist = dist
            best_persona = persona
    if min_dist < 8:
        return best_persona
    # 否则返回一个描述性短语
    return get_persona_description(dimensions)

def get_persona_description(dimensions):
    adj_map = {
        'openness': {1: '务实', 2: '传统', 5: '开放', 8: '好奇', 9: '创新'},
        'conscientiousness': {1: '随性', 2: '灵活', 5: '可靠', 8: '自律', 9: '勤奋'},
        'extraversion': {1: '内向', 2: '沉默', 5: '平和', 8: '外向', 9: '健谈'},
        'agreeableness': {1: '固执', 2: '批判', 5: '随和', 8: '耐心', 9: '宽容'},
        'neuroticism': {1: '冷静', 2: '坚韧', 5: '平衡', 8: '敏感', 9: '共情'}
    }
    parts = []
    for dim, mapping in adj_map.items():
        score = dimensions[dim]
        if score <= 3:
            adj = mapping[1] if score == 1 else mapping[2]
        elif score <= 6:
            adj = mapping[5]
        else:
            adj = mapping[8] if score <= 8 else mapping[9]
        parts.append(adj)
    return "、".join(parts)

def build_personality_prompt(dimensions):
    level_adverbs = {
        1: '极低', 2: '非常低', 3: '较低', 4: '略低',
        5: '中等', 6: '略高', 7: '较高', 8: '非常高', 9: '极高'
    }
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
    for dim, name in [('openness', '开放性'), ('conscientiousness', '尽责性'),
                      ('extraversion', '外向性'), ('agreeableness', '宜人性'),
                      ('neuroticism', '神经质')]:
        score = dimensions[dim]
        desc_parts.append(f"{name}水平为{level_adverbs[score]}。" + eval(f"{dim}_descs")[score])

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
        st.error(f"AI回复生成失败: {e}")
        # 本地 fallback
        persona = get_closest_persona(dimensions)
        fallback_replies = {
            "热情洋溢": "哇！今天天气真好，一起出去玩吧！😊✨",
            "理性冷静": "嗯...这件事我们可以理性分析一下~ 😌"
        }
        return fallback_replies.get(persona, "我在这里听着呢。")

def analyze_user_state(text):
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
        if content.startswith('```json'):
            content = content[7:]
        if content.startswith('```'):
            content = content[3:]
        if content.endswith('```'):
            content = content[:-3]
        result = json.loads(content.strip())
        for key in default_result:
            if key not in result:
                result[key] = default_result[key]
        return result
    except Exception as e:
        return default_result

def adjust_dimensions_by_emotion(dimensions, user_text):
    new_dims = dimensions.copy()
    text_lower = user_text.lower()
    adjustments = {
        'openness': 0, 'conscientiousness': 0, 'extraversion': 0,
        'agreeableness': 0, 'neuroticism': 0
    }
    if any(w in text_lower for w in EMOTION_KEYWORDS['sadness']):
        adjustments['neuroticism'] -= 0.5
        adjustments['agreeableness'] += 0.5
    if any(w in text_lower for w in EMOTION_KEYWORDS['anxiety']):
        adjustments['neuroticism'] -= 0.3
        adjustments['extraversion'] -= 0.2
        adjustments['conscientiousness'] += 0.2
    if any(w in text_lower for w in EMOTION_KEYWORDS['anger']):
        adjustments['agreeableness'] -= 0.5
        adjustments['neuroticism'] += 0.2
    if any(w in text_lower for w in EMOTION_KEYWORDS['joy']):
        adjustments['extraversion'] += 0.3
        adjustments['openness'] += 0.2
    for dim in new_dims:
        new_dims[dim] = max(1, min(9, new_dims[dim] + adjustments[dim]))
    return new_dims

def calculate_safety_score(dimensions, text=""):
    aggression_base = (dimensions['neuroticism'] / 9) * 0.5 + ((10 - dimensions['agreeableness']) / 9) * 0.5
    deceit_base = ((10 - dimensions['conscientiousness']) / 9) * 0.6 + ((10 - dimensions['agreeableness']) / 9) * 0.4
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
        st.error(f"描述分析失败: {e}")
        return {'openness':5, 'conscientiousness':5, 'extraversion':5, 'agreeableness':5, 'neuroticism':5}

# -------------------- UI 布局 --------------------
st.markdown("""
<style>
    .stChatMessage { padding: 0.5rem 1rem; }
    .dimension-slider { margin-bottom: 0.5rem; }
    .risk-low { background-color: #2ecc71; color: white; padding: 4px 12px; border-radius: 20px; }
    .risk-mid { background-color: #f1c40f; color: black; padding: 4px 12px; border-radius: 20px; }
    .risk-high { background-color: #e74c3c; color: white; padding: 4px 12px; border-radius: 20px; }
</style>
""", unsafe_allow_html=True)

st.title("🏰 人格模拟系统")

# 侧边栏：模式切换、名字、人格形容塑造
with st.sidebar:
    st.header("⚙️ 控制面板")
    therapy_mode = st.checkbox("🫂 心理倾听模式", value=st.session_state.therapy_mode)
    if therapy_mode != st.session_state.therapy_mode:
        st.session_state.therapy_mode = therapy_mode
        if therapy_mode:
            # 自动应用情绪倾听者预设
            st.session_state.dimensions = dimension_to_persona['情绪倾听者'].copy()
            st.success("已进入心理倾听模式，人格已调整为「情绪倾听者」")

    st.divider()
    guardian_name = st.text_input("AI 名称", value=st.session_state.guardian_name)
    if guardian_name != st.session_state.guardian_name:
        st.session_state.guardian_name = guardian_name

    st.divider()
    st.subheader("✏️ 人格形容塑造")
    persona_desc = st.text_area("用文字描述理想人格", placeholder="例如：一个开放、勤奋、外向、友善且情绪稳定的人...")
    if st.button("✨ 应用描述塑造人格"):
        if persona_desc:
            new_dims = analyze_description_to_dimensions(persona_desc)
            st.session_state.dimensions = new_dims
            st.success("人格已根据描述更新！")
        else:
            st.warning("请输入描述")

    st.divider()
    st.subheader("📦 数据导出")
    if st.button("📥 导出聊天数据"):
        export_data = {
            "export_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "mode": "心理倾听模式" if st.session_state.therapy_mode else "人格塑造模式",
            "ai_name": st.session_state.guardian_name,
            "ai_dimensions": st.session_state.dimensions,
            "messages": st.session_state.messages
        }
        st.download_button(
            label="下载 JSON",
            data=json.dumps(export_data, ensure_ascii=False, indent=2),
            file_name=f"chat_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json"
        )

# 主区域分为两列：左（对话+维度调节），右（状态监测+安全评估）
col1, col2 = st.columns([2.5, 1.5])

with col1:
    # 当前人格显示
    current_persona = get_closest_persona(st.session_state.dimensions)
    icon = personality_icons.get(current_persona, "😊")
    st.markdown(f"### {icon} 当前人格：{current_persona}")

    # 五维滑块
    with st.expander("🎚️ 调节五维人格参数", expanded=True):
        cols = st.columns(5)
        dim_labels = {
            "openness": "🎨 开放性", "conscientiousness": "📋 尽责性",
            "extraversion": "🌊 外向性", "agreeableness": "😊 宜人性",
            "neuroticism": "💧 神经质"
        }
        for i, (dim, label) in enumerate(dim_labels.items()):
            with cols[i]:
                new_val = st.slider(label, 1, 9, st.session_state.dimensions[dim], key=f"slider_{dim}")
                if new_val != st.session_state.dimensions[dim]:
                    st.session_state.dimensions[dim] = new_val

        # 预设按钮行
        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("🔻 全极低 (1)"):
                for dim in st.session_state.dimensions:
                    st.session_state.dimensions[dim] = 1
                st.rerun()
        with c2:
            if st.button("⚖️ 全中等 (5)"):
                for dim in st.session_state.dimensions:
                    st.session_state.dimensions[dim] = 5
                st.rerun()
        with c3:
            if st.button("🔺 全极高 (9)"):
                for dim in st.session_state.dimensions:
                    st.session_state.dimensions[dim] = 9
                st.rerun()

        # 模式专属预设
        if st.session_state.therapy_mode:
            st.caption("心理倾听者模板")
            t1, t2, t3 = st.columns(3)
            with t1:
                if st.button("🤗 无条件积极关注"):
                    st.session_state.dimensions = therapy_preset_map["unconditionalPositiveRegard"].copy()
                    st.rerun()
            with t2:
                if st.button("💬 冷静提问者"):
                    st.session_state.dimensions = therapy_preset_map["socraticQuestioner"].copy()
                    st.rerun()
            with t3:
                if st.button("🌱 温和挑战者"):
                    st.session_state.dimensions = therapy_preset_map["gentleChallenger"].copy()
                    st.rerun()
        else:
            st.caption("快速预设人格")
            preset_cols = st.columns(4)
            presets = ["热情洋溢", "理性冷静", "敏感多虑", "情绪倾听者"]
            for idx, preset in enumerate(presets):
                with preset_cols[idx % 4]:
                    if st.button(f"{personality_icons.get(preset, '🎭')} {preset}"):
                        st.session_state.dimensions = dimension_to_persona[preset].copy()
                        st.rerun()

    # 聊天界面
    st.subheader("💬 对话")
    chat_container = st.container()
    with chat_container:
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
                st.caption(msg.get("time", ""))

    # 输入框
    user_input = st.chat_input("说点什么...")
    if user_input:
        # 添加用户消息
        now = datetime.now().strftime("%H:%M")
        st.session_state.messages.append({"role": "user", "content": user_input, "time": now})
        with chat_container:
            with st.chat_message("user"):
                st.markdown(user_input)
                st.caption(now)

        # 生成 AI 回复
        with st.spinner(f"{st.session_state.guardian_name} 正在思考..."):
            reply = get_ai_response(user_input, st.session_state.dimensions)
        now = datetime.now().strftime("%H:%M")
        st.session_state.messages.append({"role": "ai", "content": reply, "time": now})
        with chat_container:
            with st.chat_message("ai"):
                st.markdown(reply)
                st.caption(now)

        # 动态演化（仅在倾听模式）
        if st.session_state.therapy_mode:
            target_dims = adjust_dimensions_by_emotion(st.session_state.dimensions, user_input)
            rate = 0.3
            new_dims = {}
            for dim in st.session_state.dimensions:
                new_val = st.session_state.dimensions[dim] + rate * (target_dims[dim] - st.session_state.dimensions[dim])
                new_dims[dim] = int(round(max(1, min(9, new_val))))
            st.session_state.dimensions = new_dims

        # 分析用户状态（倾听模式）
        if st.session_state.therapy_mode:
            st.session_state.latest_user_state = analyze_user_state(user_input)

        # 记录历史（用于展示，非必须）
        st.session_state.analysis_history.append({
            "text": reply[:100],
            "persona": current_persona,
            "time": now
        })

with col2:
    st.subheader("🛡️ 安全评估")
    safety = calculate_safety_score(st.session_state.dimensions)
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        st.metric("攻击性", f"{safety['aggression_score']}%")
    with col_b:
        st.metric("欺骗风险", f"{safety['deceit_score']}%")
    with col_c:
        st.metric("抑郁倾向", f"{safety['depression_score']}%")

    risk_class = "risk-low" if safety['risk_level'] == "低" else ("risk-mid" if safety['risk_level'] == "中" else "risk-high")
    st.markdown(f"综合风险等级：<span class='{risk_class}'>{safety['risk_level']}</span>", unsafe_allow_html=True)

    if st.button("🔍 检测当前输入风险"):
        last_user = next((m["content"] for m in reversed(st.session_state.messages) if m["role"] == "user"), "")
        if last_user:
            safety_with_text = calculate_safety_score(st.session_state.dimensions, last_user)
            st.info(f"文本增强后风险：{safety_with_text['risk_level']} (攻击性{safety_with_text['aggression_score']}%)")
        else:
            st.warning("没有用户输入")

    if st.session_state.therapy_mode:
        st.divider()
        st.subheader("🧠 用户心理状态")
        if st.session_state.latest_user_state:
            state = st.session_state.latest_user_state
            st.metric("压力指数", f"{state['stress_index']}%")
            st.write(f"主要情绪：{state['main_emotion']}")
            st.write(f"情绪效价：{state['valence']}")
            with st.expander("详细分数"):
                st.write(f"焦虑：{state['anxiety_score']}%")
                st.write(f"抑郁：{state['depression_score']}%")
                st.write(f"愤怒：{state['anger_score']}%")
        else:
            st.write("暂无分析数据，发送消息后自动分析")

    st.divider()
    st.subheader("📖 最近对话记录")
    for item in st.session_state.analysis_history[-5:]:
        st.caption(f"{item['time']} - {personality_icons.get(item['persona'], '🌟')} {item['persona']}")
        st.write(f"_{item['text']}_")
