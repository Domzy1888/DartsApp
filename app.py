import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import time
from datetime import datetime, timedelta
import extra_streamlit_components as stx

# 1. Page Configuration
st.set_page_config(page_title="PDC Predictor Pro", page_icon="🎯", layout="wide")

# --- 2. THE BOOTSTRAP LOGIN (GitHub Fix: Re-instantiate to catch cookies) ---
if 'username' not in st.session_state: 
    st.session_state['username'] = ""
if 'audio_played' not in st.session_state: 
    st.session_state['audio_played'] = False
if 'logging_out' not in st.session_state:
    st.session_state['logging_out'] = False

# We use a dedicated manager just to check for the cookie at the very start
if st.session_state['username'] == "" and not st.session_state['logging_out']:
    boot_manager = stx.CookieManager(key="boot_loader")
    time.sleep(1.0) # Critical window for mobile browsers to sync
    saved_user = boot_manager.get(cookie="pdc_user_login")
    if saved_user:
        st.session_state['username'] = saved_user
        st.rerun()

# --- 3. PREFERENCE SYNCING ---
pref_manager = stx.CookieManager(key="pref_loader")
saved_mute = pref_manager.get(cookie="pdc_mute")
initial_mute = True if saved_mute == "True" else False

saved_page = pref_manager.get(cookie="pdc_page")
page_options = ["Predictions", "Leaderboard", "Rival Watch", "Admin"]
initial_page_index = page_options.index(saved_page) if saved_page in page_options else 0

# Define page globally to prevent NameError
page = saved_page if saved_page in page_options else "Predictions"

# --- 4. DATA & STYLING ---
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

st.markdown("""
    <style>
    @keyframes pulse-red { 0% { color: #ff4b4b; opacity: 1; } 50% { color: #ff0000; opacity: 0.5; } 100% { color: #ff4b4b; opacity: 1; } }
    .stApp { background: linear-gradient(rgba(0,0,0,0.6), rgba(0,0,0,0.6)), url("https://cdn.images.express.co.uk/img/dynamic/4/590x/secondary/5856693.jpg?r=1735554407217"); background-size: cover; background-attachment: fixed; }
    h1, h2, h3, p, label { color: white !important; font-weight: bold; }
    [data-testid="stSidebarContent"] { background-color: #111111 !important; }
    .match-card { border: 2px solid #ffd700; border-radius: 20px; background-image: linear-gradient(rgba(0,0,0,0.5), rgba(0,0,0,0.5)), url("https://news.paddypower.com/assets/uploads/2023/12/Paddy-Power-World-Darts-Championship.jpg"); background-size: cover; padding: 20px; margin-bottom: 10px; }
    .match-wrapper { display: flex; align-items: flex-start; justify-content: space-around; width: 100%; gap: 5px; }
    .player-box { flex: 1; display: flex; flex-direction: column; align-items: center; text-align: center; }
    .player-img { width: 100%; max-width: 120px; border-radius: 10px; border: 2px solid #ffd700; }
    .vs-text { color: #ffd700 !important; font-size: 1.5rem !important; font-weight: 900 !important; margin-top: 40px; }
    .player-name { font-size: 1.1rem !important; font-weight: 900 !important; color: #ffd700 !important; margin-top: 10px; min-height: 3em; }
    .timer-text { font-weight: bold; font-size: 1.1rem; text-align: center; margin-bottom: 15px; }
    .timer-urgent { animation: pulse-red 1s infinite; font-weight: 900; }
    div.stButton > button { background-color: #ffd700 !important; color: black !important; font-weight: 900 !important; border-radius: 10px; width: 100%; }
    </style>
""", unsafe_allow_html=True)

# --- 5. SIDEBAR & AUTH ---
st.sidebar.title("🎯 PDC PREDICTOR")
mute_audio = st.sidebar.toggle("🔈 Mute Walk-on Music", value=initial_mute)

if mute_audio != initial_mute and not st.session_state['logging_out']:
    stx.CookieManager(key="set_mute").set("pdc_mute", str(mute_audio), expires_at=datetime.now() + timedelta(days=30))

