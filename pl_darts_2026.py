import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import time
from datetime import datetime
import extra_streamlit_components as stx

# 1. Page Configuration
st.set_page_config(page_title="PDC PL Predictor 2026", page_icon="🎯", layout="wide")

# --- 2. COOKIE & SESSION INITIALIZATION ---
if 'cookie_manager' not in st.session_state:
    st.session_state['cookie_manager'] = stx.CookieManager(key="pdc_pl_v5_final")
if 'username' not in st.session_state:
    st.session_state['username'] = ""

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

# --- 4. STYLING (BetMGM Vegas Gold + Fixed Alignment) ---
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
    
    /* Sidebar Text & Labels */
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] p, [data-testid="stSidebar"] label {
        color: #C4B454 !important;
        font-weight: bold;
    }

    /* FIX: Force Login Button Text to BLACK */
    [data-testid="stSidebar"] button p {
        color: #000000 !important;
        font-weight: 900 !important;
    }

    /* Centered Subheader for Night */
    .night-header {
        text-align: center;
        color: #C4B454 !important;
        font-size: 1.5rem;
        font-weight: bold;
        text-transform: uppercase;
        margin-bottom: 20px;
    }

    /* Match Card UI */
    .pl-card { 
        border: 1px solid #C4B454; 
        border-radius: 12px; 
        background: rgba(20, 20, 20, 0.95); 
        padding: 15px; 
        margin-bottom: 15px;
    }
    
    /* FIX: Player Name Box - Forces vertical alignment of images */
    .player-name-container {
        min-height: 3em; 
        display: flex;
        align-items: center;
        justify-content: center;
        margin-top: 8px;
    }

    h1, h2, h3 { color: #C4B454 !important; text-transform: uppercase; letter-spacing: 1px; }
    
    /* Selectbox Styling */
    div[data-baseweb="select"] > div {
        background-color: #1c1c1c !important;
        color: white !important;
        border: 1px solid #C4B454 !important;
        border-radius: 8px !important;
    }

    /* BetMGM Gold Buttons */
    div.stButton > button {
        background: #C4B454 !important;
        color: #000000 !important;
        font-weight: 900 !important;
        border: none !important;
        width: 100% !important;
        border-radius: 8px !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- 5. AUTHENTICATION SIDEBAR ---
st.sidebar.title("🎯 PL 2026 PREDICTOR")
if st.session_state['username'] == "":
    u_attempt = st.sidebar.text_input("Username", key="login_user")
    p_attempt = st.sidebar.text_input("Password", type="password", key="login_pass")
    if st.sidebar.button("Login"):
        u_df = get_data("Users")
        # Ensure password is treated as string for comparison
        match = u_df[(u_df['Username'] == u_attempt) & (u_df['Password'].astype(str) == str(p_attempt))]
        if not match.empty:
            st.session_state['username'] = u_attempt
            st.rerun()
        else:
            st.sidebar.error("Invalid Credentials")
else:
    st.sidebar.write(f"Logged in: **{st.session_state['username']}**")
    if st.sidebar.button("Logout"):
        st.session_state['username'] = ""
        st.rerun()

# --- 6. RENDER MATCH FUNCTION ---
def render_match(p1, p2, key):
    img1 = img_lookup.get(p1, "https://via.placeholder.com/150")
    img2 = img_lookup.get(p2, "https://via.placeholder.com/150")
    
    st.markdown(f"""
        <div class="pl-card">
            <div style="display: flex; justify-content: space-around; align-items: flex-start; margin-bottom: 15px;">
                <div style="text-align: center; width: 45%;">
                    <img src="{img1}" style="width: 100%; max-width: 90px; border-radius: 10px;">
                    <div class="player-name-container">
                        <p style="font-size: 0.85rem; color: #C4B454 !important; margin:0;">{p1}</p>
                    </div>
                </div>
                <div style="color: #C4B454; font-size: 1.4rem; font-weight: 900; margin-top: 30px;">VS</div>
                <div style="text-align: center; width: 45%;">
                    <img src="{img2}" style="width: 100%; max-width: 90px;
