import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# 1. Page Configuration
st.set_page_config(page_title="Darts Predictor", page_icon="🎯")

# 2. Connection to Google Sheets
# Ensure your SPREADSHEET_URL is set in your secrets.toml
conn = st.connection("gsheets", type=GSheetsConnection)
SPREADSHEET_URL = st.secrets["connections"]["gsheets"]["spreadsheet"]

# 3. Sidebar Navigation
st.sidebar.title("🎯 Menu")
page = st.sidebar.radio("Go to", ["Predictions", "Leaderboard", "Admin"])

# --- PAGE: PREDICTIONS ---
if page == "Predictions":
    st.title("🎯 Submit Your Prediction")
    
    # Load Matches
    matches_df = conn.read(spreadsheet=SPREADSHEET_URL, worksheet="Matches", ttl=0)
    
    if not matches_df.empty:
        user = st.text_input("Enter your name (e.g., Domzy):")
        match_choice = st.selectbox("Select Match", matches_df['Match_ID'].astype(str) + ": " + matches_df['Player1'] + " vs " + matches_df['Player2'])
        match_id = match_choice.split(":")[0]
        
        score_pred = st.text_input("Predict Score (e.g., 3-1):")
        
        if st.button("Lock Prediction"):
            # logic to append to 'Predictions' sheet
            new_data = pd.DataFrame([{"Username": user, "Match_ID": match_id, "Score": score_pred}])
            # You can add the conn.update logic here to save it
            st.success(f"Prediction for {match_choice} saved!")
    else:
        st.info("No matches available yet.")

# --- PAGE: LEADERBOARD ---
elif page == "Leaderboard":
    st.title("🏆 Competition Standings")
    
    try:
        p_df = conn.read(spreadsheet=SPREADSHEET_URL, worksheet="Predictions", ttl=0)
        r_df = conn.read(spreadsheet=SPREADSHEET_URL, worksheet="Results", ttl=0)

        if not r_df.empty and not p_df.empty:
            p_df['Match_ID'] = p_df['Match_ID'].astype(str)
            r_df['Match_ID'] = r_df['Match_ID'].astype(str)

            # Join the tables
            merged = p_df.merge(r_df, on="Match_ID")

            def calc_pts(row):
                # Compare User Score (Score_x) to Actual Score (Score_y)
                if str(row['Score_x']).strip() == str(row['Score_y']).strip():
                    return 3
                return 0

            merged['Points'] = merged.apply(calc_pts, axis=1)
            
            # Group by Username
            leaderboard = merged.groupby('Username')['Points'].sum().reset_index()
            leaderboard = leaderboard.sort_values(by='Points', ascending=False)
            
            st.table(leaderboard.set_index('Username'))
        else:
            st.info("No results recorded yet. Check back after the match!")
            
    except Exception as e:
        st.error(f"Error: {e}")

# --- PAGE: ADMIN ---
elif page == "Admin":
    st.title("🛠 Admin: Enter Results")
    st.write("Enter the final match scores here to update the leaderboard.")
    # You can add a form here later to update the 'Results' tab automatically!
