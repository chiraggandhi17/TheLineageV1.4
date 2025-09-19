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
When asked for books, places, or events, if no relevant information exists, you must respond with ONLY the single word 'None'.
When asked for book recommendations, provide a numbered list. For each book, include the title, a one-sentence description, and a markdown link to search for it on Amazon.in.
When asked to generate a contemplative practice, present it as a series of 2-4 simple, actionable steps in a numbered list. The practice must be a practical exercise, not a philosophical explanation.
"""

# --- DATABASES ---
MASTER_IMAGES = {
    "Ramana Maharshi": "https://upload.wikimedia.org/wikipedia/commons/4/4b/Ramana_Maharshi_1935.jpg",
    "Nisargadatta Maharaj": "https://upload.wikimedia.org/wikipedia/en/8/8f/Nisargadatta.jpg",
    "Adi Shankaracharya": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c5/Adi_Shankaracharya.jpg/800px-Adi_Shankaracharya.jpg",
    "Rumi": "https://upload.wikimedia.org/wikipedia/commons/thumb/6/67/Mevlana_Rumi.jpg/800px-Mevlana_Rumi.jpg"
}
PLACEHOLDER_IMAGE = "https://static.thenounproject.com/png/1230421-200.png"

PATHS = {
    "anger_path": {
        "title": "A 5-Day Path on Anger",
        "vritti": "Anger",
        "tasks": [
            {"day": 1, "type": "lineage", "target": "Advaita Vedanta", "tradition": "Indic Traditions (Hinduism)", "instruction": "Explore the Advaita Vedanta perspective. Reflect on how the idea of the 'ego' relates to your experience of anger."},
            {"day": 2, "type": "master", "target": "Ramana Maharshi", "lineage": "Advaita Vedanta", "instruction": "Focus on the teachings of Ramana Maharshi. After reading, try the 'Begin a Guided Practice' section below."},
            {"day": 3, "type": "journal", "instruction": "Reflect on the last two days. Journal on the question: 'When anger arises, where does it come from and who is it happening to?'"},
            {"day": 4, "type": "lineage", "target": "Sufism", "tradition": "Abrahamic Mysticism", "instruction": "Explore a different perspective from Sufism. Notice any similarities or differences to the previous teachings."},
            {"day": 5, "type": "journal", "instruction": "Final reflection. How has your understanding of anger shifted? Write down one practical insight you can carry forward."}
        ]
    }
}

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

def parse_teachings(text):
    if not text: return {}
    sections = {}
    parts = re.split(r'###\s*(Core Philosophical Concepts|The Prescribed Method or Practice|Reference to Key Texts)', text)
    if len(parts) > 1:
        for i in range(1, len(parts), 2):
            heading, content = parts[i].strip(), parts[i+1].strip()
            if "Concepts" in heading: sections["concepts"] = content
            elif "Method" in heading: sections["method"] = content
            elif "Texts" in heading: sections["texts"] = content
    return sections

def find_master_image_url(master_name_from_ai):
    master_name_lower = master_name_from_ai.lower()
    for known_name, url in MASTER_IMAGES.items():
        keywords = known_name.lower().replace("sri", "").replace("maharaj", "").split()
        if all(keyword in master_name_lower for keyword in keywords):
            return url
    return PLACEHOLDER_IMAGE

# --- SESSION STATE INITIALIZATION ---
if 'stage' not in st.session_state:
    st.session_state.stage = "main_menu"

def full_restart():
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.session_state.stage = "main_menu"

# --- MAIN APP UI ---
st.title("🧘 Spiritual Navigator")
load_custom_css()
st.caption("An interactive guide to ancient wisdom on modern emotions.")

if st.session_state.stage == "main_menu":
    st.subheader("Welcome")
    st.write("Choose how you would like to begin your journey.")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Single Exploration", use_container_width=True):
            st.session_state.stage = "start_single_query"
            st.rerun()
    with col2:
        if st.button("Contemplative Path", use_container_width=True):
            st.session_state.stage = "path_selection"
            st.rerun()

elif st.session_state.stage == "start_single_query":
    vritti_input = st.text_input("Enter an emotion, tendency, or 'vritti' to begin:", key="vritti_input")
    if vritti_input:
        full_restart()
        st.session_state.vritti = vritti_input
        st.session_state.stage = "show_traditions"
        st.rerun()
    if st.button("Back to Main Menu"):
        st.session_state.stage = "main_menu"
        st.rerun()

elif st.session_state.stage == "path_selection":
    st.subheader("Choose a Contemplative Path")
    for path_key, path_data in PATHS.items():
        if st.button(path_data["title"], use_container_width=True):
            st.session_state.current_path = path_key
            st.session_state.stage = "day_selection" 
            st.rerun()
    st.divider()
    if st.button("Back to Main Menu"):
        st.session_state.stage = "main_menu"
        st.rerun()

elif st.session_state.stage == "day_selection":
    path_data = PATHS[st.session_state.current_path]
    st.subheader(path_data["title"])
    st.write("Select a day to begin your contemplation.")
    
    for task in path_data["tasks"]:
        if st.button(f"Day {task['day']}: {task['type'].title()} - {task.get('target', 'Reflection')}", use_container_width=True):
            st.session_state.current_day = task['day']
            st.session_state.stage = "on_path_task"
            st.rerun()
            
    st.divider()
    if st.button("Choose a Different Path"):
        st.session_state.stage = "path_selection"
        if 'current_path' in st.session_state: del st.session_state.current_path
        st.rerun()

elif st.session_state.stage == "on_path_task":
    path_data = PATHS[st.session_state.current_path]
    day_index = st.session_state.current_day - 1
    task = path_data["tasks"][day_index]
    st.header(f"{path_data['title']}")
    st.subheader(f"Day {task['day']}: {task['type'].replace('_', ' ').title()}")
    st.info(f"**Today's Focus:** {task['instruction']}")
    st.divider()
    
    # Display content based on the task type
    if task["type"] == "lineage":
        st.subheader(f"Exploring: {task['target']}")
        # Simplified display for lineage content
        st.write(f"Content about {task['target']} on the topic of {path_data['vritti']} would be displayed here.")
    
    elif task["type"] == "master":
        st.session_state.chosen_master = task["target"]
        st.session_state.vritti = path_data["vritti"]
        st.session_state.chosen_lineage = task["lineage"]
        
        if 'teachings' not in st.session_state:
            with st.spinner("Distilling the wisdom..."):
                prompt = f"What were {st.session_state.chosen_master}'s teachings on {st.session_state.vritti}?"
                response_text, _ = call_gemini(prompt)
                st.session_state.teachings = parse_teachings(response_text or "")
        
        if st.session_state.get('teachings'):
             tab1, tab2, tab3 = st.tabs(["**Core Concepts**", "**The Method**", "**Key Texts**"])
             with tab1: st.markdown(st.session_state.teachings.get("concepts", "Not available."))
             with tab2: st.markdown(st.session_state.teachings.get("method", "Not available."))
             with tab3: st.markdown(st.session_state.teachings.get("texts", "Not available."))
        else:
            st.warning("Could not load teachings at this moment.")

    elif task["type"] == "journal":
        st.text_area("Your Reflections:", height=200, key=f"journal_{day_index}", help="Entries are for this session only and will reset when you leave.")
    
    st.divider()
    if st.button("Back to Day Selection"):
        st.session_state.stage = "day_selection"
        if 'teachings' in st.session_state: del st.session_state['teachings']
        st.rerun()

elif st.session_state.stage == "show_traditions":
    st.subheader(f"Exploring: {st.session_state.vritti.capitalize()}")
    if 'traditions' not in st.session_state:
        with st.spinner("Consulting the world's wisdom traditions..."):
            prompt = f"For the emotion '{st.session_state.vritti}', list broad spiritual/religious Traditions. Use umbrella terms like 'Indic Traditions (Hinduism)', 'Buddhist Traditions', 'Taoist Traditions', etc."
            response_text, history = call_gemini(prompt)
            if response_text:
                st.session_state.traditions = parse_list(response_text)
                st.session_state.chat_history = history
    st.write("First, choose a broad tradition:")
    st.markdown('<div class="button-container">', unsafe_allow_html=True)
    for i, tradition in enumerate(st.session_state.get('traditions', [])):
        if st.button(tradition, key=f"tradition_{i}"):
            st.session_state.chosen_tradition = tradition
            st.session_state.stage = "show_lineages"
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    st.divider()
    if st.button("Back to Main Menu"):
        st.session_state.stage = "main_menu"
        st.rerun()

elif st.session_state.stage == "show_lineages":
    st.subheader(f"Tradition: {st.session_state.chosen_tradition}")
    if 'lineages' not in st.session_state:
        with st.spinner(f"Finding schools within {st.session_state.chosen_tradition}..."):
            prompt = f"Within the tradition of **{st.session_state.chosen_tradition}**, list specific Schools, Philosophies, or Lineages that have teachings on '{st.session_state.vritti}'."
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

elif st.session_state.stage == "show_teachings":
    st.subheader(f"Teachings of {st.session_state.chosen_master}")
    st.caption(f"From the **{st.session_state.chosen_lineage}** perspective.")
    if 'teachings' not in st.session_state:
        with st.spinner("Distilling the wisdom..."):
            prompt = f"What were {st.session_state.chosen_master}'s teachings on {st.session_state.vritti}?"
            response_text, _ = call_gemini(prompt, st.session_state.chat_history)
            if response_text:
                st.session_state.teachings = parse_teachings(response_text)
    if st.session_state.get('teachings'):
        tab1, tab2, tab3 = st.tabs(["**Core Concepts**", "**The Method**", "**Key Texts**"])
        with tab1: st.markdown(st.session_state.teachings.get("concepts", "No information provided."))
        with tab2: st.markdown(st.session_state.teachings.get("method", "No information provided."))
        with tab3: st.markdown(st.session_state.teachings.get("texts", "No information provided."))
        st.divider()
        # The dynamic contemplative practice
        st.subheader("Contemplative Practice")
        if st.button("Begin a Guided Practice"):
            with st.spinner("Generating a relevant practice..."):
                practice_prompt = f"Based on the teachings of {st.session_state.chosen_master} from the {st.session_state.chosen_lineage} tradition regarding '{st.session_state.vritti}', generate a short, guided contemplative practice. Present it as 2-4 simple, actionable steps in a numbered list."
                practice_response, _ = call_gemini(practice_prompt)
                st.session_state.practice_text = practice_response
        if 'practice_text' in st.session_state:
            st.info("Follow these prompts for inner reflection.")
            st.markdown(st.session_state.practice_text)
    else:
        st.warning("Could not parse the teachings for this master.")
    st.divider()
    if st.button("Back to Masters List"):
        st.session_state.stage = "show_masters"
        keys_to_clear = ['teachings', 'practice_text']
        for key in keys_to_clear:
            if key in st.session_state: del st.session_state[key]
        st.rerun()