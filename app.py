import streamlit as st
import google.generativeai as genai
import os
import re

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Spiritual Navigator",
    page_icon="🧘",
    layout="centered"
)

# --- THEME & STYLING ---
def load_custom_css():
    st.markdown("""
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Lato:wght@400;700&display=swap');
            :root {
                --primary-color: #4A909A;
                --background-color: #F0F2F6;
                --secondary-background-color: #FFFFFF;
                --text-color: #31333F;
                --font: 'Lato', sans-serif;
            }
            .stApp, .stApp h1, .stApp h2, .stApp h3, .stApp p, .stApp li, .stApp label, .stApp .stMarkdown {
                color: var(--text-color) !important;
            }
            body, .stApp { background-color: var(--background-color); }
            h1, h2, h3 { font-family: var(--font); }
            .stTabs [data-baseweb="tab"][aria-selected="true"] {
                background-color: transparent;
                color: var(--primary-color);
                border-bottom: 2px solid var(--primary-color);
            }
            .button-container { display: flex; flex-wrap: wrap; gap: 10px; justify-content: center; margin-bottom: 20px; }
            .stButton>button { border-radius: 20px; border: 1px solid var(--primary-color); color: var(--primary-color); background-color: transparent; transition: all 0.3s ease-in-out; padding: 5px 15px; }
            .stButton>button:hover { color: var(--secondary-background-color); background-color: var(--primary-color); }
            .st-emotion-cache-1r6slb0, .st-emotion-cache-p5msec { 
                border-radius: 10px; padding: 1rem; background-color: var(--secondary-background-color); 
                box-shadow: 0 4px 8px rgba(0,0,0,0.08); transition: box-shadow 0.3s ease-in-out; 
            }
            .st-emotion-cache-1r6slb0:hover, .st-emotion-cache-p5msec:hover { 
                box-shadow: 0 8px 16px rgba(0,0,0,0.12);
            }
        </style>
    """, unsafe_allow_html=True)

# --- API CONFIGURATION ---
api_key = "AIzaSyCnVxCjbGDV2Y56bC6xGWC0KfjBV9daAQE"
if not api_key or "GEMINI_API_KEY" in api_key:
    st.error("Please add your Gemini API key to the code!")
    st.stop()
genai.configure(api_key=api_key)

# --- SYSTEM INSTRUCTION (THE "GEM" PROMPT) ---
system_instruction = """
You are the 'Spiritual Navigator', a specialized AI guide. The user will specify a language for you to respond in. All your responses, including lists and teachings, must be in that specified language.
CRITICAL RULE: All lists you generate MUST be in a numbered list format (e.g., "1. Item one\n2. Item two"). Respond with ONLY the numbered list.
When providing the detailed teaching, structure it with clear markdown headings: "### Core Philosophical Concepts", "### The Prescribed Method or Practice", and "### Reference to Key Texts" (translate these headings into the user's chosen language).
When asked for books, places, or events, if no relevant information exists, you must respond with ONLY the single word 'None' (in English).
When asked for book recommendations, provide a numbered list. For each book, include the title (in its original language if possible), a one-sentence description, and a markdown link to search for it on Amazon.in.
When asked to generate a contemplative practice, present it as a series of simple, actionable steps. After the steps, if a relevant and soothing bhajan, chant, or hymn is associated with the teaching, add a section called "### Suggested Listening" (translated to the user's language) and provide a markdown link to a YouTube search for it.
"""

# --- DATABASES & HELPERS ---
PLACEHOLDER_IMAGE = "https://static.thenounproject.com/png/1230421-200.png"

def call_gemini(prompt, history=None):
    try:
        model = genai.GenerativeModel(model_name='gemini-1.5-pro-latest', system_instruction=system_instruction)
        chat = model.start_chat(history=history or [])
        response = chat.send_message(prompt)
        return response.text, chat.history
    except Exception as e:
        st.error(f"An error occurred with the API call: {e}")
        return None, None

def parse_list(text):
    if not text: return []
    items = re.findall(r'^\s*[\*\-\d]+\.?\s*(.+)$', text, re.MULTILINE)
    cleaned_items = [item.strip().replace('**', '') for item in items if item.strip()]
    return cleaned_items

def parse_teachings(text):
    if not text: return {}
    sections = {}
    parts = re.split(r'###\s*(.*)', text)
    if len(parts) > 1:
        try:
            sections[parts[1].strip()] = parts[2].strip()
            sections[parts[3].strip()] = parts[4].strip()
            sections[parts[5].strip()] = parts[6].strip()
        except IndexError:
            sections["Content"] = text 
    else:
        sections["Content"] = text
    return sections

