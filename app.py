import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# 1. Page Configuration
st.set_page_config(page_title="Darts Predictor", page_icon="🎯")

# 2. Connection to Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)
SPREADSHEET_URL = st.secrets["connections"]["gsheets"]["spreadsheet"]

# 3. Sidebar Navigation
st.sidebar.title("🎯 Menu")
page = st.sidebar.radio("Go to", ["Predictions", "Leaderboard", "Admin"])

# --- PAGE: PREDICTIONS ---
if page == "Predictions":
    st.title("🎯 Submit Your Prediction")
    
    matches_df = conn.read(spreadsheet=SPREADSHEET_URL, worksheet="Matches", ttl=0)
    
    if not matches_df.empty:
        user = st.text_input("Enter your name:")
        match_choice = st.selectbox("Select Match", matches_df['Match_ID'].astype(str) + ": " + matches_df['Player1'] + " vs " + matches_df['Player2'])
        match_id = match_choice.split(":")[0]
        
        score_pred = st.text_input("Predict Score (e.g., 3-1)")
        
        if st.button("Lock Prediction"):
            # Check if fields are filled
            if user and score_pred:
                new_pred = pd.DataFrame([{"Username": user, "Match_ID": match_id, "Score": score_pred}])
                # Get existing predictions to append
                existing_preds = conn.read(spreadsheet=SPREADSHEET_URL, worksheet="Predictions", ttl=0)
                updated_preds = pd.concat([existing_preds, new_pred], ignore_index=True)
                conn.update(spreadsheet=SPREADSHEET_URL, worksheet="Predictions", data=updated_preds)
                st.success(f"Prediction saved for {user}!")
                st.balloons()
            else:
                st.warning("Please enter your name and a score.")
    else:
        st.info("No matches found in the sheet.")

# --- PAGE: LEADERBOARD ---
elif page == "Leaderboard":
    st.title("🏆 Competition Standings")
    
    try:
        p_df = conn.read(spreadsheet=SPREADSHEET_URL, worksheet="Predictions", ttl=0)
        r_df = conn.read(spreadsheet=SPREADSHEET_URL, worksheet="Results", ttl=0)

        if not r_df.empty and not p_df.empty:
            p_df['Match_ID'] = p_df['Match_ID'].astype(str)
            r_df['Match_ID'] = r_df['Match_ID'].astype(str)

            # Merge predictions with actual results
            merged = p_df.merge(r_df, on="Match_ID", suffixes=('_user', '_real'))

            def calculate_domzy_points(row):
                try:
                    # Split "3-1" into [3, 1]
                    u_p1, u_p2 = map(int, str(row['Score_user']).split('-'))
                    r_p1, r_p2 = map(int, str(row['Score_real']).split('-'))

                    # RULE 1: Exact Match (3 Points)
                    if u_p1 == r_p1 and u_p2 == r_p2:
                        return 3
                    
                    # RULE 2: Correct Winner (1 Point)
                    u_winner = "P1" if u_p1 > u_p2 else "P2"
                    r_winner = "P1" if r_p1 > r_p2 else "P2"
                    
                    if u_winner == r_winner:
                        return 1
                    
                    return 0
                except:
                    return 0 # Handles cases where score format is wrong

            merged['Points'] = merged.apply(calculate_domzy_points, axis=1)
            
            # Group by Username and sum points
            leaderboard = merged.groupby('Username')['Points'].sum().reset_index()
            leaderboard = leaderboard.sort_values(by='Points', ascending=False)
            
            st.table(leaderboard.set_index('Username'))
        else:
            st.info("Results aren't in yet. Keep an eye on the oche!")
            
    except Exception as e:
        st.error(f"Syncing Error: {e}")

# --- PAGE: ADMIN ---
elif page == "Admin":
    st.title("🛠 Admin: Enter Results")
    
    password = st.text_input("Admin Password", type="password")
    if password == "darts2025": # You can change this!
        matches_df = conn.read(spreadsheet=SPREADSHEET_URL, worksheet="Matches", ttl=0)
        
        if not matches_df.empty:
            match_to_update = st.selectbox("Select Finished Match", 
                                           matches_df['Match_ID'].astype(str) + ": " + matches_df['Player1'] + " vs " + matches_df['Player2'])
            
            official_score = st.text_input("Final Score (e.g., 3-0)")
            
            if st.button("Update Leaderboard"):
                match_id = match_to_update.split(":")[0]
                new_result = pd.DataFrame([{"Match_ID": match_id, "Score": official_score}])
                
                # Append to Results tab
                existing_results = conn.read(spreadsheet=SPREADSHEET_URL, worksheet="Results", ttl=0)
                updated_results = pd.concat([existing_results, new_result], ignore_index=True)
                conn.update(spreadsheet=SPREADSHEET_URL, worksheet="Results", data=updated_results)
                
                st.success("Result recorded! Check the Leaderboard.")
    else:
        st.write("Please enter the password to access admin tools.")
