import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import time
from datetime import datetime, timedelta
import extra_streamlit_components as stx
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests
try:
    from bs4 import BeautifulSoup
except ImportError:
    pass

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
        return df.dropna(how='all').fillna(0)
    except:
        return pd.DataFrame()

# --- 5. STYLING ---
st.markdown("""
    <style>
    .stApp { background: linear-gradient(rgba(0,0,0,0.6), rgba(0,0,0,0.6)), url("https://cdn.images.express.co.uk/img/dynamic/4/590x/secondary/5856693.jpg?r=1735554407217"); background-size: cover; background-attachment: fixed; }
    h1, h2, h3, p, label { color: white !important; font-weight: bold; }
    [data-testid="stSidebarContent"] { background-color: #111111 !important; }
    
    /* Force Horizontal in Dialog */
    div[data-testid="stDialog"] [data-testid="stHorizontalBlock"] {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        gap: 5px !important;
    }
    div[data-testid="stDialog"] [data-testid="column"] { min-width: 0 !important; flex: 1 1 auto !important; }

    .player-img-h2h { width: 100% !important; border-radius: 8px; border: 1px solid #ffd700; }
    .match-card { border: 2px solid #ffd700; border-radius: 20px; background: rgba(0,0,0,0.5); padding: 15px; margin-bottom: 10px; }
    .match-wrapper { display: flex; align-items: flex-start; justify-content: space-around; width: 100%; }
    .player-box { flex: 1; display: flex; flex-direction: column; align-items: center; text-align: center; }
    .player-img { width: 100%; max-width: 100px; border-radius: 10px; }
    .vs-text { color: #ffd700 !important; font-size: 1.2rem !important; font-weight: 900 !important; margin-top: 30px; }
    .player-name { font-size: 0.9rem !important; color: #ffd700 !important; margin-top: 5px; }
    
    div.stButton > button { background-color: #ffd700 !important; color: #000 !important; font-weight: bold; width: 100%; }
    
    div[data-testid="stDialog"] div[role="dialog"] {
        background-color: #000 !important;
        border: 2px solid #ffd700 !important;
    }

    .stat-row-ui { display: flex; align-items: center; justify-content: space-between; margin-bottom: 4px; }
    .stat-bar-bg { height: 8px; background: #222; border-radius: 4px; overflow: hidden; display: flex; width: 100%; }
    .bar-gold { background: #ffd700; height: 100%; }
    .bar-blue { background: #007bff; height: 100%; }
    </style>
""", unsafe_allow_html=True)

# --- 6. H2H POP-UP ENGINE ---
@st.dialog("TALE OF THE TAPE", width="large")
def show_h2h(p1, p2):
    s_df = get_data("Stats")
    d1 = s_df[s_df['Player'] == p1].iloc[0] if not s_df.empty and p1 in s_df['Player'].values else None
    d2 = s_df[s_df['Player'] == p2].iloc[0] if not s_df.empty and p2 in s_df['Player'].values else None

    c1, c2, c3 = st.columns([1, 1.8, 1])
    with c1:
        img1 = d1['Player_Image'] if d1 is not None and 'Player_Image' in d1 else ""
        st.markdown(f"<div style='text-align:center;'><img src='{img1}' class='player-img-h2h'><p style='font-size: 10px;'>{p1}</p></div>", unsafe_allow_html=True)
    with c3:
        img2 = d2['Player_Image'] if d2 is not None and 'Player_Image' in d2 else ""
        st.markdown(f"<div style='text-align:center;'><img src='{img2}' class='player-img-h2h'><p style='font-size: 10px;'>{p2}</p></div>", unsafe_allow_html=True)
    with c2:
        # Robust stat mapping to prevent 'nan'
        metrics = [("TITLES", "PDC_Titles"), ("AVG", "Tournament_Avg"), ("CHK %", "Checkout_Pct"), ("180s", "180s")]
        for label, col in metrics:
            v1 = float(d1[col]) if d1 is not None and col in d1 and pd.notnull(d1[col]) else 0.0
            v2 = float(d2[col]) if d2 is not None and col in d2 and pd.notnull(d2[col]) else 0.0
            total = v1 + v2 if (v1 + v2) > 0 else 1
            st.markdown(f"""
                <div style="margin-bottom:8px;">
                    <div class="stat-row-ui">
                        <span style="color:#ffd700; font-size:12px;">{v1}</span>
                        <span style="font-size:9px; color:#aaa;">{label}</span>
                        <span style="color:#007bff; font-size:12px;">{v2}</span>
                    </div>
                    <div class="stat-bar-bg">
                        <div class="bar-gold" style="width:{(v1/total)*100}%;"></div>
                        <div class="bar-blue" style="width:{(v2/total)*100}%;"></div>
                    </div>
                </div>
            """, unsafe_allow_html=True)

# --- 7. SIDEBAR AUTH & NAVIGATION ---
st.sidebar.title("🎯 PDC PREDICTOR")
mute_audio = st.sidebar.toggle("🔈 Mute Music", value=initial_mute)
if mute_audio != initial_mute:
    cookie_manager.set("pdc_mute", str(mute_audio), expires_at=datetime.now() + timedelta(days=30))
st.sidebar.divider()

