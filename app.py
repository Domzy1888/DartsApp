if st.sidebar.button("Go"):
u_df = get_data("Users")
if not u_df.empty:
            match = u_
            match = u_df[(u_df['Username'].astype(str) == u_attempt) & (u_df['Password'].astype(str) == str(p_attempt))]
            if not match.empty:
                st.session_state['username'] = u_attempt
                st.rerun()
            else: st.sidebar.error("Invalid Login")
else:
    st.sidebar.write(f"Logged in: **{st.session_state['username']}**")
    if st.sidebar.button("Logout"):
        st.session_state['username'] = ""; st.rerun()

st.sidebar.divider()
page = st.sidebar.radio("Navigate", ["Predictions", "Leaderboard", "Rival Watch", "Admin"])

# --- SCORING ENGINE (ID Safe) ---
def get_leaderboard_data():
    p_df = get_data("Predictions")
    r_df = get_data("Results")
    if p_df.empty or r_df.empty: return pd.DataFrame(columns=['Username', 'Current Points'])
    
    # ID Unification: Treat everything as a clean string
    p_df = p_df.dropna(subset=['Match_ID'])
    r_df = r_df.dropna(subset=['Match_ID'])
    p_df['MID'] = p_df['Match_ID'].astype(str).str.replace('.0', '', regex=False)
    r_df['MID'] = r_df['Match_ID'].astype(str).str.replace('.0', '', regex=False)
    
    merged = p_df.merge(r_df, on="MID", suffixes=('_u', '_r'))
    def calc(r):
        try:
            u1, u2 = map(int, str(r['Score_u']).split('-'))
            r1, r2 = map(int, str(r['Score_r']).split('-'))
            if u1 == r1 and u2 == r2: return 3
            return 1 if (u1 > u2 and r1 > r2) or (u1 < u2 and r1 < r2) else 0
        except: return 0
    merged['Pts'] = merged.apply(calc, axis=1)
    return merged.groupby('Username')['Pts'].sum().reset_index().rename(columns={'Pts': 'Current Points'}).sort_values('Current Points', ascending=False)

# --- PAGE: PREDICTIONS (With Date Filter & Timer) ---
if page == "Predictions":
    if st.session_state['username'] == "":
        st.warning("Please sign in.")
    else:
        st.title("Upcoming Matches")
        m_df = get_data("Matches").dropna(subset=['Match_ID', 'Player1', 'Date'])
        p_df = get_data("Predictions")
        r_df = get_data("Results")
        now = datetime.now()

        # Date Filter
        m_df['Date_Parsed'] = pd.to_datetime(m_df['Date'], errors='coerce')
        m_df = m_df.dropna(subset=['Date_Parsed'])
        days = sorted(m_df['Date_Parsed'].dt.date.unique())
        
        if days:
            sel_day = st.selectbox("📅 Select Match Day", days)
            day_matches = m_df[m_df['Date_Parsed'].dt.date == sel_day]
            
            open_list = []
            for _, row in day_matches.iterrows():
                mid = str(row['Match_ID']).replace('.0', '')
                if not r_df.empty and mid in r_df['Match_ID'].astype(str).str.replace('.0', '', regex=False).values: continue
                
                # Countdown Logic
                diff = row['Date_Parsed'] - now
                mins = diff.total_seconds() / 60
                
                if mins > 60: timer = f"<div class='timer-text' style='color:#00ff00;'>Starts in {int(mins/60)}h {int(mins%60)}m</div>"
                elif 10 < mins <= 60: timer = f"<div class='timer-text' style='color:#ffd700;'>Starts in {int(mins)}m</div>"
                elif 0 < mins <= 10: timer = f"<div class='timer-text timer-urgent'>⚠️ STARTING IN {int(mins)}m</div>"
                else: timer = "<div class='timer-text' style='color:#ff4b4b;'>Locked / Live</div>"

                st.markdown(f"<div class='match-card'>{timer}<div class='match-wrapper'><div class='player-box'><img src=\"{row.get('P1_Image', '')}\" class='player-img'><div class='player-name'>{row['Player1']}</div></div><div class='vs-text'>VS</div><div class='player-box'><img src=\"{row.get('P2_Image', '')}\" class='player-img'><div class='player-name'>{row['Player2']}</div></div></div></div>", unsafe_allow_html=True)

                done = not p_df[(p_df['Username'] == st.session_state['username']) & (p_df['Match_ID'].astype(str).str.replace('.0', '', regex=False) == mid)].empty if not p_df.empty else False

                if done: st.success("Prediction Locked ✅")
                elif mins <= 0: st.error("Closed 🔒")
                else:
                    open_list.append(mid)
                    c1, c2 = st.columns(2)
                    with c1: s1 = st.selectbox(f"{row['Player1']}", range(11), key=f"s1_{mid}")
                    with c2: s2 = st.selectbox(f"{row['Player2']}", range(11), key=f"s2_{mid}")
                    if 'temp' not in st.session_state: st.session_state.temp = {}
                    st.session_state.temp[mid] = f"{s1}-{s2}"

            if open_list and st.button("🔒 LOCK ALL PREDICTIONS"):
                new = [{"Username": st.session_state['username'], "Match_ID": m, "Score": st.session_state.temp.get(m, "0-0")} for m in open_list]
                conn.update(spreadsheet=URL, worksheet="Predictions", data=pd.concat([p_df, pd.DataFrame(new)], ignore_index=True))
                st.cache_data.clear(); st.success("Saved!"); time.sleep(1); st.rerun()

