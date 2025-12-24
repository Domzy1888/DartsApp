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
    return conn.read(spreadsheet=URL, worksheet=worksheet, ttl=0)

# 4. Pro Styling
def apply_pro_styling():
    st.markdown(
        f"""
        <style>
        /* Main App Background - 0.5 Gradient */
        .stApp {{
            background: linear-gradient(rgba(0,0,0,0.5), rgba(0,0,0,0.5)), 
                        url("https://cdn.images.express.co.uk/img/dynamic/4/590x/secondary/5856693.jpg?r=1735554407217");
            background-size: cover; background-position: center; background-attachment: fixed;
        }}
        h1, h2, h3, p {{ color: white !important; }}
        
        /* SIDEBAR STYLING */
        [data-testid="stSidebarContent"] {{ background-color: #111111 !important; }}
        
        /* THE ULTIMATE SIDEBAR TAB FIX */
        /* Targets the container for the collapse/expand button */
        section[data-testid="stSidebar"] + div {{
            display: block !important;
        }}

        [data-testid="stSidebarCollapsedControl"], 
        .st-emotion-cache-6qob1r {{ 
            background-color: #ffd700 !important;
            border-radius: 0 12px 12px 0 !important;
            width: 55px !important;
            height: 55px !important;
            left: 0px !important;
            top: 85px !important; /* Lowered further to guarantee clearing the 3-dot menu */
            position: fixed !important;
            z-index: 1000001 !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            box-shadow: 5px 0px 15px rgba(0,0,0,0.6) !important;
            opacity: 1 !important;
            visibility: visible !important;
        }}
        
        /* Ensure the icon stays black and visible */
        [data-testid="stSidebarCollapsedControl"] svg,
        .st-emotion-cache-6qob1r svg {{
            fill: #000000 !important;
            color: #000000 !important;
            width: 32px !important;
            height: 32px !important;
        }}

        /* The Match Card - 0.5 Gradient & Paddy Power Ally Pally URL */
        [data-testid="stVerticalBlock"] > div:has(.match-wrapper) {{
            border: 2px solid #ffd700 !important;
            border-radius: 20px !important;
            background-image: linear-gradient(rgba(0,0,0,0.5), rgba(0,0,0,0.5)), 
                              url("https://news.paddypower.com/assets/uploads/2023/12/Paddy-Power-World-Darts-Championship.jpg");
            background-size: cover;
            background-position: center;
            padding: 20px !important; 
            margin-bottom: 25px !important;
        }}
        
        .match-wrapper {{ display: flex; align-items: center; justify-content: space-between; width: 100%; gap: 15px; }}
        .player-box {{ flex: 1; text-align: center; }}
        .player-img {{ width: 100%; max-width: 180px; border-radius: 10px; }}
        .vs-text-styled {{ color: #ffd700 !important; font-size: 2.2rem !important; font-weight: 900 !important; text-shadow: 3px 3px 6px #000; }}
        .player-name-styled {{ font-size: 1.4rem !important; font-weight: 900 !important; color: #ffd700 !important; text-shadow: 3px 3px 6px #000; }}
        
        /* Digital Timer Styling */
        .digital-timer {{
            background-color: rgba(0, 0, 0, 0.85);
            border: 2px solid #ffd700;
            border-radius: 8px;
            font-family: 'Courier New', Courier, monospace;
            padding: 6px 15px;
            display: inline-block;
            margin-bottom: 15px;
        }}

        /* Buttons */
        div.stButton > button {{
            background-color: #ffd700 !important;
            color: #000 !important;
            font-weight: bold !important;
            border-radius: 12px !important;
            height: 3.8em !important;
            border: none !important;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

apply_pro_styling()

# --- Logic continues as before ---
# (Rest of your app code here: Session State, Sidebar login, Pages etc.)
