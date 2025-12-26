import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# 1. Page Configuration
st.set_page_config(page_title="Darts Predictor Pro", page_icon="🎯", layout="wide")

# 2. Connection
conn = st.connection("gsheets", type=GSheetsConnection)
URL = st.secrets["connections"]["gsheets"]["spreadsheet"]

# 3. Data Fetching
@st.cache_data(ttl=10) # Lowered TTL so updates show faster
def get_data(worksheet):
    try:
        df = conn.read(spreadsheet=URL, worksheet=worksheet, ttl=0)
        return df.dropna(how='all')
    except:
        return pd.DataFrame()

# 4. Styling (Transparent Tables Fix)
st.markdown("""
    <style>
    .stApp { 
        background: linear-gradient(rgba(0,0,0,0.6), rgba(0,0,0,0.6)), 
                    url("https://cdn.images.express.co.uk/img/dynamic/4/590x/secondary/5856693.jpg?r=1735554407217"); 
        background-size: cover; background-attachment: fixed; 
    }
    h1, h2, h3, p, label { color: white !important; }
    [data-testid="stSidebarContent"] { background-color: #111111 !important; }
    
    /* KILL WHITE TABLE BACKGROUNDS */
    [data-testid="stDataFrame"], [data-testid="stTable"] {
        background-color: rgba(0,0,0,0.4) !important;
        border-radius: 10px;
    }
    .st-emotion-cache-1wivap2 { background-color: transparent !important; } 
    
    div.stButton > button { 
        background-color: #ffd700 !important; color: black !important; 
        font-weight: bold; width: 100%; border-radius: 10px; 
    }
    </style>
""", unsafe_allow_html=True)

# 5. Session State
if 'username' not in st.session_state: st.session_state['username'] = ""

# --- LOGIN LOGIC ---
st.sidebar.title("🎯 PDC PREDICTOR")
if st.session_state['username'] == "":
    auth_mode = st.sidebar.radio("Entry", ["Login", "Register"])
    u_attempt = st.sidebar.text_input("Username").strip()
    p_attempt = st.sidebar.text_input("Password", type="password")
    if st.sidebar.button("Go"):
        u_df = get_data("Users")
        if not u_df.empty:
            match = u_df[(u_df['Username'].astype(str) == u_attempt) & (u_df['Password'].astype(str) == p_attempt)]
            if not match.empty:
                st.session_state['username'] = u_attempt
                st.rerun()
            else: st.sidebar.error("Invalid Login")
else:
    st.sidebar.write(f"Logged in: **{st.session_state['username']}**")
    if st.sidebar.button("Logout"):
        st.session_state['username'] = ""; st.rerun()

st.sidebar.divider()
page = st.sidebar.radio("Navigate", ["Predictions", "Leaderboard", "Rival Watch", "Admin"])

# --- SCORING ENGINE ---
def get_leaderboard_data():
    p_df = get_data("Predictions")
    r_df = get_data("Results")
    if p_df.empty or r_df.empty: return pd.DataFrame(columns=['Username', 'Current Points'])
    
    # Convert IDs to string and drop only the nan rows
    p_df = p_df[p_df['Match_ID'].notna()]
    r_df = r_df[r_df['Match_ID'].notna()]
    p_df['Match_ID'] = p_df['Match_ID'].astype(str)
    r_df['Match_ID'] = r_df['Match_ID'].astype(str)
    
    merged = p_df.merge(r_df, on="Match_ID", suffixes=('_u', '_r'))
    def calc(r):
        try:
            u1, u2 = map(int, str(r['Score_u']).split('-'))
            r1, r2 = map(int, str(r['Score_r']).split('-'))
            if u1 == r1 and u2 == r2: return 3
            return 1 if (u1 > u2 and r1 > r2) or (u1 < u2 and r1 < r2) else 0
        except: return 0
    merged['Pts'] = merged.apply(calc, axis=1)
    return merged.groupby('Username')['Pts'].sum().reset_index().rename(columns={'Pts': 'Current Points'})

# --- PAGES ---
if page == "Predictions":
    if st.session_state['username'] == "":
        st.warning("Please sign in.")
    else:
        st.title("Upcoming Matches")
        m_df = get_data("Matches")
        # Only drop rows if Player names are missing
        m_df = m_df.dropna(subset=['Player1', 'Player2'])
        for _, row in m_df.iterrows():
            st.write(f"### {row['Player1']} vs {row['Player2']}")
            # (Insert your Match Card HTML/Buttons here)

elif page == "Leaderboard":
    st.title("🏆 Leaderboard")
    lb = get_leaderboard_data()
    st.dataframe(lb.sort_values('Current Points', ascending=False), hide_index=True, width="stretch")

elif page == "Rival Watch":
    st.title("👀 Rival Watch")
    m_df = get_data("Matches").dropna(subset=['Match_ID', 'Player1'])
    p_df = get_data("Predictions")
    
    # Create valid options list (skipping nans)
    options = []
    for _, r in m_df.iterrows():
        try:
            val = f"{int(float(r['Match_ID']))}: {r['Player1']} vs {r['Player2']}"
            options.append(val)
        except: continue
        
    if options:
        sel = st.selectbox("Pick a Match", options)
        mid = sel.split(":")[0]
        lb = get_leaderboard_data()
        match_p = p_df[p_df['Match_ID'].astype(str).str.contains(mid)]
        rivals = match_p.merge(lb, on="Username", how="left").fillna(0)
        st.dataframe(rivals[['Username', 'Score', 'Current Points']], hide_index=True, width="stretch")

elif page == "Admin":
    st.title("⚙️ Admin Hub")
    pw = st.text_input("Admin Password", type="password")
    if pw == "darts2025":
        st.success("Admin Access Granted")
        # Insert result entry logic here
