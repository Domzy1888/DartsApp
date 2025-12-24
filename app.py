import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# 1. Page Configuration
st.set_page_config(page_title="Darts Predictor Pro", page_icon="🎯", layout="wide")

# 2. Connection to Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)
URL = st.secrets["connections"]["gsheets"]["spreadsheet"]

# 3. MOBILE-OPTIMIZED FORCED STYLING
def apply_pro_styling():
    st.markdown(
        """
        <style>
        /* 1. Force the app to stay dark regardless of phone settings */
        :root {
            --primary-color: #ffd700;
            --background-color: #0e1117;
            --secondary-background-color: #262730;
            --text-color: #ffffff;
        }

        /* 2. Background Fix for Mobile (No more white background) */
        .stApp {
            background: linear-gradient(rgba(0,0,0,0.85), rgba(0,0,0,0.85)), 
                        url("https://images.unsplash.com/photo-1547427735-33750bb20671?q=80&w=2000");
            background-size: cover;
            background-position: center;
            background-attachment: scroll !important; /* Fixed breaks on iPhone Safari */
        }

        /* 3. Kill the Blue Text in Sidebar */
        [data-testid="stSidebarContent"] {
            background-color: #111111 !important;
        }
        
        [data-testid="stSidebar"] label p, [data-testid="stSidebar"] p {
            color: white !important;
            font-weight: bold !important;
            font-size: 1.1rem !important;
        }
        
        /* Highlight the selected radio button text in gold */
        [data-testid="stSidebar"] div[role="radiogroup"] label {
            color: #ffd700 !important;
        }

        /* 4. Match Card Styling */
        .match-card {
            background-color: rgba(35, 35, 35, 0.9) !important; 
            border: 2px solid #ffd700 !important;
            padding: 15px;
            border-radius: 15px;
            margin-bottom: 20px;
            text-align: center;
            color: white !important;
        }

        .player-label {
            font-size: 1.2rem;
            font-weight: bold;
            color: #ffffff !important;
            margin-top: 5px;
        }

        .vs-text {
            color: #ffd700 !important;
            font-size: 2rem;
            font-weight: 900;
            text-shadow: 1px 1px 2px black;
        }
        
        /* Force dropdowns to stay dark on mobile light mode */
        div[data-baseweb="select"] > div {
            background-color: #1a1a1a !important;
            color: white !important;
            border: 1px solid #444 !important;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

apply_pro_styling()

# 4. Session State for Login
if 'username' not in st.session_state:
    st.session_state['username'] = ""

# --- SIDEBAR: AUTHENTICATION ---
st.sidebar.title("🎯 PDC WORLD CHAMPS")
if st.session_state['username'] == "":
    auth_mode = st.sidebar.radio("Entry", ["Login", "Register"])
    if auth_mode == "Register":
        new_user = st.sidebar.text_input("New Username").strip()
        new_pwd = st.sidebar.text_input("New Password", type="password")
        if st.sidebar.button("Create Account"):
            user_df = conn.read(spreadsheet=URL, worksheet="Users", ttl=0)
            if new_user in user_df['Username'].values:
                st.sidebar.error("Taken!")
            else:
                reg_df = pd.DataFrame([{"Username": new_user, "Password": new_pwd}])
                conn.update(spreadsheet=URL, worksheet="Users", data=pd.concat([user_df, reg_df], ignore_index=True))
                st.sidebar.success
