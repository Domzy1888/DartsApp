import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# 1. Page Configuration
st.set_page_config(page_title="Darts Predictor Pro", page_icon="🎯", layout="wide")

# 2. Connection to Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)
URL = st.secrets["connections"]["gsheets"]["spreadsheet"]

# 3. OVERHAULED CSS: Forced Dark Theme & Mobile Fixes
def apply_pro_styling():
    st.markdown(
        """
        <style>
        /* Force the app background and image */
        .stApp {
            background-image: url("https://images.unsplash.com/photo-1547427735-33750bb20671?q=80&w=2000");
            background-attachment: fixed;
            background-size: cover;
            background-position: center;
        }

        /* Stronger dark overlay that works on mobile */
        [data-testid="stAppViewContainer"]::before {
            content: "";
            position: fixed;
            top: 0; left: 0; width: 100%; height: 100%;
            background-color: rgba(0, 0, 0, 0.8) !important;
            z-index: -1;
        }

        /* Fix Sidebar Text (Remove blue links/hard-to-read text) */
        [data-testid="stSidebar"] {
            background-color: rgba(15, 15, 15, 0.95) !important;
        }
        
        /* TARGET SIDEBAR RADIO TEXT: Change blue to White/Gold */
        [data-testid="stSidebar"] label, [data-testid="stSidebar"] p {
            color: white !important;
            font-weight: bold !important;
        }
        
        [data-testid="stWidgetLabel"] p {
            color: #ffd700 !important; /* Makes widget labels Gold */
        }

        /* Match Card: Force dark background and white text */
        .match-card {
            background-color: rgba(40, 40, 40, 0.7) !important;
            border: 2px solid rgba(255, 255, 255, 0.1) !important;
            padding: 20px;
            border-radius: 15px;
            margin-bottom: 25px;
            text-align: center;
            color: white !important;
        }

        /* Force Player names to be white/gold regardless of phone settings */
        .player-label {
            font-size: 20px;
            font-weight: bold;
            color: #ffffff !important;
            margin-top: 10px;
            display: block;
        }

        .vs-text {
            color: #ffd700 !important;
            font-size: 32px;
            font-weight: 900;
        }

        /* Streamlit Default Overrides for Mobile */
        h1, h2, h3, p, span {
            color: white !important;
        }
        
        /* Fix for selectbox text being invisible on some mobile light modes */
        div[data-baseweb="select"] > div {
            background-color: #222 !important;
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
st.sidebar.title("🎯 PDC WORLD CHAMPS")
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
                st.sidebar.success("Success! Please Login.")
    else:
        user_attempt = st.sidebar.text_input("Username").strip()
        pwd_attempt = st.sidebar.text_input("Password", type="password")
        if st.sidebar.button("Sign In"):
            user_df = conn.read(spreadsheet=URL, worksheet="Users", ttl=0)
            match = user_df[(user_df['Username'] == user_attempt) & (user_df['Password'].astype(str) == str(pwd_attempt))]
            if not match.empty:
                st.session_state['username'] = user_attempt
                st.rerun()
            else:
                st.sidebar.error("Invalid Credentials")
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
        st.title("🏹 Today's Matchups")
        
        matches_df = conn.read(spreadsheet=URL, worksheet="Matches", ttl=60)
        preds_df = conn.read(spreadsheet=URL, worksheet="Predictions", ttl=0)
        results_df = conn.read(spreadsheet=URL, worksheet="Results", ttl=0)

        for index, row in matches_df.iterrows():
            m_id = str(row['Match_ID'])
            is_closed = m_id in results_df['Match_ID'].astype(str).values if not results_df.empty else False
            already_done = not preds_df[(preds_df['Username'] == st.session_state['username']) & (preds_df['Match_ID'].astype(str) == m_id)].empty if not preds_df.empty else False

            st.markdown('<div class="match-card">', unsafe_allow_html=True)
            c1, c2, c3 = st.columns([2, 1, 2])
            
            with c1:
                img1 = row['P1_Image'] if pd.notna(row['P1_Image']) else "https://via.placeholder.com/150"
                st.image(img1, width=120)
                st.markdown(f"<div class='player-label'>{row['Player1']}</div>", unsafe_allow_html=True)
            with c2:
                st.markdown("<div style='height: 40px;'></div>", unsafe_allow_html=True)
                st.markdown("<div class='vs-text'>VS</div>", unsafe_allow_html=True)
            with c3:
                img2 = row['P2_Image'] if pd.notna(row['P2_Image']) else "https://via.placeholder.com/150"
                st.image(img2, width=120)
                st.markdown(f"<div class='player-label'>{row['Player2']}</div>", unsafe_allow_html=True)

            st.markdown("<hr style='border-top: 1px solid rgba(255,255,255,0.1);'>", unsafe_allow_html=True)

            if is_closed:
                st.info("🎯 Match Closed")
            elif already_done:
                st.success("LOCKED IN ✅")
            else:
                sc1, sc2, sc3 = st.columns([1, 1, 1])
                with sc1: s1 = st.selectbox(f"{row['Player1']} Score", range(11), key=f"s1_{m_id}")
                with sc2: s2 = st.selectbox(f"{row['Player2']} Score", range(11), key=f"s2_{m_id}")
                with sc3:
                    st.write("") 
                    if st.button("LOCK", key=f"btn_{m_id}"):
                        st.cache_data.clear()
                        current_p = conn.read(spreadsheet=URL, worksheet="Predictions", ttl=0)
                        new_p = pd.DataFrame([{"Username": st.session_state['username'], "Match_ID": m_id, "Score": f"{s1}-{s2}"}])
                        conn.update(spreadsheet=URL, worksheet="Predictions", data=pd.concat([current_p, new_p], ignore_index=True))
                        st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

# (Remainder of the Leaderboard/Admin code stays the same)
elif page == "Leaderboard":
    st.title("🏆 Leaderboard")
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
        st.dataframe(lb, use_container_width=True, hide_index=True)

# ... [Include Rival Watch and Admin sections as per previous code] ...
