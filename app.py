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

# --- THEME & STYLING (FINAL FIX) ---
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
            .stButton>button { 
                border-radius: 20px; 
                border: 1px solid var(--primary-color); 
                color: var(--primary-color); 
                /* FIX: Set a solid background color for readability */
                background-color: var(--secondary-background-color); 
                transition: all 0.3s ease-in-out; 
                padding: 5px 15px; 
            }
            .stButton>button:hover { 
                color: var(--secondary-background-color); 
                background-color: var(--primary-color); 
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

# --- GUIDING PRINCIPLES QUIZ QUESTIONS ---
QUESTIONS = [
    {
        "question": "When facing a problem, I tend to:",
        "options": ["Analyze it logically.", "Feel my way through it intuitively.", "Seek guidance from wisdom texts.", "Take action and learn by doing."],
        "key": "q1"
    },
    {
        "question": "I feel most connected to the divine through:",
        "options": ["Silent contemplation.", "Devotional practices.", "Intellectual understanding.", "Service to others."],
        "key": "q2"
    },
    {
        "question": "I prefer a path that is:",
        "options": ["Well-structured with clear steps.", "Fluid and adaptable.", "Focused on a single, ultimate truth.", "Embraces multiple perspectives."],
        "key": "q3"
    }
]

# --- SYSTEM INSTRUCTION (THE "GEM" PROMPT) ---
system_instruction = """
You are the 'Spiritual Navigator', a specialized AI guide. 
When asked for anonymous teachings, provide a numbered list of 5 brief, one-or-two sentence summaries. Do NOT name the master or tradition.
When asked to identify lineages for a teaching, first provide a one-sentence summary of the types of lineages. Then, provide a numbered list of ONLY the lineage names. Example:
These teachings are found in mystical traditions focused on devotional love.
1. Sufism
2. Bhakti Yoga
When asked for a list of masters for a SINGLE lineage, respond with a numbered list. For each master, provide their name, time period, and a key associated location, separated by '|'.
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

def parse_lineage_summary_and_list(text):
    if not text: return "Could not determine lineages.", []
    summary = text.split('\n')[0]
    lineages = re.findall(r'^\s*\d+\.\s*(.+)$', text, re.MULTILINE)
    return summary, lineages

def parse_masters_list(text):
    if not text: return []
    masters_list = []
    pattern = re.compile(r"^\s*\d+\.\s*(.+?)\s*\|\s*(.+?)\s*\|\s*(.+)$", re.MULTILINE)
    matches = pattern.findall(text)
    for match in matches:
        masters_list.append({
            "name": match[0].strip(),
            "period": match[1].strip(),
            "location": match[2].strip()
        })
    return masters_list

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

# --- STAGE 1: START ---
# --- STAGE 1: START ---
if st.session_state.stage == "start":
    st.caption("An interactive guide to ancient wisdom on modern emotions.")
    st.session_state.vritti = st.text_input("To begin, what emotion or tendency are you exploring?", key="vritti_input")
    
    st.write("---")
    st.subheader("Optional: Share your Guiding Principles")
    
    # This loop reads from the QUESTIONS list you added above
    answers = {}
    for q in QUESTIONS:
        answers[q['key']] = st.radio(q['question'], q['options'], key=q['key'], index=None)

    if st.button("Begin Exploration"):
        if st.session_state.vritti:
            # Collate answers into a personality summary
            summary = [answers[q['key']] for q in QUESTIONS if answers[q['key']]]
            st.session_state.principles_summary = " ".join(summary)
            
            # Move to the next stage
            st.session_state.stage = "show_anonymous_teachings"
            st.rerun()
        else:
            st.warning("Please enter an emotion or tendency to begin.")

# --- STAGE 2: SHOW ANONYMOUS TEACHINGS ---
elif st.session_state.stage == "show_anonymous_teachings":
    st.subheader(f"Insights on: {st.session_state.vritti.capitalize()}")
    if 'teachings' not in st.session_state:
        with st.spinner("Finding teachings that resonate with you..."):
            prompt = f"Provide 5 brief, anonymous teaching summaries from different spiritual traditions about the emotion '{st.session_state.vritti}'."
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
                st.session_state.stage = "show_lineage_list"
                st.rerun()
    st.divider()
    if st.button("Start Over"):
        restart_app()
        st.rerun()

# --- STAGE 3: SHOW LIST OF RELEVANT LINEAGES ---
elif st.session_state.stage == "show_lineage_list":
    st.info(f"You chose: \"{st.session_state.chosen_teaching}\"")
    if 'lineage_list' not in st.session_state:
        with st.spinner("Identifying the associated traditions..."):
            prompt = f"The teaching '{st.session_state.chosen_teaching}' is about '{st.session_state.vritti}'. First, provide a one-sentence summary of what these lineages have in common. Then, provide a numbered list of ONLY the names of the associated spiritual lineages."
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
            st.session_state.stage = "show_masters"
            st.rerun()
    
    st.divider()
    if st.button("Back to Teachings"):
        st.session_state.stage = "show_anonymous_teachings"
        keys_to_clear = ['lineage_summary', 'lineage_list', 'chosen_teaching']
        for key in keys_to_clear:
            if key in st.session_state: del st.session_state[key]
        st.rerun()

# --- STAGE 4: SHOW MASTERS FROM CHOSEN LINEAGE ---
elif st.session_state.stage == "show_masters":
    st.header(st.session_state.chosen_lineage)
    if 'masters_list' not in st.session_state:
        with st.spinner(f"Finding masters from the {st.session_state.chosen_lineage} lineage..."):
            prompt = f"For the lineage '{st.session_state.chosen_lineage}', provide a numbered list of key masters who spoke on '{st.session_state.vritti}'. For each, include their name, time period, and a key associated location, separated by '|'."
            response = call_gemini(prompt)
            st.session_state.raw_response = response
            if response:
                st.session_state.masters_list = parse_masters_list(response)
    
    if not st.session_state.get('masters_list'):
        st.warning("Could not parse the list of masters from the AI's response.")
        with st.expander("Show Raw AI Response (for debugging)"):
            st.code(st.session_state.get('raw_response', "No response from AI."))
    else:
        st.write("Choose a master to learn more:")
        for i, master in enumerate(st.session_state.get('masters_list', [])):
            with st.container():
                st.markdown(f"**{master['name']}**")
                st.caption(f"{master.get('period', 'Unknown')} | {master.get('location', 'Unknown')}")
                if st.button("Explore Teachings", key=f"master_{i}"):
                    st.session_state.chosen_master = master['name']
                    st.session_state.stage = "show_final_teachings"
                    st.rerun()
                st.markdown("---")

    if st.button("Back to Lineage List"):
        st.session_state.stage = "show_lineage_list"
        keys_to_clear = ['masters_list', 'chosen_lineage', 'raw_response']
        for key in keys_to_clear:
            if key in st.session_state: del st.session_state[key]
        st.rerun()

# --- STAGE 5: SHOW FINAL TEACHINGS AND RESOURCES ---
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
        st.subheader("Discover More & Contemplate")
        disc_tabs = st.tabs(["📚 Further Reading", "📍 Places to Visit", "🗓️ Annual Events", "🙏 Practice & Music"])

        with disc_tabs[0]: # Further Reading
            st.markdown(f"**Recommended Books from {st.session_state.chosen_master}**")
            # ... (Full logic for this tab would go here)
        with disc_tabs[1]: # Places
            st.markdown(f"**Places Associated with {st.session_state.chosen_master}**")
            # ... (Full logic for this tab would go here)
        with disc_tabs[2]: # Events
            st.markdown(f"**Events Related to the {st.session_state.chosen_lineage} Tradition**")
            # ... (Full logic for this tab would go here)
        with disc_tabs[3]: # Practice & Music
            st.markdown(f"**A Contemplative Practice**")
            # ... (Full logic for this tab would go here)
    
    st.divider()
    if st.button("Back to Masters List"):
        st.session_state.stage = "show_masters"
        if 'final_teachings' in st.session_state: del st.session_state['final_teachings']
        st.rerun()