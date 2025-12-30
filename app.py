import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import time
from datetime import datetime, timedelta
import extra_streamlit_components as stx
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# 1. Page Configuration
st.set_page_config(page_title="PDC Predictor Pro", page_icon="🎯", layout="wide")

# --- 2. GMAIL MAILING ENGINE ---
def send_reminders():
    try:
        conn_internal = st.connection("gsheets", type=GSheetsConnection)
        spreadsheet_url = st.secrets["connections"]["gsheets"]["spreadsheet"]
        u_df = conn_internal.read(spreadsheet=spreadsheet_url, worksheet="Users", ttl=0)
        p_df = conn_internal.read(spreadsheet=spreadsheet_url, worksheet="Predictions", ttl=0)
        m_df = conn_internal.read(spreadsheet=spreadsheet_url, worksheet="Matches", ttl=0)
        today = datetime.now().date()
        m_df['Date_Parsed'] = pd.to_datetime(m_df['Date']).dt.date
        todays_mids = m_df[m_df['Date_Parsed'] == today]['Match_ID'].astype(str).str.replace('.0', '', regex=False).tolist()
        if not todays_mids: return "No matches today."
        users_with_email = u_df[u_df['Email'].astype(str).str.contains("@", na=False)]
        remind_count = 0
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(st.secrets["gmail"]["user"], st.secrets["gmail"]["password"])
        for _, user in users_with_email.iterrows():
            user_preds = p_df[p_df['Username'] == user['Username']]
            user_pred_mids = user_preds['Match_ID'].astype(str).str.replace('.0', '', regex=False).tolist()
            if not all(mid in user_pred_mids for mid in todays_mids):
                msg = MIMEMultipart()
                msg['From'] = f"PDC Predictor <{st.secrets['gmail']['user']}>"
                msg['To'] = user['Email']
                msg['Subject'] = "🎯 Darts Reminder: Matches Start Today!"
                body = f"Hi {user['Username']},\n\nMatches are starting today! Don't forget to head over to the app and lock in your predictions.\n\nGood luck!"
                msg.attach(MIMEText(body, 'plain'))
                server.send_message(msg)
                remind_count += 1
        server.quit()
        return f"Success: {remind_count} reminders sent."
    except Exception as e: return f"Gmail Error: {str(e)}"

# GitHub Trigger Logic
if st.query_params.get("trigger_reminders") == "true":
    result = send_reminders()
    st.write(result)
    st.stop()

# --- 3. COOKIE & SESSION INITIALIZATION ---
if 'cookie_manager' not in st.session_state:
    st.session_state['cookie_manager'] = stx.CookieManager(key="pdc_global_cookie_manager")

cookie_manager = st.session_state['cookie_manager']
if 'username' not in st.session_state: st.session_state['username'] = ""
if 'audio_played' not in st.session_state: st.session_state['audio_played'] = False
if 'logging_out' not in st.session_state: st.session_state['logging_out'] = False

if st.session_state['username'] == "" and not st.session_state['logging_out']:
    saved_user = cookie_manager.get(cookie="pdc_user_login")
    if saved_user:
        st.session_state['username'] = saved_user
        st.rerun()

# --- 4. PREFERENCES & DATA ---
saved_mute = cookie_manager.get(cookie="pdc_mute")
initial_mute = True if saved_mute == "True" else False
saved_page = cookie_manager.get(cookie="pdc_page")
page_options = ["Predictions", "Leaderboard", "Rival Watch", "Highlights", "Admin"]
initial_page_index = page_options.index(saved_page) if saved_page in page_options else 0
page = saved_page if saved_page in page_options else "Predictions"

CHASE_THE_SUN_URL = "https://github.com/Domzy1888/DartsApp/raw/refs/heads/main/ytmp3free.cc_darts-chase-the-sun-extended-15-minutes-youtubemp3free.org.mp3"
conn = st.connection("gsheets", type=GSheetsConnection)
URL = st.secrets["connections"]["gsheets"]["spreadsheet"]

