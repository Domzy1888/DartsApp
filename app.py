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
        return df.dropna(how='all') 
    except:
        return pd.DataFrame()

# 4. Pro Styling (Transparent Table Focus)
def apply_pro_styling():
    st.markdown(
        f"""
        <style>
        .stApp {{
            background: linear-gradient(rgba(0,0,0,0.5), rgba(0,0,0,0.5)), 
                        url("https://cdn.images.express.co.uk/img/dynamic/4/590x/secondary/5856693.jpg?r=1735554407217");
            background-size: cover; background-position: center; background-attachment: fixed;
        }}
        h1, h2, h3, p {{ color: white !important; font-weight: bold; }}
        [data-testid="stSidebarContent"] {{ background-color: #111111 !important; }}
        
        /* Forces transparency on the new Streamlit dataframes */
        [data-testid="stDataFrame"] {{
            background-color: rgba(0, 0, 0, 0.5) !important;
            border: 1px solid #ffd700;
            border-radius: 10px;
        }}
        [data-testid="stDataFrame"] div, [data-testid="stDataFrame"] canvas {{
            background-color: transparent !important;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

apply_pro_styling()

if 'username' not in st.session_state: st.session_state['username'] = ""

# --- SHARED SCORING LOGIC ---
def get_leaderboard_data():
    p_df = get_data("Predictions").dropna(subset=['Match_ID', 'Score'])
    r_df = get_data("Results").dropna(subset=['Match_ID', 'Score'])
    if r_df.empty or p_df.empty:
        return pd.DataFrame(columns=['Username', 'Current Points'])
    
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
    return merged.groupby('Username')['Pts'].sum().reset_index().rename(columns={'Pts': 'Current Points'})

# --- SIDEBAR & NAVIGATION ---
st.sidebar.title("🎯 PDC PREDICTOR")
# ... (Sign-in logic remains here) ...

page = st.sidebar.radio("Navigate", ["Predictions", "Leaderboard", "Rival Watch", "Admin"])

# --- PAGE: RIVAL WATCH (With Current Points) ---
if page == "Rival Watch":
    st.title("👀 Rival Watch")
    m_df = get_data("Matches").dropna(subset=['Match_ID', 'Player1'])
    p_df = get_data("Predictions").dropna(subset=['Match_ID'])
    
    if not m_df.empty:
        # 1. Clean Match Dropdown (No 'nan')
        match_options = (
            m_df['Match_ID'].astype(int).astype(str) + ": " + 
            m_df['Player1'] + " vs " + m_df['Player2']
        ).tolist()
        
        m_sel = st.selectbox("Pick a Match:", match_options)
        mid = m_sel.split(":")[0]
        
        # 2. Get Live Leaderboard for "Current Points" column
        lb_df = get_leaderboard_data()
        
        # 3. Get Predictions for this match
        match_p = p_df[p_df['Match_ID'].astype(str) == mid].drop_duplicates('Username', keep='last')
        
        if not match_p.empty:
            # Merge predictions with their current leaderboard standing
            rival_display = match_p.merge(lb_df, on="Username", how="left").fillna(0)
            rival_display['Current Points'] = rival_display['Current Points'].astype(int)
            
            # Show Table
            st.dataframe(
                rival_display[['Username', 'Score', 'Current Points']], 
                hide_index=True, 
                width="stretch"
            )
        else:
            st.info("No predictions for this match yet.")

# --- PAGE: LEADERBOARD ---
elif page == "Leaderboard":
    st.title("🏆 Leaderboard")
    lb = get_leaderboard_data()
    if not lb.empty:
        st.dataframe(lb.sort_values('Current Points', ascending=False), hide_index=True, width="stretch")
    else:
        st.info("No scores calculated yet.")
