import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import time
from datetime import datetime

###############################################################################
##### SECTION 1: PAGE CONFIGURATION                                       #####
###############################################################################
st.set_page_config(page_title="PDC PL Predictor 2026", page_icon="🎯", layout="wide")

if 'username' not in st.session_state:
    st.session_state['username'] = ""
if 'current_page' not in st.session_state:
    st.session_state['current_page'] = "Matches"

conn = st.connection("gsheets", type=GSheetsConnection)
URL = st.secrets["connections"]["gsheets"]["spreadsheet"]

@st.cache_data(ttl=2)
def get_data(worksheet):
    try:
        df = conn.read(spreadsheet=URL, worksheet=worksheet, ttl=0)
        return df.dropna(how='all')
    except: return pd.DataFrame()

###############################################################################
##### SECTION 2: CSS - AGGRESSIVE UNIFORM BUTTONS                         #####
###############################################################################
st.markdown("""
    <style>
    /* 1. Main Background */
    .stApp { 
        background: linear-gradient(rgba(0,0,0,0.8), rgba(0,0,0,0.8)), 
                    url("https://i.postimg.cc/d1kXbbDk/2025PLFinal-Gen-View.jpg"); 
        background-size: cover; background-attachment: fixed; 
    }
    
    /* 2. Sidebar styling */
    [data-testid="stSidebar"], [data-testid="stSidebarContent"] {
        background-color: #111111 !important;
        border-right: 1px solid #C4B454;
    }

    /* 3. FORCE FULL WIDTH BUTTONS */
    /* This overrides the 'shrink-wrap' behavior seen in your screenshots */
    [data-testid="stSidebar"] .stButton button {
        width: 100% !important;
        display: flex !important;
        justify-content: flex-start !important; /* Aligns text/icon to left */
        padding-left: 20px !important;
        background-color: #C4B454 !important;
        color: #000000 !important;
        font-weight: 600 !important;
        border: none !important;
        text-transform: uppercase;
        border-radius: 4px;
        height: 45px;
        margin-bottom: 5px !important;
    }

    [data-testid="stSidebar"] .stButton button:hover {
        background-color: #e5d464 !important;
    }

    /* 4. Match Cards & Dropdowns */
    .pl-card { 
        border: 1px solid #C4B454; border-radius: 12px; 
        background: rgba(20, 20, 20, 0.95); padding: 15px; margin-bottom: 15px; 
    }
    div[data-baseweb="select"] > div {
        background-color: rgba(30, 30, 30, 0.9) !important;
        color: white !important;
        border: 1px solid #C4B454 !important;
    }
    
    /* Text styling */
    h1, h2, h3 { color: #C4B454 !important; text-transform: uppercase; font-weight: 900 !important; }
    .stMarkdown p, .stText p { color: white !important; font-weight: 500 !important; }
    </style>
""", unsafe_allow_html=True)

