import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import time
from datetime import datetime

# 1. Page Configuration
st.set_page_config(page_title="PDC Predictor Pro", page_icon="🎯", layout="wide")

# 2. Connection
conn = st.connection("gsheets", type=GSheetsConnection)
URL = st.secrets["connections"]["gsheets"]["spreadsheet"]

# 3. Robust Data Fetching
@st.cache_data(ttl=5)
def get_data(worksheet):
    try:
        df = conn.read(spreadsheet=URL, worksheet=worksheet, ttl=0)
        return df.dropna(how='all')
    except:
        return pd.DataFrame()

# 4. Global Styling (Pulsing Red & Transparent Tables)
st.markdown("""
    <style>
    @keyframes pulse-red {
        0% { color: #ff4b4b; opacity: 1; }
        50% { color: #ff0000; opacity: 0.5; }
        100% { color: #ff4b4b; opacity: 1; }
    }
    .stApp { 
        background: linear-gradient(rgba(0,0,0,0.6), rgba(0,0,0,0.6)), 
                    url("https://cdn.images.express.co.uk/img/dynamic/4/590x/secondary/5856693.jpg?r=1735554407217"); 
        background-size: cover; background-attachment: fixed; 
    }
    h1, h2, h3, p, label { color: white !important; font-weight: bold; }
    [data-testid="stSidebarContent"] { background-color: #111111 !important; }
    
    /* Table Transparency Nuclear Option */
    [data-testid="stDataFrame"], [data-testid="stTable"], .st-emotion-cache-1wivap2 {
        background-color: rgba(0,0,0,0.4) !important;
        border-radius: 10px;
    }

    .match-card {
        border: 2px solid #ffd700;
        border-radius: 20px;
        background-image: linear-gradient(rgba(0,0,0,0.5), rgba(0,0,0,0.5)), 
                          url("https://news.paddypower.com/assets/uploads/2023/12/Paddy-Power-World-Darts-Championship.jpg");
        background-size: cover; background-position: center;
        padding: 20px; margin-bottom: 10px;
    }
    .match-wrapper { display: flex; align-items: center; justify-content: space-between; width: 100%; gap: 15px; }
    .player-box { flex: 1; text-align: center; }
    .player-img { width: 100%; max-width: 140px; border-radius: 10px; border: 2px solid #ffd700; }
    .vs-text { color: #ffd700 !important; font-size: 2rem !important; font-weight: 900 !important; }
    .player-name { font-size: 1.3rem !important; font-weight: 900 !important; color: #ffd700 !important; }
    
    .timer-text { font-weight: bold; font-size: 1.1rem; text-align: center; margin-bottom: 15px; }
    .timer-urgent { animation: pulse-red 1s infinite; font-weight: 900; }
    
    div.stButton > button { background-color: #ffd700 !important; color: black !important; font-weight: bold; border-radius: 10px; }
    </style>
""", unsafe_allow_html=True)

if 'username' not in st.session_state: st.session_state['username'] = ""

# --- SIDEBAR & AUTH ---
st.sidebar.title("🎯 PDC PREDICTOR")
if st.session_state['username'] == "":
    auth_mode = st.sidebar.radio("Entry", ["Login", "Register"])
    u_attempt = st.sidebar.text_input("Username").strip()
    p_attempt = st.sidebar.text_input("Password", type="password")
    if st.sidebar.button("Go"):
        u_df = get_data("Users")
        if not u_df.empty:
            match = u_
