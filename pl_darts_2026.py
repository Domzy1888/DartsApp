import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import time
from datetime import datetime, timedelta
import extra_streamlit_components as stx

# 1. Page Configuration
st.set_page_config(page_title="PDC PL Predictor 2026", page_icon="🎯", layout="wide")

# --- 2. COOKIE & SESSION INITIALIZATION ---
if 'cookie_manager' not in st.session_state:
    st.session_state['cookie_manager'] = stx.CookieManager(key="pdc_pl_cookie_manager_v4")
cookie_manager = st.session_state['cookie_manager']
if 'username' not in st.session_state: st.session_state['username'] = ""

# --- 3. CONNECTION SETUP ---
conn = st.connection("gsheets", type=GSheetsConnection)
URL = st.secrets["connections"]["gsheets"]["spreadsheet"]

@st.cache_data(ttl=5)
def get_data(worksheet):
    try:
        df = conn.read(spreadsheet=URL, worksheet=worksheet, ttl=0)
        return df.dropna(how='all')
    except:
        return pd.DataFrame()

# --- 4. STYLING (The Final Polished Version) ---
# Primary BetMGM Gold: #C4B454
st.markdown("""
    <style>
    /* Main Background */
    .stApp { 
        background: linear-gradient(rgba(0,0,0,0.85), rgba(0,0,0,0.85)), 
                    url("https://cdn.images.express.co.uk/img/dynamic/4/590x/secondary/5856693.jpg?r=1735554407217"); 
        background-size: cover; 
        background-attachment: fixed; 
    }
    
    /* Dark Sidebar & Gold Accents */
    [data-testid="stSidebar"], [data-testid="stSidebarContent"] {
        background-color: #111111 !important;
        border-right: 1px solid #C4B454;
    }
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] p, [data-testid="stSidebar"] label {
        color: #C4B454 !important;
        font-weight: bold;
    }
    
    /* Force Login Button Text to Black */
    div.stButton > button p {
        color: #000000 !important;
        font-weight: 900 !important;
    }
    
    /* Centering the Subheader */
    .centered-header {
        text-align: center;
        color: #C4B454 !important;
        width: 100%;
        display: block;
        margin-bottom: 20px;
        text-transform: uppercase;
    }

    /* Match Card UI */
    .pl-card { 
        border: 1px solid #C4B454; 
        border-radius: 12px; 
        background: rgba(20, 20, 20, 0.95); 
        padding: 15px; 
        margin-bottom: 15px;
    }
    
    /* Player Name Box - Forces Alignment */
    .player-name-container {
        min-height: 2.5em; 
        display: flex;
        align-items: center;
        justify-content: center;
        margin-top: 8px;
    }

    h1, h2, h3 { color: #C4B454 !important; text-transform: uppercase; letter-spacing: 1px; }
    p, label { color: white !important; font-weight: bold; }
    
    div[data-baseweb="select"] > div {
        background-color: #1c1c1c !important;
        color: white !important;
        border: 1px solid #C4B454 !important;
        border-radius: 8px !important;
    }

    /* Primary Gold Button */
    div.stButton > button {
        background: #C4B454 !important;
        color: #000000 !important;
        font-weight: 900 !important;
        border: none !important;
        width: 100% !important;
        border-radius: 8px !important;
        text-transform: uppercase;
    }
    </style>
""", unsafe_allow_html=True)

# --- 5. AUTHENTICATION ---
st.sidebar.title("🎯 PL 2026 PREDICTOR")
if st.session_state['username'] == "":
    u_attempt = st.sidebar.text_input("Username")
