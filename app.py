import streamlit as st
from st_paywall import add_auth

# 1. PAGE SETUP (Must be the very first command)
st.set_page_config(
    page_title="PDC Predictor Pro", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# 2. AUTHENTICATION GATE
# This ensures users log in before seeing any data or hearing music
# add_auth(required=True)

# 3. CUSTOM CSS (Hide Audio Player & Branding, Keep Sidebar Toggle)
st.markdown("""
    <style>
    /* Hides 'Made with Streamlit' footer */
    footer {visibility: hidden;}
    
    /* Hides the colored line at the top */
    [data-testid="stDecoration"] {display: none;}
    
    /* Hides the default gray audio player box */
    audio { display: none; }

    /* Hides Hamburger Menu but keeps the sidebar arrow clickable */
    #MainMenu {visibility: hidden;}
    header {background: transparent;}
    
    /* Card styling for matches */
    .match-card {
        background-color: #262730;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #464b5d;
        margin-bottom: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# 4. AUDIO ENGINE (Walk-on Music)
CHASE_THE_SUN_URL = "https://github.com/Domzy1888/DartsApp/raw/refs/heads/main/ytmp3free.cc_darts-chase-the-sun-extended-15-minutes-youtubemp3free.org.mp3"

# Initialize session state so it doesn't restart on every click
if 'audio_played' not in st.session_state:
    st.session_state.audio_played = False

# Sidebar Controls
with st.sidebar:
    st.title("Settings")
    mute_audio = st.toggle("🔈 Mute Audio", value=False)
    st.divider()
    # Add your logout or user info here if you had it in 1.0

# Play only if NOT muted and HAS NOT played yet this session
if not mute_audio and not st.session_state.audio_played:
    st.audio(CHASE_THE_SUN_URL, format="audio/mp3", autoplay=True)
    st.session_state.audio_played = True

# 5. MAIN CONTENT (Your Original 1.0 Tabs & Logic)
st.title("🎯 PDC Predictor Pro")

tab1, tab2 = st.tabs(["🎯 Predict", "📊 Standings"])

with tab1:
    st.subheader("Upcoming Matches")
    
    # --- YOUR ORIGINAL 1.0 MATCH LOADING CODE GOES HERE ---
    # Example structure:
    # conn = st.connection("gsheets", type=GSheetsConnection)
    # df = conn.read(worksheet="Matches")
    # for index, row in df.iterrows():
    #     st.markdown(f'<div class="match-card">', unsafe_allow_html=True)
    #     # Your match display logic...
    #     st.markdown('</div>', unsafe_allow_html=True)
    
    st.info("Match data will load here based on your Google Sheet.")

with tab2:
    st.subheader("Leaderboard")
    # --- YOUR ORIGINAL 1.0 STANDINGS CODE GOES HERE ---
    st.info("Standings will appear here.")
