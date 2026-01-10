import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import time
from datetime import datetime

# 1. PAGE CONFIGURATION
st.set_page_config(page_title="PDC PL Predictor 2026", page_icon="🎯", layout="wide")

if 'username' not in st.session_state: st.session_state['username'] = ""
if 'current_page' not in st.session_state: st.session_state['current_page'] = "Matches"

conn = st.connection("gsheets", type=GSheetsConnection)
URL = st.secrets["connections"]["gsheets"]["spreadsheet"]

@st.cache_data(ttl=60)
def get_data(worksheet):
    try:
        df = conn.read(spreadsheet=URL, worksheet=worksheet, ttl=0)
        df = df.dropna(how='all').reset_index(drop=True)
        df.columns = df.columns.str.strip()
        return df
    except: return pd.DataFrame()

# 2. THEMED CSS
st.markdown("""
    <style>
    .stApp { 
        background: linear-gradient(rgba(0,0,0,0.8), rgba(0,0,0,0.8)), 
                    url("https://i.postimg.cc/d1kXbbDk/2025PLFinal-Gen-View.jpg"); 
        background-size: cover; background-attachment: fixed; 
    }
    
    [data-testid="stSidebar"] {
        background-color: rgba(15, 15, 15, 0.98) !important;
        border-right: 1px solid #C4B454;
    }
    
    [data-testid="stSidebarContent"] { color: white !important; }

    html, body, [class*="st-"] p, label, .stMarkdown, .stText, [data-testid="stWidgetLabel"] p {
        color: white !important; font-weight: 500 !important;
    }
    h1, h2, h3 { color: #C4B454 !important; text-transform: uppercase; font-weight: 900 !important; }
    
    .leaderboard-ui {
        width: 100%; border-collapse: collapse; background: rgba(15, 15, 15, 0.95);
        border: 1px solid #C4B454; border-radius: 10px; overflow: hidden;
    }
    .leaderboard-ui th { background-color: #C4B454; color: black; padding: 15px; text-align: left; font-weight: 900; }
    .leaderboard-ui td { padding: 15px; border-bottom: 1px solid #333; color: white; }

    div.stButton > button {
        background-color: #C4B454 !important; color: black !important;
        font-weight: 700 !important; text-transform: uppercase; width: 100% !important;
        border-radius: 4px; height: 45px;
    }
    div.stButton > button:hover { background-color: #e5d464 !important; }

    div[data-baseweb="select"] > div {
        background-color: rgba(30, 30, 30, 0.9) !important;
        color: white !important; border: 1px solid #C4B454 !important;
    }

    .countdown-box {
        background: rgba(0,0,0,0.8); 
        border: 2px solid #C4B454; 
        border-radius: 10px; 
        padding: 10px; 
        width: 70px; 
        text-align: center;
    }
    </style>
""", unsafe_allow_html=True)

