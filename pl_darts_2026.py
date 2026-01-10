import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import time
from datetime import datetime
from streamlit_option_menu import option_menu

###############################################################################
##### SECTION 1: PAGE CONFIGURATION                                       #####
###############################################################################
st.set_page_config(page_title="PDC PL Predictor 2026", page_icon="🎯", layout="wide")

if 'username' not in st.session_state:
    st.session_state['username'] = ""

conn = st.connection("gsheets", type=GSheetsConnection)
URL = st.secrets["connections"]["gsheets"]["spreadsheet"]

@st.cache_data(ttl=2)
def get_data(worksheet):
    try:
        df = conn.read(spreadsheet=URL, worksheet=worksheet, ttl=0)
        return df.dropna(how='all')
    except: return pd.DataFrame()

###############################################################################
##### SECTION 2: THE "NUCLEAR" UI FIXES                                    #####
###############################################################################
st.markdown("""
    <style>
    /* 1. Main App Background */
    .stApp { 
        background: linear-gradient(rgba(0,0,0,0.8), rgba(0,0,0,0.8)), 
                    url("https://i.postimg.cc/d1kXbbDk/2025PLFinal-Gen-View.jpg"); 
        background-size: cover; background-attachment: fixed; 
    }
    
    /* 2. Sidebar Background */
    [data-testid="stSidebar"], [data-testid="stSidebarContent"] {
        background-color: #111111 !important;
        border-right: 1px solid #C4B454;
    }

    /* 3. THE MENU FIX: Removing the White Container */
    /* Target the component container specifically */
    div[data-component-name="st_option_menu"] {
        background-color: transparent !important;
    }
    
    div[data-component-name="st_option_menu"] iframe {
        background-color: transparent !important;
        color-scheme: dark !important;
    }

    /* 4. DROPDOWN (SELECTBOX) FIX: Dark Background + White Text */
    div[data-baseweb="select"] > div {
        background-color: rgba(30, 30, 30, 0.9) !important;
        color: white !important;
        border: 1px solid #C4B454 !important;
    }
    
    /* Ensure dropdown list items are also dark */
    ul[role="listbox"] {
        background-color: #1a1a1a !important;
    }
    
    div[data-testid="stSelectbox"] label p {
        color: #C4B454 !important;
        font-weight: 500 !important;
    }

    /* 5. TEXT WEIGHT & COLOR (Weight 500 for prose) */
    h1, h2, h3 { color: #C4B454 !important; text-transform: uppercase; font-weight: 900 !important; }
    
    .stMarkdown p, .stText p, [data-testid="stWidgetLabel"] p { 
        color: white !important; 
        font-weight: 500 !important; 
    }

    /* 6. BUTTON STYLING (GOLD #C4B454) */
    div.stButton > button { 
        background: #C4B454 !important; 
        color: #000000 !important; 
        font-weight: 500 !important; 
        border: none !important; 
        text-transform: uppercase;
        width: 100%;
        border-radius: 8px;
    }
    
    /* 7. CARDS */
    .pl-card { 
        border: 1px solid #C4B454; 
        border-radius: 12px; 
        background: rgba(20, 20, 20, 0.95); 
        padding: 15px; 
        margin-bottom: 15px; 
    }

    /* Leaderboard Table */
    .betmgm-table { width: 100%; border-collapse: collapse; background: rgba(20,20,20,0.9); border-radius: 10px; overflow: hidden; color: white; }
    .betmgm-table th { background: #C4B454; color: black; padding: 12px; text-align: left; text-transform: uppercase; font-weight: 900; }
    .betmgm-table td { padding: 12px; border-bottom: 1px solid #333; font-weight: 500; }
    </style>
""", unsafe_allow_html=True)

###############################################################################
##### SECTION 3: AUTH & SIDEBAR                                           #####
###############################################################################
with st.sidebar:
    st.markdown("<h1 style='text-align: center; margin-bottom: 0;'>🎯 PL 2026</h1>", unsafe_allow_html=True)
    
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
        selected_page = "Matches"
    else:
        st.markdown(f"<p style='text-align:center;'>Logged in as: <span style='color:#C4B454;'>{st.session_state['username']}</span></p>", unsafe_allow_html=True)
        
        menu_options = ["Matches", "Leaderboard"]
        if st.session_state['username'].lower() == "domzy":
            menu_options.append("Admin")
            
        selected_page = option_menu(
            menu_title=None, 
            options=menu_options,
            icons=["play-btn", "trophy", "gear"],
            menu_icon="none",
            default_index=0,
            styles={
                "container": {"background-color": "transparent !important", "padding": "0px", "border": "none !important"},
                "nav-link": {
                    "color": "white", 
                    "font-weight": "500", 
                    "text-transform": "uppercase",
                    "background-color": "transparent"
                },
                "nav-link-selected": {"background-color": "#C4B454", "color": "black", "font-weight": "700"},
            }
        )
        
        st.write("---")
        if st.button("LOGOUT"):
            st.session_state['username'] = ""
            st.rerun()

###############################################################################
##### SECTION 4: HELPER FUNCTIONS                                         #####
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
##### SECTION 5: MAIN APP LOGIC                                           #####
###############################################################################
if st.session_state['username'] != "":
    players_df = get_data("Players")
    img_lookup = dict(zip(players_df['Name'], players_df['Image_URL'])) if not players_df.empty else {}
    admin_df = get_data("PL_2026_Admin")

    if selected_page == "Matches":
        if not admin_df.empty:
            selected_night = st.selectbox("Select Night", admin_df['Night'].unique())
            night_data = admin_df[admin_df['Night'] == selected_night].iloc[0]
            cutoff_val = night_data['Cutoff']
            
            st.markdown(f"<h1 style='text-align: center;'>📍 {night_data['Venue']}</h1>", unsafe_allow_html=True)
            st.markdown(f"<h2 style='text-align: center;'>{selected_night}</h2>", unsafe_allow_html=True)
            st.markdown("<p style='text-align:center; font-weight:500; margin-bottom:0;'>TIME UNTIL ENTRIES CLOSE</p>", unsafe_allow_html=True)
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

    elif selected_page == "Leaderboard":
        st.title("🏆 Season Standings")
        lb_df = get_data("PL_Leaderboard")
        if not lb_df.empty:
            lb_df = lb_df.sort_values(by="Total", ascending=False)
            html = "<table class='betmgm-table'><tr><th>Rank</th><th>User</th><th>Points</th></tr>"
            for i, row in enumerate(lb_df.itertuples(), 1):
                html += f"<tr><td>{i}</td><td>{row.Username}</td><td>{int(row.Total)}</td></tr>"
            st.markdown(html + "</table>", unsafe_allow_html=True)
else:
    st.markdown("<h1 style='text-align: center; margin-top: 100px;'>🎯 Welcome</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; font-weight: 500;'>Please login in the sidebar.</p>", unsafe_allow_html=True)
