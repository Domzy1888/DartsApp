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

# 4. Pro Styling - STABLE VERSION
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
        
        /* SIDEBAR CONTENT */
        [data-testid="stSidebarContent"] {{ background-color: #111111 !important; }}
        
        /* The Match Card - 0.5 Gradient & Paddy Power URL */
        [data-testid="stVerticalBlock"] > div:has(.match-wrapper) {{
            border: 2px solid #ffd700 !important;
            border-radius: 20px !important;
            background-image: linear-gradient(rgba(0,0,0,0.5), rgba(0,0,0,0.5)), 
                              url("https://news.paddypower.com/assets/uploads/2023/12/Paddy-Power-World-Darts-Championship.jpg");
            background-size: cover;
            background-position: center;
            padding: 20px !important; 
            margin-bottom: 25px !important;
            box-shadow: 0 10px 30px rgba(0,0,0,0.6);
        }}
        
        .match-wrapper {{ display: flex; align-items: center; justify-content: space-between; width: 100%; gap: 15px; }}
        .player-box {{ flex: 1; text-align: center; }}
        
        .player-img {{ 
            width: 100%; 
            max-width: 180px; 
            border-radius: 10px; 
            border: none !important;
        }}
        
        .vs-text-styled {{ 
            color: #ffd700 !important; 
            font-size: 2.2rem !important; 
            font-weight: 900 !important; 
            text-shadow: 3px 3px 6px #000; 
        }}
        
        .player-name-styled {{ 
            font-size: 1.4rem !important; font-weight: 900 !important; 
            color: #ffd700 !important; margin-top: 10px;
            text-shadow: 3px 3px 6px #000;
        }}
        
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
            height: 3.8em !important;
        }}
        
        div[data-baseweb="select"] > div {{ background-color: #222 !important; color: white !important; border: 1px solid #444 !important; }}
        </style>
        """,
        unsafe_allow_html=True
    )

apply_pro_styling()

# --- Logic follows ---
if 'username' not in st.session_state: st.session_state['username'] = ""
if 'temp_preds' not in st.session_state: st.session_state.temp_preds = {}

st.sidebar.title("🎯 PDC PREDICTOR")
if st.session_state['username'] == "":
    auth_mode = st.sidebar.radio("Entry", ["Login", "Register"])
    u_attempt = st.sidebar.text_input("Username").strip()
    p_attempt = st.sidebar.text_input("Password", type="password")
    if st.sidebar.button("Go"):
        u_df = get_data("Users")
        if auth_mode == "Login":
            match = u_df[(u_df['Username'] == u_attempt) & (u_df['Password'].astype(str) == str(p_attempt))]
            if not match.empty:
                st.session_state['username'] = u_attempt
                st.rerun()
            else: st.sidebar.error("Invalid Login")
        else:
            new_reg = pd.DataFrame([{"Username": u_attempt, "Password": p_attempt}])
            conn.update(spreadsheet=URL, worksheet="Users", data=pd.concat([u_df, new_reg], ignore_index=True))
            st.sidebar.success("Registered! Login now.")
else:
    st.sidebar.write(f"Logged in: **{st.session_state['username']}**")
    if st.sidebar.button("Logout"):
        st.session_state['username'] = ""; st.session_state.temp_preds = {}; st.rerun()

st.sidebar.divider()
page = st.sidebar.radio("Navigate", ["Predictions", "Leaderboard", "Rival Watch", "Admin"])

# --- PAGE: PREDICTIONS ---
if page == "Predictions":
    if st.session_state['username'] == "":
        st.warning("Please sign in to view matchups.")
    else:
        st.title("Upcoming Matches")
        m_df = get_data("Matches"); p_df = get_data("Predictions"); r_df = get_data("Results")
        now = datetime.now()
        if 'Date' in m_df.columns:
            m_df['Date_Parsed'] = pd.to_datetime(m_df['Date'])
            unique_dates = sorted(m_df['Date_Parsed'].dt.date.unique())
            view_date = st.selectbox("📅 Select Match Day", unique_dates, 
                                     index=unique_dates.index(now.date()) if now.date() in unique_dates else 0)
            display_df = m_df[m_df['Date_Parsed'].dt.date == view_date]
        else: display_df = m_df

        open_matches_list = []
        for _, row in display_df.iterrows():
            m_id = str(row['Match_ID'])
            if m_id in r_df['Match_ID'].astype(str).values if not r_df.empty else False: continue
            user_preds = p_df[p_df['Username'] == st.session_state['username']]
            already_done = m_id in user_preds['Match_ID'].astype(str).values if not user_preds.empty else False
            match_time = pd.to_datetime(row['Date'])
            seconds_left = (match_time - now).total_seconds()
            is_locked_by_time = seconds_left < 0

            with st.container():
                if not already_done and not is_locked_by_time:
                    h, rem = divmod(int(seconds_left), 3600); m, _ = divmod(rem, 60)
                    t_clr = "#00FF00" if seconds_left > 1800 else "#FFA500" if seconds_left > 600 else "#FF0000"
                    st.markdown(f'<div style="text-align: center;"><div class="digital-timer" style="color: {t_clr};">⏱️ {h:02d}:{m:02d} TO START</div></div>', unsafe_allow_html=True)
                elif is_locked_by_time and not already_done:
                    st.markdown(f'<div style="text-align: center;"><div class="digital-timer" style="color: #ff4b4b;">🔒 ENTRY CLOSED</div></div>', unsafe_allow_html=True)

                p1_img = row['P1_Image'] if pd.notna(row['P1_Image']) else "https://via.placeholder.com/150"
                p2_img = row['P2_Image'] if pd.notna(row['P2_Image']) else "https://via.placeholder.com/150"
                
                st.markdown(f"""
                    <div class="match-wrapper">
                        <div class="player-box">
                            <img src="{p1_img}" class="player-img">
                            <div class="player-name-styled">{row['Player1']}</div>
                        </div>
                        <div class="vs-text-styled">VS</div>
                        <div class="player-box">
                            <img src="{p2_img}" class="player-img">
                            <div class="player-name-styled">{row['Player2']}</div>
                        </div>
                    </div>
                """, unsafe_allow_html=True)

                if already_done: st.success("Locked In ✅")
                elif not is_locked_by_time:
                    open_matches_list.append(m_id)
                    c1, c2 = st.columns(2)
                    with c1: s1 = st.selectbox(f"{row['Player1']}", range(11), key=f"s1_{m_id}")
                    with c2: s2 = st.selectbox(f"{row['Player2']}", range(11), key=f"s2_{m_id}")
                    st.session_state.temp_preds[m_id] = f"{s1}-{s2}"

        if open_matches_list:
            if st.button("🔒 LOCK ALL PREDICTIONS"):
                new_data = [{"Username": st.session_state['username'], "Match_ID": m_id, "Score": st.session_state.temp_preds.get(m_id, "0-0")} for m_id in open_matches_list]
                current_p = conn.read(spreadsheet=URL, worksheet="Predictions", ttl=0)
                conn.update(spreadsheet=URL, worksheet="Predictions", data=pd.concat([current_p, pd.DataFrame(new_data)], ignore_index=True))
                st.session_state.temp_preds = {}; st.cache_data.clear()
                st.success("Scores Locked!"); time.sleep(1.5); st.rerun()

# (Leaderboard, Rival Watch, Admin pages remain the same)
