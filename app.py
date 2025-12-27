import streamlit as st
from st_paywall import add_auth

# 1. PAGE CONFIG (Must be the very first Streamlit command)
st.set_page_config(page_title="PDC Predictor Pro", layout="wide", initial_sidebar_state="expanded")

# 2. AUTHENTICATION GATE
# This restores your 1.0 Login screen
add_auth(required=True)

# 3. CUSTOM CSS (Restores Sidebar & Hides Audio Bar)
st.markdown("""
    <style>
    /* Hides Streamlit branding but keeps sidebar toggle clickable */
    footer {visibility: hidden;}
    [data-testid="stDecoration"] {display: none;}
    #MainMenu {visibility: hidden;}
    
    /* Hides the gray audio player box */
    audio { display: none; }
    
    /* Optional: Makes the sidebar look cleaner */
    header {background: transparent;}
    </style>
    """, unsafe_allow_html=True)

# 4. AUDIO ENGINE
CHASE_THE_SUN_URL = "https://github.com/Domzy1888/DartsApp/raw/refs/heads/main/ytmp3free.cc_darts-chase-the-sun-extended-15-minutes-youtubemp3free.org.mp3"

# Initialize session state so audio only plays once
if 'audio_played' not in st.session_state:
    st.session_state.audio_played = False

# Sidebar Controls
with st.sidebar:
    st.title("App Settings")
    mute_audio = st.toggle("🔈 Mute Audio", value=False)
    st.divider()

# Only play if not muted and hasn't played yet this session
if not mute_audio and not st.session_state.audio_played:
    st.audio(CHASE_THE_SUN_URL, format="audio/mp3", autoplay=True)
    st.session_state.audio_played = True

# 5. MAIN APP CONTENT (Restoring your 1.0 Tabs)
st.title("🎯 PDC Predictor Pro")

tab1, tab2 = st.tabs(["🎯 Predict", "📊 Standings"])

with tab1:
    st.subheader("Upcoming Matchups")
    # --- PASTE YOUR GOOGLE SHEETS LOADING CODE HERE ---
    # This is where your code from 1.0 that fetches matches goes.
    st.info("Ready to load matches from Google Sheets...")

with tab2:
    st.subheader("League Table")
    # --- PASTE YOUR STANDINGS CODE HERE ---
    st.info("Leaderboard will appear here.")
