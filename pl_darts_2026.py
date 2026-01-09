import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import time
from datetime import datetime
import extra_streamlit_components as stx

# 1. Page Configuration
st.set_page_config(page_title="PDC PL Predictor 2026", page_icon="🎯", layout="wide")

# --- 2. SESSION INITIALIZATION ---
if 'username' not in st.session_state:
    st.session_state['username'] = ""

# --- 3. CONNECTION SETUP ---
conn = st.connection("gsheets", type=GSheetsConnection)
URL = st.secrets["connections"]["gsheets"]["spreadsheet"]

@st.cache_data(ttl=2)
def get_data(worksheet):
    try:
        df = conn.read(spreadsheet=URL, worksheet=worksheet, ttl=0)
        return df.dropna(how='all')
    except:
        return pd.DataFrame()

# --- 4. THE BETMGM STYLING ---
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
    .player-name-container p {{ color: white !important; font-weight: bold; text-align: center; }}
    h1, h2, h3 {{ color: #C4B454 !important; text-transform: uppercase; letter-spacing: 1px; }}
    
    /* BetMGM Leaderboard Style */
    .betmgm-table {{ width: 100%; border-collapse: collapse; background: rgba(20,20,20,0.9); border-radius: 10px; overflow: hidden; color: white; }}
    .betmgm-table th {{ background: #C4B454; color: black; padding: 12px; text-align: left; text-transform: uppercase; font-weight: 900; }}
    .betmgm-table td {{ padding: 12px; border-bottom: 1px solid #333; }}
    .betmgm-table tr:hover {{ background: rgba(196, 180, 84, 0.1); }}
    
    div[data-baseweb="select"] > div {{ background-color: #1c1c1c !important; color: white !important; border: 1px solid #C4B454 !important; }}
    div.stButton > button {{ background: #C4B454 !important; color: #000000 !important; font-weight: 900 !important; width: 100% !important; border: none; }}
    </style>
""", unsafe_allow_html=True)

# --- 5. RENDER MATCH FUNCTION ---
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
    return st.selectbox(f"Winner: {p1} vs {p2}", ["Select Winner", p1, p2], key=key, label_visibility="collapsed", disabled=disabled)

# --- 6. SIDEBAR NAVIGATION ---
st.sidebar.title("🎯 PL 2026 PREDICTOR")
if st.session_state['username'] == "":
    u_attempt = st.sidebar.text_input("Username")
    p_attempt = st.sidebar.text_input("Password", type="password")
    if st.sidebar.button("Login"):
        u_df = get_data("Users")
        match = u_df[(u_df['Username'] == u_attempt) & (u_df['Password'].astype(str) == str(p_attempt))]
        if not match.empty:
            st.session_state['username'] = u_attempt
            st.rerun()
else:
    st.sidebar.write(f"User: **{st.session_state['username']}**")
    menu = st.sidebar.radio("NAVIGATE", ["Matches", "Leaderboard", "Rival Watch", "Highlights", "Admin"])
    if st.sidebar.button("Logout"):
        st.session_state['username'] = ""
        st.rerun()

# --- 7. MAIN APP LOGIC ---
if st.session_state['username'] == "":
    st.markdown("<h1 style='text-align: center;'>Please login to continue</h1>", unsafe_allow_html=True)
else:
    players_df = get_data("Players")
    img_lookup = dict(zip(players_df['Name'], players_df['Image_URL']))
    admin_df = get_data("PL_2026_Admin")
    subs_df = get_data("User_Submissions")

    if menu == "Matches":
        night_choice = st.selectbox("Select Night", admin_df['Night'].unique())
        night_data = admin_df[admin_df['Night'] == night_choice].iloc[0]
        st.markdown(f"<h1 style='text-align: center;'>📍 {night_data['Venue']}</h1>", unsafe_allow_html=True)
        st.markdown(f"<div class='night-header'>{night_data['Night']}</div>", unsafe_allow_html=True)

        # Cutoff Logic
        cutoff_dt = datetime.strptime(str(night_data['Cutoff']), "%Y-%m-%d %H:%M")
        is_locked = datetime.now() > cutoff_dt
        if is_locked: st.error("🔒 Submissions closed.")
        
        user_sub = subs_df[(subs_df['Username'] == st.session_state['username']) & (subs_df['Night'] == night_choice)]
        if not user_sub.empty: 
            st.warning("✅ Predictions submitted.")
            is_locked = True

        # Render Bracket (Simplified for brevity, re-insert full render logic)
        qf1w = render_match(night_data['QF1-P1'], night_data['QF1-P2'], f"qf1_{night_choice}", disabled=is_locked)
        # ... (Repeat for QF2-QF4, SF1-SF2, Final)
        # If all selected, show Submit button

    elif menu == "Leaderboard":
        st.title("🏆 Season Standings")
        lb_df = get_data("PL_Leaderboard")
        if not lb_df.empty:
            lb_df = lb_df.sort_values(by="Total", ascending=False)
            # Custom HTML table for BetMGM feel
            html = "<table class='betmgm-table'><tr><th>Rank</th><th>Username</th><th>Total Points</th></tr>"
            for i, row in enumerate(lb_df.itertuples(), 1):
                html += f"<tr><td>{i}</td><td>{row.Username}</td><td>{row.Total}</td></tr>"
            html += "</table>"
            st.markdown(html, unsafe_allow_html=True)

    elif menu == "Admin":
        if st.session_state['username'].lower() == "admin":
            st.subheader("⚙️ Scoring Engine")
            res_night = st.selectbox("Update Results for:", admin_df['Night'].unique())
            n_row = admin_df[admin_df['Night'] == res_night].iloc[0]
            
            # (Winner Selectors as built in previous turn)
            # AQF1, AQF2... AFINAL selectors here...

            if st.button("CALCULATE & UPDATE SHEET"):
                lb_df = get_data("PL_Leaderboard")
                # Scoring Logic comparison against User_Submissions
                # 1. Calculate points for THIS night
                # 2. Add to existing Total in lb_df
                # 3. Update Sheets:
                # conn.update(spreadsheet=URL, worksheet="PL_Leaderboard", data=updated_lb_df)
                st.success(f"Sheet updated for {res_night}!")
        else:
            st.error("Admin Access Only.")
