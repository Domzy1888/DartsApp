import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import time
from datetime import datetime

###############################################################################
##### SECTION 1: PAGE CONFIG & SESSION INITIALIZATION                     #####
###############################################################################
st.set_page_config(page_title="PDC PL Predictor 2026", page_icon="🎯", layout="wide")

if 'username' not in st.session_state:
    st.session_state['username'] = ""

###############################################################################
##### SECTION 2: DATA CONNECTION & LOAD FUNCTIONS                         #####
###############################################################################
conn = st.connection("gsheets", type=GSheetsConnection)
URL = st.secrets["connections"]["gsheets"]["spreadsheet"]

@st.cache_data(ttl=2)
def get_data(worksheet):
    try:
        df = conn.read(spreadsheet=URL, worksheet=worksheet, ttl=0)
        df.columns = df.columns.str.strip() # Remove accidental spaces in headers
        return df.dropna(how='all')
    except Exception:
        return pd.DataFrame()

###############################################################################
##### SECTION 3: CSS STYLING (BetMGM Theme)                               #####
###############################################################################
st.markdown(f"""
    <style>
    .stApp {{ 
        background: linear-gradient(rgba(0,0,0,0.8), rgba(0,0,0,0.8)), 
                    url("https://i.postimg.cc/d1kXbbDk/2025PLFinal-Gen-View.jpg"); 
        background-size: cover; background-attachment: fixed; 
    }}
    [data-testid="stSidebar"], [data-testid="stSidebarContent"] {{
        background-color: #111111 !important; border-right: 1px solid #C4B454;
    }}
    .night-header {{ text-align: center; color: #C4B454 !important; font-size: 1.8rem; font-weight: 900; text-transform: uppercase; margin-bottom: 5px; }}
    .pl-card {{ border: 1px solid #C4B454; border-radius: 12px; background: rgba(20, 20, 20, 0.95); padding: 15px; margin-bottom: 15px; }}
    .player-name-container p {{ color: white !important; font-weight: bold; text-align: center; }}
    h1, h2, h3 {{ color: #C4B454 !important; text-transform: uppercase; }}
    div.stButton > button {{ background: #C4B454 !important; color: #000000 !important; font-weight: 900 !important; border: none; width: 100%; }}
    div[data-baseweb="select"] > div {{ background-color: #1c1c1c !important; color: white !important; border: 1px solid #C4B454 !important; }}
    </style>
""", unsafe_allow_html=True)

###############################################################################
##### SECTION 4: HELPER FUNCTIONS (MATCH RENDERER)                         #####
###############################################################################
def render_match(p1, p2, key, img_lookup, disabled=False):
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
    return st.selectbox(f"Winner: {p1} vs {p2}", ["Select Winner", p1, p2], key=key, label_visibility="collapsed", disabled=disabled)

###############################################################################
##### SECTION 5: SIDEBAR NAVIGATION & LOGIN                               #####
###############################################################################
st.sidebar.title("🎯 PL PREDICTOR 2026")
if st.session_state['username'] == "":
    u_attempt = st.sidebar.text_input("Username")
    p_attempt = st.sidebar.text_input("Password", type="password")
    if st.sidebar.button("Login"):
        u_df = get_data("Users")
        if not u_df.empty:
            match = u_df[(u_df['Username'] == u_attempt) & (u_df['Password'].astype(str) == str(p_attempt))]
            if not match.empty:
                st.session_state['username'] = u_attempt
                st.rerun()
            else: st.sidebar.error("Invalid Credentials")
else:
    st.sidebar.write(f"Logged in: **{st.session_state['username']}**")
    menu = st.sidebar.radio("NAVIGATE", ["Matches", "Leaderboard", "Rival Watch", "Highlights", "Admin"])
    if st.sidebar.button("Logout"):
        st.session_state['username'] = ""
        st.rerun()

###############################################################################
##### SECTION 6: DATA LOADING & WELCOME MESSAGE                           #####
###############################################################################
if st.session_state['username'] == "":
    st.markdown("<h1 style='text-align: center;'>Welcome to the 2026 Premier League Predictor</h1>", unsafe_allow_html=True)
    st.info("Please login on the sidebar to enter your predictions.")
