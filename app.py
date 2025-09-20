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
            .st-emotion-cache-1r6slb0, .st-emotion-cache-p5msec, .quote-container { 
                border-radius: 10px; padding: 1.5rem; background-color: var(--secondary-background-color); 
                box-shadow: 0 4px 8px rgba(0,0,0,0.08); margin-bottom: 1rem;
            }
            .quote-text { font-size: 1.2rem; font-style: italic; text-align: center; margin-bottom: 1rem; }
        </style>
    """, unsafe_allow_html=True)

# --- API CONFIGURATION ---
api_key = "AIzaSyCfy-Pu4t_I5PH1a03f7zqAV2cy7Ofjx-4"
if not api_key or "GEMINI_API_KEY" in api_key:
    st.error("Please add your Gemini API key to the code!")
    st.stop()
genai.configure(api_key=api_key)

# --- SYSTEM INSTRUCTION (THE "GEM" PROMPT) ---
system_instruction = """
You are the 'Spiritual Navigator', a specialized AI guide. 
CRITICAL RULE: All lists you generate MUST be in a numbered list format (e.g., "1. Item one\n2. Item two"). Respond with ONLY the numbered list.
When asked for quotes, you must respond in the format: "1. 'The quote or summary.' - Master Name (Lineage)". Only use quotes from recognized spiritual masters, saints, or gurus.
When providing detailed teachings, structure it with clear markdown headings: "### Core Philosophical Concepts", "### The Prescribed Method or Practice", and "### Reference to Key Texts".
When asked for books, places, or events, if no relevant information exists, you must respond with ONLY the single word 'None'.
When asked for book recommendations, respond with a markdown table with columns: Book, Description, and Link (to search on Amazon.in).
When asked to generate a contemplative practice, present it as a series of simple, actionable steps. After the steps, if a relevant and soothing bhajan, chant, or hymn is associated, add a section '### Suggested Listening' and a markdown link to a YouTube search for it.
"""

# --- NEW: Nature Gateway Database ---
NATURE_ELEMENTS = [
    {"name": "Thunder", "image": "https://images.unsplash.com/photo-1605727228956-2736e8342242?q=80&w=1000&auto=format&fit=crop"},
    {"name": "Waterfall", "image": "https://images.unsplash.com/photo-1547005380-61fec8f86a59?q=80&w=1000&auto=format&fit=crop"},
    {"name": "Rain", "image": "https://images.unsplash.com/photo-1519692933481-e14e24672b14?q=80&w=1000&auto=format&fit=crop"},
    {"name": "Ocean Waves", "image": "https://images.unsplash.com/photo-1589279756961-689334ac1a73?q=80&w=1000&auto=format&fit=crop"},
    {"name": "Desert", "image": "https://images.unsplash.com/photo-1473580044384-7ba9967e16a0?q=80&w=1000&auto=format&fit=crop"},
    {"name": "Forest", "image": "https://images.unsplash.com/photo-1448375240586-882707db888b?q=80&w=1000&auto=format&fit=crop"},
]
PLACEHOLDER_IMAGE = "https://static.thenounproject.com/png/1230421-200.png"

# --- HELPER FUNCTIONS ---
def call_gemini(prompt):
    try:
        model = genai.GenerativeModel(model_name='gemini-1.5-pro-latest', system_instruction=system_instruction)
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        st.error(f"An error occurred with the API call: {e}")
        return None

def parse_list(text):
    if not text: return []
    items = re.findall(r'^\s*[\*\-\d]+\.?\s*(.+)$', text, re.MULTILINE)
    cleaned_items = [item.strip().replace('**', '') for item in items if item.strip()]
    return cleaned_items

def parse_quotes(text):
    if not text: return []
    pattern = re.compile(r"^\s*\d+\.\s*['\"](.*?)['\"]\s*-\s*(.*?)\s*\((.*?)\)", re.MULTILINE)
    matches = pattern.findall(text)
    quotes_list = [{"quote": match[0].strip(), "master": match[1].strip(), "lineage": match[2].strip()} for match in matches]
    return quotes_list

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
    # This can be expanded with a proper image database if desired
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

if st.session_state.stage == "start":
    st.caption("Let nature be your guide. Choose an element to begin exploring your inner world.")
    
    num_columns = 3
    cols = st.columns(num_columns)
    for i, element in enumerate(NATURE_ELEMENTS):
        with cols[i % num_columns]:
            st.image(element["image"])
            if st.button(element["name"], key=f"nature_{i}", use_container_width=True):
                st.session_state.chosen_nature = element["name"]
                st.session_state.stage = "show_emotions"
                st.rerun()

elif st.session_state.stage == "show_emotions":
    st.subheader(f"Reflecting on: {st.session_state.chosen_nature}")
    if 'emotions' not in st.session_state:
        with st.spinner(f"Finding emotions related to {st.session_state.chosen_nature}..."):
            prompt = f"List 3-5 emotions commonly associated with '{st.session_state.chosen_nature}'. Respond with only a numbered list."
            response_text = call_gemini(prompt)
            if response_text:
                st.session_state.emotions = parse_list(response_text)
    
    st.write("Which of these feelings resonates with you right now?")
    st.markdown('<div class="button-container">', unsafe_allow_html=True)
    for i, emotion in enumerate(st.session_state.get('emotions', [])):
        if st.button(emotion, key=f"emotion_{i}"):
            st.session_state.chosen_emotion = emotion
            st.session_state.stage = "show_quotes"
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    st.divider()
    if st.button("Back to Nature"):
        restart_app()
        st.rerun()

elif st.session_state.stage == "show_quotes":
    st.subheader(f"Wisdom on: {st.session_state.chosen_emotion}")
    if 'quotes' not in st.session_state:
        with st.spinner("Gathering insights from across traditions..."):
            prompt = f"For the emotion '{st.session_state.chosen_emotion}', generate a list of 5 impactful, one-line quotes or teaching summaries from different spiritual masters and lineages. Only use quotes from recognized masters, saints, or gurus. The format must be: \"1. 'The quote.' - Master Name (Lineage)\""
            response_text = call_gemini(prompt)
            if response_text:
                st.session_state.quotes = parse_quotes(response_text)
    
    st.write("Choose the insight that resonates with you most:")
    for i, item in enumerate(st.session_state.get('quotes', [])):
        with st.container():
            st.markdown(f"<div class='quote-container'><p class='quote-text'>“{item['quote']}”</p>", unsafe_allow_html=True)
            if st.button(f"Explore the teachings of {item['master']}", key=f"quote_{i}", use_container_width=True):
                st.session_state.chosen_quote = item
                st.session_state.stage = "show_masters"
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)
    
    st.divider()
    if st.button("Back to Emotions"):
        st.session_state.stage = "show_emotions"
        if 'quotes' in st.session_state: del st.session_state['quotes']
        st.rerun()

elif st.session_state.stage == "show_masters":
    lineage = st.session_state.chosen_quote['lineage']
    st.subheader(f"Exploring the {lineage} Lineage")
    if 'masters' not in st.session_state:
        with st.spinner(f"Finding masters from the {lineage} lineage..."):
            prompt = f"List 5 key masters from the '{lineage}' lineage who have teachings relevant to '{st.session_state.chosen_emotion}'. Include the master from the original quote: {st.session_state.chosen_quote['master']}."
            response_text = call_gemini(prompt)
            if response_text:
                st.session_state.masters = parse_list(response_text)

    st.write("Choose a master to learn from:")
    for i, master in enumerate(st.session_state.get('masters', [])):
        col1, col2 = st.columns([1, 4])
        with col1:
            st.image(PLACEHOLDER_IMAGE, width=70) # Using placeholder as image finding is complex
        with col2:
            st.write(f"**{master}**")
            if st.button(f"Dive into teachings", key=f"master_{i}", use_container_width=True):
                st.session_state.chosen_master = master
                st.session_state.stage = "show_teachings"
                st.rerun()
    st.divider()
    if st.button("Back to Quotes"):
        st.session_state.stage = "show_quotes"
        if 'masters' in st.session_state: del st.session_state['masters']
        st.rerun()


elif st.session_state.stage == "show_teachings":
    st.subheader(f"Teachings of {st.session_state.chosen_master}")
    st.caption(f"From the **{st.session_state.chosen_quote['lineage']}** perspective on **{st.session_state.chosen_emotion}**.")
    if 'teachings' not in st.session_state:
        with st.spinner("Distilling the wisdom..."):
            prompt = f"What were {st.session_state.chosen_master}'s core teachings regarding {st.session_state.chosen_emotion}? Structure the response with markdown headings: '### Core Philosophical Concepts', '### The Prescribed Method or Practice', and '### Reference to Key Texts'."
            response_text = call_gemini(prompt)
            if response_text:
                st.session_state.teachings = parse_teachings(response_text)
    
    if st.session_state.get('teachings'):
        tab1, tab2, tab3 = st.tabs(["**Core Concepts**", "**The Method**", "**Key Texts**"])
        with tab1: st.markdown(st.session_state.teachings.get("concepts", "No information provided."))
        with tab2: st.markdown(st.session_state.teachings.get("method", "No information provided."))
        with tab3: st.markdown(st.session_state.teachings.get("texts", "No information provided."))
        
        st.divider()
        st.subheader("Discover More & Contemplate")
        disc_tabs = st.tabs(["📚 Further Reading", "📍 Places to Visit", "🙏 Practice & Journal"])
        
        with disc_tabs[0]: # Further Reading
             # Auto-loading content
            if 'books' not in st.session_state:
                with st.spinner("Finding relevant books..."):
                    prompt = f"Suggest 2-3 books for understanding {st.session_state.chosen_master}'s core teachings on topics like {st.session_state.chosen_emotion}. Respond with a markdown table with columns: Book, Description, and Link (to search on Amazon.in)."
                    st.session_state.books = call_gemini(prompt) or "None"
            if "None" in st.session_state.books:
                st.info("No specific book recommendations were found.")
            else:
                st.markdown(st.session_state.books)
        
        with disc_tabs[1]: # Places to Visit
            if 'places' not in st.session_state:
                with st.spinner("Locating significant places..."):
                    prompt = f"Is there a significant place to visit associated with {st.session_state.chosen_master}? Respond with a markdown table with columns: Place, Description, and Location. If no significant place exists, respond with ONLY the word 'None'."
                    st.session_state.places = call_gemini(prompt) or "None"
            if "None" in st.session_state.places:
                st.info(f"No specific places are associated with {st.session_state.chosen_master}.")
            else:
                st.markdown(st.session_state.places)

        with disc_tabs[2]: # Practice & Journal
            st.info("A practice to deepen your understanding.")
            if 'practice_text' not in st.session_state:
                with st.spinner("Generating a relevant practice..."):
                    prompt = f"Based on the teachings of {st.session_state.chosen_master} regarding '{st.session_state.chosen_emotion}', generate a short, guided contemplative practice. Present it as 2-4 simple, actionable steps in a numbered list. After the steps, if a relevant and soothing bhajan, chant, or hymn is associated, add a section '### Suggested Listening' and a markdown link to a YouTube search for it."
                    st.session_state.practice_text = call_gemini(prompt) or "No practice could be generated."
            st.markdown(st.session_state.practice_text)
            st.text_area("Your Contemplation Journal:", height=150, key="journal_entry", help="Entries are for this session only.")
    
    st.divider()
    if st.button("Back to Masters List"):
        st.session_state.stage = "show_masters"
        keys_to_clear = ['teachings', 'books', 'places', 'practice_text']
        for key in keys_to_clear:
            if key in st.session_state: del st.session_state[key]
        st.rerun()