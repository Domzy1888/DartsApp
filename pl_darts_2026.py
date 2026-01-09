import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import time
from datetime import datetime
import extra_streamlit_components as stx

###############################################################################
##### SECTION 1: PAGE CONFIGURATION                                       #####
###############################################################################
st.set_page_config(page_title="PDC PL Predictor 2026", page_icon="🎯", layout="wide")

if 'username' not in st.session_state:
    st.session_state['username'] = ""

###############################################################################
##### SECTION 2: CONNECTION SETUP                                         #####
###############################################################################
conn = st.connection("gsheets", type=GSheetsConnection)
URL = st.secrets["connections"]["gsheets"]["spreadsheet"]

@st.cache_data(ttl=2)
def get_data(worksheet):
    try:
        df = conn.read(spreadsheet=URL, worksheet=worksheet, ttl=0)
        return df.dropna(how='all')
    except:
        return pd.DataFrame()

###############################################################################
##### SECTION 3: STYLING                                                  #####
###############################################################################
st.markdown(f"""
    <style>
    .stApp {{ 
        background: linear-gradient(rgba(0,0,0,0.8), rgba(0,0,0,0.8)), 
                    url("https://i.postimg.cc/d1kXbbDk/2025PLFinal-Gen-View.jpg"); 
        background-size: cover; background-attachment: fixed; 
    }}
    [data-testid="stSidebar"], [data-testid="stSidebarContent"] {{
        background-color: #111111 !important; border-right: 1px solid #C4B454;
    }}
    [data-testid="stSidebar"] button p {{ color: #000000 !important; font-weight: 900 !important; }}
    h1, h2, h3 {{ color: #C4B454 !important; text-transform: uppercase; font-weight: 900 !important; }}
    .stMarkdown p, .stText p {{ color: white !important; }}
    .night-header {{ text-align: center; color: #C4B454 !important; font-size: 1.8rem; font-weight: 900; text-transform: uppercase; }}
    
    .betmgm-table {{ width: 100%; border-collapse: collapse; background: rgba(20,20,20,0.9); border-radius: 10px; overflow: hidden; color: white; }}
    .betmgm-table th {{ background: #C4B454; color: black; padding: 12px; text-align: left; text-transform: uppercase; font-weight: 900; }}
    .betmgm-table td {{ padding: 12px; border-bottom: 1px solid #333; }}

    .timer-container {{ display: flex; justify-content: center; gap: 10px; margin-bottom: 25px; }}
    .timer-box {{ background: #1c1c1c; border: 1px solid #C4B454; border-radius: 8px; padding: 10px; min-width: 65px; text-align: center; }}
    .timer-val {{ color: #C4B454; font-size: 1.5rem; font-weight: 900; display: block; }}
    .timer-label {{ color: white; font-size: 0.65rem; text-transform: uppercase; }}
    
    .pl-card {{ border: 1px solid #C4B454; border-radius: 12px; background: rgba(20, 20, 20, 0.95); padding: 15px; margin-bottom: 15px; }}
    .player-name-container p {{ color: white !important; font-weight: bold; text-align: center; }}
    
    div[data-baseweb="select"] > div {{ background-color: #1c1c1c !important; color: white !important; border: 1px solid #C4B454 !important; }}
    div.stButton > button {{ background: #C4B454 !important; color: #000000 !important; font-weight: 900 !important; width: 100% !important; border: none; }}
    </style>
""", unsafe_allow_html=True)

###############################################################################
##### SECTION 4: AUTH & NAVIGATION                                        #####
###############################################################################
st.sidebar.title("🎯 PL 2026 PREDICTOR")
if st.session_state['username'] == "":
    u_attempt = st.sidebar.text_input("Username", key="login_user")
    p_attempt = st.sidebar.text_input("Password", type="password", key="login_pass")
    if st.sidebar.button("Login"):
        u_df = get_data("Users")
        if not u_df.empty:
            match = u_df[(u_df['Username'] == u_attempt) & (u_df['Password'].astype(str) == str(p_attempt))]
            if not match.empty:
                st.session_state['username'] = u_attempt
                st.rerun()
            else: st.sidebar.error("Invalid Credentials")
else:
    st.sidebar.write(f"Logged in: **{st.session_state['username']}**")
    menu = st.sidebar.radio("NAVIGATE", ["Matches", "Leaderboard"])
    if st.sidebar.button("Logout"):
        st.session_state['username'] = ""
        st.rerun()

