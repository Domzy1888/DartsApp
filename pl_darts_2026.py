import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import time
from datetime import datetime

###############################################################################
##### SECTION 1: PAGE CONFIG & SESSION INITIALIZATION                     #####
###############################################################################
st.set_page_config(page_title="PDC PL Predictor 2026", page_icon="🎯", layout="wide")

if 'username' not in st.session_state:
    st.session_state['username'] = ""

###############################################################################
##### SECTION 2: DATA CONNECTION & LOAD FUNCTIONS                         #####
###############################################################################
conn = st.connection("gsheets", type=GSheetsConnection)
URL = st.secrets["connections"]["gsheets"]["spreadsheet"]

@st.cache_data(ttl=2)
def get_data(worksheet):
    try:
        df = conn.read(spreadsheet=URL, worksheet=worksheet, ttl=0)
        # Standardize column names to prevent KeyError
        df.columns = df.columns.str.strip()
        return df.dropna(how='all')
    except Exception:
        return pd.DataFrame()

###############################################################################
##### SECTION 3: CSS STYLING (BetMGM Theme)                               #####
###############################################################################
st.markdown(f"""
    <style>
    .stApp {{ 
        background: linear-gradient(rgba(0,0,0,0.8), rgba(0,0,0,0.8)), 
                    url("https://i.postimg.cc/d1kXbbDk/2025PLFinal-Gen-View.jpg"); 
        background-size: cover; background-attachment: fixed; 
    }}
    [data-testid="stSidebar"], [data-testid="stSidebarContent"] {{
        background-color: #111111 !important; border-right: 1px solid #C4B454;
    }}
    .night-header {{ text-align: center; color: #C4B454 !important; font-size: 1.8rem; font-weight: 900; text-transform: uppercase; margin-bottom: 5px; }}
    .pl-card {{ border: 1px solid #C4B454; border-radius: 12px; background: rgba(20, 20, 20, 0.95); padding: 15px; margin-bottom: 15px; }}
    h1, h2, h3 {{ color: #C4B454 !important; text-transform: uppercase; }}
    div.stButton > button {{ background: #C4B454 !important; color: #000000 !important; font-weight: 900 !important; border: none; }}
    </style>
""", unsafe_allow_html=True)

###############################################################################
##### SECTION 4: HELPER FUNCTIONS (MATCH RENDERER)                         #####
###############################################################################
def render_match(p1, p2, key, img_lookup, disabled=False):
    img1 = img_lookup.get(p1, "https://via.placeholder.com/150")
    img2 = img_lookup.get(p2, "https://via.placeholder.com/150")
    st.markdown(f"""
        <div class="pl-card">
            <div style="display: flex; justify-content: space-around; align-items: center;">
                <div style="text-align: center; width: 40%;">
                    <img src="{img1}" style="width: 80px; border-radius: 10px;">
                    <p style="color:white; margin:0; font-size:0.8rem;">{p1}</p>
                </div>
                <div style="color: #C4B454; font-weight: 900;">VS</div>
                <div style="text-align: center; width: 40%;">
                    <img src="{img2}" style="width: 80px; border-radius: 10px;">
                    <p style="color:white; margin:0; font-size:0.8rem;">{p2}</p>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    return st.selectbox(f"Winner: {p1} vs {p2}", ["Select Winner", p1, p2], key=key, label_visibility="collapsed", disabled=disabled)

###############################################################################
##### SECTION 5: SIDEBAR & LOGIN                                          #####
###############################################################################
st.sidebar.title("🎯 PL PREDICTOR")
if st.session_state['username'] == "":
    u_attempt = st.sidebar.text_input("Username")
    p_attempt = st.sidebar.text_input("Password", type="password")
    if st.sidebar.button("Login"):
        u_df = get_data("Users")
        if not u_df.empty and u_attempt in u_df['Username'].values:
            st.session_state['username'] = u_attempt
            st.rerun()
else:
    menu = st.sidebar.radio("NAVIGATE", ["Matches", "Leaderboard", "Rival Watch", "Admin"])
    if st.sidebar.button("Logout"):
        st.session_state['username'] = ""
        st.rerun()

###############################################################################
##### SECTION 6: MAIN APP LOGIC (MATCHES & BRACKET)                       #####
###############################################################################
if st.session_state['username'] != "":
    players_df = get_data("Players")
    admin_df = get_data("PL_2026_Admin")
    subs_df = get_data("User_Submissions")
    img_lookup = dict(zip(players_df['Name'], players_df['Image_URL'])) if not players_df.empty else {}

    if menu == "Matches" and not admin_df.empty:
        night_choice = st.selectbox("Select Night", admin_df['Night'].unique())
        night_data = admin_df[admin_df['Night'] == night_choice].iloc[0]
        
        st.markdown(f"<h1 style='text-align: center;'>📍 {night_data['Venue']}</h1>", unsafe_allow_html=True)

        # LOCK LOGIC
        is_locked = False
        try:
            cutoff_dt = pd.to_datetime(night_data['Cutoff'])
            if datetime.now() > cutoff_dt:
                is_locked = True
                st.error("🔒 The cutoff time has passed.")
        except Exception: pass

        # QUARTER FINALS
        st.markdown("### 1️⃣ Quarter Finals")
        qf1 = render_match(night_data['QF1-P1'], night_data['QF1-P2'], f"qf1_{night_choice}", img_lookup, is_locked)
        qf2 = render_match(night_data['QF2-P1'], night_data['QF2-P2'], f"qf2_{night_choice}", img_lookup, is_locked)
        qf3 = render_match(night_data['QF3-P1'], night_data['QF3-P2'], f"qf3_{night_choice}", img_lookup, is_locked)
        qf4 = render_match(night_data['QF4-P1'], night_data['QF4-P2'], f"qf4_{night_choice}", img_lookup, is_locked)

        # PROGRESSIVE REVEAL
        if all(x != "Select Winner" for x in [qf1, qf2, qf3, qf4]):
            st.divider()
            st.markdown("### 2️⃣ Semi Finals")
            sf1 = render_match(qf1, qf2, f"sf1_{night_choice}", img_lookup, is_locked)
            sf2 = render_match(qf3, qf4, f"sf2_{night_choice}", img_lookup, is_locked)

            if all(x != "Select Winner" for x in [sf1, sf2]):
                st.divider()
                st.markdown("### 🏆 The Final")
                final = render_match(sf1, sf2, f"fin_{night_choice}", img_lookup, is_locked)
                
                if final != "Select Winner" and not is_locked:
                    if st.button("LOCK PREDICTIONS"):
                        st.success("Locked! (Connection to Sheets logic goes here)")

    elif menu == "Leaderboard":
        st.subheader("🏆 Season Rankings")
        st.info("Leaderboard will update after Night 1.")