@st.cache_data(ttl=5)
def get_data(worksheet):
    try:
        df = conn.read(spreadsheet=URL, worksheet=worksheet, ttl=0)
        return df.dropna(how='all')
    except:
        return pd.DataFrame()

# --- 5. STYLING ---
st.markdown("""
    <style>
    @keyframes pulse-red { 0% { color: #ff4b4b; opacity: 1; } 50% { color: #ff0000; opacity: 0.5; } 100% { color: #ff4b4b; opacity: 1; } }
    .stApp { background: linear-gradient(rgba(0,0,0,0.6), rgba(0,0,0,0.6)), url("https://cdn.images.express.co.uk/img/dynamic/4/590x/secondary/5856693.jpg?r=1735554407217"); background-size: cover; background-attachment: fixed; }
    h1, h2, h3, p, label { color: white !important; font-weight: bold; }
    [data-testid="stSidebarContent"] { background-color: #111111 !important; }
    .match-card { border: 2px solid #ffd700; border-radius: 20px; background-image: linear-gradient(rgba(0,0,0,0.5), rgba(0,0,0,0.5)), url("https://news.paddypower.com/assets/uploads/2023/12/Paddy-Power-World-Darts-Championship.jpg"); background-size: cover; background-position: center; padding: 20px; margin-bottom: 10px; }
    .match-wrapper { display: flex; align-items: flex-start; justify-content: space-around; width: 100%; gap: 5px; }
    .player-box { flex: 1; display: flex; flex-direction: column; align-items: center; text-align: center; }
    .player-img { width: 100%; max-width: 120px; border-radius: 10px; border: none !important; }
    .vs-text { color: #ffd700 !important; font-size: 1.5rem !important; font-weight: 900 !important; margin-top: 40px; }
    .player-name { font-size: 1.1rem !important; font-weight: 900 !important; color: #ffd700 !important; margin-top: 10px; min-height: 3em; }
    .timer-text { font-weight: bold; font-size: 1.1rem; text-align: center; margin-bottom: 15px; }
    .timer-urgent { animation: pulse-red 1s infinite; font-weight: 900; }
    div.stButton > button, div.stFormSubmitButton > button, .custom-link-button { background-color: #ffd700 !important; color: #000000 !important; font-weight: 900 !important; border-radius: 10px !important; width: 100% !important; border: none !important; text-decoration: none !important; display: inline-block; padding: 10px 20px; text-align: center; cursor: pointer; }
    div.stButton > button p, div.stFormSubmitButton > button p { color: #000000 !important; margin: 0; }
    
    /* Dialog Modal Custom Styling */
    div[data-testid="stDialog"] > div {
        background-image: linear-gradient(rgba(0,0,0,0.85), rgba(0,0,0,0.85)), url("https://news.paddypower.com/assets/uploads/2023/12/Paddy-Power-World-Darts-Championship.jpg");
        background-size: cover;
        background-position: center;
        border: 2px solid #ffd700;
        border-radius: 15px;
    }
    .stat-row-ui { display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px; }
    .stat-bar-bg { height: 12px; background: #222; border-radius: 6px; overflow: hidden; display: flex; width: 100%; border: 1px solid #444; }
    .bar-gold { background: #ffd700; height: 100%; }
    .bar-blue { background: #007bff; height: 100%; }
    .player-label-modal { color: white; font-size: 14px; font-weight: bold; text-transform: uppercase; margin-top: 10px; }
    </style>
""", unsafe_allow_html=True)

