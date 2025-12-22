import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta

# --- 1. PAGE CONFIG & STYLING ---
st.set_page_config(page_title="Darts Predictor 2025", page_icon="🎯", layout="wide")

# 🟢 PASTE YOUR GOOGLE SHEET URL HERE:
SPREADSHEET_URL = "Darts_Competition"

# Custom CSS for the "Ally Pally" Dark Mode Vibe
st.markdown("""
    <style>
    .stApp {
        background-color: #0E1117;
        color: white;
    }
    .stButton>button {
        width: 100%;
        border-radius: 5px;
        height: 3em;
        background-color: #FFD700;
        color: black;
        font-weight: bold;
    }
    [data-testid="stExpander"] {
        background-color: #1C212D;
        border: 1px solid #31333F;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATABASE CONNECTION ---
conn = st.connection("gsheets", type=GSheetsConnection)

# --- 3. LOGIN LOGIC ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

def login():
    st.title("🎯 PDC World Championship Predictor")
    with st.container():
        # Changed the label to be clearer
        username = st.text_input("Enter your name")
        password = st.text_input("Access Code", type="password")
        if st.button("Login"):
            if password == "Darts2025":  
                st.session_state.logged_in = True
                st.session_state.username = username
                st.rerun()
            else:
                st.error("Wrong access code, mate!")

if not st.session_state.logged_in:
    login()
    st.stop()

# --- 4. NAVIGATION ---
page = st.sidebar.radio("Go to", ["🎯 Predictions", "🏆 Leaderboard", "👀 Rival Watch", "🛠 Admin"])

# --- 5. PAGE: PREDICTIONS ---
if page == "🎯 Predictions":
    st.header(f"Welcome, {st.session_state.username}!")
    st.write("Submit your scores for upcoming matches. Locked 1 min before start.")
    
    # 🟢 FIXED: Added the URL and set TTL to 0 so it updates instantly
    matches_df = conn.read(spreadsheet=SPREADSHEET_URL, worksheet="Matches", ttl=0)

    
    if matches_df.empty:
        st.warning("No matches found in the Google Sheet!")
    else:
        for _, row in matches_df.iterrows():
            match_time = pd.to_datetime(row['Match_Time'])
            is_locked = datetime.now() >= (match_time - timedelta(minutes=1))
            
            with st.container(border=True):
                col1, col2, col3 = st.columns([1.5, 1, 1.5])
                with col1:
                    # Using a placeholder if image link is missing
                    p1_img = row['P1_Image'] if pd.notnull(row['P1_Image']) else "https://via.placeholder.com/80"
                    st.image(p1_img, width=80)
                    st.write(f"**{row['Player1']}**")
                with col2:
                    st.markdown("<h2 style='text-align: center;'>VS</h2>", unsafe_allow_html=True)
                    st.caption(f"Starts: {row['Match_Time']}")
                with col3:
                    p2_img = row['P2_Image'] if pd.notnull(row['P2_Image']) else "https://via.placeholder.com/80"
                    st.image(p2_img, width=80)
                    st.write(f"**{row['Player2']}**")
                
                if is_locked:
                    st.warning("🔒 Match Started - Entry Closed")
                else:
                    with st.expander("Submit Prediction"):
                        with st.form(key=f"form_{row['Match_ID']}"):
                            winner = st.selectbox("Who wins?", [row['Player1'], row['Player2']])
                            score = st.select_slider("Correct Score", options=["4-0", "4-1", "4-2", "4-3", "3-4", "2-4", "1-4", "0-4"])
                            if st.form_submit_button("Lock in Score"):
                                new_pred = pd.DataFrame([{"Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
                                                          "Username": st.session_state.username, 
                                                          "Match_ID": row['Match_ID'], "Winner": winner, "Score": score}])
                                
                                # 🟢 FIXED: Added URL to the updates
                                existing = conn.read(spreadsheet=SPREADSHEET_URL, worksheet="Predictions", ttl=0)
                                updated = pd.concat([existing, new_pred], ignore_index=True)
                                conn.update(spreadsheet=SPREADSHEET_URL, worksheet="Predictions", data=updated)
                                st.success("Prediction Saved!")

# --- 6. PAGE: LEADERBOARD & RIVAL WATCH ---
elif page == "🏆 Leaderboard" or page == "👀 Rival Watch":
    # 🟢 FIXED: Added URL to these reads
    preds = conn.read(spreadsheet=SPREADSHEET_URL, worksheet="Predictions", ttl=0)
    results = conn.read(spreadsheet=SPREADSHEET_URL, worksheet="Results", ttl=0)
    
    if page == "🏆 Leaderboard":
        st.header("Standings")
        if not results.empty and not preds.empty:
            merged = preds.merge(results, on="Match_ID")
            def get_pts(row):
                if row['Winner_x'] == row['Winner_y']:
                    return 3 if row['Score_x'] == row['Score_y'] else 1
                return 0
            merged['Points'] = merged.apply(get_pts, axis=1)
            leaderboard = merged.groupby("Username")['Points'].sum().sort_values(ascending=False).reset_index()
            st.table(leaderboard)
        else:
            st.info("No matches finished yet!")

    elif page == "👀 Rival Watch":
        st.header("What did the others guess?")
        if not preds.empty:
            st.dataframe(preds)
        else:
            st.info("No predictions yet!")

# --- 7. PAGE: ADMIN PANEL ---
elif page == "🛠 Admin":
    pwd = st.text_input("Admin Password", type="password")
    if pwd == "PDC_BOSS_2025":
        st.subheader("Enter Match Result")
        with st.form("admin_res"):
            m_id = st.text_input("Match ID")
            a_winner = st.text_input("Winner Name")
            a_score = st.text_input("Final Score (e.g. 4-2)")
            if st.form_submit_button("Publish Result"):
                # 🟢 FIXED: Added URL to Admin update
                res_df = conn.read(spreadsheet=SPREADSHEET_URL, worksheet="Results", ttl=0)
                new_res = pd.DataFrame([{"Match_ID": m_id, "Winner": a_winner, "Score": a_score}])
                updated_res = pd.concat([res_df, new_res], ignore_index=True)
                conn.update(spreadsheet=SPREADSHEET_URL, worksheet="Results", data=updated_res)
                st.success("Result Published!")
    
    st.divider()
st.header("🏆 Competition Leaderboard")

try:
    # 1. Fetch the data
    preds_df = conn.read(spreadsheet=SPREADSHEET_URL, worksheet="Predictions", ttl=0)
    results_df = conn.read(spreadsheet=SPREADSHEET_URL, worksheet="Results", ttl=0)

    # Clean the data: Ensure Match_ID is a string so they join correctly
    preds_df['Match_ID'] = preds_df['Match_ID'].astype(str)
    results_df['Match_ID'] = results_df['Match_ID'].astype(str)

    if not results_df.empty and not preds_df.empty:
        # 2. Merge Predictions and Results on Match_ID
        # Preds Score becomes 'Score_x', Results Score becomes 'Score_y'
        merged = preds_df.merge(results_df, on="Match_ID")

        def calculate_points(row):
            # Perfect Score (3 pts): Prediction matches Result exactly
            # Using your auto-generated header name 'Score'
            if str(row['Score_x']).strip() == str(row['Score_y']).strip():
                return 3
            
            # Since your current setup only has one 'Score' column,
            # we'll start with 3pts for exact matches. 
            # (We can add Winner logic once you have P1_Score/P2_Score columns!)
            return 0

        # Apply logic
        merged['Points'] = merged.apply(calculate_points, axis=1)

        # 3. Group by 'Username' (matching your B1 header)
        leaderboard = merged.groupby('Username')['Points'].sum().reset_index()
        leaderboard = leaderboard.sort_values(by='Points', ascending=False)

        # 4. Display
        st.table(leaderboard.set_index('Username'))
    else:
        st.info("Leaderboard will appear once results are entered in the Google Sheet!")

except Exception as e:
    st.error(f"Leaderboard Error: {e}")
    # This helps us see the headers if it fails
    if 'preds_df' in locals():
        st.write("Predictions headers found:", preds_df.columns.tolist())