# --- PAGE: RIVAL WATCH (Fixed Empty Table) ---
elif page == "Rival Watch":
    st.title("👀 Rival Watch")
    m_df = get_data("Matches").dropna(subset=['Match_ID', 'Player1'])
    p_df = get_data("Predictions")
    
    opts = [f"{str(r['Match_ID']).replace('.0', '')}: {r['Player1']} vs {r['Player2']}" for _, r in m_df.iterrows()]
    if opts:
        sel = st.selectbox("Pick a Match:", opts)
        target = sel.split(":")[0]
        lb = get_leaderboard_data()
        if not p_df.empty:
            p_df['MID'] = p_df['Match_ID'].astype(str).str.replace('.0', '', regex=False)
            match_p = p_df[p_df['MID'] == target].drop_duplicates('Username', keep='last')
            rivals = match_p.merge(lb, on="Username", how="left").fillna(0)
            rivals['Current Points'] = rivals['Current Points'].astype(int)
            st.dataframe(rivals[['Username', 'Score', 'Current Points']], hide_index=True, width="stretch")

# --- PAGE: LEADERBOARD ---
elif page == "Leaderboard":
    st.title("🏆 Leaderboard")
    st.dataframe(get_leaderboard_data(), hide_index=True, width="stretch")

# --- PAGE: ADMIN ---
elif page == "Admin":
    st.title("⚙️ Admin Hub")
    if st.text_input("Admin Password", type="password") == "darts2025":
        m_df = get_data("Matches").dropna(subset=['Match_ID', 'Player1'])
        target = st.selectbox("Select Match", [f"{str(r['Match_ID']).replace('.0', '')}: {r['Player1']} vs {r['Player2']}" for _, r in m_df.iterrows()])
        c1, c2 = st.columns(2)
        with c1: r1 = st.selectbox("P1", range(11))
        with c2: r2 = st.selectbox("P2", range(11))
        if st.button("Submit Result"):
            old = get_data("Results")
            new = pd.concat([old, pd.DataFrame([{"Match_ID": target.split(":")[0], "Score": f"{r1}-{r2}"}])])
            conn.update(spreadsheet=URL, worksheet="Results", data=new)
            st.cache_data.clear(); st.success("Result Published!"); st.rerun()
