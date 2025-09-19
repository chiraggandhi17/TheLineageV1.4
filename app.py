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
You are the 'Spiritual Navigator', a specialized AI guide. 
CRITICAL RULE: All lists you generate MUST be in a numbered list format (e.g., "1. Item one\n2. Item two"). Respond with ONLY the numbered list.
When providing the detailed teaching, structure it with clear markdown headings: "### Core Philosophical Concepts", "### The Prescribed Method or Practice", and "### Reference to Key Texts".
"""

# --- MASTER IMAGE DATABASE ---
MASTER_IMAGES = {
    "Ramana Maharshi": "https://upload.wikimedia.org/wikipedia/commons/4/4b/Ramana_Maharshi_1935.jpg",
    "Nisargadatta Maharaj": "https://upload.wikimedia.org/wikipedia/en/8/8f/Nisargadatta.jpg",
    "Adi Shankaracharya": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c5/Adi_Shankaracharya.jpg/800px-Adi_Shankaracharya.jpg",
    "Rumi": "https://upload.wikimedia.org/wikipedia/commons/thumb/6/67/Mevlana_Rumi.jpg/800px-Mevlana_Rumi.jpg"
}
PLACEHOLDER_IMAGE = "https://static.thenounproject.com/png/1230421-200.png"

# --- HELPER FUNCTIONS ---
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

def find_master_image_url(master_name_from_ai):
    master_name_lower = master_name_from_ai.lower()
    for known_name, url in MASTER_IMAGES.items():
        keywords = known_name.lower().replace("sri", "").replace("maharaj", "").split()
        if all(keyword in master_name_lower for keyword in keywords):
            return url
    return PLACEHOLDER_IMAGE

# --- SESSION STATE INITIALIZATION ---
if 'stage' not in st.session_state:
    st.session_state.stage = "start"

def restart_app():
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.session_state.stage = "start"

# --- MAIN APP UI ---
st.title("🧘 Spiritual Navigator")
load_custom_css()
st.caption("An interactive guide to ancient wisdom on modern emotions.")

if st.session_state.stage == "start":
    vritti_input = st.text_input("Enter an emotion, tendency, or 'vritti' to begin:", key="vritti_input")
    if vritti_input:
        restart_app()
        st.session_state.vritti = vritti_input
        st.session_state.stage = "show_traditions" # RE-ARCHITECTED: First step is now traditions
        st.rerun()

# --- RE-ARCHITECTED STAGE 1: SHOW TRADITIONS ---
elif st.session_state.stage == "show_traditions":
    st.subheader(f"Exploring: {st.session_state.vritti.capitalize()}")
    if 'traditions' not in st.session_state:
        with st.spinner("Consulting the world's wisdom traditions..."):
            prompt = f"For the emotion '{st.session_state.vritti}', list the broad spiritual/religious **Traditions** that have discussed it. Use umbrella terms like 'Indic Traditions (Hinduism)', 'Buddhist Traditions', 'Taoist Traditions', 'Abrahamic Mysticism (Sufism)', etc."
            response_text, history = call_gemini(prompt)
            if response_text:
                st.session_state.traditions = parse_list(response_text)
                st.session_state.chat_history = history
    
    st.write("First, choose a broad tradition:")
    st.markdown('<div class="button-container">', unsafe_allow_html=True)
    for i, tradition in enumerate(st.session_state.get('traditions', [])):
        if st.button(tradition, key=f"tradition_{i}"):
            st.session_state.chosen_tradition = tradition
            st.session_state.stage = "show_lineages" # Move to the new lineages stage
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    st.divider()
    if st.button("Start Over"):
        restart_app()
        st.rerun()

# --- RE-ARCHITECTED STAGE 2: SHOW LINEAGES WITHIN A TRADITION ---
elif st.session_state.stage == "show_lineages":
    st.subheader(f"Tradition: {st.session_state.chosen_tradition}")
    if 'lineages' not in st.session_state:
        with st.spinner(f"Finding schools within {st.session_state.chosen_tradition}..."):
            prompt = f"Within the tradition of **{st.session_state.chosen_tradition}**, list the specific **Schools, Philosophies, or Lineages** that have teachings on '{st.session_state.vritti}'."
            response_text, history = call_gemini(prompt, st.session_state.chat_history)
            if response_text:
                st.session_state.lineages = parse_list(response_text)
                st.session_state.chat_history = history
    
    st.write("Next, choose a specific school or lineage:")
    st.markdown('<div class="button-container">', unsafe_allow_html=True)
    for i, lineage in enumerate(st.session_state.get('lineages', [])):
        if st.button(lineage, key=f"lineage_{i}"):
            st.session_state.chosen_lineage = lineage
            st.session_state.stage = "show_masters"
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    st.divider()
    if st.button("Back to Traditions"):
        st.session_state.stage = "show_traditions"
        # Clear data from this stage and subsequent stages
        keys_to_clear = ['lineages', 'masters', 'chosen_tradition']
        for key in keys_to_clear:
            if key in st.session_state: del st.session_state[key]
        st.rerun()

elif st.session_state.stage == "show_masters":
    st.subheader(f"School: {st.session_state.chosen_lineage}")
    if 'masters' not in st.session_state:
        with st.spinner(f"Finding masters..."):
            prompt = f"List masters from the {st.session_state.chosen_lineage} lineage who discussed {st.session_state.vritti}."
            response_text, history = call_gemini(prompt, st.session_state.chat_history)
            st.session_state.raw_response = response_text
            if response_text:
                st.session_state.masters = parse_list(response_text)
                st.session_state.chat_history = history

    if not st.session_state.get('masters'):
        st.warning("No relevant masters were found for this topic.")
    else:
        st.write("Choose a master to learn from:")
        for i, master in enumerate(st.session_state.get('masters', [])):
            col1, col2 = st.columns([1, 4])
            with col1:
                image_url = find_master_image_url(master)
                st.image(image_url, width=70)
            with col2:
                st.write(f"**{master}**")
                if st.button(f"Explore Teachings", key=f"master_{i}"):
                    st.session_state.chosen_master = master
                    st.session_state.stage = "show_teachings"
                    st.rerun()
    
    st.divider()
    if st.button("Back to Schools/Lineages"):
        st.session_state.stage = "show_lineages"
        if 'masters' in st.session_state: del st.session_state['masters']
        st.rerun()

# --- The final stage, show_teachings, remains largely the same ---
elif st.session_state.stage == "show_teachings":
    st.subheader(f"Teachings of {st.session_state.chosen_master}")
    st.caption(f"From the **{st.session_state.chosen_lineage}** perspective.")
    
    if 'teachings' not in st.session_state:
        with st.spinner("Distilling the wisdom..."):
            prompt = f"What were {st.session_state.chosen_master}'s teachings on {st.session_state.vritti}?"
            response_text, history = call_gemini(prompt, st.session_state.chat_history)
            if response_text:
                st.session_state.teachings = parse_teachings(response_text)
    
    if st.session_state.get('teachings'):
        tab1, tab2, tab3 = st.tabs(["**Core Concepts**", "**The Method**", "**Key Texts**"])
        with tab1: st.markdown(st.session_state.teachings.get("concepts", "No information provided."))
        with tab2: st.markdown(st.session_state.teachings.get("method", "No information provided."))
        with tab3: st.markdown(st.session_state.teachings.get("texts", "No information provided."))
    else:
        st.warning("Could not parse the teachings for this master.")

    st.divider()
    if st.button("Back to Masters List"):
        st.session_state.stage = "show_masters"
        if 'teachings' in st.session_state: del st.session_state['teachings']
        st.rerun()