else:
    players_df = get_data("Players")
    admin_df = get_data("PL_2026_Admin")
    subs_df = get_data("User_Submissions")
    
    img_lookup = {}
    if not players_df.empty:
        img_lookup = dict(zip(players_df['Name'], players_df['Image_URL']))

    ###########################################################################
    ##### SECTION 7: MATCHES PAGE LOGIC (RELIABLE FULL LAYOUT)            #####
    ###########################################################################
    if menu == "Matches":
        if not admin_df.empty:
            night_choice = st.selectbox("Select Night", admin_df['Night'].unique())
            night_data = admin_df[admin_df['Night'] == night_choice].iloc[0]
            
            st.markdown(f"<h1 style='text-align: center;'>📍 {night_data['Venue']}</h1>", unsafe_allow_html=True)
            st.markdown(f"<div class='night-header'>{night_data['Night']}</div>", unsafe_allow_html=True)

            # Check Cutoff
            is_locked = False
            try:
                cutoff_dt = pd.to_datetime(night_data['Cutoff'])
                if datetime.now() > cutoff_dt:
                    is_locked = True
                    st.error("🔒 Submissions are now closed for this night.")
            except: pass

            # Check existing sub
            user_sub = subs_df[(subs_df['Username'] == st.session_state['username']) & (subs_df['Night'] == night_choice)]
            if not user_sub.empty: 
                st.warning("✅ You have already submitted predictions.")
                is_locked = True

            # BRACKET - 4 Quarter Finals
            st.markdown("### 1️⃣ Quarter Finals")
            qf1 = render_match(night_data['QF1-P1'], night_data['QF1-P2'], f"q1_{night_choice}", img_lookup, is_locked)
            qf2 = render_match(night_data['QF2-P1'], night_data['QF2-P2'], f"q2_{night_choice}", img_lookup, is_locked)
            qf3 = render_match(night_data['QF3-P1'], night_data['QF3-P2'], f"q3_{night_choice}", img_lookup, is_locked)
            qf4 = render_match(night_data['QF4-P1'], night_data['QF4-P2'], f"q4_{night_choice}", img_lookup, is_locked)

            # 2 Semi Finals
            st.divider()
            st.markdown("### 2️⃣ Semi Finals")
            sf1_opt = [qf1, qf2] if "Select Winner" not in [qf1, qf2] else ["Select Winner"]
            sf2_opt = [qf3, qf4] if "Select Winner" not in [qf3, qf4] else ["Select Winner"]
            
            sf1 = render_match(sf1_opt[0], sf1_opt[-1], f"s1_{night_choice}", img_lookup, is_locked)
            sf2 = render_match(sf2_opt[0], sf2_opt[-1], f"s2_{night_choice}", img_lookup, is_locked)

            # The Final
            st.divider()
            st.markdown("### 🏆 The Final")
            f_opt = [sf1, sf2] if "Select Winner" not in [sf1, sf2] else ["Select Winner"]
            final = render_match(f_opt[0], f_opt[-1], f"f_{night_choice}", img_lookup, is_locked)

            # Submit Button (Only shows if all picked and not locked)
            if not is_locked:
                if all(x != "Select Winner" for x in [qf1, qf2, qf3, qf4, sf1, sf2, final]):
                    if st.button("LOCK PREDICTIONS"):
                        new_row = pd.DataFrame([{
                            "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
                            "Username": st.session_state['username'],
                            "Night": night_choice,
                            "QF1": qf1, "QF2": qf2, "QF3": qf3, "QF4": qf4,
                            "SF1": sf1, "SF2": sf2, "Final": final
                        }])
                        conn.update(spreadsheet=URL, worksheet="User_Submissions", data=pd.concat([subs_df, new_row], ignore_index=True))
                        st.success("Predictions Saved!"); time.sleep(1); st.rerun()
                else:
                    st.info("Complete your bracket to enable the submit button.")

    ###########################################################################
    ##### SECTION 8: OTHER PAGES (LEADERBOARD / RIVAL WATCH)              #####
    ###########################################################################
    elif menu == "Leaderboard":
        st.title("🏆 Leaderboard")
        # Same logic as before...
    
    elif menu == "Admin":
        if st.session_state['username'].lower() == "admin":
            st.title("⚙️ Admin")
            # Same logic as before...