def find_master_image_url(master_name):
    if 'image_cache' not in st.session_state:
        st.session_state.image_cache = {}
    if master_name in st.session_state.image_cache:
        return st.session_state.image_cache[master_name]
    
    with st.spinner(f"Finding image for {master_name}..."):
        prompt = f"Find a publicly available, direct image link for the spiritual master '{master_name}'. The URL must end in .jpg, .jpeg, or .png. A good source is Wikimedia Commons. If you cannot find a link, respond with ONLY the word 'None'."
        url_response, _ = call_gemini(prompt)
        if url_response and url_response.strip().lower().startswith('http'):
            image_url = url_response.strip()
        else:
            image_url = PLACEHOLDER_IMAGE
        st.session_state.image_cache[master_name] = image_url
        return image_url

# --- LANGUAGE FEATURE RESTORED ---
if 'stage' not in st.session_state:
    st.session_state.stage = "start"
if 'language' not in st.session_state:
    st.session_state.language = "English"

def restart_app():
    lang = st.session_state.language
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.session_state.stage = "start"
    st.session_state.language = lang

L10N = {
    "English": {
        "caption": "An interactive guide to ancient wisdom on modern emotions.",
        "input_prompt": "Enter an emotion, tendency, or 'vritti' to begin:",
        "start_over": "Start Over",
        "choose_lang": "Choose your language:",
        "exploring": "Exploring",
        "choose_path": "Choose a path to explore further:",
        "path": "Path",
        "finding_masters": "Finding masters...",
        "no_masters": "No relevant masters were found for this topic.",
        "choose_master": "Choose a master to learn from:",
        "explore_teachings": "Explore Teachings",
        "back_to_lineages": "Back to Lineages",
        "teachings_of": "Teachings of",
        "on": "On",
        "from": "from the",
        "perspective": "perspective",
        "distilling_wisdom": "Distilling the wisdom...",
        "could_not_parse": "The AI's response could not be parsed.",
        "show_raw": "Show Raw AI Response",
        "no_response": "No response was received.",
        "back_to_masters": "Back to Masters List",
        "guided_practice": "Generate a Guided Practice",
        "practice_info": "Follow these prompts for inner reflection.",
    },
    "Gujarati": {
        "caption": "આધુનિક લાગણીઓ પર પ્રાચીન જ્ઞાન માટેની ઇન્ટરેક્ટિવ માર્ગદર્શિકા.",
        "input_prompt": "શરૂ કરવા માટે ભાવના, વૃત્તિ અથવા 'વૃત્તિ' દાખલ કરો:",
        "start_over": "ફરીથી શરૂ કરો",
        "choose_lang": "તમારી ભાષા પસંદ કરો:",
        "exploring": "અન્વેષણ",
        "choose_path": "વધુ અન્વેષણ કરવા માટે એક માર્ગ પસંદ કરો:",
        "path": "માર્ગ",
        "finding_masters": "ગુરુઓ શોધી રહ્યા છીએ...",
        "no_masters": "આ વિષય માટે કોઈ સંબંધિત ગુરુ મળ્યા નથી.",
        "choose_master": "શીખવા માટે ગુરુ પસંદ કરો:",
        "explore_teachings": "શિક્ષાઓનું અન્વેષણ કરો",
        "back_to_lineages": "વંશ પર પાછા જાઓ",
        "teachings_of": "ની શિક્ષાઓ",
        "on": "વિષય પર",
        "from": "ના",
        "perspective": "પરિપ્રેક્ષ્યમાં",
        "distilling_wisdom": "જ્ઞાનને નિસ્યંદિત કરી રહ્યા છીએ...",
        "could_not_parse": "AI ના પ્રતિભાવને પાર્સ કરી શકાયો નથી.",
        "show_raw": "કાચો AI પ્રતિભાવ બતાવો",
        "no_response": "કોઈ પ્રતિભાવ મળ્યો નથી.",
        "back_to_masters": "ગુરુઓની સૂચિ પર પાછા જાઓ",
        "guided_practice": "માર્ગદર્શિત અભ્યાસ બનાવો",
        "practice_info": "આંતરિક પ્રતિબિંબ માટે આ સંકેતોને અનુસરો.",
    }
}

# --- MAIN APP UI ---
st.title("🧘 Spiritual Navigator")
load_custom_css()
txt = L10N[st.session_state.language]
st.caption(txt["caption"])

if st.session_state.stage == "start":
    lang_options = list(L10N.keys())
    st.session_state.language = st.selectbox(
        L10N["English"]["choose_lang"] + " / " + L10N["Gujarati"]["choose_lang"],
        options=lang_options,
        index=lang_options.index(st.session_state.language)
    )
    vritti_input = st.text_input(txt["input_prompt"], key="vritti_input")
    if vritti_input:
        st.session_state.vritti = vritti_input
        st.session_state.stage = "show_lineages"
        st.rerun()

