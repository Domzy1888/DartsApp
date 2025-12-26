import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import time
from datetime import datetime

# 1. Page Configuration
st.set_page_config(page_title="Darts Predictor Pro", page_icon="🎯", layout="wide")

# 2. Connection to Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)
URL = st.secrets["connections"]["gsheets"]["spreadsheet"]

# 3. Cached Data Reading
@st.cache_data(ttl=60)
def get_data(worksheet):
    try:
        df = conn.read(spreadsheet=URL, worksheet=worksheet, ttl=0)
        return df.dropna(how='all') # Removes empty rows
    except:
        return pd.DataFrame()

# 4. Pro Styling
def apply_pro_styling():
    st.markdown(
        f"""
        <style>
        .stApp {{
            background: linear-gradient(rgba(0,0,0,0.5), rgba(0,0,0,0.5)), 
                        url("https://cdn.images.express.co.uk/img/dynamic/4/590x/secondary/5856693.jpg?r=1735554407217");
            background-size: cover; background-position: center; background-attachment: fixed;
        }}
        h1, h2, h3, p {{ color: white !important; }}
        [data-testid="stSidebarContent"] {{ background-color: #111111 !important; }}
        
        /* Transparent Table Background */
        [data-testid="stDataFrame"] {{
            background-color: rgba(0, 0, 0, 0.6) !important;
            border-radius: 10px;
            padding: 10px;
        }}
        
        /* The Match Card */
        [data-testid="stVerticalBlock"] > div:has(.match-wrapper) {{
            border: 2px solid #ffd700 !important;
            border-radius: 20px !important;
            background-image: linear-gradient(rgba(0,0,0,0.5), rgba(0,0,0,0.5)), 
                              url("https://news.paddypower.com/assets/uploads/2023/12/Paddy-Power-World-Darts-Championship.jpg");
            background-size: cover; background-position: center;
            padding: 20px !important; margin-bottom: 25px !important;
        }}
        
        .match-wrapper {{ display: flex; align-items: center; justify-content: space-between; width: 100%; gap: 15px; }}
        .player-box {{ flex: 1; text-align: center; }}
        .player-img {{ width: 100%; max-width: 180px; border-radius: 10px; }}
        .vs-text-styled {{ color: #ffd700 !important; font-size: 2rem !important; font-weight: 900 !important; text-shadow: 2px 2px 4px #000; }}
        .player-name-styled {{ font-size: 1.3rem !important; font-weight: 900 !important; color: #ffd700 !important; text-shadow: 2px 2px 4px #000; }}
        
        div.stButton > button {{
            background-color: #ffd700 !important;
            color: #000 !important;
            font-weight: bold !important;
            width: 100% !important; border-radius: 12px !important; height: 3.8em !important;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

apply_pro_styling()

if 'username' not in st.session_state: st.session_state['username'] = ""
if 'temp_preds' not in st.session_state: st.session_state.temp_preds = {}

# --- SIDEBAR ---
st.sidebar.title("🎯 PDC PREDICTOR")
if st.session_state['username'] == "":
    auth_mode = st.sidebar.radio("Entry", ["Login", "Register"])
    u_attempt = st.sidebar.text_input("Username").strip()
    p_attempt = st.sidebar.text_input("Password", type="password")
    if st.sidebar.button("Go"):
        u_df = get_data("Users")
        if not u_df.empty:
            if auth_mode == "Login":
                match = u_df[(u_df['Username'].astype(str) == u_attempt) & (u_df['Password'].astype(str) == str(p_attempt))]
                if not match.empty:
                    st.session_state['username'] = u_attempt
                    st.rerun()
                else: st.sidebar.error("Invalid Login")
            else:
                new_reg = pd.DataFrame([{"Username": u_attempt, "Password": p_attempt}])
                conn.update(spreadsheet=URL, worksheet="Users", data=pd.concat([u_df, new_reg], ignore_index=True))
                st.sidebar.success("Registered! Login now.")
else:
    st.sidebar.write(f"Logged in: **{st.session_state['username']}**")
    if st.sidebar.button("Logout"):
        st.session_state['username'] = ""; st.rerun()

st.sidebar.divider()
page = st.sidebar.radio("Navigate", ["Predictions", "Leaderboard", "Rival Watch", "Admin"])

# --- PAGE: PREDICTIONS ---
if page == "Predictions":
    if st.session_state['username'] == "":
        st.warning("Please sign in to view matchups.")
    else:
        st.title("Upcoming Matches")
        m_df = get_data("Matches").dropna(subset=['Date', 'Match_ID'])
        p_df = get_data("Predictions")
        r_df = get_data
