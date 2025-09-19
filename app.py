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
When asked for books, places, or events, respond with a markdown table with appropriate columns (e.g., Book|Description|Link).
When asked to generate a contemplative practice, present it as a series of simple, actionable steps. After the steps, if a relevant and soothing bhajan, chant, or hymn is associated with the teaching, add a section called "### Suggested Listening" and provide a markdown link to a YouTube search for it.
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
    parts = re.split(r'###\s*(Core Philosophical Concepts|The Prescribed Method or Practice|Reference to Key Texts)', text)
    if len(parts) > 1:
        for i in range(1, len(parts), 2):
            heading, content = parts[i].strip(), parts[i+1].strip()
            if "Concepts" in heading: sections["concepts"] = content
            elif "Method" in heading: sections["method"] = content
            elif "Texts" in heading: sections["texts"] = content
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
                    keys_to_clear = ['teachings', 'books', 'places', 'events', 'practice_text']
                    for key in keys_to_clear:
                        if key in st.session_state: del st.session_state[key]
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
            prompt = f"What were {st.session_state.chosen_master}'s teachings on {st.session_state.vritti}? Structure the response with markdown headings: '### Core Philosophical Concepts', '### The Prescribed Method or Practice', and '### Reference to Key Texts'."
            response_text, history = call_gemini(prompt, st.session_state.chat_history)
            st.session_state.raw_response = response_text
            if response_text:
                st.session_state.teachings = parse_teachings(response_text)
                st.session_state.chat_history = history
            else:
                st.session_state.teachings = {}
    if st.session_state.get('teachings'):
        tab1, tab2, tab3 = st.tabs(["**Core Concepts**", "**The Method**", "**Key Texts**"])
        with tab1: st.markdown(st.session_state.teachings.get("concepts", "No information provided."))
        with tab2: st.markdown(st.session_state.teachings.get("method", "No information provided."))
        with tab3: st.markdown(st.session_state.teachings.get("texts", "No information provided."))
        
        st.divider()

        # --- MODIFIED: "Discover More" and "Contemplate" now use auto-loading tabs ---
        st.subheader("Discover More & Contemplate")
        disc_tabs = st.tabs(["📚 Further Reading", "📍 Places to Visit", "🗓️ Annual Events", "🙏 Practice & Journal"])

        with disc_tabs[0]:
            if 'books' not in st.session_state:
                with st.spinner("Finding relevant books..."):
                    prompt = f"Suggest 2-3 books for understanding {st.session_state.chosen_master}'s core teachings on topics like {st.session_state.vritti}. Respond with a markdown table with columns: Book, Description, and Link (to search on Amazon.in)."
                    response, _ = call_gemini(prompt, st.session_state.chat_history)
                    st.session_state.books = response or "None"
            if "None" in st.session_state.books.strip():
                st.info("No specific book recommendations were found.")
            else:
                st.markdown(st.session_state.books)
        
        with disc_tabs[1]:
            if 'places' not in st.session_state:
                with st.spinner("Locating significant places..."):
                    prompt = f"Is there a significant place to visit associated with {st.session_state.chosen_master}? Respond with a markdown table with columns: Place, Description, and Location. If no significant place exists, respond with ONLY the word 'None'."
                    response, _ = call_gemini(prompt, st.session_state.chat_history)
                    st.session_state.places = response or "None"
            if "None" in st.session_state.places.strip():
                st.info(f"No specific places are associated with {st.session_state.chosen_master}.")
            else:
                st.markdown(st.session_state.places)

        with disc_tabs[2]:
            if 'events' not in st.session_state:
                with st.spinner("Checking for annual events..."):
                    prompt = f"Are there any special annual events or festivals associated with {st.session_state.chosen_master}? Respond with a markdown table with columns: Event, Description, and 'Time of Year'. If no regular events are associated, respond with ONLY the word 'None'."
                    response, _ = call_gemini(prompt, st.session_state.chat_history)
                    st.session_state.events = response or "None"
            if "None" in st.session_state.events.strip():
                st.info(f"No specific annual events are associated with {st.session_state.chosen_master}.")
            else:
                st.markdown(st.session_state.events)
        
        with disc_tabs[3]:
            st.info("A practice to deepen your understanding.")
            if 'practice_text' not in st.session_state:
                with st.spinner("Generating a relevant practice..."):
                    prompt = f"Based on the teachings of {st.session_state.chosen_master} regarding '{st.session_state.vritti}', generate a short, guided contemplative practice. Present it as 2-4 simple, actionable steps in a numbered list. After the steps, if a relevant and soothing bhajan, chant, or hymn is associated, add a section '### Suggested Listening' and a markdown link to a YouTube search for it."
                    response, _ = call_gemini(prompt)
                    st.session_state.practice_text = response or "No practice could be generated."
            st.markdown(st.session_state.practice_text)
            st.text_area("Your Contemplation Journal:", height=150, key="journal_entry", help="Entries are for this session only.")

    else:
        st.warning("The AI's response could not be parsed into the teaching tabs.")
        with st.expander("Show Raw AI Response"):
            st.code(st.session_state.get('raw_response', "No response was received."))
    
    st.markdown("---")
    if st.button("Back to Masters List"):
        st.session_state.stage = "show_masters"
        keys_to_clear = ['teachings', 'books', 'places', 'events', 'practice_text', 'raw_response']
        for key in keys_to_clear:
            if key in st.session_state: del st.session_state[key]
        st.rerun()
    if st.button("Start Over"):
        restart_app()
        st.rerun()