import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import time

# 1. Page Configuration
st.set_page_config(page_title="Darts Predictor Pro", page_icon="🎯", layout="wide")

# 2. Connection to Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)
URL = st.secrets["connections"]["gsheets"]["spreadsheet"]

# 3. STYLING: Background, Forced Side-by-Side, and Name Colors
def apply_pro_styling():
    st.markdown(
        f"""
        <style>
        .stApp {{
            background: linear-gradient(rgba(0,0,0,0.8), rgba(0,0,0,0.8)), 
                        url("https://cdn.images.express.co.uk/img/dynamic/4/590x/secondary/5856693.jpg?r=1735554407217");
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
        }}

        h1, h2, h3, p {{ color: white !important; }}

        [data-testid="stSidebarContent"] {{ background-color: #111111 !important; }}
        [data-testid="stSidebar"] label p, [data-testid="stSidebar"] p {{
            color: white !important;
            font-weight: bold !important;
        }}

        [data-testid="stVerticalBlock"] > div:has(.match-wrapper) {{
            border: 2px solid #ffd700 !important;
            border-radius: 15px !important;
            background-color: rgba(20, 20, 20, 0.85) !important;
            padding: 15px !important;
            margin-bottom: 20px !important;
        }}

        .match-wrapper {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            width: 100%;
            gap: 10px;
        }}

        .player-box {{ flex: 1; text-align: center; }}
        .player-img {{ width: 100%; max-width: 120px; border-radius: 10px; }}
        
        .vs-text-styled {{
            color: #ffd700 !important;
            font-size: 1.8rem !important;
            font-weight: 900 !important;
            flex: 0.5;
            text-align: center;
        }}

        /* FIX: High Visibility Player Names */
        .player-name-styled {{
            font-size: 1.1rem !important;
            font-weight: 900 !important;
            color: #ffd700 !important;
            margin-top: 8px;
            text-align: center;
        }}

        div.stButton > button {{
            background-color: #ffd700 !important;
            color: #000 !important;
            font-weight: bold !important;
            width: 100% !important;
            border-radius: 10px !important;
            height: 3em !important;
        }}

        div[data-baseweb="select"] > div {{
            background-color: #333 !important;
            color: white !important;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

apply_pro_styling()

# 4. Session State
if 'username' not in st.session_state:
    st.session_state['username'] = ""

# --- SIDEBAR: AUTH & NAVIGATION ---
st.sidebar.title("🎯 PDC PREDICTOR")

if st.session_state['username'] == "":
    auth_mode = st.sidebar.radio("Entry", ["Login", "Register"])
    if auth_mode == "Register":
        new_user = st.sidebar.text_input("New Username").strip()
        new_pwd = st.sidebar.text_input("New Password", type="password")
        if st.sidebar.button("Create Account"):
            user_df = conn.read(spreadsheet=URL, worksheet="Users", ttl=0)
            if new_user in user_df['Username'].values:
                st.sidebar.error("Taken!")
            else:
                reg_df = pd.DataFrame([{"Username": new_user, "Password": new_pwd}])
                conn.update(spreadsheet=URL, worksheet="Users", data=pd.concat([user_df, reg_df], ignore_index=True))
                st.sidebar.success("Success! Login now.")
    else:
        u_attempt = st.sidebar.text_input("Username").strip()
        p_attempt = st.sidebar.text_input("Password", type="password")
        if st.sidebar.button("Sign In"):
            u_df = conn.read(spreadsheet=URL, worksheet="Users", ttl=0)
            match = u_df[(u_df['Username'] == u_attempt) & (u_df['Password'].astype(str) == str(p_attempt))]
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
# THIS DEFINES THE 'page' VARIABLE
page = st.sidebar.radio("Navigate", ["Predictions", "Leaderboard", "Rival Watch", "Admin"])

# --- PAGE LOGIC ---
if page == "Predictions":
    if st.session_state['username'] == "":
        st.warning("Please sign in to view matchups.")
    else:
        st.title("Match Predictions")
        
        try:
            matches_df = conn.read(spreadsheet=URL, worksheet="Matches", ttl=10)
            preds_df = conn.read(spreadsheet=URL, worksheet="Predictions", ttl=0)
            results_df = conn.read(spreadsheet=URL, worksheet="Results", ttl=0)
        except Exception:
            st.error("Google Sheets is refreshing. Please wait a moment.")
            st.stop()

        for index, row in matches_df.iterrows():
            m_id = str(row['Match_ID'])
            is_closed = m_id in results_df['Match_ID'].astype(str).values if not results_df.empty else False
            already_done = not preds_df[(preds_df['Username'] == st.session_state['username']) & (preds_df['Match_ID'].astype(str) == m_id)].empty if not preds_df.empty else False

            with st.container():
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

                if is_closed:
                    st.info("Match Closed")
                elif already_done:
                    st.success("Locked In ✅")
                else:
                    sc1, sc2 = st.columns(2)
                    with sc1: s1 = st.selectbox(f"{row['Player1']}", range(11), key=f"s1_{m_id}")
                    with sc2: s2 = st.selectbox(f"{row['Player2']}", range(11), key=f"s2_{m_id}")
                    
                    if st.button(f"LOCK PREDICTION", key=f"btn_{m_id}"):
                        with st.spinner("Saving..."):
                            st.cache_data.clear()
                            new_p = pd.DataFrame([{"Username": st.session_state['username'], "Match_ID": m_id, "Score": f"{s1}-{s2}"}])
                            current_preds = conn.read(spreadsheet=URL, worksheet="Predictions", ttl=0)
                            updated_df = pd.concat([current_preds, new_p], ignore_index=True)
                            conn.update(spreadsheet=URL, worksheet="Predictions", data=updated_df)
                            time.sleep(1) # Small buffer for Google API
                            st.rerun()

elif page == "Leaderboard":
    st.title("Leaderboard")
    p_df = conn.read(spreadsheet=URL, worksheet="Predictions", ttl=0)
    r_df = conn.read(spreadsheet=URL, worksheet="Results", ttl=0)
    if not r_df.empty and not p_df.empty:
        p_df['Match_ID'] = p_df['Match_ID'].astype(str)
        r_df['Match_ID'] = r_df['Match_ID'].astype(str)
        merged = p_df.merge(r_df, on="Match_ID", suffixes=('_u', '_r'))
        def calc(r):
            u1, u2 = map(int, str(r['Score_u']).split('-'))
            r1, r2 = map(int, str(r['Score_r']).split('-'))
            if u1 == r1 and u2 == r2: return 3
            if (u1 > u2 and r1 > r2) or (u1 < u2 and r1 < r2): return 1
            return 0
        merged['Pts'] = merged.apply(calc, axis=1)
        lb = merged.groupby('Username')['Pts'].sum().reset_index().sort_values('Pts', ascending=False)
        st.table(lb)

elif page == "Rival Watch":
    st.title("Rival Watch")
    m_df = conn.read(spreadsheet=URL, worksheet="Matches", ttl=60)
    p_df = conn.read(spreadsheet=URL, worksheet="Predictions", ttl=0)
    if not m_df.empty:
        m_sel = st.selectbox("Check Predictions for:", m_df['Match_ID'].astype(str) + ": " + m_df['Player1'] + " vs " + m_df['Player2'])
        mid = m_sel.split(":")[0]
        match_p = p_df[p_df['Match_ID'].astype(str) == mid]
        if not match_p.empty:
            st.table(match_p[['Username', 'Score']].set_index('Username'))

elif page == "Admin":
    st.title("Admin Results Hub")
    if st.text_input("Admin Key", type="password") == "darts2025":
        m_df = conn.read(spreadsheet=URL, worksheet="Matches", ttl=0)
        target = st.selectbox("Select Finished Match", m_df['Match_ID'].astype(str) + ": " + m_df['Player1'] + " vs " + m_df['Player2'])
        c1, c2 = st.columns(2)
        with c1: r1 = st.selectbox("Actual P1", range(11))
        with c2: r2 = st.selectbox("Actual P2", range(11))
        if st.button("Finalize Result"):
            st.cache_data.clear()
            old_res = conn.read(spreadsheet=URL, worksheet="Results", ttl=0)
            new_res = pd.DataFrame([{"Match_ID": target.split(":")[0], "Score": f"{r1}-{r2}"}])
            conn.update(spreadsheet=URL, worksheet="Results", data=pd.concat([old_res, new_res], ignore_index=True))
            st.success("Result Published!")
