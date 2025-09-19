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
api_key = "PASTE_YOUR_GEMINI_API_KEY_HERE"
if not api_key or "GEMINI_API_KEY" in api_key:
    st.error("Please add your Gemini API key to the code!")
    st.stop()
genai.configure(api_key=api_key)

# --- SYSTEM INSTRUCTION (THE "GEM" PROMPT) ---
system_instruction = """
You are the 'Spiritual Navigator', a specialized AI guide. 
CRITICAL RULE: All lists you generate MUST be in a numbered list format (e.g., "1. Item one\n2. Item two"). Respond with ONLY the numbered list.
When providing the detailed teaching, structure it with clear markdown headings: "### Core Philosophical Concepts", "### The Prescribed Method or Practice", and "### Reference to Key Texts".
When asked to find an image URL, you must find a publicly available, direct link to an image file (ending in .jpg, .jpeg, or .png). A good source is Wikimedia Commons. If you cannot find a reliable, direct image link, you MUST respond with ONLY the single word 'None'.
"""

# --- IMAGE LOGIC REWRITE ---
# The MASTER_IMAGES dictionary is no longer needed.
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

# --- IMAGE LOGIC REWRITE: This function now calls the AI ---
def find_master_image_url(master_name):
    """
    Dynamically finds an image URL for a master by calling the Gemini API.
    Caches results to avoid repeated calls.
    """
    # Initialize cache in session state if it doesn't exist
    if 'image_cache' not in st.session_state:
        st.session_state.image_cache = {}

    # 1. Check the cache first
    if master_name in st.session_state.image_cache:
        return st.session_state.image_cache[master_name]

    # 2. If not in cache, call the AI
    with st.spinner(f"Finding image for {master_name}..."):
        prompt = f"Find a publicly available, direct image link for the spiritual master '{master_name}'. The URL must end in .jpg, .jpeg, or .png. A good source is Wikimedia Commons. If you cannot find a link, respond with ONLY the word 'None'."
        # We don't need chat history for this specific, one-off query
        url_response, _ = call_gemini(prompt)

        # 3. Process the response
        if url_response and url_response.strip().lower().startswith('http'):
            image_url = url_response.strip()
        else:
            image_url = PLACEHOLDER_IMAGE
        
        # 4. Store the result in the cache and return it
        st.session_state.image_cache[master_name] = image_url
        return image_url

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
        st.session_state.stage = "show_lineages"
        st.rerun()

elif st.session_state.stage == "show_lineages":
    st.subheader(f"Exploring: {st.session_state.vritti.capitalize()}")
    if 'lineages' not in st.session_state:
        with st.spinner("Consulting the ancient traditions..."):
            prompt = f"Give me a list of spiritual lineages that talk about {st.session_state.vritti}."
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
    if st.button("Start Over"):
        restart_app()
        st.rerun()

elif st.session_state.stage == "show_masters":
    st.subheader(f"Path: {st.session_state.chosen_lineage}")
    
    if 'masters' not in st.session_state:
        with st.spinner(f"Finding masters from the {st.session_state.chosen_lineage} lineage..."):
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
                # This now calls the new, dynamic function
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
    # This stage remains unchanged
    st.subheader(f"Teachings of {st.session_state.chosen_master}")
    # ... (Code for this stage is the same as previous versions)
    pass # Placeholder for brevity, but the logic is unchanged.