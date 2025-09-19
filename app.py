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
"""

# --- MASTER IMAGE DATABASE & HELPER ---
MASTER_IMAGES = {
    "Ramana Maharshi": "https://upload.wikimedia.org/wikipedia/commons/4/4b/Ramana_Maharshi_1935.jpg",
    "Nisargadatta Maharaj": "https://upload.wikimedia.org/wikipedia/en/8/8f/Nisargadatta.jpg",
    "Adi Shankaracharya": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c5/Adi_Shankaracharya.jpg/800px-Adi_Shankaracharya.jpg",
    "Rumi": "https://upload.wikimedia.org/wikipedia/commons/thumb/6/67/Mevlana_Rumi.jpg/800px-Mevlana_Rumi.jpg",
    "Sai Baba of Shirdi": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c3/Sai_Baba_of_Shirdi_-_enhanced.jpg/800px-Sai_Baba_of_Shirdi_-_enhanced.jpg",
    "Kabir": "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e1/Kabir.jpg/800px-Kabir.jpg",
    "Guru Nanak": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a2/Guru_Nanak_Dev_Ji.jpg/800px-Guru_Nanak_Dev_Ji.jpg",
    "J. Krishnamurti": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/89/Jiddu_Krishnamurti_in_1920s.jpg/800px-Jiddu_Krishnamurti_in_1920s.jpg"
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
        keywords = known_name.lower().replace("sri", "").replace("maharaj", "").replace("of shirdi","").split()
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
        st.session_state.stage = "show_traditions"
        st.rerun()

elif st.session_state.stage == "show_traditions":
    st.subheader(f"Exploring: {st.session_state.vritti.capitalize()}")
    if 'traditions' not in st.session_state:
        with st.spinner("Consulting the world's wisdom traditions..."):
            # --- MODIFIED: Added Featured Masters to the prompt for better context ---
            featured_masters_str = ", ".join(["Sai Baba of Shirdi", "J. Krishnamurti", "Kabir", "Guru Nanak"])
            prompt = f"For the emotion '{st.session_state.vritti}', list broad spiritual/religious Traditions. Include relevant traditions for masters like {featured_masters_str}. Use umbrella terms like 'Indic Traditions (Hinduism)', 'Sikhism', 'Sufism', 'Bhakti Movement', etc."
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
    if st.button("Start Over"):
        restart_app()
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
            prompt = f"List masters from the {st.session_state.chosen_lineage} school of thought who discussed {st.session_state.vritti}."
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

        # --- MODIFIED: "Discover More" and "Contemplate" now use auto-loading tabs ---
        st.subheader("Discover More & Contemplate")
        disc_tabs = st.tabs(["📚 Further Reading", "📍 Places to Visit", "🗓️ Annual Events", "🙏 Practice & Journal"])

        with disc_tabs[0]: # Further Reading
            if 'books' not in st.session_state:
                with st.spinner("Finding relevant books..."):
                    prompt = f"Suggest 2-3 books for understanding {st.session_state.chosen_master}'s core teachings on topics like {st.session_state.vritti}. For each book, provide the title, a one-sentence description, and a markdown link to search for it on Amazon.in."
                    response, _ = call_gemini(prompt, st.session_state.chat_history)
                    st.session_state.books = response or "None"
            if "None" in st.session_state.books.strip():
                st.info("No specific book recommendations were found.")
            else:
                st.markdown(st.session_state.books)
        
        with disc_tabs[1]: # Places to Visit
            if 'places' not in st.session_state:
                with st.spinner("Locating significant places..."):
                    prompt = f"Is there a significant place to visit associated with {st.session_state.chosen_master}? If yes, provide a numbered list with the place name, a one-sentence description, and its location. If no significant place exists, respond with ONLY the word 'None'."
                    response, _ = call_gemini(prompt, st.session_state.chat_history)
                    st.session_state.places = response or "None"
            if "None" in st.session_state.places.strip():
                st.info(f"No specific places are associated with {st.session_state.chosen_master}.")
            else:
                st.markdown(st.session_state.places)

        with disc_tabs[2]: # Annual Events
            if 'events' not in st.session_state:
                with st.spinner("Checking for annual events..."):
                    prompt = f"Are there any special annual events or festivals associated with {st.session_state.chosen_master}? If yes, provide a numbered list with the event name, a brief description, and the typical time of year it occurs. If no regular events are associated, respond with ONLY the word 'None'."
                    response, _ = call_gemini(prompt, st.session_state.chat_history)
                    st.session_state.events = response or "None"
            if "None" in st.session_state.events.strip():
                st.info(f"No specific annual events are associated with {st.session_state.chosen_master}.")
            else:
                st.markdown(st.session_state.events)
        
        with disc_tabs[3]: # Practice & Journal
            st.info("A practice to deepen your understanding.")
            if 'practice_text' not in st.session_state:
                with st.spinner("Generating a relevant practice..."):
                    prompt = f"Based on the teachings of {st.session_state.chosen_master} regarding '{st.session_state.vritti}', generate a short, guided contemplative practice. Present it as 2-4 simple, actionable steps in a numbered list."
                    response, _ = call_gemini(prompt)
                    st.session_state.practice_text = response or "No practice could be generated."
            st.markdown(st.session_state.practice_text)
            st.text_area("Your Contemplation Journal:", height=150, key="journal_entry", help="Entries are for this session only.")

    else:
        st.warning("Could not parse the teachings for this master.")
    
    st.markdown("---")
    if st.button("Back to previous page"):
        if st.session_state.get('chosen_lineage') == "their unique teachings":
            st.session_state.stage = "show_traditions"
        else:
            st.session_state.stage = "show_masters"
        keys_to_clear = ['teachings', 'books', 'places', 'events', 'practice_text', 'chosen_master']
        for key in keys_to_clear:
            if key in st.session_state: del st.session_state[key]
        st.rerun()