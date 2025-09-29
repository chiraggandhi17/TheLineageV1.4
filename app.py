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
            .st-emotion-cache-1r6slb0, .st-emotion-cache-p5msec, .quote-container, .lineage-card { 
                border-radius: 10px; padding: 1.5rem; background-color: var(--secondary-background-color); 
                box-shadow: 0 4px 8px rgba(0,0,0,0.08); margin-bottom: 1.5rem;
            }
            .quote-text {
                font-size: 1.2rem;
                font-style: italic;
                text-align: center;
                margin-bottom: 1rem;
            }
        </style>
    """, unsafe_allow_html=True)

# --- API CONFIGURATION ---
try:
    api_key = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=api_key)
except (KeyError, FileNotFoundError):
    st.error("API key not found. Please add your GOOGLE_API_KEY to your Streamlit secrets.")
    st.stop()

# --- SYSTEM INSTRUCTION (THE "GEM" PROMPT) ---
system_instruction = """
You are the 'Spiritual Navigator', a specialized AI guide. 
When asked for anonymous teachings, provide a numbered list of 5 brief, one-or-two sentence summaries of spiritual teachings. Do NOT name the master, school, or tradition.
When asked to identify a teaching, you must identify the SINGLE MOST PROMINENT spiritual lineage associated with it. Then, provide a numbered list of masters from that lineage. For each master, provide their name, their time period, and a key associated location. The format MUST be:
Lineage: Name of the Lineage
Masters:
1. Master Name | Time Period | Location
2. Master Name | Time Period | Location
When providing detailed teachings, structure it with clear markdown headings: "### Core Philosophical Concepts", "### The Prescribed Method or Practice", and "### Reference to Key Texts".
When asked for books, places, events, or music, if no relevant information exists, you must respond with ONLY the single word 'None'.
"""

# --- HELPER FUNCTIONS ---
def call_gemini(prompt):
    try:
        model = genai.GenerativeModel(model_name='gemini-2.5-flash')
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        st.error(f"An error occurred with the API call: {e}")
        return None

def parse_anonymous_teachings(text):
    if not text: return []
    return re.findall(r'^\s*\d+\.\s*(.+)$', text, re.MULTILINE)

# --- FIX: More robust parsing for the lineage and master list ---
def parse_lineage_and_masters(text):
    if not text: return "Unknown Tradition", []
    
    lineage_match = re.search(r"Lineage:\s*(.*)", text, re.IGNORECASE)
    lineage = lineage_match.group(1).strip() if lineage_match else "Unknown Tradition"
    
    masters_text = text.split("Masters:")[1] if "Masters:" in text else text
    masters_list = []
    
    # Regex to find lines starting with a number, then capture 3 parts separated by '|'
    pattern = re.compile(r"^\s*\d+\.\s*(.+?)\s*\|\s*(.+?)\s*\|\s*(.+)$", re.MULTILINE)
    matches = pattern.findall(masters_text)
    
    for match in matches:
        masters_list.append({
            "name": match[0].strip(),
            "period": match[1].strip(),
            "location": match[2].strip()
        })
    return lineage, masters_list

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

# --- SESSION STATE INITIALIZATION ---
if 'stage' not in st.session_state:
    st.session_state.stage = "start"

def restart_app():
    for key in list(st.session_state.keys()): del st.session_state[key]
    st.session_state.stage = "start"

# --- MAIN APP UI ---
st.title("🧘 Spiritual Navigator")
load_custom_css()

if st.session_state.stage == "start":
    st.caption("An interactive guide to ancient wisdom on modern emotions.")
    st.session_state.vritti = st.text_input("To begin, what emotion or tendency are you exploring?", key="vritti_input")
    st.write("---")
    st.subheader("Optional: Share your Guiding Principles")
    QUESTIONS = [
        {"question": "When facing a problem, I tend to:", "options": ["Analyze it logically.", "Feel my way through it intuitively.", "Seek guidance from wisdom texts.", "Take action and learn by doing."], "key": "q1"},
        {"question": "I feel most connected to the divine through:", "options": ["Silent contemplation.", "Devotional practices.", "Intellectual understanding.", "Service to others."], "key": "q2"},
        {"question": "I prefer a path that is:", "options": ["Well-structured with clear steps.", "Fluid and adaptable.", "Focused on a single, ultimate truth.", "Embraces multiple perspectives."], "key": "q3"}
    ]
    answers = {}
    for q in QUESTIONS:
        answers[q['key']] = st.radio(q['question'], q['options'], key=q['key'], index=None)
    if st.button("Begin Exploration"):
        if st.session_state.vritti:
            summary = [answers[q['key']] for q in QUESTIONS if answers[q['key']]]
            st.session_state.principles_summary = " ".join(summary)
            st.session_state.stage = "show_anonymous_teachings"
            st.rerun()
        else:
            st.warning("Please enter an emotion or tendency to begin.")

elif st.session_state.stage == "show_anonymous_teachings":
    st.subheader(f"Insights on: {st.session_state.vritti.capitalize()}")
    if 'teachings' not in st.session_state:
        with st.spinner("Finding teachings that resonate with you..."):
            prompt = f"Based on a user who is exploring '{st.session_state.vritti}' and whose guiding principles are '{st.session_state.principles_summary}', provide 5 brief, anonymous teaching summaries from different spiritual traditions. Do NOT name the tradition or the master."
            response = call_gemini(prompt)
            st.session_state.raw_response = response
            if response:
                st.session_state.teachings = parse_anonymous_teachings(response)
    if not st.session_state.get('teachings'):
        st.warning("Could not find specific teachings. Please try another emotion.")
        with st.expander("Show Raw AI Response (for debugging)"):
            st.code(st.session_state.get('raw_response', "No response from AI."))
    else:
        st.write("Choose the teaching that resonates with you most:")
        for i, teaching in enumerate(st.session_state.teachings):
            if st.button(teaching, key=f"teaching_{i}", use_container_width=True):
                st.session_state.chosen_teaching = teaching
                st.session_state.stage = "show_lineage_reveal"
                st.rerun()
    st.divider()
    if st.button("Start Over"):
        restart_app()
        st.rerun()

elif st.session_state.stage == "show_lineage_reveal":
    st.info(f"The teaching you chose resonates with:")
    if 'revealed_lineage' not in st.session_state:
        with st.spinner("Unveiling the tradition..."):
            prompt = f"The user chose the teaching: '{st.session_state.chosen_teaching}'. Which spiritual lineage and which masters are associated with this teaching? For each master, provide their name, their time period, and a key associated location. Respond in the required format."
            response = call_gemini(prompt)
            st.session_state.raw_response_reveal = response
            if response:
                lineage, masters = parse_lineage_and_masters(response)
                st.session_state.revealed_lineage = lineage
                st.session_state.masters_list = masters

    st.header(st.session_state.get('revealed_lineage', 'Unknown Lineage'))
    
    if not st.session_state.get('masters_list'):
        st.warning("Could not parse the list of masters from the AI's response.")
        with st.expander("Show Raw AI Response (for debugging)"):
            st.code(st.session_state.get('raw_response_reveal', "No response from AI."))
    else:
        st.write("Choose a master to learn more:")
        for i, master in enumerate(st.session_state.get('masters_list', [])):
            with st.container():
                st.markdown(f"**{master['name']}**")
                st.caption(f"{master.get('period', 'Unknown')} | {master.get('location', 'Unknown')}")
                if st.button("Explore Teachings", key=f"master_{i}"):
                    st.session_state.chosen_master = master['name']
                    st.session_state.chosen_lineage = st.session_state.revealed_lineage
                    st.session_state.stage = "show_final_teachings"
                    st.rerun()
                st.markdown("---")

    if st.button("Back to Teachings"):
        st.session_state.stage = "show_anonymous_teachings"
        keys_to_clear = ['revealed_lineage', 'masters_list', 'raw_response_reveal']
        for key in keys_to_clear:
            if key in st.session_state: del st.session_state[key]
        st.rerun()

elif st.session_state.stage == "show_final_teachings":
    st.subheader(f"Teachings of {st.session_state.chosen_master}")
    st.caption(f"From the **{st.session_state.chosen_lineage}** perspective on **{st.session_state.vritti.capitalize()}**.")
    if 'final_teachings' not in st.session_state:
        with st.spinner("Distilling the wisdom..."):
            prompt = f"What were {st.session_state.chosen_master}'s core teachings regarding {st.session_state.vritti}? Structure the response with the markdown headings: '### Core Philosophical Concepts', '### The Prescribed Method or Practice', and '### Reference to Key Texts'."
            response = call_gemini(prompt)
            if response:
                st.session_state.final_teachings = parse_teachings(response)
    
    if st.session_state.get('final_teachings'):
        tab1, tab2, tab3 = st.tabs(["**Core Concepts**", "**The Method**", "**Key Texts**"])
        with tab1: st.markdown(st.session_state.final_teachings.get("concepts", "No information provided."))
        with tab2: st.markdown(st.session_state.final_teachings.get("method", "No information provided."))
        with tab3: st.markdown(st.session_state.final_teachings.get("texts", "No information provided."))
    
    st.divider()
    if st.button("Back to Masters List"):
        st.session_state.stage = "show_lineage_reveal"
        if 'final_teachings' in st.session_state: del st.session_state['final_teachings']
        st.rerun()