elif st.session_state.stage == "show_lineages":
    st.subheader(f"{txt['exploring']}: {st.session_state.vritti.capitalize()}")
    if 'lineages' not in st.session_state:
        with st.spinner("Consulting the ancient traditions..."):
            prompt = f"Respond in {st.session_state.language}. Give me a list of spiritual lineages that talk about {st.session_state.vritti}."
            response_text, history = call_gemini(prompt)
            if response_text:
                st.session_state.lineages = parse_list(response_text)
                st.session_state.chat_history = history
    st.write(txt["choose_path"])
    st.markdown('<div class="button-container">', unsafe_allow_html=True)
    for i, lineage in enumerate(st.session_state.get('lineages', [])):
        if st.button(lineage, key=f"lineage_{i}"):
            st.session_state.chosen_lineage = lineage
            st.session_state.stage = "show_masters"
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    st.divider()
    if st.button(txt["start_over"]):
        restart_app()
        st.rerun()

elif st.session_state.stage == "show_masters":
    st.subheader(f"{txt['path']}: {st.session_state.chosen_lineage}")
    if 'masters' not in st.session_state:
        with st.spinner(txt["finding_masters"]):
            prompt = f"Respond in {st.session_state.language}. List masters from the {st.session_state.chosen_lineage} lineage who discussed {st.session_state.vritti}."
            response_text, history = call_gemini(prompt, st.session_state.chat_history)
            st.session_state.raw_response = response_text
            if response_text:
                st.session_state.masters = parse_list(response_text)
                st.session_state.chat_history = history
    if not st.session_state.get('masters'):
        st.warning(txt["no_masters"])
    else:
        st.write(txt["choose_master"])
        for i, master in enumerate(st.session_state.get('masters', [])):
            col1, col2 = st.columns([1, 4])
            with col1:
                image_url = find_master_image_url(master)
                st.image(image_url, width=70)
            with col2:
                st.write(f"**{master}**")
                if st.button(txt["explore_teachings"], key=f"master_{i}"):
                    st.session_state.chosen_master = master
                    st.session_state.stage = "show_teachings"
                    st.rerun()
    st.divider()
    if st.button(txt["back_to_lineages"]):
        st.session_state.stage = "show_lineages"
        if 'masters' in st.session_state: del st.session_state['masters']
        st.rerun()
    if st.button(txt["start_over"]):
        restart_app()
        st.rerun()

elif st.session_state.stage == "show_teachings":
    st.subheader(f"{txt['teachings_of']} {st.session_state.chosen_master}")
    st.caption(f"{txt['on']} **{st.session_state.vritti.capitalize()}** {txt['from']} **{st.session_state.chosen_lineage}** {txt['perspective']}")
    if 'teachings' not in st.session_state:
        with st.spinner(txt["distilling_wisdom"]):
            prompt = f"Respond in {st.session_state.language}. What were {st.session_state.chosen_master}'s teachings on {st.session_state.vritti}? Structure the response with clear markdown headings for 'Core Philosophical Concepts', 'The Prescribed Method or Practice', and 'Reference to Key Texts', translating those headings into {st.session_state.language}."
            response_text, history = call_gemini(prompt, st.session_state.chat_history)
            st.session_state.raw_response = response_text
            if response_text:
                st.session_state.teachings = parse_teachings(response_text)
                st.session_state.chat_history = history
            else:
                st.session_state.teachings = {}
    if st.session_state.get('teachings'):
        headings = list(st.session_state.teachings.keys())
        if headings:
            tab_objects = st.tabs([f"**{h}**" for h in headings])
            for i, tab in enumerate(tab_objects):
                with tab:
                    st.markdown(st.session_state.teachings[headings[i]])
        st.divider()
        st.subheader("Contemplative Practice")
        if st.button(txt["guided_practice"]):
            with st.spinner("Generating a relevant practice..."):
                practice_prompt = f"Respond in {st.session_state.language}. Based on the teachings of {st.session_state.chosen_master} regarding '{st.session_state.vritti}', generate a short, guided contemplative practice. Present it as a series of 2-4 simple, actionable steps in a numbered list. After the steps, if a relevant and soothing bhajan, chant, or hymn is associated with the teaching, add a section called '### Suggested Listening' and provide a markdown link to a YouTube search for it."
                practice_response, _ = call_gemini(practice_prompt)
                st.session_state.practice_text = practice_response
        if 'practice_text' in st.session_state:
            st.info(txt["practice_info"])
            st.markdown(st.session_state.practice_text)
    else:
        st.warning(txt["could_not_parse"])
        with st.expander(txt["show_raw"]):
            st.code(st.session_state.get('raw_response', txt["no_response"]))
    st.markdown("---")
    if st.button(txt["back_to_masters"]):
        st.session_state.stage = "show_masters"
        keys_to_clear = ['teachings', 'raw_response', 'practice_text']
        for key in keys_to_clear:
            if key in st.session_state: del st.session_state[key]
        st.rerun()
    if st.button(txt["start_over"]):
        restart_app()
        st.rerun()