# --- PAGE: PREDICTIONS ---
if page == "Predictions":
    if st.session_state['username'] == "":
        st.warning("Please sign in to view matchups.")
    else:
        st.title("Match Predictions")
        
        # We wrap the read in a try/except block to handle API glitches gracefully
        try:
            matches_df = conn.read(spreadsheet=URL, worksheet="Matches", ttl=10) # Lower TTL helps refresh
            preds_df = conn.read(spreadsheet=URL, worksheet="Predictions", ttl=0)
            results_df = conn.read(spreadsheet=URL, worksheet="Results", ttl=0)
        except Exception as e:
            st.error("Google is busy! Please wait 5 seconds and refresh.")
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
                    
                    if st.button(f"LOCK PREDICTION: {row['Player1']} vs {row['Player2']}", key=f"btn_{m_id}"):
                        # 1. Clear cache so the next read is fresh
                        st.cache_data.clear()
                        
                        # 2. Prepare data
                        new_p = pd.DataFrame([{"Username": st.session_state['username'], "Match_ID": m_id, "Score": f"{s1}-{s2}"}])
                        
                        # 3. Update Google Sheets
                        try:
                            # IMPORTANT: We read the VERY latest data right before updating to avoid the API error
                            current_preds = conn.read(spreadsheet=URL, worksheet="Predictions", ttl=0)
                            updated_df = pd.concat([current_preds, new_p], ignore_index=True)
                            conn.update(spreadsheet=URL, worksheet="Predictions", data=updated_df)
                            
                            st.toast("Prediction Saved!", icon="🎯")
                            st.rerun()
                        except Exception:
                            st.error("Connection lost. Please try clicking Lock again in 3 seconds.")

# (Keep Leaderboard and other pages as they were)