# 3. SCORING ENGINE & COUNTDOWN
def calculate_leaderboard():
    subs = get_data("User_Submissions")
    results = get_data("PL_Results")
    users = get_data("Users")
    if users.empty: return pd.DataFrame(columns=["Username", "Total"])
    scores = {str(user): 0 for user in users['Username'].unique()}
    if not subs.empty and not results.empty:
        for _, res_row in results.iterrows():
            night = res_row['Night']
            night_subs = subs[subs['Night'] == night]
            for _, sub_row in night_subs.iterrows():
                u = str(sub_row['Username'])
                if u in scores:
                    pts = 0
                    if sub_row['QF1'] == res_row['QF1']: pts += 2
                    if sub_row['QF2'] == res_row['QF2']: pts += 2
                    if sub_row['QF3'] == res_row['QF3']: pts += 2
                    if sub_row['QF4'] == res_row['QF4']: pts += 2
                    if sub_row['SF1'] == res_row['SF1']: pts += 3
                    if sub_row['SF2'] == res_row['SF2']: pts += 3
                    if sub_row['Final'] == res_row['Final']: pts += 5
                    scores[u] += pts
    lb = pd.DataFrame(list(scores.items()), columns=["Username", "Total"])
    return lb.sort_values(by="Total", ascending=False)

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
                <div style='display: flex; justify-content: center; gap: 10px; margin-top: 10px; margin-bottom: 20px;'>
                    <div class='countdown-box'>
                        <div style='font-size: 1.5rem; font-weight: 900; color: #C4B454;'>{days}</div>
                        <div style='font-size: 0.5rem; color: white;'>DAYS</div>
                    </div>
                    <div class='countdown-box'>
                        <div style='font-size: 1.5rem; font-weight: 900; color: #C4B454;'>{hours:02d}</div>
                        <div style='font-size: 0.5rem; color: white;'>HRS</div>
                    </div>
                    <div class='countdown-box'>
                        <div style='font-size: 1.5rem; font-weight: 900; color: #C4B454;'>{minutes:02d}</div>
                        <div style='font-size: 0.5rem; color: white;'>MINS</div>
                    </div>
                </div>
            """
    except: pass
    return "<h3 style='text-align:center; color:#C4B454;'>⛔️ ENTRIES CLOSED</h3>"

# 4. HELPERS
def render_match(p1, p2, key, img_lookup, disabled=False):
    img1 = img_lookup.get(p1, "https://via.placeholder.com/150")
    img2 = img_lookup.get(p2, "https://via.placeholder.com/150")
    st.markdown(f"""
        <div style="border: 1px solid #C4B454; border-radius: 12px; background: rgba(20, 20, 20, 0.95); padding: 15px; margin-bottom: 10px;">
            <div style="display: flex; justify-content: space-around; align-items: center;">
                <div style="text-align: center; width: 40%;"><img src="{img1}" style="width: 75px; border-radius: 8px;"><br>{p1}</div>
                <div style="color: #C4B454; font-weight: 900; font-size: 1.2rem;">VS</div>
                <div style="text-align: center; width: 40%;"><img src="{img2}" style="width: 75px; border-radius: 8px;"><br>{p2}</div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    return st.selectbox(f"Winner", ["Select Winner", p1, p2], key=key, label_visibility="collapsed", disabled=disabled)

# 5. SIDEBAR
with st.sidebar:
    st.image("https://i.postimg.cc/8kr9Yqnx/darts-logo-big.png", width='stretch')
    st.markdown("<h1 style='text-align: center; font-size: 1.5rem;'>MATCH PREDICTOR</h1>", unsafe_allow_html=True)

    if st.session_state['username'] == "":
        u_in = st.text_input("Username")
        p_in = st.text_input("Password", type="password")
        if st.button("LOGIN"):
            udf = get_data("Users")
            if not udf[(udf['Username'].astype(str)==str(u_in)) & (udf['Password'].astype(str)==str(p_in))].empty:
                st.session_state['username'] = u_in; st.rerun()
            else: st.error("Invalid Login")
    else:
        st.write(f"Logged in: **{st.session_state['username']}**")
        if st.button("Matches"): st.session_state['current_page'] = "Matches"
        if st.button("Leaderboard"): st.session_state['current_page'] = "Leaderboard"
        if st.session_state['username'].lower() == "domzy":
            if st.button("Admin"): st.session_state['current_page'] = "Admin"
        if st.button("Logout"): 
            st.session_state['username'] = ""
            st.session_state['current_page'] = "Matches"
            st.rerun()

