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

# 3. Cached Data Reading with Error Handling
@st.cache_data(ttl=60)
def get_data(worksheet):
    try:
        df = conn.read(spreadsheet=URL, worksheet=worksheet, ttl=0)
        # Drop completely empty rows that cause Float errors
        return df.dropna(how='all') 
    except Exception as e:
        st.error(f"Error loading {worksheet}: Check your Google Sheet structure.")
        return pd.DataFrame()

# 4. Pro Styling (Transparent Table & Layout)
def apply_pro_styling():
    st.markdown(
        f"""
        <style>
        .stApp {{
            background: linear-gradient(rgba(0,0,0,0.5), rgba(0,0,0,0.5)), 
                        url("https://cdn.images.express.co.uk/img/dynamic/4/590x/secondary/5856693.jpg?r=1735554407217");
            background-size: cover; background-position: center; background-attachment: fixed;
        }}
        /* Fix Table Transparency */
        [data-testid="stDataFrame"] {{
            background-color: rgba(0, 0, 0, 0.4) !important;
            border: 1px solid #444;
            border-radius: 10px;
        }}
        h1, h2, h3, p {{ color: white !important; }}
        [data-testid="stSidebarContent"] {{ background-color: #111111 !important; }}
        
        /* Match Card Styling */
        [data-testid="stVerticalBlock"] > div:has(.match-wrapper) {{
            border: 2px solid #ffd700 !important;
            border-radius: 20px !important;
            background-image: linear-gradient(rgba(0,0,0,0.5), rgba(0,0,0,0.5)), 
                              url("https://news.paddypower.com/assets/uploads/2023/12/Paddy-Power-World-Darts-Championship.jpg");
            background-size: cover; background-position: center;
            padding: 20px !important; margin-bottom: 25px !important;
        }}
        .match-wrapper {{ display: flex; align-items: center; justify-content: space-between; width: 100%; gap: 15px; }}
        .player-img {{ width: 100%; max-width: 180px; border-radius: 10px; }}
        .vs-text-styled {{ color: #ffd700 !important; font-size: 2rem !important; font-weight: 900 !important; }}
        .player-name-styled {{ font-size: 1.3rem !important; font-weight: 900 !important; color: #ffd700 !important; }}
        
        div.stButton > button {{
            background-color: #ffd700 !important;
            color: #000 !important;
            font-weight: bold !important;
            width: 100% !important; border-radius: 12px !important;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

apply_pro_styling()

# 5. Session State Initialize
if 'username' not in st.session_state: st.session_state['username'] = ""
if 'temp_preds' not in st.session_state: st.session_state.temp_preds = {}

# --- SIDEBAR: LOGIN & NAVIGATION ---
st.sidebar.title("🎯 PDC PREDICTOR")

# This block ensures login boxes appear if not logged in
if st.session_state['username'] == "":
    auth_mode = st.sidebar.radio("Entry", ["Login", "Register"])
    u_attempt = st.sidebar.text_input("Username", key="login_user").strip()
    p_attempt = st.sidebar.text_input("Password", type="password", key="login_pass")
    
    if st.sidebar.button("Go"):
        u_df = get_data("Users")
        if not u_df.empty:
            if auth_mode == "Login":
                # Ensure we compare strings to avoid Float errors
                match = u_df[(u_df['Username'].astype(str) == u_attempt) & 
                             (u_df['Password'].astype(str) == str(p_attempt))]
                if not match.empty:
                    st.session_state['username'] = u_attempt
                    st.rerun()
                else: st.sidebar.error("Invalid Login")
            else:
                new_reg = pd.DataFrame([{"Username": u_attempt, "Password": p_attempt}])
                conn.