st.sidebar.divider()

if st.session_state['username'] == "":
    auth_mode = st.sidebar.radio("Entry", ["Login", "Register"])
    u_attempt = st.sidebar.text_input("Username").strip()
    p_attempt = st.sidebar.text_input("Password", type="password")
    if st.sidebar.button("Go"):
        u_df = get_data("Users")
        if not u_df.empty:
            match = u_df[(u_df['Username'].astype(str) == u_attempt) & (u_df['Password'].astype(str) == str(p_attempt))]
            if not match.empty:
                st.session_state['username'] = u_attempt
                st.session_state['logging_out'] = False
                stx.CookieManager(key="write_login").set("pdc_user_login", u_attempt, expires_at=datetime.now() + timedelta(days=30))
                st.rerun()
            else: st.sidebar.error("Invalid Login")
else:
    if not mute_audio and not st.session_state['audio_played']:
        st.audio(CHASE_THE_SUN_URL, format="audio/mp3", autoplay=True)
        st.session_state['audio_played'] = True

    st.sidebar.write(f"Logged in: **{st.session_state['username']}**")
    page = st.sidebar.radio("Navigate", page_options, index=initial_page_index)
    
    if page != saved_page and not st.session_state['logging_out']:
        stx.CookieManager(key="set_page").set("pdc_page", page, expires_at=datetime.now() + timedelta(days=30))

    if st.sidebar.button("Logout"):
        st.session_state['logging_out'] = True
        st.session_state['username'] = ""
        st.session_state['audio_played'] = False
        try:
            stx.CookieManager(key="del_login").delete("pdc_user_login")
        except: pass
        time.sleep(0.5)
        st.rerun()

# --- 6. SCORING ENGINE ---
def get_leaderboard_data():
    p_df = get_data("Predictions")
    r_df = get_data("Results")
    if p_df.empty or r_df.empty: return pd.DataFrame(columns=['Username', 'Current Points'])
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

# --- 7. PAGES ---
if page == "Predictions":
    if st.session_state['username'] == "":
        st.warning("Please sign in.")
    else:
        st.title("Upcoming Matches")
        m_df = get_data("Matches").dropna(subset=['Match_ID', 'Player1', 'Date'])
        p_df = get_data("Predictions")
        r_df = get_data("Results")
        now = datetime.now()
        m_df['Date_Parsed'] = pd.to_datetime(m_df['Date'], errors='coerce')
        days = sorted(m_df['Date_Parsed'].dt.date.unique())
        
        if days:
            sel_day = st.selectbox("📅 Select Match Day", days)
            day_matches = m_df[m_df['Date_Parsed'].dt.date == sel_day]
            with st.form("prediction_form", clear_on_submit=False):
                open_list = []
                for _, row in day_matches.iterrows():
                    mid = str(row['Match_ID']).replace('.0', '')
                    if not r_df.empty and mid in r_df['Match_ID'].astype(str).str.replace('.0', '', regex=False).values: continue
                    diff = row['Date_Parsed'] - now
                    mins = diff.total_seconds() / 60
                    
                    if mins > 60: timer = f"<div class='timer-text' style='color:#00ff00;'>Starts in {int(mins/60)}h {int(mins%60)}m</div>"
                    elif 0 < mins <= 60: timer = f"<div class='timer-text timer-urgent'>⚠️ STARTING SOON</div>"
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
                if st.form_submit_button("🔒 LOCK ALL PREDICTIONS") and open_list:
                    new = [{"Username": st.session_state['username'], "Match_ID": m, "Score": st.session_state.temp.get(m, "0-0")} for m in open_list]
                    conn.update(spreadsheet=URL, worksheet="Predictions", data=pd.concat([p_df, pd.DataFrame(new)], ignore_index=True))
                    st.cache_data.clear(); st.success("Saved!"); time.sleep(1); st.rerun()

elif page == "Leaderboard":
    st.title("🏆 Leaderboard")
    st.dataframe(get_leaderboard_data(), hide_index=True, width="stretch")

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
