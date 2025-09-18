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
            
            /* --- THEME OVERRIDE --- */
            :root {
                --primary-color: #4A909A; /* Muted Teal / Slate */
                --background-color: #F0F2F6; /* Soft Off-White / Light Gray */
                --secondary-background-color: #FFFFFF; /* Pure White for contrast */
                --text-color: #31333F; /* Dark Charcoal */
                --font: 'Lato', sans-serif;
            }

            /* Force text color on all primary text elements */
            .stApp, .stApp h1, .stApp h2, .stApp h3, .stApp p, .stApp li, .stApp label, .stApp .stMarkdown {
                color: var(--text-color) !important;
            }
            body { background-color: var(--background-color); }
            .stApp { background-color: var(--background-color); }

            /* --- WIDGET STYLING --- */
            h1, h2, h3 { font-family: var(--font); }
            .stTabs [data-baseweb="tab"][aria-selected="true"] {
                background-color: transparent;
                color: var(--primary-color);
                border-bottom: 2px solid var(--primary-color);
            }
            .button-container { display: flex; flex-wrap: wrap; gap: 10px; justify-content: center; margin-bottom: 20px; }
            .stButton>button { border-radius: 20px; border: 1px solid var(--primary-color); color: var(--primary-color); background-color: transparent; transition: all 0.3s ease-in-out; padding: 5px 15px; }
            .stButton>button:hover { color: var(--secondary-background-color); background-color: var(--primary-color); }
            
            /* Class for containers like master cards */
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
            ai_lineages = parse_list(response_text) if response_text else []
            base_lineages = ["Advaita Vedanta"]
            combined = base_lineages + [l for l in ai_lineages if l not in base_lineages]
            st.session_state.lineages = combined
            st.session_state.chat_history = history
    
    st.write("Choose a path to explore further:")
    st.markdown('<div class="button-container">', unsafe_allow_html=True)
    for i, lineage in enumerate(st.session_state.lineages):
        if st.button(lineage, key=f"lineage_{i}"):
            st.session_state.chosen_lineage = lineage
            st.session_state.stage = "show_masters"
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    st.divider()
    if st.button("Go Back"):
        restart_app()
        st.rerun()

elif st.session_state.stage == "show_masters":
    st.subheader(f"Path: {st.session_state.chosen_lineage}")
    
    if 'masters' not in st.session_state:
        with st.spinner(f"Finding masters..."):
            known_masters_str = ", ".join(MASTER_IMAGES.keys())
            prompt = f"From this list of masters: [{known_masters_str}], which ones are most relevant to the lineage '{st.session_state.chosen_lineage}' and the topic of '{st.session_state.vritti}'? Respond with only a numbered list of the relevant names, exactly as they appear in the list I provided."
            response_text, history = call_gemini(prompt, st.session_state.chat_history)
            st.session_state.raw_response = response_text
            if response_text:
                st.session_state.masters = parse_list(response_text)
                st.session_state.chat_history = history

    if not st.session_state.get('masters'):
        st.warning("No relevant masters found in our primary database for this topic.")
        with st.expander("Show Raw AI Response (for debugging)"):
            st.code(st.session_state.raw_response or "No response was received.")
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
                    keys_to_clear = ['teachings', 'books', 'places', 'events']
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
            prompt = f"What were {st.session_state.chosen_master}'s teachings on {st.session_state.vritti}?"
            response_text, history = call_gemini(prompt, st.session_state.chat_history)
            if response_text:
                st.session_state.teachings = parse_teachings(response_text)
                st.session_state.chat_history = history

    if st.session_state.get('teachings'):
        tab1, tab2, tab3 = st.tabs(["**Core Concepts**", "**The Method**", "**Key Texts**"])
        with tab1:
            st.markdown(st.session_state.teachings.get("concepts", "No information provided."))
        with tab2:
            st.markdown(st.session_state.teachings.get("method", "No information provided."))
        with tab3:
            st.markdown(st.session_state.teachings.get("texts", "No information provided."))
        
        st.divider()
        
        st.write("Discover More:")
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("📚 Books", use_container_width=True):
                with st.spinner("Finding relevant books..."):
                    prompt = f"Suggest 2-3 of the most important books for understanding the core teachings of {st.session_state.chosen_master}. These teachings will help in understanding topics like {st.session_state.vritti}. For each book, provide the title, a one-sentence description, and a markdown link to search for it on Amazon.in."
                    response, _ = call_gemini(prompt, st.session_state.chat_history)
                    st.session_state.books = response
        with col2:
            # --- FIX: Added the missing closing parenthesis ')' ---
            if st.button("📍 Places", use_container_width=True):
                with st.spinner("Locating significant places..."):
                    prompt = f"Is there a significant place to visit associated with {st.session_state.chosen_master}? If yes, provide a numbered list with the place name, a one-sentence description, and its location. If no significant place exists, respond with ONLY the word 'None'."
                    response, _ = call_gemini(prompt, st.session_state.chat_history)
                    st.session_state.places = response
        with col3:
            if st.button("🗓️ Events", use_container_width=True):
                with st.spinner("Checking for annual events..."):
                    prompt = f"Are there any special annual events or festivals associated with {st.session_state.chosen_master}? If yes, provide a numbered list with the event name, a brief description, and the typical time of year it occurs. If no regular events are associated, respond with ONLY the word 'None'."
                    response, _ = call_gemini(prompt, st.session_state.chat_history)
                    st.session_state.events = response

        # Display sections based on button clicks
        if 'books' in st.session_state and st.session_state.books:
            st.subheader("📚 Further Reading")
            if "None" in st.session_state.books.strip():
                st.info("No specific book recommendations were found for this topic.")
            else:
                st.markdown(st.session_state.books)

        if 'places' in st.session_state and st.session_state.places:
            st.subheader("📍 Places to Visit")
            if "None" in st.session_state.places.strip():
                st.info(f"No specific places are associated with {st.session_state.chosen_master}.")
            else:
                st.markdown(st.session_state.places)
        
        if 'events' in st.session_state and st.session_state.events:
            st.subheader("🗓️ Annual Events")
            if "None" in st.session_state.events.strip():
                st.info(f"No specific annual events are associated with {st.session_state.chosen_master}.")
            else:
                st.markdown(st.session_state.events)
    
    st.markdown("---")
    if st.button("Back to Masters List"):
        st.session_state.stage = "show_masters"
        keys_to_clear = ['teachings', 'books', 'places', 'events']
        for key in keys_to_clear:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()

    if st.button("Start Over"):
        restart_app()
        st.rerun()