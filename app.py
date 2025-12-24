import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# 1. Page Configuration
st.set_page_config(page_title="Darts Predictor Pro", page_icon="🎯", layout="wide")

# 2. Connection to Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)
URL = st.secrets["connections"]["gsheets"]["spreadsheet"]

# 3. ADVANCED CSS: Mobile Container & Background Fix
def apply_pro_styling():
    st.markdown(
        f"""
        <style>
        /* Force background with your requested URL */
        .stApp {{
            background: linear-gradient(rgba(0,0,0,0.8), rgba(0,0,0,0.8)), 
                        url("https://cdn.images.express.co.uk/img/dynamic/4/590x/secondary/5856693.jpg?r=1735554407217");
            background-size: cover;
            background-position: center;
            background-attachment: scroll;
        }}

        /* Header Fix */
        h1, h2, h3, .stMarkdown p {{
            color: white !important;
        }}

        /* Sidebar Fixes */
        [data-testid="stSidebarContent"] {{
            background-color: #111111 !important;
        }}
        [data-testid="stSidebar"] label p, [data-testid="stSidebar"] p {{
            color: white !important;
            font-weight: bold !important;
        }}

        /* FIX: The Gold Border Container */
        /* We target the specific container type Streamlit uses for our cards */
        [data-testid="stVerticalBlock"] > div:has(div.match-card) {{
            border: 2px solid #ffd700 !important;
            border-radius: 15px !important;
            background-color: rgba(20, 20, 20, 0.85) !important;
            padding: 20px !important;
            margin-bottom: 25px !important;
        }}

        /* Inner card content - removal of border here to avoid double lines */
        .match-card {{
            color: white !important;
            text-align: center;
        }}

        .player-label {{
            font-size: 1.3rem;
            font-weight: bold;
            color: white !important;
            margin-top: 10px;
        }}

        .vs-text {{
            color: #ffd700 !important;
            font-size: 2.2rem;
            font-weight: 900;
            text-shadow: 2px 2px 4px #000;
        }}

        /* High-Contrast Gold Button */
        div.stButton > button {{
            background-color: #ffd700 !important;
            color: #000000 !important;
            font-weight: bold !important;
            width: 100% !important;
            border-radius: 10px !important;
            border: none !important;
            height: 3.5em !important;
            margin-top: 10px !important;
        }}

        /* Dropdown Fix */
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

            # The card div is now inside the block we target with CSS
            with st.container():
                st.markdown('<div class="match-card">', unsafe_allow_html=True)
                
                # Head to Head
                c1, c2, c3 = st.columns([2, 1, 2])
                with c1:
                    img1 = row['P1_Image'] if pd.notna(row['P1_Image']) else "https://via.placeholder.com/150"
                    st.image(img1)
                    st.markdown(f"<div class='player-label'>{row['Player1']}</div>", unsafe_allow_html=True)
                with c2:
                    st.markdown("<div class='vs-text' style='text-align:center; padding-top:20px;'>VS</div>", unsafe_allow_html=True)
                with c3:
                    img2 = row['P2_Image'] if pd.notna(row['P2_Image']) else "https://via.placeholder.com/150"
                    st.image(img2)
                    st.markdown(f"<div class='player-label'>{row['Player2']}</div>", unsafe_allow_html=True)

                if is_closed:
                    st.info("Match Closed")
                elif already_done:
                    st.success("Locked In ✅")
                else:
                    # Dropdowns
                    sc1, sc2 = st.columns(2)
                    with sc1: 
                        s1 = st.selectbox(f"{row['Player1']} Score", range(11), key=f"s1_{m_id}")
                    with sc2: 
                        s2 = st.selectbox(f"{row['Player2']} Score", range(11), key=f"s2_{m_id}")
                    
                    # Prediction Button
                    if st.button(f"LOCK PREDICTION: {row['Player1']} vs {row['Player2']}", key=f"btn_{m_id}"):
                        st.cache_data.clear()
                        current_preds = conn.read(spreadsheet=URL, worksheet="Predictions", ttl=0)
                        new_p = pd.DataFrame([{"Username": st.session_state['username'], "Match_ID": m_id, "Score": f"{s1}-{s2}"}])
                        conn.update(spreadsheet=URL, worksheet="Predictions", data=pd.concat([current_preds, new_p], ignore_index=True))
                        st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

# (Leaderboard, Rival Watch, and Admin code remains the same as your previous version)
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

elif page == "Rival Watch":
    st.title("Rival Watch")
    m_df = conn.read(spreadsheet=URL, worksheet="Matches", ttl=60)
    p_df = conn.read(spreadsheet=URL, worksheet="Predictions", ttl=60)
    if not m_df.empty:
        m_sel = st.selectbox("Check Predictions for:", m_df['Match_ID'].astype(str) + ": " + m_df['Player1'] + " vs " + m_df['Player2'])
        mid = m_sel.split(":")[0]
        match_p = p_df[p_df['Match_ID'].astype(str) == mid]
        if not match_p.empty:
            st.table(match_p[['Username', 'Score']].set_index('Username'))

elif page == "Admin":
    st.title("Admin Results Hub")
    if st.text_input("Admin Key", type="password") == "darts2025":
        m_df = conn.read(spreadsheet=URL, worksheet="Matches", ttl=60)
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
