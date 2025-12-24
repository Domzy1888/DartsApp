import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# 1. Page Configuration
st.set_page_config(page_title="Darts Predictor Pro", page_icon="🎯", layout="wide")

# 2. Connection to Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)
URL = st.secrets["connections"]["gsheets"]["spreadsheet"]

# 3. UPDATED MOBILE-STURDY STYLING
def apply_pro_styling():
    st.markdown(
        """
        <style>
        /* Force background visibility */
        .stApp {
            background: linear-gradient(rgba(0,0,0,0.75), rgba(0,0,0,0.75)), 
                        url("https://cdn.pixabay.com/photo/2020/03/10/16/47/darts-4919501_1280.jpg");
            background-size: cover;
            background-position: center;
            background-attachment: scroll;
        }

        /* Title Fix: Force White */
        h1 {
            color: white !important;
        }

        /* Sidebar Fixes */
        [data-testid="stSidebarContent"] {
            background-color: #111111 !important;
        }
        [data-testid="stSidebar"] label p, [data-testid="stSidebar"] p {
            color: white !important;
            font-weight: bold !important;
        }

        /* Match Card Fix: Ensure it expands to fit content */
        .match-card {
            background-color: rgba(20, 20, 20, 0.85) !important; 
            border: 2px solid #ffd700 !important;
            padding: 20px;
            border-radius: 15px;
            margin-bottom: 25px;
            display: block; /* Force block display to wrap content */
            overflow: auto; /* Clear floats */
            color: white !important;
        }

        .player-label {
            font-size: 1.3rem;
            font-weight: bold;
            color: white !important;
            margin-bottom: 10px;
        }

        .vs-text {
            color: #ffd700 !important;
            font-size: 2rem;
            font-weight: 900;
            margin: 10px 0;
        }

        /* Button Fix */
        div.stButton > button {
            background-color: #ffd700 !important;
            color: #000000 !important;
            font-weight: bold !important;
            width: 100%;
            border-radius: 10px;
            border: none;
            margin-top: 15px;
        }

        /* Fix invisible dropdown text */
        div[data-baseweb="select"] > div {
            background-color: #333 !important;
            color: white !important;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

apply_pro_styling()

# 4. Session State
if 'username' not in st.session_state:
    st.session_state['username'] = ""

# --- SIDEBAR: AUTHENTICATION ---
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
page = st.sidebar.radio("Navigate", ["Predictions", "Leaderboard", "Rival Watch", "Admin"])

# --- PAGE: PREDICTIONS ---
if page == "Predictions":
    if st.session_state['username'] == "":
        st.warning("Please sign in to view matchups.")
    else:
        st.title("Match Predictions")
        
        matches_df = conn.read(spreadsheet=URL, worksheet="Matches", ttl=60)
        preds_df = conn.read(spreadsheet=URL, worksheet="Predictions", ttl=0)
        results_df = conn.read(spreadsheet=URL, worksheet="Results", ttl=0)

        for index, row in matches_df.iterrows():
            m_id = str(row['Match_ID'])
            is_closed = m_id in results_df['Match_ID'].astype(str).values if not results_df.empty else False
            already_done = not preds_df[(preds_df['Username'] == st.session_state['username']) & (preds_df['Match_ID'].astype(str) == m_id)].empty if not preds_df.empty else False

            # Wrap everything inside the card div
            st.markdown('<div class="match-card">', unsafe_allow_html=True)
            
            # Use columns inside the card
            c1, c2, c3 = st.columns([2, 1, 2])
            with c1:
                img1 = row['P1_Image'] if pd.notna(row['P1_Image']) else "https://via.placeholder.com/150"
                st.image(img1)
                st.markdown(f"<div class='player-label'>{row['Player1']}</div>", unsafe_allow_html=True)
            with c2:
                st.markdown("<div class='vs-text' style='text-align:center;'>VS</div>", unsafe_allow_html=True)
            with c3:
                img2 = row['P2_Image'] if pd.notna(row['P2_Image']) else "https://via.placeholder.com/150"
                st.image(img2)
                st.markdown(f"<div class='player-label'>{row['Player2']}</div>", unsafe_allow_html=True)

            if is_closed:
                st.info("Match Closed")
            elif already_done:
                st.success("Locked In ✅")
            else:
                sc1, sc2 = st.columns(2)
                with sc1: 
                    s1 = st.selectbox(f"{row['Player1']} Score", range(11), key=f"s1_{m_id}")
                with sc2: 
                    s2 = st.selectbox(f"{row['Player2']} Score", range(11), key=f"s2_{m_id}")
                
                if st.button(f"LOCK PREDICTION: {row['Player1']} vs {row['Player2']}", key=f"btn_{m_id}"):
                    st.cache_data.clear()
                    current_p = conn.read(spreadsheet=URL, worksheet="Users", ttl=0) # Note: changed back to Predictions if that was a typo in previous iterations
                    # Ensure we are appending to the right sheet
                    current_preds = conn.read(spreadsheet=URL, worksheet="Predictions", ttl=0)
                    new_p = pd.DataFrame([{"Username": st.session_state['username'], "Match_ID": m_id, "Score": f"{s1}-{s2}"}])
                    conn.update(spreadsheet=URL, worksheet="Predictions", data=pd.concat([current_preds, new_p], ignore_index=True))
                    st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

# --- (Other pages remain same) ---
elif page == "Leaderboard":
    st.title("Leaderboard")
    p_df = conn.read(spreadsheet=URL, worksheet="Predictions", ttl=60)
    r_df = conn.read(spreadsheet=URL, worksheet="Results", ttl=60)
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
