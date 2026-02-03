import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import time
from datetime import datetime

# 1. PAGE CONFIGURATION
st.set_page_config(page_title="PL Predictor", page_icon="https://i.postimg.cc/8kr9Yqnx/darts-logo-big.png", layout="wide")

if 'username' not in st.session_state: st.session_state['username'] = ""
if 'current_page' not in st.session_state: st.session_state['current_page'] = "Matches"
if 'reg_mode' not in st.session_state: st.session_state['reg_mode'] = False

conn = st.connection("gsheets", type=GSheetsConnection)
URL = st.secrets["connections"]["gsheets"]["spreadsheet"]

# --- NAME SUBSTITUTION MAP ---
# Keeps the UI clean while maintaining sheet integrity
NAME_MAP = {
    "Michael van Gerwen": "MVG"
}

def get_display_name(full_name):
    return NAME_MAP.get(full_name, full_name)

@st.cache_data(ttl=60)
def get_data(worksheet):
    try:
        df = conn.read(spreadsheet=URL, worksheet=worksheet, ttl=0)
        df = df.dropna(how='all').reset_index(drop=True)
        df.columns = df.columns.str.strip()
        return df
    except: return pd.DataFrame()

# --- SEQUENTIAL FORM HELPER ---
def get_form(player):
    results = get_data("PL_Results")
    admin = get_data("PL_2026_Admin")
    
    win_css = "display:inline-block; width:18px; height:18px; line-height:18px; background:#00FF00; color:black; border-radius:3px; font-size:10px; font-weight:900; margin:1px;"
    loss_css = "display:inline-block; width:18px; height:18px; line-height:18px; background:#FF0000; color:white; border-radius:3px; font-size:10px; font-weight:900; margin:1px;"
    dash_css = "display:inline-block; width:18px; height:18px; line-height:18px; background:#444; color:#888; border-radius:3px; font-size:10px; font-weight:900; margin:1px;"

    if results.empty or admin.empty: 
        return "".join([f"<div style='{dash_css}'>-</div>" for _ in range(5)])
    
    player_results = []
    for _, row in results.iterrows():
        night = row['Night']
        n_admin = admin[admin['Night'] == night]
        if n_admin.empty: continue
        n_admin = n_admin.iloc[0]
        
        qf_matchups = [
            (n_admin['QF1-P1'], n_admin['QF1-P2'], row['QF1']),
            (n_admin['QF2-P1'], n_admin['QF2-P2'], row['QF2']),
            (n_admin['QF3-P1'], n_admin['QF3-P2'], row['QF3']),
            (n_admin['QF4-P1'], n_admin['QF4-P2'], row['QF4'])
        ]
        
        won_qf = False
        for p1, p2, winner in qf_matchups:
            if player == p1 or player == p2:
                if player == winner:
                    player_results.append(f"<div style='{win_css}'>W</div>")
                    won_qf = True
                else:
                    player_results.append(f"<div style='{loss_css}'>L</div>")
        
        if won_qf:
            if player == row['SF1'] or player == row['SF2']:
                player_results.append(f"<div style='{win_css}'>W</div>")
                if player == row['Final']:
                    player_results.append(f"<div style='{win_css}'>W</div>")
                else:
                    player_results.append(f"<div style='{loss_css}'>L</div>")
            else:
                player_results.append(f"<div style='{loss_css}'>L</div>")

    form_list = player_results[-5:]
    while len(form_list) < 5:
        form_list.insert(0, f"<div style='{dash_css}'>-</div>")
    
    return f"<div style='margin-top:8px;'>{''.join(form_list)}</div>"

