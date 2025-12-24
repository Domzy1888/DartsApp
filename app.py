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
        h1, h2, h3, p, span {{ color: white !important; }}
        
        /* SIDEBAR CONTENT */
        [data-testid="stSidebarContent"] {{ background-color: #111111 !important; }}
        
        /* STABLE SIDEBAR BUTTON FIX */
        /* We use transform scale to make it bigger without moving its 'home' position */
        [data-testid="stHeader"] {{
            background: transparent !important;
        }}

        /* Specifically targets the sidebar toggle button area */
        [data-testid="stSidebarCollapsedControl"] {{
            transform: scale(1.5) !important; /* Makes the button 50% larger */
            transform-origin: left center !important;
            margin-left: 20px !important;
            background-color: #ffd700 !important;
            border-radius: 8px !important;
            padding: 5px !important;
            border: 1px solid black !important;
        }}

        /* Make the icon inside pure black */
        [data-testid="stSidebarCollapsedControl"] svg {{
            fill: black !important;
            color: black !important;
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
        
        .digital-timer {{
            background-color: rgba(0, 0, 0, 0.85);
            border: 2px solid #ffd700;
            border-radius: 8px;
            font-family: 'Courier New', Courier, monospace;
            padding: 6px 15px;
            display: inline-block;
            margin-bottom: 15px;
        }}

        div.stButton > button {{
            background-color: #ffd700 !important;
            color: #000 !important;
            font-weight: bold !important;
            width: 100% !important;
            border-radius: 12px !important;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

apply_pro_styling()

# --- Rest of your code follows ---