# --- 6. H2H POP-UP ENGINE ---
@st.dialog("TALE OF THE TAPE", width="large")
def show_h2h(p1, p2):
    s_df = get_data("Stats")
    d1 = s_df[s_df['Player'] == p1].iloc[0] if not s_df.empty and p1 in s_df['Player'].values else None
    d2 = s_df[s_df['Player'] == p2].iloc[0] if not s_df.empty and p2 in s_df['Player'].values else None

    # Column configuration to put players on the wings
    c1, c2, c3 = st.columns([1, 2, 1])

    with c1: # Left Player (Gold)
        img1 = d1['Player_Image'] if d1 is not None else ""
        st.markdown(f"<div style='text-align:center;'><img src='{img1}' style='width:100%; border-radius:10px; border:2px solid #ffd700;'><div class='player-label-modal'>{p1}</div></div>", unsafe_allow_html=True)

    with c3: # Right Player (Blue)
        img2 = d2['Player_Image'] if d2 is not None else ""
        st.markdown(f"<div style='text-align:center;'><img src='{img2}' style='width:100%; border-radius:10px; border:2px solid #007bff;'><div class='player-label-modal'>{p2}</div></div>", unsafe_allow_html=True)

    with c2: # Central Stats
        stats_list = [
            ("WORLD TITLES", "World_Titles"),
            ("PDC TITLES", "PDC_Titles"),
            ("AVG", "Tournament_Avg"),
            ("CHECKOUT %", "Checkout_Pct"),
            ("180s", "180s")
        ]
        
        for label, key in stats_list:
            v1 = float(d1[key]) if d1 is not None else 0
            v2 = float(d2[key]) if d2 is not None else 0
            total = v1 + v2 if (v1 + v2) > 0 else 1
            w1, w2 = (v1 / total) * 100, (v2 / total) * 100
            
            st.markdown(f"""
                <div style="margin-bottom:12px;">
                    <div class="stat-row-ui">
                        <span style="color:#ffd700; font-size:18px;">{v1}</span>
                        <span style="color:#aaa; font-size:10px; font-weight:bold;">{label}</span>
                        <span style="color:#007bff; font-size:18px;">{v2}</span>
                    </div>
                    <div class="stat-bar-bg">
                        <div class="bar-gold" style="width:{w1}%;"></div>
                        <div class="bar-blue" style="width:{w2}%;"></div>
                    </div>
                </div>
            """, unsafe_allow_html=True)

# --- 7. SIDEBAR & AUTH ---
st.sidebar.title("🎯 PDC PREDICTOR")
mute_audio = st.sidebar.toggle("🔈 Mute Walk-on Music", value=initial_mute)
if mute_audio != initial_mute:
    cookie_manager.set("pdc_mute", str(mute_audio), expires_at=datetime.now() + timedelta(days=30))

st.sidebar.divider()

if st.session_state['username'] == "":
    auth_mode = st.sidebar.radio("Entry", ["Login", "Register"])
    u_attempt = st.sidebar.text_input("Username").strip()
    p_attempt = st.sidebar.text_input("Password", type="password")
    if auth_mode == "Register":
        email_val = st.sidebar.text_input("Email (Optional)").strip()
    if st.sidebar.button("Go"):
        u_df = get_data("Users")
        if auth_mode == "Register":
            if u_attempt and p_attempt:
                if not u_df.empty and u_attempt in u_df['Username'].astype(str).values: st.sidebar.error("Taken.")
                else:
                    new_user = pd.DataFrame([{"Username": u_attempt, "Password": p_attempt, "Email": email_val if 'email_val' in locals() else ""}])
                    conn.update(spreadsheet=URL, worksheet="Users", data=pd.concat([u_df, new_user], ignore_index=True))
                    st.sidebar.success("Created! Login now."); time.sleep(1); st.rerun()
        else:
            if not u_df.empty:
                match = u_df[(u_df['Username'].astype(str) == u_attempt) & (u_df['Password'].astype(str) == str(p_attempt))]
                if not match.empty:
                    st.session_state['username'] = u_attempt
                    st.session_state['logging_out'] = False
                    cookie_manager.set("pdc_user_login", u_attempt, expires_at=datetime.now() + timedelta(days=30))
                    st.rerun()
                else: st.sidebar.error("Invalid Login")
