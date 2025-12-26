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
        return df.dropna(how='all') # Removes phantom empty rows at the bottom
    except:
        return pd.DataFrame()

# 4. Pro Styling
def apply_pro_styling():
    st.markdown(
        f"""
        <style>
        .stApp {{
            background: linear-gradient(rgba(0,0,0,0.5), rgba(0,0,0,0.5)), 
                        url("https://cdn.images.express.co.uk/img/dynamic/4/590x/secondary/5856693.jpg?r=1735554407217");
            background-size: cover; background-position: center; background-attachment: fixed;
        }}
        h1, h2, h3, p {{ color: white !important; }}
        [data-testid="stSidebarContent"] {{ background-color: #111111 !important; }}
        
        /* FORCE DATAFRAME TRANSPARENCY & DARK MODE */
        [data-testid="stDataFrame"] {{
            background-color: rgba(0, 0, 0, 0.4) !important;
            border-radius: 10px;
        }}
        
        /* The Match Card */
        [data-testid="stVerticalBlock"] > div:has(.match-wrapper) {{
            border: 2px solid #ffd700 !important;
            border-radius: 20px !important;
            background-image: linear-gradient(rgba(0,0,0,0.5), rgba(0,0,0,0.5)), 
                              url("https://news.paddypower.com/assets/uploads/2023/12/Paddy-Power-World-Darts-Championship.jpg");
            background-size: cover; background-position: center;
            padding: 20px !important; margin-bottom: 25px !important;
        }}
        
        .match-wrapper {{ display: flex; align-items: center; justify-content: space-between; width: 100%; gap: 15px; }}
        .player-box {{ flex: 1; text-align: center; }}
        .player-img {{ width: 100%; max-width: 180px; border-radius: 10px; }}
        .vs-text-styled {{ color: #ffd700 !important; font-size: 2rem !important; font-weight: 900 !important; text-shadow: 2px 2px 4px #000; }}
        .player-name-styled {{ font-size: 1.3rem !important; font-weight: 900 !important; color: #ffd700 !important; text-shadow: 2px 2px 4px #000; }}
        
        .digital-timer {{
            background-color: rgba(0, 0, 0, 0.9);
            border: 2px solid #333;
            border-radius: 8px;
            font-family: 'Courier New', Courier, monospace;
            padding: 6px 15px; display: inline-block; margin-bottom: 15px;
        }}

        div.stButton > button {{
            background-color: #ffd700 !important;
            color: #000 !important;
            font-weight: bold !important;
            width: 100% !important; border-radius: 12px !important; height: 3.8em !important;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

apply_pro_styling()

if 'username' not in st.session_state: st.session_state['username'] = ""
if 'temp_preds' not in st.session_state: st.session_state.temp_preds = {}

# --- SIDEBAR & NAVIGATION ---
st.sidebar.title("🎯 PDC PREDICTOR")
# ... (Your existing login logic here) ...

st.sidebar.divider()
page = st.sidebar.radio("Navigate", ["Predictions", "Leaderboard", "Rival Watch", "Admin"])

# --- PAGE: PREDICTIONS ---
if page == "Predictions":
    if st.session_state['username'] == "":
        st.warning("Please sign in.")
    else:
        st.title("Upcoming Matches")
        m_df = get_data("Matches").dropna(subset=['Date', 'Match_ID']) # Clean data
        p_df = get_data("Predictions")
        r_df = get_data("Results")
        now = datetime.now()

        m_df['Date_Parsed'] = pd.to_datetime(m_df['Date'])
        unique_dates = sorted(m_df['Date_Parsed'].dt.date.unique())
        
        if unique_dates:
            view_date = st.selectbox("📅 Select Match Day", unique_dates, 
                                     index=unique_dates.index(now.date()) if now.date() in unique_dates else 0)
            display_df = m_df[m_df['Date_Parsed'].dt.date == view_date]
            
            open_matches_list = []
            for _, row in display_df.iterrows():
                m_id = str(row['Match_ID'])
                if not r_df.empty and m_id in r_df['Match_ID'].astype(str).values: continue
                
                # Check for existing prediction
                already_done = False
                if not p_df.empty:
                    already_done = not p_df[(p_df['Username'] == st.session_state['username']) & (p_df['Match_ID'].astype(str) == m_id)].empty

                match_time = pd.to_datetime(row['Date'])
                is_locked_by_time = (match_time - now).total_seconds() < 0

                with st.container():
                    st.markdown(f"""
                        <div class="match-wrapper">
                            <div class="player-box">
                                <img src="{row['P1_Image']}" class="player-img">
                                <div class="player-name-styled">{row['Player1']}</div>
                            </div>
                            <div class="vs-text-styled">VS</div>
                            <div class="player-box">
                                <img src="{row['P2_Image']}" class="player-img">
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
                    new_entries = [{"Username": st.session_state['username'], "Match_ID": m_id, "Score": st.session_state.temp_preds.get(m_id, "0-0")} for m_id in open_matches_list]
                    conn.update(spreadsheet=URL, worksheet="Predictions", data=pd.concat([p_df, pd.DataFrame(new_entries)], ignore_index=True))
                    st.cache_data.clear(); st.rerun()

# --- PAGE: LEADERBOARD ---
elif page == "Leaderboard":
    st.title("🏆 Leaderboard")
    p_df = get_data("Predictions").dropna(subset=['Score']) # FIX: Remove empty scores
    r_df = get_data("Results").dropna(subset=['Score']) # FIX: Remove empty results
    
    if not r_df.empty and not p_df.empty:
        merged = p_df.merge(r_df, on="Match_ID", suffixes=('_u', '_r'))
        
        def calc_pts(r):
            try:
                # Safely convert to string before splitting to avoid AttributeError
                u1, u2 = map(int, str(r['Score_u']).split('-'))
                r1, r2 = map(int, str(r['Score_r']).split('-'))
                if u1 == r1 and u2 == r2: return 3
                if (u1 > u2 and r1 > r2) or (u1 < u2 and r1 < r2): return 1
            except: return 0 # Catches any malformed scores (like "7-")
            return 0
            
        merged['Pts'] = merged.apply(calc_pts, axis=1)
        lb = merged.groupby('Username')['Pts'].sum().reset_index().sort_values('Pts', ascending=False)
        st.dataframe(lb, hide_index=True, width='stretch')

# --- RIVAL WATCH ---
elif page == "Rival Watch":
    st.title("👀 Rival Watch")
    m_df = get_data("Matches").dropna(subset=['Match_ID'])
    p_df = get_data("Predictions")
    if not m_df.empty and not p_df.empty:
        m_sel = st.selectbox("Pick a Match:", m_df['Match_ID'].astype(str) + ": " + m_df['Player1'] + " vs " + m_df['Player2'])
        mid = m_sel.split(":")[0]
        match_p = p_df[p_df['Match_ID'].astype(str) == mid]
        st.dataframe(match_p[['Username', 'Score']], hide_index=True, width='stretch')
