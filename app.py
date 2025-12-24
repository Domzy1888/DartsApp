import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# 1. Page Configuration - 'wide' is better for side-by-side matchups
st.set_page_config(page_title="Darts Predictor Pro", page_icon="🎯", layout="wide")

# 2. Connection to Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)
URL = st.secrets["connections"]["gsheets"]["spreadsheet"]

# 3. Custom CSS: Fixed Background & Match Cards
def apply_pro_styling():
    st.markdown(
        """
        <style>
        /* Fixed Background Image */
        [data-testid="stAppViewContainer"] {
            background-image: url("https://images.unsplash.com/photo-1547427735-33750bb20671?q=80&w=2000");
            background-attachment: fixed;
            background-size: cover;
        }

        /* Dark Overlay for text clarity */
        [data-testid="stAppViewContainer"]::before {
            content: "";
            position: fixed;
            top: 0; left: 0; width: 100%; height: 100%;
            background-color: rgba(0, 0, 0, 0.75);
            z-index: -1;
        }

        /* Sidebar Glassmorphism */
        [data-testid="stSidebar"] {
            background-color: rgba(20, 20, 20, 0.85) !important;
            backdrop-filter: blur(10px);
        }

        /* The Match Card */
        .match-card {
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.15);
            padding: 25px;
            border-radius: 20px;
            margin-bottom: 30px;
            backdrop-filter: blur(15px);
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.8);
            text-align: center;
        }

        .player-label {
            font-size: 22px;
            font-weight: 800;
            color: #ffffff;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-top: 15px;
        }

        .vs-text {
            color: #ffd700;
            font-size: 36px;
            font-weight: 900;
            margin: 0;
            text-shadow: 2px 2px 4px #000;
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
            
            # Checks
            is_closed = m_id in results_df['Match_ID'].astype(str).values if not results_df.empty else False
            already_done = not preds_df[(preds_df['Username'] == st.session_state['username']) & (preds_df['Match_ID'].astype(str) == m_id)].empty if not preds_df.empty else False

            # Match Card Container
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
                st.info("🎯 RESULTS ARE IN - Match Closed")
            elif already_done:
                st.success("LOCKED IN ✅")
            else:
                # Prediction Inputs
                sc1, sc2, sc3 = st.columns([1, 1, 1])
                with sc1: s1 = st.selectbox(f"{row['Player1']} Score", range(11), key=f"s1_{m_id}")
                with sc2: s2 = st.selectbox(f"{row['Player2']} Score", range(11), key=f"s2_{m_id}")
                with sc3:
                    st.write("") # Spacer
                    if st.button("LOCK SCORE", key=f"btn_{m_id}"):
                        st.cache_data.clear()
                        # Final verification
                        fresh_res = conn.read(spreadsheet=URL, worksheet="Results", ttl=0)
                        if m_id in fresh_res['Match_ID'].astype(str).values:
                            st.error("Too late!")
                        else:
                            current_p = conn.read(spreadsheet=URL, worksheet="Predictions", ttl=0)
                            new_p = pd.DataFrame([{"Username": st.session_state['username'], "Match_ID": m_id, "Score": f"{s1}-{s2}"}])
                            conn.update(spreadsheet=URL, worksheet="Predictions", data=pd.concat([current_p, new_p], ignore_index=True))
                            st.balloons()
                            st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

# --- PAGE: LEADERBOARD ---
elif page == "Leaderboard":
    st.title("🏆 Hall of Fame")
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
    else:
        st.info("Tournament just starting! No results recorded yet.")

# --- RIVAL WATCH ---
elif page == "Rival Watch":
    st.title("👀 Watch the Field")
    m_df = conn.read(spreadsheet=URL, worksheet="Matches", ttl=60)
    p_df = conn.read(spreadsheet=URL, worksheet="Predictions", ttl=60)
    if not m_df.empty:
        m_sel = st.selectbox("Check Predictions for:", m_df['Match_ID'].astype(str) + ": " + m_df['Player1'] + " vs " + m_df['Player2'])
        mid = m_sel.split(":")[0]
        match_p = p_df[p_df['Match_ID'].astype(str) == mid]
        if not match_p.empty:
            st.table(match_p[['Username', 'Score']].set_index('Username'))
        else:
            st.write("No predictions for this match yet.")

# --- ADMIN ---
elif page == "Admin":
    st.title("🛠 Admin Results Hub")
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
