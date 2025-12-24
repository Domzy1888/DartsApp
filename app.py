import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import time

# 1. Page Configuration
st.set_page_config(page_title="Darts Predictor Pro", page_icon="🎯", layout="wide")

# 2. Connection to Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)
URL = st.secrets["connections"]["gsheets"]["spreadsheet"]

# 3. Cached Data Reading (Reduces API hits)
@st.cache_data(ttl=60)
def get_data(worksheet):
    return conn.read(spreadsheet=URL, worksheet=worksheet, ttl=0)

# 4. Pro Styling (Mobile-First, Side-by-Side)
def apply_pro_styling():
    st.markdown(
        f"""
        <style>
        .stApp {{
            background: linear-gradient(rgba(0,0,0,0.8), rgba(0,0,0,0.8)), 
                        url("https://cdn.images.express.co.uk/img/dynamic/4/590x/secondary/5856693.jpg?r=1735554407217");
            background-size: cover; background-position: center; background-attachment: fixed;
        }}
        h1, h2, h3, p {{ color: white !important; }}
        [data-testid="stSidebarContent"] {{ background-color: #111111 !important; }}
        
        /* The Gold Match Card */
        [data-testid="stVerticalBlock"] > div:has(.match-wrapper) {{
            border: 2px solid #ffd700 !important;
            border-radius: 15px !important;
            background-color: rgba(20, 20, 20, 0.85) !important;
            padding: 15px !important; margin-bottom: 20px !important;
        }}
        
        .match-wrapper {{ display: flex; align-items: center; justify-content: space-between; width: 100%; gap: 10px; }}
        .player-box {{ flex: 1; text-align: center; }}
        .player-img {{ width: 100%; max-width: 100px; border-radius: 10px; }}
        .vs-text-styled {{ color: #ffd700 !important; font-size: 1.5rem !important; font-weight: 900 !important; flex: 0.5; text-align: center; }}
        
        .player-name-styled {{ 
            font-size: 1.1rem !important; font-weight: 900 !important; 
            color: #ffd700 !important; margin-top: 8px; text-align: center; 
        }}
        
        /* High-Visibility Bulk Lock Button */
        div.stButton > button {{
            background-color: #ffd700 !important;
            color: #000 !important;
            font-weight: bold !important;
            width: 100% !important;
            border-radius: 10px !important;
            height: 3.5em !important;
            font-size: 1.2rem !important;
        }}
        
        div[data-baseweb="select"] > div {{
            background-color: #333 !important;
            color: white !important;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

apply_pro_styling()

# 5. Session State Initialization
if 'username' not in st.session_state: st.session_state['username'] = ""
if 'temp_preds' not in st.session_state: st.session_state.temp_preds = {}

# --- SIDEBAR: AUTH & NAVIGATION ---
st.sidebar.title("🎯 PDC PREDICTOR")

if st.session_state['username'] == "":
    auth_mode = st.sidebar.radio("Entry", ["Login", "Register"])
    u_attempt = st.sidebar.text_input("Username").strip()
    p_attempt = st.sidebar.text_input("Password", type="password")
    if st.sidebar.button("Go"):
        u_df = get_data("Users")
        if auth_mode == "Login":
            match = u_df[(u_df['Username'] == u_attempt) & (u_df['Password'].astype(str) == str(p_attempt))]
            if not match.empty:
                st.session_state['username'] = u_attempt
                st.rerun()
            else: st.sidebar.error("Invalid Login")
        else:
            new_reg = pd.DataFrame([{"Username": u_attempt, "Password": p_attempt}])
            conn.update(spreadsheet=URL, worksheet="Users", data=pd.concat([u_df, new_reg], ignore_index=True))
            st.sidebar.success("Registered! Please Login.")
else:
    st.sidebar.write(f"Logged in: **{st.session_state['username']}**")
    if st.sidebar.button("Logout"):
        st.session_state['username'] = ""; st.session_state.temp_preds = {}; st.rerun()

st.sidebar.divider()
page = st.sidebar.radio("Navigate", ["Predictions", "Leaderboard", "Rival Watch", "Admin"])

# --- PAGE: PREDICTIONS ---
if page == "Predictions":
    if st.session_state['username'] == "":
        st.warning("Please sign in to view matchups.")
    else:
        st.title("Match Predictions")
        
        m_df = get_data("Matches")
        p_df = get_data("Predictions")
        r_df = get_data("Results")

        open_matches_list = []

        for _, row in m_df.iterrows():
            m_id = str(row['Match_ID'])
            is_closed = m_id in r_df['Match_ID'].astype(str).values if not r_df.empty else False
            # Filter duplicates if they exist
            user_preds = p_df[p_df['Username'] == st.session_state['username']]
            already_done = m_id in user_preds['Match_ID'].astype(str).values if not user_preds.empty else False
            
            with st.container():
                p1_img = row['P1_Image'] if pd.notna(row['P1_Image']) else "https://via.placeholder.com/150"
                p2_img = row['P2_Image'] if pd.notna(row['P2_Image']) else "https://via.placeholder.com/150"
                
                st.markdown(f"""
                    <div class="match-wrapper">
                        <div class="player-box">
                            <img src="{p1_img}" class="player-img">
                            <div class="player-name-styled">{row['Player1']}</div>
                        </div>
                        <div class="vs-text-styled">VS</div>
                        <div class="player-box">
                            <img src="{p2_img}" class="player-img">
                            <div class="player-name-styled">{row['Player2']}</div>
                        </div>
                    </div>
                """, unsafe_allow_html=True)

                if is_closed:
                    st.info("Match Closed")
                elif already_done:
                    st.success("Locked In ✅")
                else:
                    open_matches_list.append(m_id)
                    c1, c2 = st.columns(2)
                    with c1: s1 = st.selectbox(f"{row['Player1']}", range(11), key=f"s1_{m_id}")
                    with c2: s2 = st.selectbox(f"{row['Player2']}", range(11), key