###############################################################################
##### SECTION 3: HELPER FUNCTIONS                                         #####
###############################################################################
def render_match(p1, p2, key, img_lookup, disabled=False):
    img1 = img_lookup.get(p1, "https://via.placeholder.com/150")
    img2 = img_lookup.get(p2, "https://via.placeholder.com/150")
    st.markdown(f"""
        <div class="pl-card">
            <div style="display: flex; justify-content: space-around; align-items: flex-start; margin-bottom: 15px;">
                <div style="text-align: center; width: 45%;">
                    <img src="{img1}" style="width: 100%; max-width: 90px; border-radius: 10px; border: 1px solid #C4B454;">
                    <p style="font-size: 0.85rem; margin-top:5px; font-weight:500; color:white;">{p1}</p>
                </div>
                <div style="color: #C4B454; font-size: 1.4rem; font-weight: 900; margin-top: 30px;">VS</div>
                <div style="text-align: center; width: 45%;">
                    <img src="{img2}" style="width: 100%; max-width: 90px; border-radius: 10px; border: 1px solid #C4B454;">
                    <p style="font-size: 0.85rem; margin-top:5px; font-weight:500; color:white;">{p2}</p>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    return st.selectbox(f"Winner: {p1} vs {p2}", ["Select Winner", p1, p2], key=key, label_visibility="collapsed", disabled=disabled)

def get_countdown(target_date_str):
    try:
        target_date = pd.to_datetime(target_date_str)
        now = datetime.now()
        diff = target_date - now
        if diff.total_seconds() > 0:
            days = diff.days
            hours, remainder = divmod(diff.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            return f"""
                <div style='display: flex; justify-content: center; gap: 10px; margin-top: 20px;'>
                    <div style='background: rgba(0,0,0,0.8); border: 2px solid #C4B454; border-radius: 10px; padding: 10px; width: 70px; text-align: center;'>
                        <div style='font-size: 1.5rem; font-weight: 900; color: #C4B454;'>{days}</div>
                        <div style='font-size: 0.5rem; color: white;'>DAYS</div>
                    </div>
                    <div style='background: rgba(0,0,0,0.8); border: 2px solid #C4B454; border-radius: 10px; padding: 10px; width: 70px; text-align: center;'>
                        <div style='font-size: 1.5rem; font-weight: 900; color: #C4B454;'>{hours:02d}</div>
                        <div style='font-size: 0.5rem; color: white;'>HRS</div>
                    </div>
                    <div style='background: rgba(0,0,0,0.8); border: 2px solid #C4B454; border-radius: 10px; padding: 10px; width: 70px; text-align: center;'>
                        <div style='font-size: 1.5rem; font-weight: 900; color: #C4B454;'>{minutes:02d}</div>
                        <div style='font-size: 0.5rem; color: white;'>MINS</div>
                    </div>
                </div>
            """
    except: pass
    return "<h3 style='text-align:center;'>🎯 ENTRIES CLOSED</h3>"

###############################################################################
##### SECTION 4: SIDEBAR NAVIGATION                                       #####
###############################################################################
with st.sidebar:
    st.markdown("<h1 style='text-align: center; margin-bottom: 20px;'>🎯 PL 2026</h1>", unsafe_allow_html=True)
    
    if st.session_state['username'] == "":
        u_attempt = st.text_input("Username", key="login_user")
        p_attempt = st.text_input("Password", type="password", key="login_pass")
        if st.button("LOGIN"):
            u_df = get_data("Users")
            match = u_df[(u_df['Username'] == u_attempt) & (u_df['Password'].astype(str) == str(p_attempt))]
            if not match.empty:
                st.session_state['username'] = u_attempt
                st.rerun()
            else: st.error("Invalid Credentials")
    else:
        st.markdown(f"<p style='text-align:center;'>Logged in: <span style='color:#C4B454;'>{st.session_state['username']}</span></p>", unsafe_allow_html=True)
        st.write("---")
        
        # NAVIGATION WITH HOLLOW ICONS
        if st.button("▷ MATCHES"):
            st.session_state['current_page'] = "Matches"
            
        if st.button("✧ LEADERBOARD"):
            st.session_state['current_page'] = "Leaderboard"
            
        if st.session_state['username'].lower() == "domzy":
            if st.button("⚙︎ ADMIN"):
                st.session_state['current_page'] = "Admin"
        
        st.markdown("<br><br><br>", unsafe_allow_html=True)
        if st.button("LOGOUT"):
            st.session_state['username'] = ""
            st.session_state['current_page'] = "Matches"
            st.rerun()

###############################################################################
##### SECTION 5: MAIN LOGIC                                               #####
###############################################################################
if st.session_state['username'] != "":
    players_df = get_data("Players")
    img_lookup = dict(zip(players_df['Name'], players_df['Image_URL'])) if not players_df.empty else {}
    admin_df = get_data("PL_2026_Admin")
    current_page = st.session_state['current_page']

    if current_page == "Matches":
        if not admin_df.empty:
            selected_night = st.selectbox("Select Night", admin_df['Night'].unique())
            night_data = admin_df[admin_df['Night'] == selected_night].iloc[0]
            cutoff_val = night_data['Cutoff']
            
            st.markdown(f"<h1 style='text-align: center;'>📍 {night_data['Venue']}</h1>", unsafe_allow_html=True)
            st.markdown(f"<h2 style='text-align: center;'>{selected_night}</h2>", unsafe_allow_html=True)
            st.markdown("<p style='text-align:center; font-weight:500;'>TIME UNTIL ENTRIES CLOSE</p>", unsafe_allow_html=True)
            st.markdown(get_countdown(cutoff_val), unsafe_allow_html=True)
            st.write("")

            subs_df = get_data("User_Submissions")
            has_submitted = not subs_df[(subs_df['Username'] == st.session_state['username']) & (subs_df['Night'] == selected_night)].empty

            st.markdown("### 1️⃣ Quarter Finals")
            q1 = render_match(night_data['QF1-P1'], night_data['QF1-P2'], "q1", img_lookup, has_submitted)
            q2 = render_match(night_data['QF2-P1'], night_data['QF2-P2'], "q2", img_lookup, has_submitted)
            q3 = render_match(night_data['QF3-P1'], night_data['QF3-P2'], "q3", img_lookup, has_submitted)
            q4 = render_match(night_data['QF4-P1'], night_data['QF4-P2'], "q4", img_lookup, has_submitted)

            if all(x != "Select Winner" for x in [q1, q2, q3, q4]):
                st.divider()
                st.markdown("### 2️⃣ Semi Finals")
                s1 = render_match(q1, q2, "s1", img_lookup, has_submitted)
                s2 = render_match(q3, q4, "s2", img_lookup, has_submitted)

                if all(x != "Select Winner" for x in [s1, s2]):
                    st.divider()
                    st.markdown("### 🏆 The Final")
                    fin = render_match(s1, s2, "fin", img_lookup, has_submitted)

                    if fin != "Select Winner" and not has_submitted:
                        if st.button("SUBMIT PREDICTIONS"):
                            new_row = pd.DataFrame([{"Timestamp": datetime.now(), "Username": st.session_state['username'], "Night": selected_night, "QF1": q1, "QF2": q2, "QF3": q3, "QF4": q4, "SF1": s1, "SF2": s2, "Final": fin}])
                            conn.update(spreadsheet=URL, worksheet="User_Submissions", data=pd.concat([subs_df, new_row]))
                            st.success("Submitted!"); time.sleep(1); st.rerun()
            if has_submitted:
                st.info("You have already submitted for this night.")

    elif current_page == "Leaderboard":
        st.title("🏆 Leaderboard")
        lb_df = get_data("PL_Leaderboard")
        if not lb_df.empty:
            lb_df = lb_df.sort_values(by="Total", ascending=False)
            html = "<table class='betmgm-table'><tr><th>Rank</th><th>User</th><th>Points</th></tr>"
            for i, row in enumerate(lb_df.itertuples(), 1):
                html += f"<tr><td>{i}</td><td>{row.Username}</td><td>{int(row.Total)}</td></tr>"
            st.markdown(html + "</table>", unsafe_allow_html=True)

    elif current_page == "Admin":
        st.title("⚙︎ Result Manager")
        res_df = get_data("PL_Results")
        night_to_edit = st.selectbox("Update Night Results", admin_df['Night'].unique())
        n_data = admin_df[admin_df['Night'] == night_to_edit].iloc[0]
        
        with st.form("admin_form"):
            aq1 = st.selectbox("QF1 Winner", [n_data['QF1-P1'], n_data['QF1-P2']])
            aq2 = st.selectbox("QF2 Winner", [n_data['QF2-P1'], n_data['QF2-P2']])
            aq3 = st.selectbox("QF3 Winner", [n_data['QF3-P1'], n_data['QF3-P2']])
            aq4 = st.selectbox("QF4 Winner", [n_data['QF4-P1'], n_data['QF4-P2']])
            as1 = st.selectbox("SF1 Winner", [aq1, aq2])
            as2 = st.selectbox("SF2 Winner", [aq3, aq4])
            afn = st.selectbox("Overall Winner", [as1, as2])
            
            if st.form_submit_button("Save Winners"):
                new_res = pd.DataFrame([{"Night": night_to_edit, "QF1": aq1, "QF2": aq2, "QF3": aq3, "QF4": aq4, "SF1": as1, "SF2": as2, "Final": afn}])
                conn.update(spreadsheet=URL, worksheet="PL_Results", data=pd.concat([res_df[res_df['Night'] != night_to_edit], new_res]))
                st.success("Results Updated!")
else:
    st.markdown("<h1 style='text-align: center; margin-top: 100px;'>🎯 Welcome</h1>", unsafe_allow_html=True)
