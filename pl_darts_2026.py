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
    st.session_state['cookie_manager'] = stx.CookieManager(key="pdc_pl_v7_locked")
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

# --- 4. STYLING (Professional BetMGM + White Player Names) ---
st.markdown("""
    <style>
    .stApp { 
        background: linear-gradient(rgba(0,0,0,0.85), rgba(0,0,0,0.85)), 
                    url("https://cdn.images.express.co.uk/img/dynamic/4/590x/secondary/5856693.jpg?r=1735554407217"); 
        background-size: cover; background-attachment: fixed; 
    }
    [data-testid="stSidebar"], [data-testid="stSidebarContent"] {
        background-color: #111111 !important; border-right: 1px solid #C4B454;
    }
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] p, [data-testid="stSidebar"] label {
        color: #C4B454 !important; font-weight: bold;
    }
    /* Login button text */
    [data-testid="stSidebar"] button p {
        color: #000000 !important; font-weight: 900 !important;
    }
    .night-header {
        text-align: center; color: #C4B454 !important; font-size: 1.5rem;
        font-weight: bold; text-transform: uppercase; margin-bottom: 20px;
    }
    .pl-card { 
        border: 1px solid #C4B454; border-radius: 12px; 
        background: rgba(20, 20, 20, 0.95); padding: 15px; margin-bottom: 15px;
    }
    .player-name-container {
        min-height: 3em; display: flex; align-items: center;
        justify-content: center; margin-top: 8px;
    }
    /* Player Names Back to White */
    .player-name-container p { color: white !important; font-weight: bold; }
    
    h1, h2, h3 { color: #C4B454 !important; text-transform: uppercase; letter-spacing: 1px; }
    div[data-baseweb="select"] > div {
        background-color: #1c1c1c !important; color: white !important;
        border: 1px solid #C4B454 !important; border-radius: 8px !important;
    }
    div.stButton > button {
        background: #C4B454 !important; color: #000000 !important;
        font-weight: 900 !important; border: none !important;
        width: 100% !important; border-radius: 8px !important;
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

# --- 6. RENDER MATCH FUNCTION (Updated Select Winner Text) ---
def render_match(p1, p2, key, disabled=False):
    img1 = img_lookup.get(p1, "https://via.placeholder.com/150")
    img2 = img_lookup.get(p2, "https://via.placeholder.com/150")
    
    st.markdown(f"""
        <div class="pl-card">
            <div style="display: flex; justify-content: space-around; align-items: flex-start; margin-bottom: 15px;">
                <div style="text-align: center; width: 45%;">
                    <img src="{img1}" style="width: 100%; max-width: 90px; border-radius: 10px;">
                    <div class="player-name-container"><p style="font-size: 0.85rem; margin:0;">{p1}</p></div>
                </div>
                <div style="color: #C4B454; font-size: 1.4rem; font-weight: 900; margin-top: 30px;">VS</div>
                <div style="text-align: center; width: 45%;">
                    <img src="{img2}" style="width: 100%; max-width: 90px; border-radius: 10px;">
                    <div class="player-name-container"><p style="font-size: 0.85rem; margin:0;">{p2}</p></div>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    winner = st.selectbox(f"Winner: {p1} vs {p2}", ["Select Winner", p1, p2], key=key, label_visibility="collapsed", disabled=disabled)
    return winner

# --- 7. MAIN APP LOGIC ---
if st.session_state['username'] == "":
    st.markdown("<h1 style='text-align: center;'>Welcome to the 2026 Premier League Predictor</h1>", unsafe_allow_html=True)
    st.info("Please login on the sidebar to enter your predictions.")
else:
    players_df = get_data("Players")
    img_lookup = dict(zip(players_df['Name'], players_df['Image_URL']))
    admin_df = get_data("PL_2026_Admin")
    admin_df.columns = admin_df.columns.str.strip()
    
    if not admin_df.empty:
        night_data = admin_df.iloc[0]
        st.markdown(f"<h1 style='text-align: center;'>📍 {night_data['Venue']}</h1>", unsafe_allow_html=True)
        st.markdown(f"<div class='night-header'>{night_data['Night']}</div>", unsafe_allow_html=True)

        # CHECK FOR PREVIOUS SUBMISSION & CUTOFF
        subs_df = get_data("User_Submissions")
        has_submitted = not subs_df[(subs_df['Username'] == st.session_state['username']) & (subs_df['Night'] == night_data['Night'])].empty
        
        # Logic for Cutoff Time (Expects a 'Cutoff' column in PL_2026_Admin format 'YYYY-MM-DD HH:MM')
        is_past_cutoff = False
        if 'Cutoff' in admin_df.columns:
            cutoff_val = datetime.strptime(str(night_data['Cutoff']), "%Y-%m-%d %H:%M")
            if datetime.now() > cutoff_val:
                is_past_cutoff = True

        lock_app = has_submitted or is_past_cutoff

        if has_submitted:
            st.warning("⚠️ You have already submitted your bracket for this night. Entries are locked.")
        elif is_past_cutoff:
            st.error("🔒 The cutoff time for this night has passed. Submissions are closed.")

        st.markdown("### 1️⃣ Quarter Finals")
        qf1w = render_match(night_data['QF1-P1'], night_data['QF1-P2'], "qf1", disabled=lock_app)
        qf2w = render_match(night_data['QF2-P1'], night_data['QF2-P2'], "qf2", disabled=lock_app)
        qf3w = render_match(night_data['QF3-P1'], night_data['QF3-P2'], "qf3", disabled=lock_app)
        qf4w = render_match(night_data['QF4-P1'], night_data['QF4-P2'], "qf4", disabled=lock_app)

        if all(x != "Select Winner" for x in [qf1w, qf2w, qf3w, qf4w]):
            st.divider()
            st.markdown("### 2️⃣ Semi Finals")
            sf1w = render_match(qf1w, qf2w, "sf1", disabled=lock_app)
            sf2w = render_match(qf3w, qf4w, "sf2", disabled=lock_app)

            if all(x != "Select Winner" for x in [sf1w, sf2w]):
                st.divider()
                st.markdown("### 🏆 The Final")
                finalw = render_match(sf1w, sf2w, "final", disabled=lock_app)

                if finalw != "Select Winner" and not lock_app:
                    if st.button("SUBMIT PREDICTIONS"):
                        new_row = pd.DataFrame([{
                            "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
                            "Username": st.session_state['username'],
                            "Night": night_data['Night'],
                            "QF1": qf1w, "QF2": qf2w, "QF3": qf3w, "QF4": qf4w,
                            "SF1": sf1w, "SF2": sf2w, "Final": finalw
                        }])
                        conn.update(spreadsheet=URL, worksheet="User_Submissions", data=pd.concat([subs_df, new_row], ignore_index=True))
                        st.success("Predictions Locked In Successfully!")
                        time.sleep(2)
                        st.rerun()
    else:
        st.warning("Admin is currently updating the next night's matches.")
