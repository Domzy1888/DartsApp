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

# --- 4. PREFERENCES ---
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
    </style>
""", unsafe_allow_html=True)

# --- 6. SIDEBAR & AUTH ---
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

# --- 7. SCORING ENGINE ---
def get_leaderboard_data():
    p_df = get_data("Predictions"); r_df = get_data("Results")
    if p_df.empty or r_df.empty: return pd.DataFrame(columns=['Username', 'Current Points'])
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
    return merged.groupby('Username')['Pts'].sum().reset_index().rename(columns={'Pts': 'Current Points'}).sort_values('Current Points', ascending=False)

# --- 8. THE H2H DIALOG ---
@st.dialog("HEAD-TO-HEAD BATTLE", width="medium")
def show_h2h_comparison(p1_name, p2_name, img1, img2):
    stats_df = get_data("Stats")
    try:
        s1 = stats_df[stats_df['Player Name'].str.contains(p1_name, case=False, na=False)].iloc[0]
        s2 = stats_df[stats_df['Player Name'].str.contains(p2_name, case=False, na=False)].iloc[0]
    except:
        st.error("Player stats not found in 'Stats' sheet.")
        return

    st.markdown(f"""
        <style>
        div[role="dialog"] {{
            background-image: linear-gradient(rgba(0,0,0,0.65), rgba(0,0,0,0.65)), 
                              url("https://news.paddypower.com/assets/uploads/2023/12/Paddy-Power-World-Darts-Championship.jpg");
            background-size: cover; border: 2px solid #ffd700; color: white; padding: 20px;
        }}
        .h2h-header {{ display: flex; justify-content: space-around; align-items: flex-start; text-align: center; }}
        .player-profile img {{ width: 140px; border-radius: 15px; border: border: none !important; background: none !important; }}
        .profile-text {{ font-size: 0.9rem; line-height: 1.4; color: #ffffff; margin-top: 10px; }}
        .vs-middle {{ font-size: 3.5rem; font-weight: 900; color: #ffd700; margin-top: 40px; }}
        .stat-label {{ text-align: center; color: #ffd700; font-weight: bold; font-size: 0.8rem; margin-top: 15px; text-transform: uppercase; }}
        .bar-container {{ display: flex; height: 16px; background: rgba(255,255,255,0.1); border-radius: 8px; overflow: hidden; margin: 5px 0; border: 1px solid rgba(255,255,255,0.2); }}
        .bar-left {{ background: #ffd700; height: 100%; }}
        .bar-right {{ background: #ff4b4b; height: 100%; }}
        </style>
        <div class="h2h-header">
            <div class="player-profile">
                <img src="{img1}"><br>
                <div class="profile-text">
                    <b style="font-size:1.2rem; color:#ffd700;">{p1_name}</b><br>
                    "{s1['Nickname']}"<br>Rank: {s1['World Ranking']}<br>Earnings: {s1['Total Earnings']}
                </div>
            </div>
            <div class="vs-middle">VS</div>
            <div class="player-profile">
                <img src="{img2}"><br>
                <div class="profile-text">
                    <b style="font-size:1.2rem; color:#ff4b4b;">{p2_name}</b><br>
                    "{s2['Nickname']}"<br>Rank: {s2['World Ranking']}<br>Earnings: {s2['Total Earnings']}
                </div>
            </div>
        </div>
        <hr style="border: 0.5px solid rgba(255,215,0,0.3); margin: 20px 0;">
    """, unsafe_allow_html=True)

    def draw_bar(label, v1, v2, max_val):
        def clean(x): return float(str(x).replace('%','').replace('£','').replace(',',''))
        n1, n2 = clean(v1), clean(v2)
        p1, p2 = (n1 / max_val) * 100, (n2 / max_val) * 100
        st.markdown(f"""
            <div class="stat-label">{label}</div>
            <div style="display: flex; justify-content: space-between; font-weight: bold; padding: 0 15px;">
                <span>{v1}</span><span>{v2}</span>
            </div>
            <div class="bar-container">
                <div class="bar-left" style="width: {p1}%"></div>
                <div style="width: 4px; background: white;"></div>
                <div class="bar-right" style="width: {p2}%"></div>
            </div>
        """, unsafe_allow_html=True)

    draw_bar("Televised Titles", s1['Televised Titles'], s2['Televised Titles'], 30)
    draw_bar("Season Win %", s1['Season Win %'], s2['Season Win %'], 100)
    draw_bar("Highest Average", s1['Highest Average'], s2['Highest Average'], 125)
    draw_bar("Checkout %", s1['Checkout %'], s2['Checkout %'], 100)
    draw_bar("180s (12m)", s1['180s (12m)'], s2['180s (12m)'], 500)

# --- 9. PAGES ---
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
            # Use separate form elements carefully to allow popups to work
            for _, row in day_matches.iterrows():
                mid = str(row['Match_ID']).replace('.0', '')
                if not r_df.empty and mid in r_df['Match_ID'].astype(str).str.replace('.0', '', regex=False).values: continue
                diff = row['Date_Parsed'] - now
                mins = diff.total_seconds() / 60
                
                if mins > 60: timer = f"<div class='timer-text' style='color:#00ff00;'>Starts in {int(mins/60)}h {int(mins%60)}m</div>"
                elif 0 < mins <= 60: timer = f"<div class='timer-text timer-urgent'>⚠️ STARTING SOON</div>"
                else: timer = "<div class='timer-text' style='color:#ff4b4b;'>Locked / Live</div>"
                
                st.markdown(f"<div class='match-card'>{timer}<div class='match-wrapper'><div class='player-box'><img src=\"{row.get('P1_Image', '')}\" class='player-img'><div class='player-name'>{row['Player1']}</div></div><div class='vs-text'>VS</div><div class='player-box'><img src=\"{row.get('P2_Image', '')}\" class='player-img'><div class='player-name'>{row['Player2']}</div></div></div></div>", unsafe_allow_html=True)
                
                # INTEGRATED STATS BUTTON (Outside form for Dialog compatibility)
                if st.button(f"📊 Stats: {row['Player1']} vs {row['Player2']}", key=f"stats_{mid}"):
                    show_h2h_comparison(row['Player1'], row['Player2'], row.get('P1_Image',''), row.get('P2_Image',''))

                with st.form(f"form_{mid}", clear_on_submit=False):
                    done = not p_df[(p_df['Username'] == st.session_state['username']) & (p_df['Match_ID'].astype(str).str.replace('.0', '', regex=False) == mid)].empty if not p_df.empty else False
                    if done: st.success("Prediction Locked ✅")
                    elif mins <= 0: st.error("Closed 🔒")
                    else:
                        c1, c2 = st.columns(2)
                        with c1: s1 = st.selectbox(f"{row['Player1']}", range(11), key=f"s1_{mid}")
                        with c2: s2 = st.selectbox(f"{row['Player2']}", range(11), key=f"s2_{mid}")
                        if st.form_submit_button("🔒 LOCK PREDICTION"):
                            score_val = f"{s1}-{s2}"
                            new_pred = pd.DataFrame([{"Username": st.session_state['username'], "Match_ID": mid, "Score": score_val}])
                            conn.update(spreadsheet=URL, worksheet="Predictions", data=pd.concat([p_df, new_pred], ignore_index=True))
                            st.cache_data.clear(); st.success("Saved!"); time.sleep(1); st.rerun()

elif page == "Leaderboard":
    st.title("🏆 Leaderboard")
    st.dataframe(get_leaderboard_data(), hide_index=True, width="stretch")

elif page == "Rival Watch":
    st.title("👀 Rival Watch")
    m_df = get_data("Matches").dropna(subset=['Match_ID', 'Player1'])
    p_df = get_data("Predictions"); opts = [f"{str(r['Match_ID']).replace('.0', '')}: {r['Player1']} vs {r['Player2']}" for _, r in m_df.iterrows()]
    if opts:
        sel = st.selectbox("Pick a Match:", opts); target = sel.split(":")[0]; lb = get_leaderboard_data()
        if not p_df.empty:
            p_df['MID'] = p_df['Match_ID'].astype(str).str.replace('.0', '', regex=False)
            match_p = p_df[p_df['MID'] == target].drop_duplicates('Username', keep='last')
            rivals = match_p.merge(lb, on="Username", how="left").fillna(0)
            st.dataframe(rivals[['Username', 'Score', 'Current Points']], hide_index=True, width="stretch")

elif page == "Highlights":
    st.title("📺 PDC Highlights")
    pdc_playlist_url = "https://www.youtube.com/embed?listType=user_uploads&list=OfficialPDC"
    st.markdown(f"""<iframe width="100%" height="600" src="{pdc_playlist_url}" title="PDC YouTube Highlights" frameborder="0" allowfullscreen style="border-radius:15px; border: 2px solid #ffd700;"></iframe>""", unsafe_allow_html=True)
    st.markdown("""<div style='text-align: center; margin-top:20px;'><a href='https://www.youtube.com/@OfficialPDC/videos' target='_blank' class='custom-link-button'>📂 View All PDC Videos on YouTube</a></div>""", unsafe_allow_html=True)

elif page == "Admin":
    st.title("⚙️ Admin Hub")
    if st.text_input("Admin Password", type="password") == "darts2025":
        m_df = get_data("Matches").dropna(subset=['Match_ID', 'Player1'])
        target = st.selectbox("Select Match", [f"{str(r['Match_ID']).replace('.0', '')}: {r['Player1']} vs {r['Player2']}" for _, r in m_df.iterrows()])
        c1, r1 = st.columns(2); c2, r2 = st.columns(2)
        with c1: r1 = st.selectbox("P1", range(11))
        with c2: r2 = st.selectbox("P2", range(11))
        if st.button("Submit Result"):
            old = get_data("Results")
            new = pd.concat([old, pd.DataFrame([{"Match_ID": target.split(":")[0], "Score": f"{r1}-{r2}"}])])
            conn.update(spreadsheet=URL, worksheet="Results", data=new)
            st.cache_data.clear(); st.success("Result Published!"); st.rerun()
