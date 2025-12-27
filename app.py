import streamlit as st
from st_paywall import add_auth

# 1. PAGE CONFIG (Must be the very first Streamlit command)
st.set_page_config(page_title="PDC Predictor Pro", layout="wide", initial_sidebar_state="expanded")

# 2. AUTHENTICATION GATE
# This brings back your login page. The rest of the code only runs if login is successful.
add_auth(required=True)

# 3. CUSTOM CSS (Fixes the Sidebar & Hides Branding)
st.markdown("""
    <style>
    /* Hides the 'Made with Streamlit' footer and top decoration line */
    footer {visibility: hidden;}
    [data-testid="stDecoration"] {display: none;}
    
    /* Hides the default Audio Player so it plays 'in the background' */
    audio { display: none; }

    /* Hides the Hamburger Menu but KEEPS the Sidebar Toggle visible */
    #MainMenu {visibility: hidden;}
    header {background: transparent;}
    </style>
    """, unsafe_allow_html=True)

# 4. AUDIO ENGINE
# Using your specific GitHub Raw link
CHASE_THE_SUN_URL = "https://github.com/Domzy1888/DartsApp/raw/refs/heads/main/ytmp3free.cc_darts-chase-the-sun-extended-15-minutes-youtubemp3free.org.mp3"

if 'audio_played' not in st.session_state:
    st.session_state.audio_played = False

# Sidebar Mute Toggle
with st.sidebar:
    st.title("App Settings")
    mute_audio = st.toggle("🔈 Mute Audio", value=False)
    st.divider()

# Only play if not muted and hasn't played yet this session
if not mute_audio and not st.session_
