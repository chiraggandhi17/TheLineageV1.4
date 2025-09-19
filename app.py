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
    # Use a more generic regex to find markdown headings, as they will be translated
    parts = re.split(r'###\s*(.*)', text)
    if len(parts) > 1:
        # This parsing is simplified and assumes 3 sections.
        # It takes content between headings.
        # A more robust solution might be needed if AI formatting varies widely.
        try:
            sections["concepts"] = parts[2].strip()
            sections["method"] = parts[4].strip()
            sections["texts"] = parts[6].strip()
        except IndexError:
            # Fallback if the AI doesn't return exactly 3 sections
            sections["concepts"] = text 
    else:
        sections["concepts"] = text # Fallback for non-structured text
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

# --- SESSION STATE INITIALIZATION ---
if 'stage' not in st.session_state:
    st.session_state.stage = "start"
if 'language' not in st.session_state:
    st.session_state.language = "English" # Default language

def restart_app():
    # Preserve language choice on restart
    lang = st.session_state.language
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.session_state.stage = "start"
    st.session_state.language = lang

# --- LOCALIZATION DICTIONARY ---
# For UI elements not generated by the AI
L10N = {
    "English": {
        "title": "Spiritual Navigator",
        "caption": "An interactive guide to ancient wisdom on modern emotions.",
        "input_prompt": "Enter an emotion, tendency, or 'vritti' to begin:",
        "start_over": "Start Over",
        # ... add all other UI text here
    },
    "Gujarati": {
        "title": "આધ્યાત્મિક માર્ગદર્શક",
        "caption": "આધુનિક લાગણીઓ પર પ્રાચીન જ્ઞાન માટેની એક ઇન્ટરેક્ટિવ માર્ગદર્શિકા.",
        "input_prompt": "શરૂ કરવા માટે લાગણી, વૃત્તિ અથવા 'વૃત્તિ' દાખલ કરો:",
        "start_over": "ફરીથી શરૂ કરો",
        # ... add all other UI text here
    },
    # Add other languages here
}

# --- MAIN APP UI ---
st.title("🧘 Spiritual Navigator")
load_custom_css()
st.caption(L10N[st.session_state.language]["caption"])

if st.session_state.stage == "start":
    # --- NEW: Language Selection ---
    lang_options = list(L10N.keys())
    st.session_state.language = st.selectbox(
        "Choose your language / તમારી ભાષા પસંદ કરો:",
        options=lang_options,
        index=lang_options.index(st.session_state.language) # Set default
    )

    vritti_input = st.text_input(L10N[st.session_state.language]["input_prompt"], key="vritti_input")
    if vritti_input:
        restart_app()
        st.session_state.vritti = vritti_input
        st.session_state.stage = "show_lineages"
        st.rerun()

elif st.session_state.stage == "show_lineages":
    st.subheader(f"Exploring: {st.session_state.vritti.capitalize()}")
    if 'lineages' not in st.session_state:
        with st.spinner("Consulting the ancient traditions..."):
            prompt = f"Respond in {st.session_state.language}. Give me a list of spiritual lineages that talk about {st.session_state.vritti}."
            response_text, history = call_gemini(prompt)
            if response_text:
                st.session_state.lineages = parse_list(response_text)
                st.session_state.chat_history = history
    
    st.write("Choose a path to explore further:")
    st.markdown('<div class="button-container">', unsafe_allow_html=True)
    for i, lineage in enumerate(st.session_state.get('lineages', [])):
        if st.button(lineage, key=f"lineage_{i}"):
            st.session_state.chosen_lineage = lineage
            st.session_state.stage = "show_masters"
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    st.divider()
    if st.button(L10N[st.session_state.language]["start_over"]):
        restart_app()
        st.rerun()

elif st.session_state.stage == "show_masters":
    st.subheader(f"Path: {st.session_state.chosen_lineage}")
    if 'masters' not in st.session_state:
        with st.spinner(f"Finding masters..."):
            prompt = f"Respond in {st.session_state.language}. List masters from the {st.session_state.chosen_lineage} lineage who discussed {st.session_state.vritti}."
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
    if st.button("Go Back to Lineages"):
        st.session_state.stage = "show_lineages"
        if 'masters' in st.session_state: del st.session_state['masters']
        st.rerun()

elif st.session_state.stage == "show_teachings":
    st.subheader(f"Teachings of {st.session_state.chosen_master}")
    st.caption(f"On **{st.session_state.vritti.capitalize()}** from the **{st.session_state.chosen_lineage}** perspective.")
    if 'teachings' not in st.session_state:
        with st.spinner("Distilling the wisdom..."):
            prompt = f"Respond in {st.session_state.language}. What were {st.session_state.chosen_master}'s teachings on {st.session_state.vritti}? Structure the response with the markdown headings: '### Core Philosophical Concepts', '### The Prescribed Method or Practice', and '### Reference to Key Texts', translating those headings into {st.session_state.language}."
            response_text, history = call_gemini(prompt, st.session_state.chat_history)
            st.session_state.raw_response = response_text
            if response_text:
                st.session_state.teachings = parse_teachings(response_text)
                st.session_state.chat_history = history
            else:
                st.session_state.teachings = {}
    if st.session_state.get('teachings'):
        # Since headings are now translated, we use the values from the parsed dict
        headings = list(st.session_state.teachings.keys())
        tab_objects = st.tabs([f"**{h.replace('_', ' ').title()}**" for h in headings])
        for tab, content_key in zip(tab_objects, headings):
            with tab:
                st.markdown(st.session_state.teachings.get(content_key, "No information provided."))
    else:
        st.warning("The AI's response could not be parsed into the teaching tabs.")
        with st.expander("Show Raw AI Response"):
            st.code(st.session_state.get('raw_response', "No response was received."))
    
    st.markdown("---")
    if st.button("Back to Masters List"):
        st.session_state.stage = "show_masters"
        keys_to_clear = ['teachings', 'raw_response']
        for key in keys_to_clear:
            if key in st.session_state: del st.session_state[key]
        st.rerun()
    if st.button(L10N[st.session_state.language]["start_over"]):
        restart_app()
        st.rerun()