else:
    if not mute_audio and not st.session_state['audio_played']:
        st.audio(CHASE_THE_SUN_URL, format="audio/mp3", autoplay=True)
        st.session_state['audio_played'] = True
    st.sidebar.write(f"Logged in: **{st.session_state['username']}**")
    page_sel = st.sidebar.radio("Navigate", page_options, index=initial_page_index)
    if page_sel != saved_page:
        cookie_manager.set("pdc_page", page_sel, expires_at=datetime.now() + timedelta(days=30))
        page = page_sel 
    if st.sidebar.button("Logout"):
        st.session_state['logging_out'] = True
        st.session_state['username'] = ""; st.session_state['audio_played'] = False
        cookie_manager.delete("pdc_user_login")
        time.sleep(0.5); st.rerun()

# --- 8. PAGES ---
if page == "Predictions":
    if st.session_state['username'] == "": st.warning("Please sign in.")
    else:
        st.title("Upcoming Matches")
        m_df = get_data("Matches").dropna(subset=['Match_ID', 'Player1', 'Date'])
        p_df = get_data("Predictions"); r_df = get_data("Results"); now = datetime.now()
        m_df['Date_Parsed'] = pd.to_datetime(m_df['Date'], errors='coerce')
        days = sorted(m_df['Date_Parsed'].dt.date.unique())
        if days:
            sel_day = st.selectbox("📅 Select Match Day", days)
            day_matches = m_df[m_df['Date_Parsed'].dt.date == sel_day]
            for _, row in day_matches.iterrows():
                mid = str(row['Match_ID']).replace('.0', '')
                if not r_df.empty and mid in r_df['Match_ID'].astype(str).str.replace('.0', '', regex=False).values: continue
                diff = row['Date_Parsed'] - now
                mins = diff.total_seconds() / 60
                if mins > 60: timer = f"<div class='timer-text' style='color:#00ff00;'>Starts in {int(mins/60)}h {int(mins%60)}m</div>"
                elif 0 < mins <= 60: timer = f"<div class='timer-text timer-urgent'>⚠️ STARTING SOON</div>"
                else: timer = "<div class='timer-text' style='color:#ff4b4b;'>Locked / Live</div>"
                
                # Container for Match Card
                st.markdown(f"<div class='match-card'>{timer}<div class='match-wrapper'><div class='player-box'><img src=\"{row.get('P1_Image', '')}\" class='player-img'><div class='player-name'>{row['Player1']}</div></div><div class='vs-text'>VS</div><div class='player-box'><img src=\"{row.get('P2_Image', '')}\" class='player-img'><div class='player-name'>{row['Player2']}</div></div></div></div>", unsafe_allow_html=True)
                
                # H2H Stats Button
                if st.button(f"📊 View Stats: {row['Player1']} vs {row['Player2']}", key=f"btn_{mid}"):
                    show_h2h(row['Player1'], row['Player2'])

                with st.form(f"form_{mid}", clear_on_submit=False):
                    done = not p_df[(p_df['Username'] == st.session_state['username']) & (p_df['Match_ID'].astype(str).str.replace('.0', '', regex=False) == mid)].empty if not p_df.empty else False
                    if done: st.success("Prediction Locked ✅")
                    elif mins <= 0: st.error("Closed 🔒")
                    else:
                        c1, c2 = st.columns(2)
                        with c1: s1 = st.selectbox(f"{row['Player1']}", range(11), key=f"s1_{mid}")
                        with c2: s2 = st.selectbox(f"{row['Player2']}", range(11), key=f"s2_{mid}")
                        if st.form_submit_button("🔒 LOCK PREDICTION"):
                            new_p = pd.DataFrame([{"Username": st.session_state['username'], "Match_ID": mid, "Score": f"{s1}-{s2}"}])
                            conn.update(spreadsheet=URL, worksheet="Predictions", data=pd.concat([p_df, new_p], ignore_index=True))
                            st.cache_data.clear(); st.success("Saved!"); time.sleep(1); st.rerun()

