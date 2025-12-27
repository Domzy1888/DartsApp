import streamlit as st
import pandas as pd
import time

# --- CONFIGURATION & LINKS ---
# Step 1: Replace this with your GitHub RAW link
CHASE_THE_SUN_URL = "https://github.com/Domzy1888/DartsApp/raw/refs/heads/main/ytmp3free.cc_darts-chase-the-sun-extended-15-minutes-youtubemp3free.org.mp3"

st.set_page_config(page_title="PDC Predictor Pro", layout="wide")

# --- CUSTOM CSS (Stealth Mode & No-Jump Heights) ---
st.markdown("""
    <style>
    /* 1. Hide Streamlit Branding & Audio Player */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    audio { display: none; }

    /* 2. Fixed Image Heights to prevent page jumping */
    .player-img-container {
        height: 100px;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    
    /* 3. Swoop-in Animation for Match Cards */
    @keyframes fadeInUp {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    .match-card {
        background-color: #1e1e1e;
        padding: 15px;
        border-radius: 12px;
        margin-bottom: 15px;
        animation: fadeInUp 0.5s ease-out;
    }
    </style>
    """, unsafe_allow_html=True)

# --- SIDEBAR (Mute & Settings) ---
st.sidebar.title("Settings")
mute_audio = st.sidebar.toggle("🔈 Mute Audio", value=False)

# --- AUDIO LOGIC ---
if 'audio_played' not in st.session_state:
    st.session_state.audio_played = False

# Only triggers once per login/session
if not mute_audio and not st.session_state.audio_played:
    st.audio(CHASE_THE_SUN_URL, format="audio/mp3", autoplay=True)
    st.session_state.audio_played = True

# --- MAIN APP ---
tab1, tab2 = st.tabs(["🎯 Predict", "📊 Standings"])

with tab1:
    st.title("Upcoming Matches")

    # --- MATCH CARD FRAGMENT ---
    # This prevents the page from jumping when selecting a score
    @st.fragment
    def match_card(match_id, p1_name, p1_img, p2_name, p2_img):
        with st.container():
            st.markdown('<div class="match-card">', unsafe_allow_html=True)
            col1, col2, col3 = st.columns([2, 1, 2])
            
            with col1:
                st.markdown(f'<div class="player-img-container"><img src="{p1_img}" width="80"></div>', unsafe_allow_html=True)
                st.write(f"**{p1_name}**")
                st.selectbox("Score", range(11), key=f"s1_{match_id}")
                
            with col2:
                st.markdown("<h3 style='text-align: center; padding-top: 30px;'>VS</h3>", unsafe_allow_html=True)
                
            with col3:
                st.markdown(f'<div class="player-img-container"><img src="{p2_img}" width="80"></div>', unsafe_allow_html=True)
                st.write(f"**{p2_name}**")
                st.selectbox("Score", range(11), key=f"s2_{match_id}")
            st.markdown('</div>', unsafe_allow_html=True)

    # Example of calling the card (you would loop through your Google Sheet data here)
    # Replace these placeholder URLs with your Top 32 Links from your Sheet
    match_card("m1", "Luke Littler", "URL_FROM_SHEET", "Luke Humphries", "URL_FROM_SHEET")
    match_card("m2", "Michael van Gerwen", "URL_FROM_SHEET", "Gerwyn Price", "URL_FROM_SHEET")
