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
        # Drop rows that are completely empty to prevent 'nan' issues
        return df.dropna(how='all')
    except:
        return pd.DataFrame()

# 4. Shared Scoring Logic (Robust Version)
def get_leaderboard_data():
    p_df = get_data("Predictions")
    r_df = get_data("Results")
    
    # Check if we actually have data to work with
    if p_df.empty or r_df.empty:
        return pd.DataFrame(columns=['Username', 'Current Points'])
    
    # Ensure IDs are strings and drop any that are blank/nan
    p_df['Match_ID'] = p_df['Match_ID'].astype(str)
    r_df['Match_ID'] = r_df['Match_ID'].astype(str)
    p_df = p_df[p_df['Match_ID'] != 'nan']
    r_df = r_df[r_df['Match_ID'] != 'nan']

    merged = p_df.merge(r_df, on="Match_ID", suffixes=('_u', '_r'))
    
    def calc_pts(r):
        try:
            # Check if scores exist before splitting
            if pd.isna(r['Score_u']) or pd.isna(r['Score_r']): return 0
            u1, u2 = map(int, str(r['Score_u']).split('-'))
            r1, r2 = map(int, str(r['Score_r']).split('-'))
            if u1 == r1 and u2 == r2: return 3
            if (u1 > u2 and r1 > r2) or (u1 < u2 and r1 < r2): return 1
        except: return 0
        return 0
        
    merged['Pts'] = merged.apply(calc_pts, axis=1)
    res = merged.groupby('Username')['Pts'].sum().reset_index()
    return res.rename(columns={'Pts': 'Current Points'}).sort_values('Current Points', ascending=False)

# 5. Styling
st.markdown("""
    <style>
    .stApp { background: linear-gradient(rgba(0,0,0,0.6), rgba(0,0,0,0.6)), url("https://cdn.images.express.co.uk/img/dynamic/4/590x/secondary/5856693.jpg?r=1735554407217"); background-size: cover; background-attachment: fixed; }
    h1, h2, h3, p { color: white !important; }
    [data-testid="stSidebarContent"] { background-color: #111111 !important; }
    div.stButton > button { background-color: #ffd700 !important; color: black !important; font-weight: bold; width: 100%; border-radius: 10px; }
    </style>
""", unsafe_allow_html=True)

# 6. Session State
if 'username' not in st.session_state: st.session_state['username'] = ""

# --- SIDEBAR: LOGIN & NAVIGATION ---
st.sidebar.title("🎯 PDC PREDICTOR")

if st.session_state['username'] == "":
    auth_mode = st.sidebar.radio("Entry", ["Login", "Register"])
    u_attempt = st.sidebar.text_input("Username").strip()
    p_attempt = st.sidebar.text_input("Password", type="password")
    if st.sidebar.button("Go"):
        u_df = get_data("Users")
        if not u_df.empty:
            if auth_mode == "Login":
                # Safe comparison to avoid errors
                u_df['Username'] = u_df['Username'].astype(str)
                u_df['Password'] = u_df['Password'].astype(str)
                match = u_df[(u_df['Username'] == u_attempt) & (u_df['Password'] == str(p_attempt))]
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
        st.session_state['username'] = ""; st.rerun()

st.sidebar.divider()
page = st.sidebar.radio("Navigate", ["Predictions", "Leaderboard", "Rival Watch", "Admin"])

# --- PAGE: RIVAL WATCH ---
if page == "Rival Watch":
    st.title("👀 Rival Watch")
    m_df = get_data("Matches")
    p_df = get_data("Predictions")
    
    if not m_df.empty:
        # CLEANUP: Remove any rows that have 'nan' Match_IDs or empty players
        m_df = m_df.dropna(subset=['Match_ID', 'Player1', 'Player2'])
        m_df['Match_ID_Str'] = m_df['Match_ID'].astype(float).astype(int).astype(str)
        
        match_options = (m_df['Match_ID_Str'] + ": " + m_df['Player1'] + " vs " + m_df['Player2']).tolist()
        
        if match_options:
            m_sel = st.selectbox("Pick a Match:", match_options)
            mid = m_sel.split(":")[0]
            
            lb_df = get_leaderboard_data()
            
            if not p_df.empty:
                p_df['Match_ID'] = p_df['Match_ID'].astype(str)
                match_p = p_df[p_df['Match_ID'] == mid].drop_duplicates('Username', keep='last')
                
                rival_display = match_p.merge(lb_df, on="Username", how="left").fillna(0)
                rival_display['Current Points'] = rival_display['Current Points'].astype(int)
                
                st.dataframe(rival_display[['Username', 'Score', 'Current Points']], hide_index=True, width="stretch")
        else:
            st.info("No matches available.")

# --- PAGE: LEADERBOARD ---
elif page == "Leaderboard":
    st.title("🏆 Leaderboard")
    lb = get_leaderboard_data()
    if not lb.empty:
        st.dataframe(lb, hide_index=True, width="stretch")
    else:
        st.info("No points calculated yet.")

# ... (Keep existing Predictions/Admin logic, ensuring they use get_data()) ...