elif page == "Leaderboard":
    st.title("🏆 Leaderboard")
    p_df = get_data("Predictions"); r_df = get_data("Results")
    if p_df.empty or r_df.empty: st.write("No scores yet.")
    else:
        p_df['MID'] = p_df['Match_ID'].astype(str).str.replace('.0', '', regex=False)
        r_df['MID'] = r_df['Match_ID'].astype(str).str.replace('.0', '', regex=False)
        merged = p_df.merge(r_df, on="MID", suffixes=('_u', '_r'))
        def calc(r):
            try:
                u1, u2 = map(int, str(r['Score_u']).split('-')); r1, r2 = map(int, str(r['Score_r']).split('-'))
                if u1 == r1 and u2 == r2: return 3
                return 1 if (u1 > u2 and r1 > r2) or (u1 < u2 and r1 < r2) else 0
            except: return 0
        merged['Pts'] = merged.apply(calc, axis=1)
        lb = merged.groupby('Username')['Pts'].sum().reset_index().rename(columns={'Pts': 'Current Points'}).sort_values('Current Points', ascending=False)
        st.dataframe(lb, hide_index=True, width="stretch")

elif page == "Rival Watch":
    st.title("👀 Rival Watch")
    m_df = get_data("Matches").dropna(subset=['Match_ID', 'Player1'])
    p_df = get_data("Predictions"); opts = [f"{str(r['Match_ID']).replace('.0', '')}: {r['Player1']} vs {r['Player2']}" for _, r in m_df.iterrows()]
    if opts:
        sel = st.selectbox("Pick a Match:", opts); target = sel.split(":")[0]
        if not p_df.empty:
            p_df['MID'] = p_df['Match_ID'].astype(str).str.replace('.0', '', regex=False)
            rivals = p_df[p_df['MID'] == target].drop_duplicates('Username', keep='last')
            st.dataframe(rivals[['Username', 'Score']], hide_index=True, width="stretch")

elif page == "Highlights":
    st.title("📺 PDC Highlights")
    pdc_playlist_url = "https://www.youtube.com/embed?listType=user_uploads&list=OfficialPDC"
    st.markdown(f"""<iframe width="100%" height="600" src="{pdc_playlist_url}" title="PDC YouTube Highlights" frameborder="0" allowfullscreen style="border-radius:15px; border: 2px solid #ffd700;"></iframe>""", unsafe_allow_html=True)

elif page == "Admin":
    st.title("⚙️ Admin Hub")
    if st.text_input("Admin Password", type="password") == "darts2025":
        # 1. Scraper Tool
        if st.button("🚀 Scrape & Update Latest 2025 Stats"):
            with st.spinner("Fetching PDC 2025 Data..."):
                try:
                    pdc_url = "https://www.pdc.tv/news/2025/12/26/202526-paddy-power-world-darts-championship-stats-update"
                    tables = pd.read_html(pdc_url)
                    st.success("Successfully fetched latest tournament stats!")
                    st.dataframe(tables[0]) # Displays the scraped stats for review
                except Exception as e: st.error(f"Scraper Error: {e}")
        
        st.divider()
        # 2. Result Entry
        m_df = get_data("Matches").dropna(subset=['Match_ID', 'Player1'])
        target = st.selectbox("Select Match to Settle", [f"{str(r['Match_ID']).replace('.0', '')}: {r['Player1']} vs {r['Player2']}" for _, r in m_df.iterrows()])
        c1, c2 = st.columns(2)
        with c1: r1 = st.selectbox("P1 Score", range(11))
        with c2: r2 = st.selectbox("P2 Score", range(11))
        if st.button("Publish Official Result"):
            old = get_data("Results")
            new_res = pd.concat([old, pd.DataFrame([{"Match_ID": target.split(":")[0], "Score": f"{r1}-{r2}"}])])
            conn.update(spreadsheet=URL, worksheet="Results", data=new_res)
            st.cache_data.clear(); st.success("Result Published!"); st.rerun()
