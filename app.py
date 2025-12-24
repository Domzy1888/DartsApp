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
        :root {
            --primary-color: #ffd700;
            --background-color: #0e1117;
            --secondary-background-color: #262730;
            --text-color: #ffffff;
        }
        .stApp {
            background: linear-gradient(rgba(0,0,0,0.85), rgba(0,0,0,0.85)), 
                        url("https://images.unsplash.com/photo-1547427735-33750bb20671?q=80&w=2000");
            background-size: cover;
            background-position: center;
            background-attachment: scroll !important;
        }
        [data-testid="stSidebarContent"] {
            background-color: #111111 !important;
        }
        [data-testid="stSidebar"] label p, [data-testid="stSidebar"] p {
            color: white !important;
            font-weight: bold !important;
            font-size: 1.1rem !important;
        }
        [data-testid="stSidebar"] div[role="radiogroup"] label {
            color: #ffd700 !important;
        }
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
                st.sidebar.success("Success! Please Login.")
    
    else:  # This is the "Login" block
        user_attempt = st.sidebar.text_input("Username").strip()
        pwd_attempt = st.sidebar.text_input("Password", type="password")
        if st.sidebar.button("Sign In"):
            user_df = conn.read(spreadsheet=URL, worksheet="Users", ttl=0)
            # Verify user exists and password matches
            match = user_df[(user_df['Username'] == user_attempt) & (user_df['Password'].astype(str) == str(pwd_attempt))]
            if not match.empty:
                st.session_state['username'] = user_attempt
                st.rerun()
            else:
                st.sidebar.error("Invalid Credentials")

else:
    st.sidebar.write(f"Logged in: **{st.session_state['username']}**")
    if st.sidebar.button("Logout"):
        st.session_state['username'] = ""
        st.rerun()

st.sidebar.divider()
page = st.sidebar.radio("Navigate", ["Predictions", "Leaderboard", "Rival Watch", "Admin"])

# --- PAGE: PREDICTIONS ---
if page == "Predictions":
    if st.session_state['username'] == "":
        st.warning("Please sign in to view matchups.")
    else:
        st.title("🏹 Today's Matchups")
        
        matches_df = conn.read(spreadsheet=URL, worksheet="Matches", ttl=60)
        preds_df = conn.read(spreadsheet=URL, worksheet="Predictions", ttl=0)
        results_df = conn.read(spreadsheet=URL, worksheet="Results", ttl=0)

        for index, row in matches_df.iterrows():
            m_id = str(row['Match_ID'])
            is_closed = m_id in results_df['Match_ID'].astype(str).values if not results_df.empty else False
            already_done = not preds_df[(preds_df['Username'] == st.session_state['username']) & (preds_df['Match_ID'].astype(str) == m_id)].empty if not preds_df.empty else False

            st.markdown('<div class="match-card">', unsafe_allow_html=True)
            c1, c2, c3 = st.columns([2, 1, 2])
            
            with c1:
                img1 = row['P1_Image'] if pd.notna(row['P1_Image']) else "https://via.placeholder.com/150"
                st.image(img1, width=120)
                st.markdown(f"<div class='player-label'>{row['Player1']}</div>", unsafe_allow_html=True)
            with c2:
                st.markdown("<div style='height: 30px;'></div>", unsafe_allow_html=True)
                st.markdown("<div class='vs-text'>VS</div>", unsafe_allow_html=True)
            with c3:
                img2 = row['P2_Image'] if pd.notna(row['P2_Image']) else "https://via.placeholder.com/150"
                st.image(img2, width=120)
                st.markdown(f"<div class='player-label'>{row['Player2']}</div>", unsafe_allow_html=True)

            st.markdown("<hr style='border-top: 1px solid rgba(255,255,255,0.1);'>", unsafe_allow_html=True)

            if is_closed:
                st.info("🎯 RESULTS ARE IN")
            elif already_done:
                st.success("LOCKED IN ✅")
            else:
                sc1, sc2, sc3 = st.columns([1, 1, 1])
                with sc1: s1 = st.selectbox(f"{row['Player1']} Score", range(11), key=f"s1_{m_id}")
