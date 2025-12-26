import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import time
from datetime import datetime, timedelta

# 1. Page Configuration
st.set_page_config(page_title="PDC Predictor Pro", page_icon="🎯", layout="wide")

# 2. Connection
conn = st.connection("gsheets", type=GSheetsConnection)
URL = st.secrets["connections"]["gsheets"]["spreadsheet"]

# 3. Data Fetching
@st.cache_data(ttl=10)
def get_data(worksheet):
    try:
        df = conn.read(spreadsheet=URL, worksheet=worksheet, ttl=0)
        return df.dropna(how='all')
    except:
        return pd.DataFrame()

# 4. Global Styling (Pulsing Red Timer & Transparency)
st.markdown("""
    <style>
    @keyframes pulse-red {
        0% { color: #ff4b4b; opacity: 1; }
        50% { color: #ff0000; opacity: 0.5; }
        100% { color: #ff4b4b; opacity: 1; }
    }
    .stApp { 
        background: linear-gradient(rgba(0,0,0,0.6), rgba(0,0,0,0.6)), 
                    url("https://cdn.images.express.co.uk/img/dynamic/4/590x/secondary/5856693.jpg?r=1735554407217"); 
        background-size: cover; background-attachment: fixed; 
    }
    h1, h2, h3, p, label { color: white !important; font-weight: bold; }
    [data-testid="stSidebarContent"] { background-color: #111111 !important; }
    
    [data-testid="stDataFrame"], [data-testid="stTable"], .st-emotion-cache-1wivap2 {
        background-color: rgba(0,0,0,0.4) !important;
        border-radius: 10px;
    }

    .match-card {
        border: 2px solid #ffd700;
        border-radius: 20px;
        background-image: linear-gradient(rgba(0,0,0,0.5), rgba(0,0,0,0.5)), 
                          url("https://news.paddypower.com/assets/uploads/2023/12/Paddy-Power-World-Darts-Championship.jpg");
        background-size: cover; background-position: center;
        padding: 20px; margin-bottom: 10px;
    }
    .match-wrapper { display: flex; align-items: center; justify-content: space-between; width: 100%; gap: 15px; }
    .player-box { flex: 1; text-align: center; }
    .player-img { width: 100%; max-width: 140px; border-radius: 10px; border: 2px solid #ffd700; }
    .vs-text { color: #ffd700 !important; font-size: 2rem !important; font-weight: 900 !important; }
    .player-name { font-size: 1.3rem !important; font-weight: 900 !important; color: #ffd700 !important; }
    
    .timer-text { font-weight: bold; font-size: 1.1rem; text-align: center; margin-bottom: 15px; }
    .timer-urgent { animation: pulse-red 1s infinite; font-weight: 900; }
    
    div.stButton > button { background-color: #ffd700 !important; color: black !important; font-weight: bold; border-radius: 10px; }
    </style>
""", unsafe_allow_html=True)

# 5. Session State
if 'username' not in st.session_state: st.session_state['username'] = ""
if 'temp_preds' not in st.session_state: st.session_state.temp_preds = {}

# --- SIDEBAR & AUTH (Fixed Indentation) ---
st.sidebar.title("🎯 PDC PREDICTOR")
if st.session_state['username'] == "":
    auth_mode = st.sidebar.radio("Entry", ["Login", "Register"])
    u_attempt = st.sidebar.text_input("Username").strip()
    p_attempt = st.sidebar.text_input("Password", type="password")
    if st.sidebar.button("Go"):
        u_df = get_data("Users")
        if not u_df.empty:
            match = u_df[(u_df['Username'].astype(str) == u_attempt) & (u_df['Password'].astype(str) == str(p_attempt))]
            if not match.empty:
                st.session_state['username'] = u_attempt
                st.rerun()
            else:
                st.sidebar.error("Invalid Login")
else:
    st.sidebar.write(f"Logged in: **{st.session_state['username']}**")
    if st.sidebar.button("Logout"):
        st.session_state['username'] = ""
        st.rerun()

st.sidebar.divider()
page = st.sidebar.radio("Navigate", ["Predictions", "Leaderboard", "Rival Watch", "Admin"])

# --- SCORING ENGINE ---
def get_leaderboard_data():
    p_df = get_data("Predictions")
    r_df = get_data("Results")
    if p_df.empty or r_df.empty: return pd.DataFrame(columns=['Username', 'Current Points'])
    
    p_df = p_df.dropna(subset=['Match_ID', 'Score'])
    r_df = r_df.dropna(subset=['Match_ID', 'Score'])
    p_df['Match_ID'] = p_df['Match_ID'].astype(float).astype(int).astype(str)
    r_df['Match_ID'] = r_df['Match_ID'].astype(float).astype(int).astype(str)
    
    merged = p_df.merge(r_df, on="Match_ID", suffixes=('_u', '_r'))
    def calc(r):
        try:
            u1, u2 = map(int, str(r['Score_u']).split('-'))
            r1, r2 = map(int, str(r['Score_r']).split('-'))
            if u1 == r1 and u2 == r2: return 3
            return 1 if (u1 > u2 and r1 > r2) or (u1 < u2 and r1 < r2) else 0
        except: return 0
    merged['Pts'] = merged.apply(calc, axis=1)
    return merged.groupby('Username')['Pts'].sum().reset_index().rename(columns={'Pts': 'Current Points'}).sort_values('Current Points', ascending=False)

