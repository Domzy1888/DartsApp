import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# 1. Page Configuration
st.set_page_config(page_title="Darts Predictor Pro", page_icon="🎯")

# 2. Connection to Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)
SPREADSHEET_URL = st.secrets["connections"]["gsheets"]["spreadsheet"]

# 3. Session State for Login
if 'username' not in st.session_state:
    st.session_state['username'] = ""

# --- SIDEBAR LOGIN & NAV ---
st.sidebar.title("👤 User Access")
if st.session_state['username'] == "":
    user_input = st.sidebar.text_input("Enter your name to login:")
    if st.sidebar.button("Login"):
        if user_input:
            st.session_state['username'] = user_input.strip()
            st.rerun()
else:
    st.sidebar.write(f"Logged in as: **{st.session_state['username']}**")
    if st.sidebar.button("Logout"):
        st.session_state['username'] = ""
        st.rerun()

st.sidebar.divider()
st.sidebar.title("🎯 Menu")
# Added "Rival Watch" to the list below
page = st.sidebar.radio("Go to", ["Predictions", "Leaderboard", "Rival Watch", "Admin"])

# --- PAGE: PREDICTIONS ---
if page == "Predictions":
    if st.session_state['username'] == "":
        st.warning("Please login via the sidebar to make predictions.")
    else:
        st.title(f"🎯 Predictions for {st.session_state['username']}")
        
        matches_df = conn.read(spreadsheet=SPREADSHEET_URL, worksheet="Matches", ttl=60)
        preds_df = conn.read(spreadsheet=SPREADSHEET_URL, worksheet="Predictions", ttl=60)

        if not matches_df.empty:
            match_choice = st.selectbox("Select Match", matches_df['Match_ID'].astype(str) + ": " + matches_df['Player1'] + " vs " + matches_df['Player2'])
            match_id = match_choice.split(":")[0]

            # Check for existing prediction
            already_predicted = False
            if not preds_df.empty:
                check = preds_df[(preds_df['Username'] == st.session_state['username']) & (preds_df['Match_ID'].astype(str) == str(match_id))]
                if not check.empty:
                    already_predicted = True

            if already_predicted:
                st.success("✅ You have already submitted a prediction for this match.")
            else:
                col1, col2 = st.columns(2)
                with col1:
                    p1_score = st.selectbox("Player 1 Score", range(0, 11))
                with col2:
                    p2_score = st.selectbox("Player 2 Score", range(0, 11))
                
                if st.button("Lock Prediction"):
                    score_string = f"{p1_score}-{p2_score}"
                    new_pred = pd.DataFrame([{"Username": st.session_state['username'], "Match_ID": match_id, "Score": score_string}])
                    
                    updated_preds = pd.concat([preds_df, new_pred], ignore_index=True)
                    conn.update(spreadsheet=SPREADSHEET_URL, worksheet="Predictions", data=updated_preds)
                    st.success("Prediction locked in!")
                    st.balloons()
                    st.rerun()
        else:
            st.info("No matches available yet.")

# --- PAGE: LEADERBOARD ---
elif page == "Leaderboard":
    st.title("🏆 Competition Standings")
    p_df = conn.read(spreadsheet=SPREADSHEET_URL, worksheet="Predictions", ttl=60)
    r_df = conn.read(spreadsheet=SPREADSHEET_URL, worksheet="Results", ttl=60)

    if not r_df.empty and not p_df.empty:
        p_df['Match_ID'] = p_df['Match_ID'].astype(str)
        r_df['Match_ID'] = r_df['Match_ID'].astype(str)
        merged = p_df.merge(r_df, on="Match_ID", suffixes=('_user', '_real'))

        def calc_pts(row):
            try:
                u_p1, u_p2 = map(int, str(row['Score_user']).split('-'))
                r_p1, r_p2 = map(int, str(row['Score_real']).split('-'))
                if u_p1 == r_p1 and u_p2 == r_p2: return 3
                if (u_p1 > u_p2 and r_p1 > r_p2) or (u_p1 < u_p2 and r_p1 < r_p2): return 1
                return 0
            except: return 0

        merged['Points'] = merged.apply(calc_pts, axis=1)
        leaderboard = merged.groupby('Username')['Points'].sum().reset_index()
        st.table(leaderboard.sort_values(by='Points', ascending=False).set_index('Username'))
    else:
        st.info("Results aren't in yet.")

# --- PAGE: RIVAL WATCH ---
elif page == "Rival Watch":
    st.title("👀 Rival Watch")
    matches_df = conn.read(spreadsheet=SPREADSHEET_URL, worksheet="Matches", ttl=60)
    preds_df = conn.read(spreadsheet=SPREADSHEET_URL, worksheet="Predictions", ttl=60)

    if not matches_df.empty and not preds_df.empty:
        match_choice = st.selectbox("Select Match to Inspect", matches_df['Match_ID'].astype(str) + ": " + matches_df['Player1'] + " vs " + matches_df['Player2'])
        match_id = match_choice.split(":")[0]
        
        match_preds = preds_df[preds_df['Match_ID'].astype(str) == str(match_id)]
        if not match_preds.empty:
            st.table(match_preds[['Username', 'Score']].set_index('Username'))
        else:
            st.info("No predictions yet for this match.")
    else:
        st.info("Nothing to watch yet.")

# --- PAGE: ADMIN ---
elif page == "Admin":
    st.title("🛠 Admin: Results Entry")
    pwd = st.text_input("Admin Password", type="password")
    if pwd == "darts2025":
        matches_df = conn.read(spreadsheet=SPREADSHEET_URL, worksheet="Matches", ttl=60)
        if not matches_df.empty:
            match_to_res = st.selectbox("Which match finished?", matches_df['Match_ID'].astype(str) + ": " + matches_df['Player1'] + " vs " + matches_df['Player2'])
            c1, c2 = st.columns(2)
            with c1: rs1 = st.selectbox("Actual P1 Score", range(0, 11))
            with c2: rs2 = st.selectbox("Actual P2 Score", range(0, 11))
            
            if st.button("Submit Official Result"):
                m_id = match_to_res.split(":")[0]
                res_df = conn.read(spreadsheet=SPREADSHEET_URL, worksheet="Results", ttl=60)
                new_res = pd.DataFrame([{"Match_ID": m_id, "Score": f"{rs1}-{rs2}"}])
                conn.update(spreadsheet=SPREADSHEET_URL, worksheet="Results", data=pd.concat([res_df, new_res], ignore_index=True))
                st.success("Result recorded!")