# 6. MAIN CONTENT
if st.session_state['username'] != "":
    players_df = get_data("Players")
    img_lookup = dict(zip(players_df['Name'], players_df['Image_URL'])) if not players_df.empty else {}
    admin_df = get_data("PL_2026_Admin")

    if st.session_state['current_page'] == "Matches":
        if not admin_df.empty:
            night = st.selectbox("Select Night", admin_df['Night'].unique())
            n_data = admin_df[admin_df['Night'] == night].iloc[0]
            st.markdown(f"<h1 style='text-align: center;'>{night}</h1>", unsafe_allow_html=True)
            st.markdown(f"<h3 style='text-align: center;'> {n_data['Venue']}</h3>", unsafe_allow_html=True)
            st.markdown(get_countdown(n_data['Cutoff']), unsafe_allow_html=True)
            
            subs_df = get_data("User_Submissions")
            done = not subs_df[(subs_df['Username'] == st.session_state['username']) & (subs_df['Night'] == night)].empty

            st.write("### Quarter Finals")
            q1 = render_match(n_data['QF1-P1'], n_data['QF1-P2'], "q1", img_lookup, done)
            q2 = render_match(n_data['QF2-P1'], n_data['QF2-P2'], "q2", img_lookup, done)
            q3 = render_match(n_data['QF3-P1'], n_data['QF3-P2'], "q3", img_lookup, done)
            q4 = render_match(n_data['QF4-P1'], n_data['QF4-P2'], "q4", img_lookup, done)

            if all(x != "Select Winner" for x in [q1, q2, q3, q4]):
                st.divider()
                st.write("### Semi Finals")
                s1 = render_match(q1, q2, "s1", img_lookup, done)
                s2 = render_match(q3, q4, "s2", img_lookup, done)
                if all(x != "Select Winner" for x in [s1, s2]):
                    st.divider()
                    st.write("### The Final")
                    fin = render_match(s1, s2, "fin", img_lookup, done)
                    if fin != "Select Winner" and not done:
                        if st.button("SUBMIT PREDICTIONS"):
                            new_row = pd.DataFrame([{"Timestamp": datetime.now(), "Username": st.session_state['username'], "Night": night, "QF1": q1, "QF2": q2, "QF3": q3, "QF4": q4, "SF1": s1, "SF2": s2, "Final": fin}])
                            conn.update(spreadsheet=URL, worksheet="User_Submissions", data=pd.concat([subs_df, new_row]))
                            st.cache_data.clear()
                            st.success("Good luck! Submission saved."); time.sleep(1); st.rerun()
            if done: st.info("Predictions locked for this night.")

    elif st.session_state['current_page'] == "Leaderboard":
        st.markdown("<h1 style='text-align: center;'>🏆 LEADERBOARD</h1>", unsafe_allow_html=True)
        lb_df = calculate_leaderboard()
        if not lb_df.empty:
            html = "<table class='leaderboard-ui'><tr><th>Rank</th><th>Player</th><th>Points</th></tr>"
            for i, row in enumerate(lb_df.itertuples(), 1):
                html += f"<tr><td>{i}</td><td>{row.Username}</td><td>{int(row.Total)}</td></tr>"
            st.markdown(html + "</table>", unsafe_allow_html=True)
        else: st.info("No scores calculated yet.")

    elif st.session_state['current_page'] == "Admin":
        st.title("⚙︎ Admin Panel")
        res_df = get_data("PL_Results")
        target = st.selectbox("Select Night to Update", admin_df['Night'].unique())
        td = admin_df[admin_df['Night'] == target].iloc[0]
        
        aq1 = st.selectbox("QF1 Winner", ["Select Winner", td['QF1-P1'], td['QF1-P2']], key="aq1")
        aq2 = st.selectbox("QF2 Winner", ["Select Winner", td['QF2-P1'], td['QF2-P2']], key="aq2")
        aq3 = st.selectbox("QF3 Winner", ["Select Winner", td['QF3-P1'], td['QF3-P2']], key="aq3")
        aq4 = st.selectbox("QF4 Winner", ["Select Winner", td['QF4-P1'], td['QF4-P2']], key="aq4")
        
        as1 = st.selectbox("SF1 Winner", ["Select Winner", aq1, aq2] if aq1 != "Select Winner" else ["Select Winner"], key="as1")
        as2 = st.selectbox("SF2 Winner", ["Select Winner", aq3, aq4] if aq3 != "Select Winner" else ["Select Winner"], key="as2")
        afn = st.selectbox("Final Winner", ["Select Winner", as1, as2] if as1 != "Select Winner" else ["Select Winner"], key="afn")
        
        if st.button("SAVE OFFICIAL RESULTS"):
            if "Select Winner" in [aq1, aq2, aq3, aq4, as1, as2, afn]:
                st.error("Please select all winners.")
            else:
                res_df = res_df[res_df['Night'].astype(str) != str(target)]
                new_res = pd.DataFrame([{"Night": target, "QF1": aq1, "QF2": aq2, "QF3": aq3, "QF4": aq4, "SF1": as1, "SF2": as2, "Final": afn}])
                updated = pd.concat([res_df, new_res]).reset_index(drop=True)
                conn.update(spreadsheet=URL, worksheet="PL_Results", data=updated)
                st.cache_data.clear()
                st.success("Scores updated live!"); time.sleep(1); st.rerun()
else:
    # Centering the logo using columns
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        st.image("https://i.postimg.cc/8kr9Yqnx/darts-logo-big.png", width='stretch')
    
    st.markdown("<h1 style='text-align: center; margin-top: -20px;'>WELCOME</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>Please login in the sidebar to view matches and enter predictions.</p>", unsafe_allow_html=True)


