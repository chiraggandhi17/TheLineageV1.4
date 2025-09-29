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
When asked for anonymous teachings, provide a numbered list of 5 brief, one-or-two sentence summaries. Do NOT name the master or tradition.
When asked to identify lineages for a teaching, first provide a one-sentence summary of the types of lineages. Then, provide a numbered list of ONLY the lineage names. Example:
These teachings are found in mystical traditions focused on devotional love.
1. Sufism
2. Bhakti Yoga
When asked for details of a SINGLE lineage, respond with a brief description of that lineage, then a sub-section "Masters from this lineage:", followed by a numbered list of masters. For each master, provide their name, time period, and a key associated location.
When providing detailed teachings, structure it with clear markdown headings: "### Core Philosophical Concepts", "### The Prescribed Method or Practice", and "### Reference to Key Texts".
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

# --- MODIFIED: Parsing functions for the new 3-step flow ---
def parse_lineage_summary_and_list(text):
    if not text: return "Could not determine lineages.", []
    summary = text.split('\n')[0] # The first line is the summary
    lineages = re.findall(r'^\s*\d+\.\s*(.+)$', text, re.MULTILINE)
    return summary, lineages

def parse_lineage_details(text):
    if not text: return "No description found.", []
    description = text.split("Masters from this lineage:")[0].strip()
    masters_text = text.split("Masters from this lineage:")[1] if "Masters from this lineage:" in text else ""
    masters_list = []
    
    # Updated regex for flexibility
    pattern = re.compile(r"^\s*\d+\.\s*(.+?)\s*\|\s*(.+?)\s*\|\s*(.+)$", re.MULTILINE)
    matches = pattern.findall(masters_text)
    
    for match in matches:
        masters_list.append({
            "name": match[0].strip(),
            "period": match[1].strip(),
            "location": match[2].strip()
        })
    return description, masters_list

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
            prompt = f"Based on a user exploring '{st.session_state.vritti}' and whose guiding principles are '{st.session_state.principles_summary}', provide 5 brief, anonymous teaching summaries from different spiritual traditions."
            response = call_gemini(prompt)
            if response:
                st.session_state.teachings = parse_anonymous_teachings(response)
    if not st.session_state.get('teachings'):
        st.warning("Could not find specific teachings. Please try another emotion.")
    else:
        st.write("Choose the teaching that resonates with you most:")
        for i, teaching in enumerate(st.session_state.teachings):
            if st.button(teaching, key=f"teaching_{i}", use_container_width=True):
                st.session_state.chosen_teaching = teaching
                st.session_state.stage = "show_lineage_list" # New stage
                st.rerun()
    st.divider()
    if st.button("Start Over"):
        restart_app()
        st.rerun()

# --- NEW STAGE: Show the list of relevant lineages ---
elif st.session_state.stage == "show_lineage_list":
    st.info(f"The teaching you chose resonates with the following traditions:")
    if 'lineage_summary' not in st.session_state:
        with st.spinner("Identifying the traditions..."):
            prompt = f"The user chose the teaching: '{st.session_state.chosen_teaching}'. First, provide a one-sentence summary of what these lineages have in common. Then, provide a numbered list of ONLY the names of the associated spiritual lineages."
            response = call_gemini(prompt)
            if response:
                summary, lineages = parse_lineage_summary_and_list(response)
                st.session_state.lineage_summary = summary
                st.session_state.lineage_list = lineages
    
    st.write(st.session_state.get('lineage_summary', ''))
    st.write("Choose a lineage to explore further:")
    for i, lineage in enumerate(st.session_state.get('lineage_list', [])):
        if st.button(lineage, key=f"lineage_list_{i}", use_container_width=True):
            st.session_state.chosen_lineage = lineage
            st.session_state.stage = "show_lineage_details" # New stage
            st.rerun()
    
    st.divider()
    if st.button("Back to Teachings"):
        st.session_state.stage = "show_anonymous_teachings"
        keys_to_clear = ['lineage_summary', 'lineage_list']
        for key in keys_to_clear:
            if key in st.session_state: del st.session_state[key]
        st.rerun()

# --- NEW STAGE: Show details and masters for the chosen lineage ---
elif st.session_state.stage == "show_lineage_details":
    st.header(st.session_state.chosen_lineage)
    if 'lineage_description' not in st.session_state:
        with st.spinner(f"Loading details for {st.session_state.chosen_lineage}..."):
            prompt = f"For the lineage '{st.session_state.chosen_lineage}', provide a brief description, then list its key masters who spoke on '{st.session_state.vritti}'. Respond in the required format."
            response = call_gemini(prompt)
            if response:
                description, masters = parse_lineage_details(response)
                st.session_state.lineage_description = description
                st.session_state.masters_list = masters
    
    st.markdown(st.session_state.get('lineage_description', ''))
    st.subheader("Masters from this lineage:")
    
    if not st.session_state.get('masters_list'):
        st.warning("Could not parse the list of masters.")
    else:
        for i, master in enumerate(st.session_state.get('masters_list', [])):
            st.markdown(f"**{master['name']}**")
            st.caption(f"{master['period']} | {master['location']}")
            if st.button("Explore Teachings", key=f"master_{i}"):
                st.session_state.chosen_master = master['name']
                st.session_state.stage = "show_final_teachings"
                st.rerun()
            st.markdown("---")
            
    if st.button("Back to Lineage List"):
        st.session_state.stage = "show_lineage_list"
        keys_to_clear = ['lineage_description', 'masters_list', 'chosen_lineage']
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
        st.session_state.stage = "show_lineage_details"
        if 'final_teachings' in st.session_state: del st.session_state['final_teachings']
        st.rerun()