# 2. THEMED CSS
st.markdown("""
    <style>
    .stApp { 
        background: linear-gradient(rgba(0,0,0,0.8), rgba(0,0,0,0.8)), 
                    url("https://i.postimg.cc/d1kXbbDk/2025PLFinal-Gen-View.jpg"); 
        background-size: cover; background-attachment: fixed; 
    }
    [data-testid="stSidebar"] { background-color: rgba(15, 15, 15, 0.98) !important; border-right: 1px solid #C4B454; }
    html, body, [class*="st-"] p, label, .stMarkdown, .stText, [data-testid="stWidgetLabel"] p { color: white !important; font-weight: 500 !important; }
    h1, h2, h3 { color: #C4B454 !important; text-transform: uppercase; font-weight: 900 !important; }
    .leaderboard-ui { width: 100%; border-collapse: collapse; background: rgba(15, 15, 15, 0.95); border: 1px solid #C4B454; border-radius: 10px; overflow: hidden; }
    .leaderboard-ui th { background-color: #C4B454; color: black; padding: 15px; text-align: left; font-weight: 900; }
    .leaderboard-ui td { padding: 15px; border-bottom: 1px solid #333; color: white; }
    div.stButton > button { background-color: #C4B454 !important; color: black !important; font-weight: 700 !important; text-transform: uppercase; width: 100% !important; border-radius: 4px; height: 45px; }
    div[data-baseweb="select"] > div { background-color: rgba(30, 30, 30, 0.9) !important; color: white !important; border: 1px solid #C4B454 !important; }
    .countdown-box { background: rgba(0,0,0,0.8); border: 2px solid #C4B454; border-radius: 10px; padding: 10px; width: 70px; text-align: center; }
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
            days, hours = diff.days, diff.seconds // 3600
            mins = (diff.seconds % 3600) // 60
            return f"""<div style='display: flex; justify-content: center; gap: 10px; margin-bottom: 20px;'>
                <div class='countdown-box'><div style='font-size: 1.5rem; font-weight: 900; color: #C4B454;'>{days}</div><div style='font-size: 0.5rem;'>DAYS</div></div>
                <div class='countdown-box'><div style='font-size: 1.5rem; font-weight: 900; color: #C4B454;'>{hours:02d}</div><div style='font-size: 0.5rem;'>HRS</div></div>
                <div class='countdown-box'><div style='font-size: 1.5rem; font-weight: 900; color: #C4B454;'>{mins:02d}</div><div style='font-size: 0.5rem;'>MINS</div></div>
            </div>"""
    except: pass
    return "<h3 style='text-align:center; color:#C4B454;'>⛔️ ENTRIES CLOSED</h3>"

# 4. HELPERS
def render_match(p1, p2, key, img_lookup, disabled=False):
    img1 = img_lookup.get(p1, "https://via.placeholder.com/150")
    img2 = img_lookup.get(p2, "https://via.placeholder.com/150")
    form1 = get_form(p1)
    form2 = get_form(p2)
    # Use display name in the HTML, but p1/p2 (full names) for the data logic
    disp1 = get_display_name(p1)
    disp2 = get_display_name(p2)
    st.markdown(f"""
        <div style="border: 1px solid #C4B454; border-radius: 12px; background: rgba(20, 20, 20, 0.95); padding: 15px; margin-bottom: 10px;">
            <div style="display: flex; justify-content: space-around; align-items: center;">
                <div style="text-align: center; width: 45%;">
                    <img src="{img1}" style="width: 80px; border-radius: 8px; border: 1px solid #333;"><br>
                    <div style="font-weight:900; margin-top:5px;">{disp1}</div>
                    {form1}
                </div>
                <div style="color: #C4B454; font-weight: 900; font-size: 1.5rem;">VS</div>
                <div style="text-align: center; width: 45%;">
                    <img src="{img2}" style="width: 80px; border-radius: 8px; border: 1px solid #333;"><br>
                    <div style="font-weight:900; margin-top:5px;">{disp2}</div>
                    {form2}
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    # The selectbox options map the full name to the display name for the user
    options = ["Select Winner", p1, p2]
    return st.selectbox("Winner", options, format_func=lambda x: get_display_name(x), key=key, label_visibility="collapsed", disabled=disabled)

# 5. SIDEBAR
with st.sidebar:
    st.image("https://i.postimg.cc/8kr9Yqnx/darts-logo-big.png", width='stretch')
    if st.session_state['username'] == "":
        if not st.session_state['reg_mode']:
            u_in = st.text_input("Username")
            p_in = st.text_input("Password", type="password")
            if st.button("LOGIN"):
                udf = get_data("Users")
                if not udf[(udf['Username'].astype(str)==str(u_in)) & (udf['Password'].astype(str)==str(p_in))].empty:
                    st.session_state['username'] = u_in; st.rerun()
                else: st.error("Invalid Login")
            if st.button("CREATE AN ACCOUNT"): st.session_state['reg_mode'] = True; st.rerun()
        else:
            new_u = st.text_input("New Username")
            new_p = st.text_input("New Password", type="password")
            if st.button("SUBMIT REGISTRATION"):
                udf = get_data("Users")
                if new_u in udf['Username'].astype(str).values: st.error("Exists!")
                elif new_u and new_p:
                    conn.update(spreadsheet=URL, worksheet="Users", data=pd.concat([udf, pd.DataFrame([{"Username": new_u, "Password": new_p}])]))
                    st.cache_data.clear(); st.session_state['reg_mode'] = False; st.rerun()
    else:
        st.write(f"Logged in: **{st.session_state['username']}**")
        if st.button("Matches"): st.session_state['current_page'] = "Matches"
        if st.button("Rival Watch"): st.session_state['current_page'] = "Rival Watch"
        if st.button("Leaderboard"): st.session_state['current_page'] = "Leaderboard"
        if st.session_state['username'].lower() == "domzy":
            if st.button("Admin"): st.session_state['current_page'] = "Admin"
        if st.button("Logout"): st.session_state['username'] = ""; st.rerun()

# 6. MAIN CONTENT
if st.session_state['username'] != "":
    players_df = get_data("Players")
    img_lookup = dict(zip(players_df['Name'], players_df['Image_URL'])) if not players_df.empty else {}
    admin_df = get_data("PL_2026_Admin")

    if st.session_state['current_page'] == "Matches":
        if not admin_df.empty:
            opts = list(admin_df['Night'].unique())
            upcoming = admin_df[pd.to_datetime(admin_df['Cutoff']) > datetime.now()]
            night = st.selectbox("Select Night", opts, index=opts.index(upcoming.iloc[0]['Night']) if not upcoming.empty else 0)
            n_data = admin_df[admin_df['Night'] == night].iloc[0]
            st.markdown(f"<h1 style='text-align: center;'>{night}</h1>", unsafe_allow_html=True)
            st.markdown(f"<h3 style='text-align: center;'>{n_data['Venue']}</h3>", unsafe_allow_html=True)
            st.markdown(get_countdown(n_data['Cutoff']), unsafe_allow_html=True)
            subs_df = get_data("User_Submissions")
            done = not subs_df[(subs_df['Username'] == st.session_state['username']) & (subs_df['Night'] == night)].empty
            st.write("### Quarter Finals")
            q1 = render_match(n_data['QF1-P1'], n_data['QF1-P2'], "q1", img_lookup, done)
            q2 = render_match(n_data['QF2-P1'], n_data['QF2-P2'], "q2", img_lookup, done)
            q3 = render_match(n_data['QF3-P1'], n_data['QF3-P2'], "q3", img_lookup, done)
            q4 = render_match(n_data['QF4-P1'], n_data['QF4-P2'], "q4", img_lookup, done)
            if all(x != "Select Winner" for x in [q1, q2, q3, q4]):
                st.divider(); st.write("### Semi Finals")
                s1 = render_match(q1, q2, "s1", img_lookup, done)
                s2 = render_match(q3, q4, "s2", img_lookup, done)
                if all(x != "Select Winner" for x in [s1, s2]):
                    st.divider(); st.write("### The Final")
                    fin = render_match(s1, s2, "fin", img_lookup, done)
                    if fin != "Select Winner" and not done:
                        if st.button("SUBMIT PREDICTIONS"):
                            new_row = pd.DataFrame([{"Timestamp": datetime.now(), "Username": st.session_state['username'], "Night": night, "QF1": q1, "QF2": q2, "QF3": q3, "QF4": q4, "SF1": s1, "SF2": s2, "Final": fin}])
                            conn.update(spreadsheet=URL, worksheet="User_Submissions", data=pd.concat([subs_df, new_row]))
                            st.cache_data.clear(); st.rerun()
            if done: st.info("Predictions locked.")

    elif st.session_state['current_page'] == "Rival Watch":
        st.markdown("<h1 style='text-align: center;'>👀 RIVAL WATCH</h1>", unsafe_allow_html=True)
        if not admin_df.empty:
            opts = list(admin_df['Night'].unique())
            sel_night = st.selectbox("View Predictions for:", opts)
            subs_df = get_data("User_Submissions")
            if not subs_df[(subs_df['Username'] == st.session_state['username']) & (subs_df['Night'] == sel_night)].empty:
                rivals = subs_df[(subs_df['Night'] == sel_night) & (subs_df['Username'] != st.session_state['username'])]
                for _, row in rivals.iterrows():
                    with st.expander(f"👤 {row['Username'].upper()}"):
                        c1, c2, c3 = st.columns(3)
                        with c1: st.write(f"**Quarters:**\n\n{get_display_name(row['QF1'])}\n\n{get_display_name(row['QF2'])}\n\n{get_display_name(row['QF3'])}\n\n{get_display_name(row['QF4'])}")
                        with c2: st.write(f"**Semis:**\n\n{get_display_name(row['SF1'])}\n\n{get_display_name(row['SF2'])}")
                        with c3: st.markdown(f"**Winner:**\n\n<h3 style='color:#C4B454;'>{get_display_name(row['Final'])}</h3>", unsafe_allow_html=True)
            else: st.warning("Submit yours first!")

    elif st.session_state['current_page'] == "Leaderboard":
        st.markdown("<h1 style='text-align: center;'>🏆 LEADERBOARD</h1>", unsafe_allow_html=True)
        lb_df = calculate_leaderboard()
        if not lb_df.empty:
            html = "<table class='leaderboard-ui'><tr><th>Rank</th><th>Player</th><th>Points</th></tr>"
            for i, row in enumerate(lb_df.itertuples(), 1): html += f"<tr><td>{i}</td><td>{row.Username}</td><td>{int(row.Total)}</td></tr>"
            st.markdown(html + "</table>", unsafe_allow_html=True)

    elif st.session_state['current_page'] == "Admin":
        res_df = get_data("PL_Results")
        target = st.selectbox("Select Night", admin_df['Night'].unique())
        td = admin_df[admin_df['Night'] == target].iloc[0]
        aq1 = st.selectbox("QF1", ["Select Winner", td['QF1-P1'], td['QF1-P2']], format_func=lambda x: get_display_name(x))
        aq2 = st.selectbox("QF2", ["Select Winner", td['QF2-P1'], td['QF2-P2']], format_func=lambda x: get_display_name(x))
        aq3 = st.selectbox("QF3", ["Select Winner", td['QF3-P1'], td['QF3-P2']], format_func=lambda x: get_display_name(x))
        aq4 = st.selectbox("QF4", ["Select Winner", td['QF4-P1'], td['QF4-P2']], format_func=lambda x: get_display_name(x))
        as1 = st.selectbox("SF1", ["Select Winner", aq1, aq2], format_func=lambda x: get_display_name(x))
        as2 = st.selectbox("SF2", ["Select Winner", aq3, aq4], format_func=lambda x: get_display_name(x))
        afn = st.selectbox("Final", ["Select Winner", as1, as2], format_func=lambda x: get_display_name(x))
        if st.button("SAVE"):
            res_df = res_df[res_df['Night'] != target]
            new_res = pd.DataFrame([{"Night": target, "QF1": aq1, "QF2": aq2, "QF3": aq3, "QF4": aq4, "SF1": as1, "SF2": as2, "Final": afn}])
            conn.update(spreadsheet=URL, worksheet="PL_Results", data=pd.concat([res_df, new_res]))
            st.cache_data.clear(); st.rerun()
else:
    st.image("https://i.postimg.cc/8kr9Yqnx/darts-logo-big.png", width=300)
    st.markdown("<h1 style='text-align: center;'>PLEASE LOGIN</h1>", unsafe_allow_html=True)
