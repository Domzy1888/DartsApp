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
        return df.dropna(how='all').fillna(0) # Fill NaN with 0 for cleaner UI
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
    
    div.stButton > button, div.stFormSubmitButton > button { background-color: #ffd700 !important; color: #000000 !important; font-weight: 900 !important; border-radius: 10px !important; width: 100% !important; border: none !important; }
    
    /* DIALOG MODAL CSS OVERRIDES */
    div[data-testid="stDialog"] div[role="dialog"] {
        background-image: linear-gradient(rgba(0,0,0,0.92), rgba(0,0,0,0.92)), url("https://news.paddypower.com/assets/uploads/2023/12/Paddy-Power-World-Darts-Championship.jpg") !important;
        background-size: cover !important;
        background-position: center !important;
        border: 2px solid #ffd700 !important;
        min-width: 90% !important;
    }
    /* Force horizontal layout for columns in the dialog */
    div[data-testid="stDialog"] [data-testid="stHorizontalBlock"] {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        justify-content: space-between !important;
    }
    div[data-testid="stDialog"] [data-testid="column"] {
        min-width: 0 !important;
        flex: 1 1 auto !important;
    }

    .stat-row-ui { display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px; }
    .stat-bar-bg { height: 12px; background: #222; border-radius: 6px; overflow: hidden; display: flex; width: 100%; border: 1px solid #444; }
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

    c1, c2, c3 = st.columns([1, 1.5, 1])
    with c1:
        img1 = d1['Player_Image'] if d1 is not None else ""
        st.markdown(f"<div style='text-align:center;'><img src='{img1}' style='width:100%; border-radius:10px; border:2px solid #ffd700;'><p style='color:white; font-size:11px;'>{p1}</p></div>", unsafe_allow_html=True)
    with c3:
        img2 = d2['Player_Image'] if d2 is not None else ""
        st.markdown(f"<div style='text-align:center;'><img src='{img2}' style='width:100%; border-radius:10px; border:2px solid #007bff;'><p style='color:white; font-size:11px;'>{p2}</p></div>", unsafe_allow_html=True)
    with c2:
        stats_list = [("WORLD TITLES", "World_Titles"), ("PDC TITLES", "PDC_Titles"), ("AVG", "Tournament_Avg"), ("CHECKOUT %", "Checkout_Pct"), ("180s", "180s")]
        for label, key in stats_list:
            v1 = float(d1[key]) if d1 is not None else 0
            v2 = float(d2[key]) if d2 is not None else 0
            total = v1 + v2 if (v1 + v2) > 0 else 1
            w1, w2 = (v1 / total) * 100, (v2 / total) * 100
            st.markdown(f"""<div style="margin-bottom:10px;"><div class="stat-row-ui"><span style="color:#ffd700; font-size:14px; font-weight:900;">{v1}</span><span style="color:#aaa; font-size:9px; letter-spacing:1px;">{label}</span><span style="color:#007bff; font-size:14px; font-weight:900;">{v2}</span></div><div class="stat-bar-bg"><div class="bar-gold" style="width:{w1}%;"></div><div class="bar-blue" style="width:{w2}%;"></div></div></div>""", unsafe_allow_html=True)

# --- 7. AUTH & NAVIGATION (Condensed) ---
# ... (Side bar logic remains the same as previous)

# --- 8. PREDICTIONS PAGE ---
if page == "Predictions":
    if st.session_state['username'] == "": st.warning("Please sign in.")
    else:
        st.title("Upcoming Matches")
        m_df = get_data("Matches").dropna(subset=['Match_ID', 'Player1', 'Date'])
        p_df = get_data("Predictions"); r_df = get_data("Results"); now = datetime.now()
        
        # Match Filtering and Rendering
        m_df['Date_Parsed'] = pd.to_datetime(m_df['Date'], errors='coerce')
        days = sorted(m_df['Date_Parsed'].dt.date.unique())
        if days:
            sel_day = st.selectbox("📅 Match Day", days)
            day_matches = m_df[m_df['Date_Parsed'].dt.date == sel_day]
            for _, row in day_matches.iterrows():
                mid = str(row['Match_ID']).replace('.0', '')
                if not r_df.empty and mid in r_df['Match_ID'].astype(str).str.replace('.0', '', regex=False).values: continue
                
                # Match Card UI
                st.markdown(f"<div class='match-card'><div class='match-wrapper'><div class='player-box'><img src=\"{row.get('P1_Image', '')}\" class='player-img'><div class='player-name'>{row['Player1']}</div></div><div class='vs-text'>VS</div><div class='player-box'><img src=\"{row.get('P2_Image', '')}\" class='player-img'><div class='player-name'>{row['Player2']}</div></div></div></div>", unsafe_allow_html=True)
                
                # Stats Dialog Trigger
                if st.button(f"📊 Tale of the Tape: {row['Player1']} vs {row['Player2']}", key=f"h2h_{mid}"):
                    show_h2h(row['Player1'], row['Player2'])

                # Prediction Form
                with st.form(f"form_{mid}"):
                    c1, c2 = st.columns(2)
                    with c1: s1 = st.selectbox(f"{row['Player1']}", range(11), key=f"s1_{mid}")
                    with c2: s2 = st.selectbox(f"{row['Player2']}", range(11), key=f"s2_{mid}")
                    submit = st.form_submit_button("🔒 LOCK PREDICTION")
                    
                    if submit:
                        new_p = pd.DataFrame([{"Username": st.session_state['username'], "Match_ID": mid, "Score": f"{s1}-{s2}"}])
                        conn.update(spreadsheet=URL, worksheet="Predictions", data=pd.concat([p_df, new_p], ignore_index=True))
                        st.cache_data.clear(); st.success("Saved!"); time.sleep(1); st.rerun()

# --- ADMIN HUB ---
elif page == "Admin":
    st.title("⚙️ Admin Hub")
    if st.text_input("Admin Password", type="password") == "darts2025":
        if st.button("🚀 Scrape Latest 2025 Stats"):
            try:
                pdc_url = "https://www.pdc.tv/news/2025/12/26/202526-paddy-power-world-darts-championship-stats-update"
                tables = pd.read_html(pdc_url, flavor='html5lib')
                st.success("Fetched!")
                st.dataframe(tables[0])
            except Exception as e: st.error(f"Error: {e}")