###############################################################################
##### SECTION 5: RENDER MATCH FUNCTION                                    #####
###############################################################################
def render_match(p1, p2, key, img_lookup, disabled=False):
    img1 = img_lookup.get(p1, "https://via.placeholder.com/150")
    img2 = img_lookup.get(p2, "https://via.placeholder.com/150")
    st.markdown(f"""
        <div class="pl-card">
            <div style="display: flex; justify-content: space-around; align-items: flex-start; margin-bottom: 15px;">
                <div style="text-align: center; width: 45%;">
                    <img src="{img1}" style="width: 100%; max-width: 90px; border-radius: 10px;">
                    <div class="player-name-container"><p style="font-size: 0.85rem; margin:0;">{p1}</p></div>
                </div>
                <div style="color: #C4B454; font-size: 1.4rem; font-weight: 900; margin-top: 30px;">VS</div>
                <div style="text-align: center; width: 45%;">
                    <img src="{img2}" style="width: 100%; max-width: 90px; border-radius: 10px;">
                    <div class="player-name-container"><p style="font-size: 0.85rem; margin:0;">{p2}</p></div>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    return st.selectbox(f"Winner: {p1} vs {p2}", ["Select Winner", p1, p2], key=key, label_visibility="collapsed", disabled=disabled)

###############################################################################
##### SECTION 6: MAIN LOGIC                                               #####
###############################################################################
if st.session_state['username'] == "":
    st.markdown("<h1 style='text-align: center;'>Welcome to the 2026 Premier League Predictor</h1>", unsafe_allow_html=True)
else:
    # Safely load and clean DataFrames
    players_df = get_data("Players")
    if not players_df.empty:
        players_df.columns = [str(col).strip() for col in players_df.columns]
    
    img_lookup = dict(zip(players_df['Name'], players_df['Image_URL'])) if not players_df.empty else {}
    
    admin_df = get_data("PL_2026_Admin")
    if not admin_df.empty:
        admin_df.columns = [str(col).strip() for col in admin_df.columns]
        
    subs_df = get_data("User_Submissions")
    if not subs_df.empty:
        subs_df.columns = [str(col).strip() for col in subs_df.columns]

    results_df = get_data("PL_Results")
    if not results_df.empty:
        results_df.columns = [str(col).strip() for col in results_df.columns]

    # --- TAB: MATCHES ---
    if menu == "Matches":
        if not admin_df.empty:
            selected_night = st.selectbox("Select Night", admin_df['Night'].unique())
            night_data = admin_df[admin_df['Night'] == selected_night].iloc[0]
            
            st.markdown(f"<h1 style='text-align: center;'>📍 {night_data['Venue']}</h1>", unsafe_allow_html=True)
            st.markdown(f"<div class='night-header'>{night_data['Night']}</div>", unsafe_allow_html=True)

            is_past_cutoff = False
            if 'Cutoff' in admin_df.columns:
                try:
                    cutoff_val = datetime.strptime(str(night_data['Cutoff']), "%Y-%m-%d %H:%M")
                    diff = cutoff_val - datetime.now()
                    if diff.total_seconds() <= 0: is_past_cutoff = True
                except: pass

            has_submitted = False
            if not subs_df.empty:
                has_submitted = not subs_df[(subs_df['Username'] == st.session_state['username']) & (subs_df['Night'] == night_data['Night'])].empty
            
            lock_app = has_submitted or is_past_cutoff

            if has_submitted: st.warning("⚠️ Submission received. Your entries are locked.")

            st.markdown("### 1️⃣ Quarter Finals")
            q1 = render_match(night_data['QF1-P1'], night_data['QF1-P2'], f"q1_{selected_night}", img_lookup, lock_app)
            q2 = render_match(night_data['QF2-P1'], night_data['QF2-P2'], f"q2_{selected_night}", img_lookup, lock_app)
            q3 = render_match(night_data['QF3-P1'], night_data['QF3-P2'], f"q3_{selected_night}", img_lookup, lock_app)
            q4 = render_match(night_data['QF4-P1'], night_data['QF4-P2'], f"q4_{selected_night}", img_lookup, lock_app)

            if all(x != "Select Winner" for x in [q1, q2, q3, q4]):
                st.divider()
                st.markdown("### 2️⃣ Semi Finals")
                s1 = render_match(q1, q2, f"s1_{selected_night}", img_lookup, lock_app)
                s2 = render_match(q3, q4, f"s2_{selected_night}", img_lookup, lock_app)

                if all(x != "Select Winner" for x in [s1, s2]):
                    st.divider()
                    st.markdown("### 🏆 The Final")
                    f1 = render_match(s1, s2, f"f1_{selected_night}", img_lookup, lock_app)

                    if f1 != "Select Winner" and not lock_app:
                        if st.button("SUBMIT PREDICTIONS"):
                            new_row = pd.DataFrame([{"Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"), "Username": st.session_state['username'], "Night": night_data['Night'], "QF1": q1, "QF2": q2, "QF3": q3, "QF4": q4, "SF1": s1, "SF2": s2, "Final": f1}])
                            conn.update(spreadsheet=URL, worksheet="User_Submissions", data=pd.concat([subs_df, new_row], ignore_index=True))
                            st.success("Submitted!"); time.sleep(1); st.rerun()

    # --- TAB: LEADERBOARD ---
    elif menu == "Leaderboard":
        st.markdown("<h1 style='text-align: center;'>🏆 Season Standings</h1>", unsafe_allow_html=True)
        
        if results_df.empty or subs_df.empty:
            st.info("Leaderboard will update once the first results are in!")
        else:
            scores = {}
            for _, sub in subs_df.iterrows():
                user = sub['Username']
                night = sub['Night']
                if user not in scores: scores[user] = 0
                
                res = results_df[results_df['Night'] == night]
                if not res.empty:
                    res = res.iloc[0]
                    # QF: 2 pts, SF: 3 pts, Final: 5 pts
                    for col in ['QF1', 'QF2', 'QF3', 'QF4']:
                        if sub[col] == res[col]: scores[user] += 2
                    for col in ['SF1', 'SF2']:
                        if sub[col] == res[col]: scores[user] += 3
                    if sub['Final'] == res['Final']: scores[user] += 5
            
            lb_data = pd.DataFrame(list(scores.items()), columns=['Username', 'Total Points']).sort_values(by='Total Points', ascending=False)
            
            html = "<table class='betmgm-table'><tr><th>Rank</th><th>User</th><th>Total Points</th></tr>"
            for i, row in enumerate(lb_data.itertuples(), 1):
                html += f"<tr><td>{i}</td><td>{row.Username}</td><td>{row._2}</td></tr>"
            st.markdown(html + "</table>", unsafe_allow_html=True)
