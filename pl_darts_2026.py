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
##### SECTION 2: CONNECTION & DATA FETCHING                               #####
###############################################################################
conn = st.connection("gsheets", type=GSheetsConnection)
URL = st.secrets["connections"]["gsheets"]["spreadsheet"]

@st.cache_data(ttl=2)
def get_data(worksheet):
    try:
        df = conn.read(spreadsheet=URL, worksheet=worksheet, ttl=0)
        return df.dropna(how='all')
    except Exception as e:
        return pd.DataFrame()

###############################################################################
##### SECTION 3: STYLING & CUSTOM CSS                                     #####
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
    .night-header {{ text-align: center; color: #C4B454 !important; font-size: 1.8rem; font-weight: 900; text-transform: uppercase; margin-bottom: 5px; }}
    
    .timer-container {{ display: flex; justify-content: center; gap: 10px; margin-bottom: 25px; }}
    .timer-box {{ background: #1c1c1c; border: 1px solid #C4B454; border-radius: 8px; padding: 10px; min-width: 65px; text-align: center; }}
    .timer-val {{ color: #C4B454; font-size: 1.5rem; font-weight: 900; display: block; }}
    .timer-label {{ color: white; font-size: 0.65rem; text-transform: uppercase; }}
    
    .pl-card {{ border: 1px solid #C4B454; border-radius: 12px; background: rgba(20, 20, 20, 0.95); padding: 15px; margin-bottom: 15px; }}
    .player-name-container p {{ color: white !important; font-weight: bold; text-align: center; }}
    h1, h2, h3 {{ color: #C4B454 !important; text-transform: uppercase; }}
    
    .betmgm-table {{ width: 100%; border-collapse: collapse; background: rgba(20,20,20,0.9); border-radius: 10px; overflow: hidden; color: white; }}
    .betmgm-table th {{ background: #C4B454; color: black; padding: 12px; text-align: left; text-transform: uppercase; font-weight: 900; }}
    .betmgm-table td {{ padding: 12px; border-bottom: 1px solid #333; }}

    div[data-baseweb="select"] > div {{ background-color: #1c1c1c !important; color: white !important; border: 1px solid #C4B454 !important; }}
    div.stButton > button {{ background: #C4B454 !important; color: #000000 !important; font-weight: 900 !important; width: 100% !important; border: none; }}
    </style>
""", unsafe_allow_html=True)

###############################################################################
##### SECTION 4: MATCH RENDERER FUNCTION                                  #####
###############################################################################
def render_match(p1, p2, key, img_lookup, disabled=False):
    # Safety Check: Use .get() to prevent KeyError if dictionary is rebuilding
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
##### SECTION 5: SIDEBAR & NAVIGATION                                     #####
###############################################################################
st.sidebar.title("🎯 PL 2026 PREDICTOR")
if st.session_state['username'] == "":
    u_attempt = st.sidebar.text_input("Username")
    p_attempt = st.sidebar.text_input("Password", type="password")
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
    menu = st.sidebar.radio("NAVIGATE", ["Matches", "Leaderboard", "Rival Watch", "Highlights", "Admin"])
    if st.sidebar.button("Logout"):
        st.session_state['username'] = ""
        st.rerun()

###############################################################################
##### SECTION 6: CORE APP LOGIC                                           #####
###############################################################################
if st.session_state['username'] == "":
    st.markdown("<h1 style='text-align: center;'>Welcome to the 2026 Premier League Predictor</h1>", unsafe_allow_html=True)
    st.info("Please login on the sidebar to enter your predictions.")
else:
    # 1. Load Data Safely
    players_df = get_data("Players")
    admin_df = get_data("PL_2026_Admin")
    subs_df = get_data("User_Submissions")

    # 2. Build Image Lookup with Safety Fixes
    img_lookup = {}
    if not players_df.empty:
        # Strip whitespace from columns to prevent KeyErrors
        players_df.columns = players_df.columns.str.strip()
        if 'Name' in players_df.columns and 'Image_URL' in players_df.columns:
            img_lookup = dict(zip(players_df['Name'], players_df['Image_URL']))
        else:
            st.error("⚠️ Data Error: 'Players' sheet is missing 'Name' or 'Image_URL' columns.")

    # 3. Clean Admin Columns
    if not admin_df.empty:
        admin_df.columns = admin_df.columns.str.strip()

    ###########################################################################
    ##### SECTION 7: MATCHES PAGE                                         #####
    ###########################################################################
    if menu == "Matches":
        if not admin_df.empty:
            night_choice = st.selectbox("Select Night", admin_df['Night'].unique())
            night_data = admin_df[admin_df['Night'] == night_choice].iloc[0]
            
            st.markdown(f"<h1 style='text-align: center;'>📍 {night_data['Venue']}</h1>", unsafe_allow_html=True)
            st.markdown(f"<div class='night-header'>{night_data['Night']}</div>", unsafe_allow_html=True)

            # TIMER LOGIC
            is_locked = False
            if 'Cutoff' in admin_df.columns:
                try:
                    cutoff_dt = datetime.strptime(str(night_data['Cutoff']), "%Y-%m-%d %H:%M")
                    diff = cutoff_dt - datetime.now()
                    if diff.total_seconds() > 0:
                        days, remainder = divmod(diff.total_seconds(), 86400)
                        hours, remainder = divmod(remainder, 3600)
                        minutes, _ = divmod(remainder, 60)
                        st.markdown("<p style='text-align:center; color:#C4B454; margin-bottom:5px; font-weight:bold;'>TIME UNTIL ENTRIES CLOSE</p>", unsafe_allow_html=True)
                        st.markdown(f"""<div class="timer-container">
                            <div class="timer-box"><span class="timer-val">{int(days)}</span><span class="timer-label">Days</span></div>
                            <div class="timer-box"><span class="timer-val">{int(hours):02d}</span><span class="timer-label">Hrs</span></div>
                            <div class="timer-box"><span class="timer-val">{int(minutes):02d}</span><span class="timer-label">Mins</span></div>
                        </div>""", unsafe_allow_html=True)
                    else:
                        is_locked = True
                        st.error("🔒 Submissions closed for this night.")
                except:
                    st.error("Check 'Cutoff' column format in Sheets (YYYY-MM-DD HH:MM)")

            # SUBMISSION CHECK
            user_sub = subs_df[(subs_df['Username'] == st.session_state['username']) & (subs_df['Night'] == night_choice)]
            if not user_sub.empty: 
                st.warning("✅ Predictions submitted for this night.")
                is_locked = True

            # QUARTER FINALS
            st.markdown("### 1️⃣ Quarter Finals")
            qf1 = render_match(night_data['QF1-P1'], night_data['QF1-P2'], f"qf1_{night_choice}", img_lookup, is_locked)
            qf2 = render_match(night_data['QF2-P1'], night_data['QF2-P2'], f"qf2_{night_choice}", img_lookup, is_locked)
            qf3 = render_match(night_data['QF3-P1'], night_data['QF3-P2'], f"qf3_{night_choice}", img_lookup, is_locked)
            qf4 = render_match(night_data['QF4-P1'], night_data['QF4-P2'], f"qf4_{night_choice}", img_lookup, is_locked)

            # SEMI FINALS
            if all(x != "Select Winner" for x in [qf1, qf2, qf3, qf4]):
                st.divider()
                st.markdown("### 2️⃣ Semi Finals")
                sf1 = render_match(qf1, qf2, f"sf1_{night_choice}", img_lookup, is_locked)
                sf2 = render_match(qf3, qf4, f"sf2_{night_choice}", img_lookup, is_locked)

                # FINAL
                if all(x != "Select Winner" for x in [sf1, sf2]):
                    st.divider()
                    st.markdown("### 🏆 The Final")
                    final = render_match(sf1, sf2, f"fin_{night_choice}", img_lookup, is_locked)
                    
                    if final != "Select Winner" and not is_locked:
                        if st.button("SUBMIT PREDICTIONS"):
                            new_row = pd.DataFrame([{
                                "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
                                "Username": st.session_state['username'],
                                "Night": night_choice,
                                "QF1": qf1, "QF2": qf2, "QF3": qf3, "QF4": qf4,
                                "SF1": sf1, "SF2": sf2,
                                "Final": final
                            }])
                            conn.update(spreadsheet=URL, worksheet="User_Submissions", data=pd.concat([subs_df, new_row], ignore_index=True))
                            st.success("Predictions Locked In!"); time.sleep(1); st.rerun()
        else:
            st.warning("Admin needs to populate the PL_2026_Admin sheet.")

    ###########################################################################
    ##### SECTION 8: LEADERBOARD PAGE                                     #####
    ###########################################################################
    elif menu == "Leaderboard":
        st.title("🏆 Season Standings")
        lb_df = get_data("PL_Leaderboard")
        if not lb_df.empty:
            lb_df = lb_df.sort_values(by="Total", ascending=False)
            html = "<table class='betmgm-table'><tr><th>Rank</th><th>User</th><th>Total Points</th></tr>"
            for i, row in enumerate(lb_df.itertuples(), 1):
                html += f"<tr><td>{i}</td><td>{row.Username}</td><td>{row.Total}</td></tr>"
            st.markdown(html + "</table>", unsafe_allow_html=True)
        else:
            st.info("Leaderboard will populate once results are processed.")

    ###########################################################################
    ##### SECTION 9: RIVAL WATCH                                          #####
    ###########################################################################
    elif menu == "Rival Watch":
        st.title("👀 Rival Watch")
        if not admin_df.empty:
            watch_night = st.selectbox("Select Night to View", admin_df['Night'].unique())
            night_row = admin_df[admin_df['Night'] == watch_night].iloc[0]
            cutoff_rv = datetime.strptime(str(night_row['Cutoff']), "%Y-%m-%d %H:%M")
            user_has_sub = not subs_df[(subs_df['Username'] == st.session_state['username']) & (subs_df['Night'] == watch_night)].empty
            
            if user_has_sub or datetime.now() > cutoff_rv:
                st.dataframe(subs_df[subs_df['Night'] == watch_night][['Username', 'QF1', 'QF2', 'QF3', 'QF4', 'SF1', 'SF2', 'Final']], hide_index=True, use_container_width=True)
            else:
                st.warning("You must submit your own predictions for this night before viewing rivals.")

    ###########################################################################
    ##### SECTION 10: HIGHLIGHTS & ADMIN                                  #####
    ###########################################################################
    elif menu == "Highlights":
        st.title("📺 PDC Highlights")
        st.video("https://www.youtube.com/watch?v=F5u_6Yp-H-U")

    elif menu == "Admin":
        if st.session_state['username'].lower() == "admin":
            st.subheader("⚙️ Scoring Engine")
            st.write("Results and Leaderboard sync logic will be finalized here.")
        else:
            st.error("Admin access required.")
