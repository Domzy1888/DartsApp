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
    st.session_state['cookie_manager'] = stx.CookieManager(key="pdc_pl_cookie_manager_v2")
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

# --- 4. STYLING (Dark Sidebar & Fixed Cards) ---
st.markdown("""
    <style>
    /* 1. Main Background */
    .stApp { 
        background: linear-gradient(rgba(0,0,0,0.7), rgba(0,0,0,0.7)), 
                    url("https://cdn.images.express.co.uk/img/dynamic/4/590x/secondary/5856693.jpg?r=1735554407217"); 
        background-size: cover; 
        background-attachment: fixed; 
    }
    
    /* 2. Dark Sidebar Fix */
    [data-testid="stSidebar"], [data-testid="stSidebarContent"] {
        background-color: #111111 !important;
    }
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] p, [data-testid="stSidebar"] label {
        color: #ffd700 !important;
        font-weight: bold;
    }
    
    /* 3. Match Card Container */
    .pl-card { 
        border: 2px solid #ffd700; 
        border-radius: 15px; 
        background: rgba(0,0,0,0.8); 
        padding: 15px; 
        margin-bottom: 20px;
        min-height: 250px; /* Ensures enough space for content */
    }
    
    /* 4. Text & Titles */
    h1, h2, h3, p, label { color: white !important; font-weight: bold; }
    
    /* Custom Styling for Selectbox inside cards */
    div[data-baseweb="select"] {
        border-radius: 10px;
    }
    </style>
""", unsafe_allow_html=True)

# --- 5. AUTHENTICATION ---
st.sidebar.title("🎯 PL 2026 PREDICTOR")
if st.session_state['username'] == "":
    u_attempt = st.sidebar.text_input("Username")
    p_attempt = st.sidebar.text_input("Password", type="password")
    if st.sidebar.button("Login"):
        u_df = get_data("Users")
        match = u_df[(u_df['Username'] == u_attempt) & (u_df['Password'] == p_attempt)]
        if not match.empty:
            st.session_state['username'] = u_attempt
            st.rerun()
else:
    st.sidebar.write(f"Logged in: **{st.session_state['username']}**")
    if st.sidebar.button("Logout"):
        st.session_state['username'] = ""
        st.rerun()

# --- 6. RENDER MATCH FUNCTION (The Fix for the Layout) ---
def render_match(p1, p2, key):
    # Retrieve URLs from lookup
    img1 = img_lookup.get(p1, "https://via.placeholder.com/150")
    img2 = img_lookup.get(p2, "https://via.placeholder.com/150")
    
    # Start HTML Container
    st.markdown(f"""
        <div class="pl-card">
            <div style="display: flex; justify-content: space-around; align-items: center; margin-bottom: 15px;">
                <div style="text-align: center; width: 40%;">
                    <img src="{img1}" style="width: 100%; max-width: 80px; border-radius: 10px; border: 1px solid #ffd700;">
                    <p style="margin-top: 5px; font-size: 0.9rem; color: #ffd700 !important;">{p1}</p>
                </div>
                <div style="color: #ffd700; font-size: 1.2rem; font-weight: 900;">VS</div>
                <div style="text-align: center; width: 40%;">
                    <img src="{img2}" style="width: 100%; max-width: 80px; border-radius: 10px; border: 1px solid #ffd700;">
                    <p style="margin-top: 5px; font-size: 0.9rem; color: #ffd700 !important;">{p2}</p>
                </div>
            </div>
    """, unsafe_allow_html=True)
    
    # Place the selector inside the container
    winner = st.selectbox(f"Winner: {p1} vs {p2}", ["Select...", p1, p2], key=key)
    
    st.markdown("</div>", unsafe_allow_html=True)
    return winner

# --- 7. MAIN APP LOGIC ---
if st.session_state['username'] == "":
    st.title("Welcome to the 2026 Premier League Predictor")
    st.info("Please login on the sidebar to enter your bracket.")
else:
    # Get Player images for lookup
    players_df = get_data("Players")
    img_lookup = dict(zip(players_df['Name'], players_df['Image_URL']))
    
    # Get Admin Schedule
    admin_df = get_data("PL_2026_Admin")
    # Clean column names just in case
    admin_df.columns = admin_df.columns.str.strip()
    
    if not admin_df.empty:
        night_data = admin_df.iloc[0]
        st.title(f"📍 {night_data['Venue']}")
        st.subheader(f"{night_data['Night']} Bracket Entry")

        # QUARTER FINALS
        st.markdown("### 1️⃣ Quarter Finals (2 pts)")
        q_cols = st.columns(4)
        
        qf1w = q_cols[0].create_match = render_match(night_data['QF1-P1'], night_data['QF1-P2'], "qf1")
        qf2w = q_cols[1].create_match = render_match(night_data['QF2-P1'], night_data['QF2-P2'], "qf2")
        qf3w = q_cols[2].create_match = render_match(night_data['QF3-P1'], night_data['QF3-P2'], "qf3")
        qf4w = q_cols[3].create_match = render_match(night_data['QF4-P1'], night_data['QF4-P2'], "qf4")

        # SEMI FINALS
        if all(x != "Select..." for x in [qf1w, qf2w, qf3w, qf4w]):
            st.divider()
            st.markdown("### 2️⃣ Semi Finals (3 pts)")
            s_cols = st.columns(2)
            sf1w = s_cols[0].create_match = render_match(qf1w, qf2w, "sf1")
            sf2w = s_cols[1].create_match = render_match(qf3w, qf4w, "sf2")

            # FINAL
            if all(x != "Select..." for x in [sf1w, sf2w]):
                st.divider()
                st.markdown("### 🏆 The Final (5 pts)")
                f_cols = st.columns([1,2,1])
                finalw = f_cols[1].create_match = render_match(sf1w, sf2w, "final")

                # Submission
                if finalw != "Select...":
                    if st.button("🚀 SUBMIT 19-POINT BRACKET"):
                        new_row = pd.DataFrame([{
                            "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
                            "Username": st.session_state['username'],
                            "Night": night_data['Night'],
                            "QF1": qf1w, "QF2": qf2w, "QF3": qf3w, "QF4": qf4w,
                            "SF1": sf1w, "SF2": sf2w, "Final": finalw
                        }])
                        existing = get_data("User_Submissions")
                        conn.update(spreadsheet=URL, worksheet="User_Submissions", data=pd.concat([existing, new_row], ignore_index=True))
                        st.balloons()
                        st.success("Your predictions are locked in!")
                        time.sleep(2)
                        st.rerun()
    else:
        st.warning("Waiting for Admin to set up the next Nightly Bracket.")