# --- PAGE: PREDICTIONS ---
if page == "Predictions":
    if st.session_state['username'] == "":
        st.warning("Please sign in.")
    else:
        st.title("Upcoming Matches")
        m_df = get_data("Matches").dropna(subset=['Match_ID', 'Player1', 'Date'])
        p_df = get_data("Predictions")
        r_df = get_data("Results")
        now = datetime.now()

        # Date Filter Logic
        m_df['Date_Parsed'] = pd.to_datetime(m_df['Date'], errors='coerce')
        m_df = m_df.dropna(subset=['Date_Parsed'])
        available_dates = sorted(m_df['Date_Parsed'].dt.date.unique())
        
        if available_dates:
            selected_date = st.selectbox("📅 Select Match Day", available_dates)
            display_df = m_df[m_df['Date_Parsed'].dt.date == selected_date]
            
            open_matches = []
            for _, row in display_df.iterrows():
                m_id = str(int(float(row['Match_ID'])))
                if not r_df.empty and m_id in r_df['Match_ID'].astype(str).values: continue
                
                # Live Timer Logic
                time_diff = row['Date_Parsed'] - now
                mins_left = time_diff.total_seconds() / 60
                
                if mins_left > 60: timer_html = f"<div class='timer-text' style='color:#00ff00;'>Starts in {int(mins_left/60)}h {int(mins_left%60)}m</div>"
                elif 10 < mins_left <= 60: timer_html = f"<div class='timer-text' style='color:#ffd700;'>Starts in {int(mins_left)}m</div>"
                elif 0 < mins_left <= 10: timer_html = f"<div class='timer-text timer-urgent'>⚠️ STARTING IN {int(mins_left)}m</div>"
                else: timer_html = "<div class='timer-text' style='color:#ff4b4b;'>Locked / Live</div>"

                st.markdown(f"""
                    <div class="match-card">
                        {timer_html}
                        <div class="match-wrapper">
                            <div class="player-box">
                                <img src="{row.get('P1_Image', '')}" class="player-img">
                                <div class="player-name">{row['Player1']}</div>
                            </div>
                            <div class="vs-text">VS</div>
                            <div class="player-box">
                                <img src="{row.get('P2_Image', '')}" class="player-img">
                                <div class="player-name">{row['Player2']}</div>
                            </div>
                        </div>
                    </div>
                """, unsafe_allow_html=True)

                done = False
                if not p_df.empty:
                    done = not p_df[(p_df['Username'] == st.session_state['username']) & (p_df['Match_ID'].astype(str) == m_id)].empty

                if done: st.success("Prediction Locked ✅")
                elif mins_left <= 0: st.error("Closed 🔒")
                else:
                    open_matches.append(m_id)
                    c1, c2 = st.columns(2)
                    with c1: s1 = st.selectbox(f"{row['Player1']}", range(11), key=f"s1_{m_id}")
                    with c2: s2 = st.selectbox(f"{row['Player2']}", range(11), key=f"s2_{m_id}")
                    st.session_state.temp_preds[m_id] = f"{s1}-{s2}"

            if open_matches:
                if st.button("🔒 LOCK ALL PREDICTIONS"):
                    new_rows = [{"Username": st.session_state['username'], "Match_ID": mid, "Score": st.session_state.temp_preds.get(mid, "0-0")} for mid in open_matches]
                    conn.update(spreadsheet=URL, worksheet="Predictions", data=pd.concat([p_df, pd.DataFrame(new_rows)], ignore_index=True))
                    st.cache_data.clear(); st.success("Saved!"); time.sleep(1); st.rerun()

# --- PAGE: RIVAL WATCH ---
elif page == "Rival Watch":
    st.title("👀 Rival Watch")
    m_df = get_data("Matches").dropna(subset=['Match_ID', 'Player1'])
    p_df = get_data("Predictions")
    
    options = []
    for _, r in m_df.iterrows():
        try:
            m_id_clean = str(int(float(r['Match_ID'])))
            options.append(f"{m_id_clean}: {r['Player1']} vs {r['Player2']}")
        except: continue
        
    if options:
        sel = st.selectbox("Pick a Match:", options)
        target_id = sel.split(":")[0]
        lb_df = get_leaderboard_data()
        
        if not p_df.empty:
            # Force cleanup of IDs to ensure they match
            p_df['Match_ID_Clean'] = p_df['Match_ID'].astype(float).astype(int).astype(str)
            match_preds = p_df[p_df['Match_ID_Clean'] == target_id].drop_duplicates('Username', keep='last')
            
            if not match_preds.empty:
                rivals = match_preds.merge(lb_df, on="Username", how="left").fillna(0)
                rivals['Current Points'] = rivals['Current Points'].astype(int)
                st.dataframe(rivals[['Username', 'Score', 'Current Points']], hide_index=True, width="stretch")
            else:
                st.info("No predictions for this match.")

# --- PAGE: LEADERBOARD ---
elif page == "Leaderboard":
    st.title("🏆 Leaderboard")
    lb = get_leaderboard_data()
    st.dataframe(lb, hide_index=True, width="stretch")

# --- PAGE: ADMIN ---
elif page == "Admin":
    st.title("⚙️ Admin Hub")
    if st.text_input("Admin Password", type="password") == "darts2025":
        m_df = get_data("Matches").dropna(subset=['Match_ID', 'Player1'])
        target = st.selectbox("Select Match", [f"{int(float(r['Match_ID']))}: {r['Player1']} vs {r['Player2']}" for _, r in m_df.iterrows()])
        c1, c2 = st.columns(2)
        with c1: r1 = st.selectbox("P1 Score", range(11))
        with c2: r2 = st.selectbox("P2 Score", range(11))
        if st.button("Submit Result"):
            old_res = get_data("Results")
            new_res = pd.concat([old_res, pd.DataFrame([{"Match_ID": target.split(":")[0], "Score": f"{r1}-{r2}"}])])
            conn.update(spreadsheet=URL, worksheet="Results", data=new_res)
            st.cache_data.clear(); st.success("Result Published!"); st.rerun()
