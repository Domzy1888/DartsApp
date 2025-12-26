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
    try:
        df = conn.read(spreadsheet=URL, worksheet=worksheet, ttl=0)
        return df.dropna(how='all') # Only drops rows that are 100% empty
    except:
        return pd.DataFrame()

# 4. Pro Styling (Corrected for Transparency and Visibility)
def apply_pro_styling():
    st.markdown(
        f"""
        <style>
        .stApp {{
            background: linear-gradient(rgba(0,0,0,0.6), rgba(0,0,0,0.6)), 
                        url("https://cdn.images.express.co.uk/img/dynamic/4/590x/secondary/5856693.jpg?r=1735554407217");
            background-size: cover; background-position: center; background-attachment: fixed;
        }}
        h1, h2, h3, p {{ color: white !important; font-weight: bold; }}
        [data-testid="stSidebarContent"] {{ background-color: #111111 !important; }}
        
        /* Transparent Table Fix - Keeping text white */
        [data-testid="stDataFrame"] {{
            background-color: rgba(0, 0, 0, 0.5) !important;
            border: 1px solid #ffd700;
            border-radius: 10px;
        }}
        
        /* Match Card Styling */
        .match-card-container {{
            border: 2px solid #ffd700;
            border-radius: 20px;
            background-image: linear-gradient(rgba(0,0,0,0.5), rgba(0,0,0,0.5)), 
                              url("https://news.paddypower.com/assets/uploads/2023/12/Paddy-Power-World-Darts-Championship.jpg");
            background-size: cover; background-position: center;
            padding: 20px; margin-bottom: 25px;
        }}
        
        .match-wrapper {{ display: flex; align-items: center; justify-content: space-between; width: 100%; gap: 15px; }}
        .player-box {{ flex: 1; text-align: center; }}
        .player-img {{ width: 100%; max-width: 180px; border-radius: 10px; border: 2px solid rgba(255,215,0,0.3); }}
        .vs-text-styled {{ color: #ffd700 !important; font-size: 2.2rem !important; font-weight: 900 !important; text-shadow: 2px 2px 4px #000; }}
        .player-name-styled {{ font-size: 1.4rem !important; font-weight: 900 !important; color: #ffd700 !important; text-shadow: 2px 2px 4px #000; }}
        
        div.stButton > button {{
            background-color: #ffd700 !important;
            color: #000 !important; font-weight: bold !important;
            width: 100% !important; border-radius: 12px !important; height: 3.5em !important;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

apply_pro_styling()

if 'username' not in st.session_state: st.session_state['username'] = ""
if 'temp_preds' not in st.session_state: st.session_state.temp_preds = {}

# --- SIDEBAR ---
st.sidebar.title("🎯 PDC PREDICTOR")
if st.session_state['username'] == "":
    auth_mode = st.sidebar.radio("Entry", ["Login", "Register"])
    u_attempt = st.sidebar.text_input("Username").strip()
    p_attempt = st.sidebar.text_input("Password", type="password")
    if st.sidebar.button("Go"):
        u_df = get_data("Users")
        if not u_df.empty:
            if auth_mode == "Login":
                match = u_df[(u_df['Username'].astype(str) == u_attempt) & (u_df['Password'].astype(str) == str(p_attempt))]
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
        m_df = get_data("Matches")
        p_df = get_data("Predictions")
        r_df = get_data("Results")
        now = datetime.now()

        if not m_df.empty and 'Date' in m_df.columns:
            m_df['Date_Parsed'] = pd.to_datetime(m_df['Date'], errors='coerce')
            m_df = m_df.dropna(subset=['Date_Parsed']) # Only drop rows with unreadable dates
            
            unique_dates = sorted(m_df['Date_Parsed'].dt.date.unique())
            if unique_dates:
                view_date = st.selectbox("📅 Select Match Day", unique_dates, 
                                         index=unique_dates.index(now.date()) if now.date() in unique_dates else 0)
                display_df = m_df[m_df['Date_Parsed'].dt.date == view_date]
                
                open_matches_list = []
                for _, row in display_df.iterrows():
                    m_id = str(row['Match_ID'])
                    # Check if result exists
                    if not r_df.empty and m_id in r_df['Match_ID'].astype(str).values: continue
                    
                    # Check if already predicted
                    already_done = False
                    if not p_df.empty:
                        already_done = not p_df[(p_df['Username'] == st.session_state['username']) & (p_df['Match_ID'].astype(str) == m_id)].empty

                    match_time = row['Date_Parsed']
                    is_locked = (match_time - now).total_seconds() < 0

                    # Use a custom div for the card to ensure styling applies
                    st.markdown(f"""
                        <div class="match-card-container">
                            <div class="match-wrapper">
                                <div class="player-box">
                                    <img src="{row.get('P1_Image', '')}" class="player-img">
                                    <div class="player-name-styled">{row.get('Player1', 'TBD')}</div>
                                </div>
                                <div class="vs-text-styled">VS</div>
                                <div class="player-box">
                                    <img src="{row.get('P2_Image', '')}" class="player-img">
                                    <div class="player-name-styled">{row.get('Player2', 'TBD')}</div>
                                </div>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)

                    if already_done: st.success("Locked In ✅")
                    elif not is_locked:
                        open_matches_list.append(m_id)
                        c1, c2 = st.columns(2)
                        with c1: s1 = st.selectbox(f"{row['Player1']}", range(11), key=f"s1_{m_id}")
                        with c2: s2 = st.selectbox(f"{row['Player2']}", range(11), key=f"s2_{m_id}")
                        st.session_state.temp_preds[m_id] = f"{s1}-{s2}"

                if open_matches_list:
                    if st.button("🔒 LOCK ALL PREDICTIONS"):
                        new_data = [{"Username": st.session_state['username'], "Match_ID": mid, "Score": st.session_state.temp_preds.get(mid, "0-0")} for mid in open_matches_list]
                        conn.update(spreadsheet=URL, worksheet="Predictions", data=pd.concat([p_df, pd.DataFrame(new_data)], ignore_index=True))
                        st.cache_data.clear(); st.success("Predictions Saved!"); time.sleep(1); st.rerun()