if st.session_state['username'] == "":
    auth_mode = st.sidebar.radio("Entry", ["Login", "Register"])
    u_attempt = st.sidebar.text_input("Username").strip()
    p_attempt = st.sidebar.text_input("Password", type="password")
    if st.sidebar.button("Go"):
        u_df = get_data("Users")
        if auth_mode == "Register":
            if u_attempt and p_attempt:
                if not u_df.empty and u_attempt in u_df['Username'].astype(str).values:
                    st.sidebar.error("Username taken.")
                else:
                    new_user = pd.DataFrame([{"Username": u_attempt, "Password": p_attempt, "Email": ""}])
                    conn.update(spreadsheet=URL, worksheet="Users", data=pd.concat([u_df, new_user], ignore_index=True))
                    st.sidebar.success("Created! Login now."); time.sleep(1); st.rerun()
        else:
            if not u_df.empty:
                match = u_df[(u_df['Username'].astype(str) == u_attempt) & (u_df['Password'].astype(str) == str(p_attempt))]
                if not match.empty:
                    st.session_state['username'] = u_attempt
                    cookie_manager.set("pdc_user_login", u_attempt, expires_at=datetime.now() + timedelta(days=30))
                    st.rerun()
                else: st.sidebar.error("Invalid Credentials")
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
        st.session_state['username'] = ""
        cookie_manager.delete("pdc_user_login")
        st.rerun()

# --- 8. PAGE CONTENT ---
if page == "Predictions":
    if st.session_state['username'] == "": st.warning("Please sign in.")
    else:
        st.title("Upcoming Matches")
        m_df = get_data("Matches").dropna(subset=['Match_ID', 'Player1'])
        p_df = get_data("Predictions"); r_df = get_data("Results"); now = datetime.now()
        
        m_df['Date_Parsed'] = pd.to_datetime(m_df['Date'], errors='coerce')
        days = sorted(m_df['Date_Parsed'].dropna().dt.date.unique())
        
        if days:
            sel_day = st.selectbox("📅 Select Match Day", days)
            day_matches = m_df[m_df['Date_Parsed'].dt.date == sel_day]
            for _, row in day_matches.iterrows():
                mid = str(row['Match_ID']).replace('.0', '')
                if not r_df.empty and mid in r_df['Match_ID'].astype(str).str.replace('.0', '', regex=False).values: continue
                
                st.markdown(f"""
                    <div class='match-card'>
                        <div class='match-wrapper'>
                            <div class='player-box'><img src="{row.get('P1_Image', '')}" class='player-img'><div class='player-name'>{row['Player1']}</div></div>
                            <div class='vs-text'>VS</div>
                            <div class='player-box'><img src="{row.get('P2_Image', '')}" class='player-img'><div class='player-name'>{row['Player2']}</div></div>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
                
                if st.button(f"📊 View Stats: {row['Player1']} vs {row['Player2']}", key=f"h2h_{mid}"):
                    show_h2h(row['Player1'], row['Player2'])

                done = not p_df[(p_df['Username'] == st.session_state['username']) & (p_df['Match_ID'].astype(str).str.replace('.0', '', regex=False) == mid)].empty if not p_df.empty else False
                
                if done: st.success("Prediction Locked ✅")
                else:
                    with st.form(f"form_{mid}"):
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
        lb = merged.groupby('Username')['Pts'].sum().reset_index().rename(columns={'Pts': 'Points'}).sort_values('Points', ascending=False)
        st.dataframe(lb, hide_index=True, use_container_width=True)

elif page == "Rival Watch":
    st.title("👁️ Rival Watch")
    u_df = get_data("Users")
    rival = st.selectbox("Select a Rival", u_df['Username'].tolist() if not u_df.empty else [])
    if rival:
        p_df = get_data("Predictions"); m_df = get_data("Matches")
        rival_preds = p_df[p_df['Username'] == rival]
        if rival_preds.empty: st.info(f"{rival} hasn't predicted yet.")
        else:
            merged = rival_preds.merge(m_df, on="Match_ID")
            for _, r in merged.iterrows():
                st.write(f"🎯 **{r['Player1']}** {r['Score']} **{r['Player2']}**")

elif page == "Highlights":
    st.title("📺 Latest PDC Highlights")
    
    # Dynamic fetch from official PDC Channel
    try:
        # Using the official PDC YouTube RSS feed for live updates
        rss_url = "https://www.youtube.com/feeds/videos.xml?channel_id=UCxOdDX55ZjdIcEMnlHp3rUw"
        response = requests.get(rss_url)
        # We use BeautifulSoup to parse the XML feed
        soup = BeautifulSoup(response.content, "xml")
        entries = soup.find_all("entry")[:3] # Gets the 3 most recent videos
        
        for entry in entries:
            title = entry.find("title").text
            link = entry.find("link")["href"]
            published = entry.find("published").text[:10] # Simplified date
            
            with st.container():
                st.subheader(f"🎯 {title}")
                st.video(link)
                st.caption(f"Published: {published}")
                st.divider()
                
    except Exception as e:
        # Robust fallback to ensure the page never stays empty
        st.warning("Currently pulling the latest featured highlights...")
        st.video("https://www.youtube.com/watch?v=UfYYCbPtzWI") 
        st.write("Visit the [Official PDC YouTube Channel](https://www.youtube.com/@officialpdc) for more.")


elif page == "Admin":
    st.title("⚙️ Admin Hub")
    if st.text_input("Admin Password", type="password") == "darts2025":
        if st.button("🚀 Scrape & Update Latest 2025 Stats"):
            with st.spinner("Fetching..."):
                try:
                    pdc_url = "https://www.pdc.tv/news/2025/12/26/202526-paddy-power-world-darts-championship-stats-update"
                    response = requests.get(pdc_url)
                    soup = BeautifulSoup(response.text, 'html5lib')
                    tables = pd.read_html(str(soup))
                    if tables:
                        conn.update(spreadsheet=URL, worksheet="Stats", data=tables[0])
                        st.success("Stats Updated Successfully!")
                        time.sleep(1)
                        st.rerun() # The missing rerun
                except Exception as e: st.error(f"Scraper Error: {str(e)}")
