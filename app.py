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
                --title-color: #4A5568;
                --font: 'Lato', sans-serif;
            }
            .stApp, .stApp h2, .stApp h3, .stApp p, .stApp li, .stApp label, .stApp .stMarkdown {
                color: var(--text-color) !important;
            }
            body, .stApp { background-color: var(--background-color); }
            h1, h2, h3 { font-family: var(--font); }
            h1 {
                font-size: 2.5rem !important;
                color: var(--title-color) !important;
                text-align: center;
            }
            .st-emotion-cache-10trblm { text-align: center; }
            .stTabs [data-baseweb="tab"][aria-selected="true"] {
                background-color: transparent;
                color: var(--primary-color);
                border-bottom: 2px solid var(--primary-color);
            }
            .button-container { display: flex; flex-wrap: wrap; gap: 10px; justify-content: center; margin-bottom: 20px; }
            .stButton>button { border-radius: 20px; border: 1px solid var(--primary-color); color: var(--primary-color); background-color: transparent; transition: all 0.3s ease-in-out; padding: 5px 15px; }
            .stButton>button:hover { color: var(--secondary-background-color); background-color: var(--primary-color); }
            .st-emotion-cache-1r6slb0, .st-emotion-cache-p5msec, .summary-container { 
                border-radius: 10px; padding: 1.5rem; background-color: var(--secondary-background-color); 
                box-shadow: 0 4px 8px rgba(0,0,0,0.08); margin-bottom: 1rem;
            }
            .summary-text { font-size: 1.1rem; font-style: italic; text-align: center; margin-bottom: 1rem; }
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
CRITICAL RULE: All lists you generate MUST be in a numbered list format.
When asked for teaching summaries, you must respond in the format: "1. **Lineage Name:** A concise, one-sentence summary of the lineage's core teaching on the topic."
When providing detailed teachings, structure it with clear markdown headings: "### Core Philosophical Concepts", "### The Prescribed Method or Practice", and "### Reference to Key Texts".
When asked for books, places, or events, if no relevant information exists, you must respond with ONLY the single word 'None'.
When asked for book recommendations, respond with a markdown table with columns: Book, Description, and Link (to search on Amazon.in).
When asked to generate a practice, it must be authentic to the specific tradition. For a Bhakti master, it might be a devotional act. For a Karma Yoga teaching, an act of selfless service. For an introspective master, a meditation. Present it as simple, actionable steps. After the steps, if a relevant and soothing bhajan or chant is associated, add a section '### Suggested Listening' and a markdown link to a YouTube search for it.
"""

# --- Nature Elements Database ---
NATURE_ELEMENTS = {
    "🌌 Expansive & Vast": ["🌊 Deep Ocean", "🏜️ Vast Desert", "✨ Starry Night Sky", "🏔️ Silent Mountain"],
    "⚡ Dynamic & Powerful": ["🏞️ Roaring Waterfall", "⛈️ Rolling Thunder", "🌊 Crashing Waves", "🔥 Wildfire"],
    "🌿 Gentle & Nurturing": ["💧 Gentle Rain", "🏞️ Flowing River", "🌲 Lush Forest", "🌅 Warm Sunrise"]
}

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

def parse_summaries(text):
    if not text: return []
    pattern = re.compile(r"^\s*\d+\.\s*\*\*(.*?):\*\*\s*(.*)", re.MULTILINE)
    matches = pattern.findall(text)
    summaries_list = [{"lineage": match[0].strip(), "summary": match[1].strip()} for match in matches]
    return summaries_list

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
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.session_state.stage = "start"

# --- MAIN APP UI ---
st.title("🧘 Spiritual Navigator")
load_custom_css()

if st.session_state.stage == "start":
    st.subheader("Let nature be your guide.")
    st.write("Choose an element below that reflects your inner state to begin.")
    
    for category, elements in NATURE_ELEMENTS.items():
        st.subheader(category)
        cols = st.columns(4)
        for i, element in enumerate(elements):
            with cols[i % 4]:
                if st.button(element, key=f"nature_{element}", use_container_width=True):
                    st.session_state.chosen_nature = element
                    st.session_state.stage = "show_emotions"
                    st.rerun()
        st.divider()

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
            st.session_state.stage = "show_summaries"
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    st.divider()
    if st.button("Back to Nature"):
        restart_app()
        st.rerun()

elif st.session_state.stage == "show_summaries":
    st.subheader(f"Wisdom on: {st.session_state.chosen_emotion}")
    if 'summaries' not in st.session_state:
        with st.spinner("Gathering insights from across traditions..."):
            prompt = f"For the emotion '{st.session_state.chosen_emotion}', provide a numbered list of 5 concise, one-sentence teaching summaries from different spiritual lineages. Only include lineages that have distinct teachings on this topic. The format must be: \"1. **Lineage Name:** Summary of the teaching.\""
            response_text = call_gemini(prompt)
            if response_text:
                st.session_state.summaries = parse_summaries(response_text)
    
    st.write("Choose the teaching that resonates with you most:")
    for i, item in enumerate(st.session_state.get('summaries', [])):
        with st.container():
            st.markdown(f"<div class='summary-container'><p class='summary-text'>“{item['summary']}”</p>", unsafe_allow_html=True)
            if st.button(f"Explore this perspective", key=f"summary_{i}", use_container_width=True):
                st.session_state.chosen_summary = item
                st.session_state.stage = "show_masters"
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)
    
    st.divider()
    if st.button("Explore More Summaries"):
        with st.spinner("Finding more perspectives..."):
            existing_lineages = [s['lineage'] for s in st.session_state.get('summaries', [])]
            prompt = f"For the emotion '{st.session_state.chosen_emotion}', provide a numbered list of 5 more teaching summaries from different spiritual lineages, excluding: {', '.join(existing_lineages)}. The format must be: \"1. **Lineage Name:** Summary of the teaching.\""
            response_text = call_gemini(prompt)
            if response_text:
                new_summaries = parse_summaries(response_text)
                st.session_state.summaries.extend(new_summaries)
        st.rerun()
    
    if st.button("Back to Emotions"):
        st.session_state.stage = "show_emotions"
        if 'summaries' in st.session_state: del st.session_state['summaries']
        st.rerun()
    if st.button("Start Over"):
        restart_app()
        st.rerun()

elif st.session_state.stage == "show_masters":
    lineage = st.session_state.chosen_summary['lineage']
    st.subheader(f"This wisdom is from the {lineage} tradition")
    st.caption(f"Let's explore some of its masters.")
    
    if 'masters' not in st.session_state:
        with st.spinner(f"Finding masters from the {lineage} lineage..."):
            prompt = f"List 5 key masters from the '{lineage}' lineage who have teachings relevant to '{st.session_state.chosen_emotion}'."
            response_text = call_gemini(prompt)
            if response_text:
                st.session_state.masters = parse_list(response_text)

    st.write("Choose a master to learn from:")
    for i, master in enumerate(st.session_state.get('masters', [])):
        with st.container():
            st.markdown(f"**{master}**")
            if st.button(f"Dive into the teachings of {master}", key=f"master_{i}", use_container_width=True):
                st.session_state.chosen_master = master
                st.session_state.stage = "show_teachings"
                st.rerun()
    
    st.divider()
    if st.button("Explore More Masters"):
        with st.spinner("Finding more masters..."):
            existing_masters = st.session_state.get('masters', [])
            prompt = f"List 5 more masters from the '{lineage}' lineage, excluding: {', '.join(existing_masters)}."
            response_text = call_gemini(prompt)
            if response_text:
                new_masters = parse_list(response_text)
                st.session_state.masters.extend(new_masters)
        st.rerun()

    if st.button("Back to Summaries"):
        st.session_state.stage = "show_summaries"
        if 'masters' in st.session_state: del st.session_state['masters']
        st.rerun()
    if st.button("Start Over"):
        restart_app()
        st.rerun()

elif st.session_state.stage == "show_teachings":
    st.subheader(f"Teachings of {st.session_state.chosen_master}")
    st.caption(f"From the **{st.session_state.chosen_summary['lineage']}** perspective on **{st.session_state.chosen_emotion}**.")
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
        st.subheader("Contemplate")
        st.info("A practice to deepen your understanding.")
        if 'practice_text' not in st.session_state:
            with st.spinner("Generating a relevant practice..."):
                # --- MODIFIED: Prompt for a more authentic and diverse practice ---
                prompt = f"Based on the core teachings of {st.session_state.chosen_master} from the {st.session_state.chosen_summary['lineage']} tradition, suggest a simple, actionable practice to help a user work with the emotion of '{st.session_state.chosen_emotion}'. The practice must be authentic to that specific tradition. For example, for a Bhakti master, it might be a devotional act like chanting. For a Karma Yoga teaching, it might be an act of selfless service. For an introspective master, it might be a meditation. Present the suggestion as a few clear, actionable steps. After the steps, if relevant, suggest a soothing bhajan, chant, or hymn with a YouTube search link."
                st.session_state.practice_text = call_gemini(prompt) or "No practice could be generated."
        st.markdown(st.session_state.practice_text)
        st.text_area("Your Contemplation Journal:", height=150, key="journal_entry", help="Entries are for this session only.")
    
    st.divider()
    if st.button("Back to Masters List"):
        st.session_state.stage = "show_masters"
        keys_to_clear = ['teachings', 'practice_text']
        for key in keys_to_clear:
            if key in st.session_state: del st.session_state[key]
        st.rerun()
    if st.button("Start Over"):
        restart_app()
        st.rerun()