# --- PAGE: LEADERBOARD ---
elif page == "Leaderboard":
    st.title("🏆 Leaderboard")
    p_df = get_data("Predictions")
    r_df = get_data("Results")
    if not r_df.empty and not p_df.empty:
        merged = p_df.merge(r_df, on="Match_ID", suffixes=('_u', '_r'))
        def calc_pts(r):
            try:
                u1, u2 = map(int, str(r['Score_u']).split('-'))
                r1, r2 = map(int, str(r['Score_r']).split('-'))
                if u1 == r1 and u2 == r2: return 3
                if (u1 > u2 and r1 > r2) or (u1 < u2 and r1 < r2): return 1
            except: return 0
            return 0
        merged['Pts'] = merged.apply(calc_pts, axis=1)
        lb = merged.groupby('Username')['Pts'].sum().reset_index().sort_values('Pts', ascending=False)
        st.dataframe(lb, hide_index=True, width="stretch")
    else:
        st.info("No results recorded yet. Check back soon!")

# --- RIVAL WATCH ---
elif page == "Rival Watch":
    st.title("👀 Rival Watch")
    m_df = get_data("Matches")
    p_df = get_data("Predictions")
    if not m_df.empty and not p_df.empty:
        m_sel = st.selectbox("Pick a Match:", m_df['Match_ID'].astype(str) + ": " + m_df['Player1'] + " vs " + m_df['Player2'])
        mid = m_sel.split(":")[0]
        match_p = p_df[p_df['Match_ID'].astype(str) == mid].drop_duplicates('Username', keep='last')
        st.dataframe(match_p[['Username', 'Score']], hide_index=True, width="stretch")

# --- ADMIN ---
elif page == "Admin":
    st.title("⚙️ Admin Hub")
    if st.text_input("Admin Key", type="password") == "darts2025":
        m_df = get_data("Matches")
        if not m_df.empty:
            target = st.selectbox("Select Match", m_df['Match_ID'].astype(str) + ": " + m_df['Player1'] + " vs " + m_df['Player2'])
            c1, c2 = st.columns(2)
            with c1: r1 = st.selectbox("Actual P1", range(11))
            with c2: r2 = st.selectbox("Actual P2", range(11))
            if st.button("Finalize Result"):
                old_res = get_data("Results")
                new_res = pd.DataFrame([{"Match_ID": target.split(":")[0], "Score": f"{r1}-{r2}"}])
                conn.update(spreadsheet=URL, worksheet="Results", data=pd.concat([old_res, new_res], ignore_index=True))
                st.cache_data.clear(); st.success("Result Published!")
