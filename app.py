import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import os
from datetime import datetime
import pytz
import base64

# ==========================================
# 1. System Configuration & Constants
# ==========================================
EGYPT_TZ = pytz.timezone('Africa/Cairo')
NEON_COLORS = ['#00d2ff', '#ffaa00', '#2ecc71', '#ff007f', '#f1c40f', '#9b59b6', '#38f9d7', '#ff7eb3', '#00f2fe', '#4facfe']

USERS_DB_FILE = "users_db.csv"
LOGIN_LOGS_FILE = "login_logs.csv"

# ==========================================
# 2. Authentication & User Management
# ==========================================
def init_auth_system():
    if not os.path.exists(USERS_DB_FILE):
        default_users = pd.DataFrame([
            {"Email": "Mohamedhatem@kk.com", "Password": "admin123", "Name": "Mohamed Hatem", "Role": "Admin", "Status": "Active"},
            {"Email": "engineer@kk.com", "Password": "123", "Name": "Site Engineer", "Role": "User", "Status": "Active"}
        ])
        default_users.to_csv(USERS_DB_FILE, index=False)
    
    if not os.path.exists(LOGIN_LOGS_FILE):
        logs_df = pd.DataFrame(columns=["Timestamp", "Name", "Email", "Role"])
        logs_df.to_csv(LOGIN_LOGS_FILE, index=False)

def log_user_entry(user_info):
    logs_df = pd.read_csv(LOGIN_LOGS_FILE)
    new_log = pd.DataFrame([{
        "Timestamp": datetime.now(EGYPT_TZ).strftime("%Y-%m-%d %H:%M:%S"),
        "Name": user_info["Name"],
        "Email": user_info["Email"],
        "Role": user_info["Role"]
    }])
    updated_logs = pd.concat([logs_df, new_log], ignore_index=True)
    updated_logs.to_csv(LOGIN_LOGS_FILE, index=False)

def authenticate_user(email, password):
    users_df = pd.read_csv(USERS_DB_FILE)
    user = users_df[(users_df["Email"].str.lower() == email.lower()) & (users_df["Password"] == password)]
    if not user.empty:
        user_data = user.iloc[0]
        if user_data["Status"] == "Active":
            st.session_state["authenticated"] = True
            st.session_state["current_user"] = user_data.to_dict()
            log_user_entry(user_data)
            return True, "Success"
        else:
            return False, "Account Suspended. Contact Administrator."
    return False, "Invalid Email or Password."

# ==========================================
# 3. 3D Glassy Chart Styling Function
# ==========================================
def style_3d_glassy(fig, chart_type="bar"):
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Montserrat", color="#d1d5da", size=12),
        margin=dict(t=50, b=20, l=20, r=20)
    )
    if chart_type in ["bar", "pie", "histogram", "treemap"]:
        fig.update_traces(marker=dict(line=dict(color='rgba(255, 255, 255, 0.4)', width=1.5)), opacity=0.85)
    elif chart_type == "line":
        fig.update_traces(line=dict(width=4), marker=dict(size=8, line=dict(color='white', width=1.5)))
        
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='rgba(255,255,255,0.05)')
    return fig

# ==========================================
# 4. History Manager
# ==========================================
class HistoryManager:
    FILE_NAME = "project_history_log.csv"
    @staticmethod
    def save_metrics(metrics_dict):
        metrics_dict['Timestamp'] = datetime.now(EGYPT_TZ).strftime("%Y-%m-%d %H:%M:%S")
        df_new = pd.DataFrame([metrics_dict])
        if os.path.exists(HistoryManager.FILE_NAME):
            df_old = pd.read_csv(HistoryManager.FILE_NAME)
            df_combined = pd.concat([df_old, df_new], ignore_index=True)
        else:
            df_combined = df_new
        df_combined.to_csv(HistoryManager.FILE_NAME, index=False)

    @staticmethod
    def load_history():
        if os.path.exists(HistoryManager.FILE_NAME):
            return pd.read_csv(HistoryManager.FILE_NAME)
        return pd.DataFrame()

    @staticmethod
    def get_delta_html(current_val, metric_key, current_file_name):
        if not os.path.exists(HistoryManager.FILE_NAME): return "" 
        history_df = pd.read_csv(HistoryManager.FILE_NAME)
        if history_df.empty or metric_key not in history_df.columns: return ""
        if 'File_Name' not in history_df.columns:
            history_df['File_Name'] = current_file_name
        file_history = history_df[history_df['File_Name'] == current_file_name]
        if file_history.empty: return "" 
        last_val = file_history.iloc[-1][metric_key]
        diff = current_val - last_val
        pct_str = "0%" if last_val == 0 else f"{abs((diff / last_val) * 100):.1f}%"
        diff_fmt = f"{int(diff)}" if isinstance(current_val, int) or float(current_val).is_integer() else f"{diff:.2f}"
        if diff > 0: return f'<div class="delta-up">▲ +{diff_fmt} ({pct_str})</div>'
        elif diff < 0: return f'<div class="delta-down">▼ {diff_fmt} ({pct_str})</div>'
        else: return f'<div class="delta-neutral">➖ No change</div>'

# ==========================================
# 5. Page Config & CSS Styling
# ==========================================
st.set_page_config(page_title="Command Center BI Dashboard", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@300;500;700;800&display=swap');
    html, body, [class*="css"] { font-family: 'Montserrat', sans-serif !important; }
    .login-container { display: flex; justify-content: center; align-items: center; min-height: 80vh; }
    .login-title { color: #1e3d59; font-weight: 800; text-align: center; margin-bottom: 20px; font-size: 24px; letter-spacing: 1px;}
    [data-testid="stAppViewContainer"] { background: radial-gradient(circle at top right, #0b1a2e, #050a11) !important; }
    [data-testid="stSidebar"] { background-color: rgba(5, 10, 17, 0.95) !important; border-right: 1px solid rgba(255, 170, 0, 0.1); }
    .metric-card { background: linear-gradient(145deg, rgba(20, 35, 54, 0.6), rgba(10, 20, 33, 0.9)); backdrop-filter: blur(15px); -webkit-backdrop-filter: blur(15px); padding: 25px; border-radius: 20px; text-align: center; border: 1px solid rgba(255, 170, 0, 0.15); border-left: 4px solid #ffaa00; box-shadow: 0 10px 30px rgba(0, 0, 0, 0.4); margin-bottom: 15px; transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275); }
    .metric-card:hover { transform: translateY(-8px) scale(1.02); border-left: 4px solid #00d2ff; box-shadow: 0 15px 35px rgba(0, 210, 255, 0.25); }
    .metric-label { color: #8da3b9; font-size: 14px; font-weight: 500; margin-bottom: 5px; text-transform: uppercase; letter-spacing: 1.5px;}
    .metric-value { color: #ffffff !important; font-size: 38px; font-weight: 800; background: -webkit-linear-gradient(#ffffff, #a0aec0); -webkit-background-clip: text; -webkit-text-fill-color: transparent;}
    .prog-bg { width: 100%; background: rgba(255,255,255,0.1); border-radius: 5px; margin-top: 15px; height: 6px; overflow: hidden;}
    .prog-fill { height: 100%; border-radius: 5px; transition: width 1s ease-in-out;}
    .stDataFrame { border: 1px solid rgba(255, 255, 255, 0.05); border-radius: 12px; overflow: hidden; }
    .delta-up { color: #2ecc71; font-size: 14px; font-weight: bold; margin-top: 8px; text-shadow: 0 0 10px rgba(46, 204, 113, 0.4);}
    .delta-down { color: #e74c3c; font-size: 14px; font-weight: bold; margin-top: 8px; text-shadow: 0 0 10px rgba(231, 76, 60, 0.4);}
    .delta-neutral { color: #95a5a6; font-size: 14px; font-weight: bold; margin-top: 8px; }
    .bi-title { color: #ffaa00; font-size: 28px; font-weight: 800; margin-top: 40px; margin-bottom: 20px; text-shadow: 0px 0px 15px rgba(255, 170, 0, 0.3);}
    .gradient-divider { height: 2px; background: linear-gradient(90deg, transparent 0%, rgba(255,170,0,0.8) 50%, transparent 100%); margin-top: 40px; margin-bottom: 40px; border: none; opacity: 0.6;}
    .alert-banner { background: linear-gradient(90deg, rgba(231,76,60,0.9), rgba(192,57,43,0.9)); padding: 20px; border-radius: 15px; color: white; display: flex; justify-content: space-between; align-items: center; margin-bottom: 25px; box-shadow: 0 10px 30px rgba(231,76,60,0.3); border-left: 5px solid #ffaa00;}
    .simulator-card { background: linear-gradient(135deg, rgba(14, 36, 57, 0.7), rgba(46, 204, 113, 0.1)); backdrop-filter: blur(12px); padding: 25px; border-radius: 20px; border: 1px solid rgba(46, 204, 113, 0.4); text-align: center; margin-top: 15px; box-shadow: 0 8px 25px rgba(46, 204, 113, 0.15);}
    .leaderboard-card { background: rgba(10, 20, 33, 0.7); padding: 25px; border-radius: 20px; border-left: 5px solid; margin-bottom: 15px; box-shadow: 0 8px 20px rgba(0,0,0,0.3);}
    .health-card { background: rgba(10, 20, 33, 0.8); backdrop-filter: blur(10px); padding: 15px 25px; border-radius: 15px; border: 1px solid rgba(255, 255, 255, 0.1); display: flex; align-items: center; justify-content: space-between; margin-bottom: 25px; box-shadow: 0 5px 15px rgba(0,0,0,0.3);}
    .ticker-wrap { width: 100%; overflow: hidden; background: linear-gradient(90deg, rgba(0, 210, 255, 0.1), rgba(0,0,0,0)); border-radius: 8px; padding: 8px 0; margin-bottom: 20px; border-left: 3px solid #00d2ff;}
    .ticker { display: inline-block; white-space: nowrap; padding-right: 100%; animation-iteration-count: infinite; animation-timing-function: linear; animation-name: ticker; animation-duration: 35s;}
    @keyframes ticker { 0% { transform: translate3d(0, 0, 0); } 100% { transform: translate3d(-100%, 0, 0); } }
    .ticker-item { display: inline-block; padding: 0 2rem; font-weight: 500; color: #d1d5da; font-size: 14px;}
    .ticker-item span { color: #ffaa00; font-weight: bold; }
    ::-webkit-scrollbar { width: 8px; height: 8px; }
    ::-webkit-scrollbar-track { background: #050a11; }
    ::-webkit-scrollbar-thumb { background: rgba(255, 170, 0, 0.5); border-radius: 10px; }
    ::-webkit-scrollbar-thumb:hover { background: rgba(255, 170, 0, 0.8); }
    @media print {
        * { -webkit-print-color-adjust: exact !important; print-color-adjust: exact !important; }
        body, [data-testid="stAppViewContainer"] { background: #050a11 !important; }
        [data-testid="stSidebar"], .stFileUploader, .stButton, header, footer, [data-testid="stSidebarCollapsedControl"], .ticker-wrap { display: none !important; }
        .main .block-container { max-width: 100% !important; padding: 5mm !important; margin: 0 !important; }
        .metric-card, .simulator-card, .leaderboard-card, .health-card, div[data-testid="stPlotlyChart"], .alert-banner { page-break-inside: avoid !important; background: #0b1a2e !important; border: 1px solid rgba(255, 170, 0, 0.4) !important; }
        .metric-value, .bi-title { -webkit-text-fill-color: white !important; color: white !important; }
        h1, h2, h3, h4, p, span, .metric-label { color: #d1d5da !important; }
        .gradient-divider { display: none !important; }
    }
    </style>
    """, unsafe_allow_html=True)

def create_card(column, label, value, delta_html="", progress=None):
    if progress is not None:
        prog_color = "#2ecc71" if progress > 80 else ("#f1c40f" if progress > 50 else "#e74c3c")
        prog_html = f'<div class="prog-bg"><div class="prog-fill" style="width: {progress}%; background: {prog_color};"></div></div>'
    else:
        prog_html = ""
    column.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">{label}</div>
            <div class="metric-value">{value}</div>
            {delta_html}
            {prog_html}
        </div>
        """, unsafe_allow_html=True)

def ai_assistant(query, data_summary):
    query = query.lower()
    if "delay" in query or "time" in query or "duration" in query:
        return f"Based on data, the average duration is {data_summary['avg_duration']} days. Check the AI Predictive section for bottleneck warnings."
    elif "dpl" in query:
        return f"Current average DPL is {data_summary['avg_dpl']}. Ensure rejected samples are re-tested after proper compaction."
    else:
        return "I am here to assist. Ask me about project logs, contractor performance, or quality control metrics."

# ==========================================
# 6. Login Screen Logic
# ==========================================
def render_login_screen():
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    col_space1, col_center, col_space2 = st.columns([1, 2, 1])
    with col_center:
        st.markdown("""
            <div style="background: white; padding: 50px; border-radius: 15px; box-shadow: 0px 10px 40px rgba(0,0,0,0.7);">
                <div style="text-align:center; margin-bottom: 20px;">
                    <h1 style="color: #1e3d59; font-weight: 800; margin:0; letter-spacing: 2px;">KK ENGINEERING</h1>
                    <p style="color: #7f8c8d; font-size: 16px; margin:0;">Command Center Portal</p>
                </div>
                <hr style="border: 0.5px solid #eee; margin-bottom: 30px;">
        """, unsafe_allow_html=True)
        st.markdown('<div class="login-title">SIGN IN</div>', unsafe_allow_html=True)
        email = st.text_input("Email Address", placeholder="@ Mohamedhatem@kk.com")
        password = st.text_input("Password", type="password", placeholder="••••••••••••")
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Secure Login", use_container_width=True, type="primary"):
            success, msg = authenticate_user(email, password)
            if success:
                st.success("Authentication Successful. Initializing System...")
                st.rerun()
            else:
                st.error(msg)
        st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ==========================================
# 7. Main Dashboard Application
# ==========================================
def render_dashboard():
    user = st.session_state["current_user"]
    
    try: st.image("5.jpg", use_container_width=True)
    except: pass

    col_h1, col_h2 = st.columns([0.8, 0.2])
    with col_h1: st.title("Mega Infrastructure Command Center 🏗️⚡")
    with col_h2:
        st.markdown(f"<div style='background:rgba(255,170,0,0.1); padding:10px; border-radius:10px; border:1px solid #ffaa00; text-align:center;'><span style='color:#d1d5da; font-size:12px;'>Logged in as</span><br><b style='color:#ffaa00;'>{user['Name']}</b><br><span style='color:#2ecc71; font-size:12px;'>{user['Role']} Account</span></div>", unsafe_allow_html=True)
        if st.button("Logout", use_container_width=True):
            st.session_state["authenticated"] = False
            st.rerun()

    if user["Role"] == "Admin":
        with st.sidebar.expander("🔐 Admin Control Panel", expanded=False):
            st.markdown("#### User Management")
            users_df = pd.read_csv(USERS_DB_FILE)
            st.dataframe(users_df[["Name", "Email", "Role", "Status"]], use_container_width=True)
            tab_add, tab_edit, tab_backup = st.tabs(["➕ Add User", "✏️ Edit/Delete", "💾 Backup DB"])
            with tab_add:
                new_email = st.text_input("New User Email", key="add_email")
                new_pass = st.text_input("New Password", type="password", key="add_pass")
                new_name = st.text_input("Full Name", key="add_name")
                new_role = st.selectbox("Assign Role", ["User", "Admin"], key="add_role")
                if st.button("Create Account"):
                    if new_email and new_pass:
                        if new_email.lower() in users_df['Email'].str.lower().values:
                            st.error("Email already exists!")
                        else:
                            new_u = pd.DataFrame([{"Email": new_email, "Password": new_pass, "Name": new_name, "Role": new_role, "Status": "Active"}])
                            pd.concat([users_df, new_u], ignore_index=True).to_csv(USERS_DB_FILE, index=False)
                            st.success("User Added Successfully!")
                            st.rerun()
            with tab_edit:
                target_email = st.selectbox("Select User", users_df['Email'].tolist(), key="edit_select")
                if target_email:
                    target_idx = users_df.index[users_df['Email'] == target_email].tolist()[0]
                    user_to_edit = users_df.iloc[target_idx]
                    edit_name = st.text_input("Edit Name", value=user_to_edit['Name'], key=f"en_{target_email}")
                    edit_pass = st.text_input("Edit Password", value=user_to_edit['Password'], type="password", key=f"ep_{target_email}")
                    edit_role = st.selectbox("Edit Role", ["User", "Admin"], index=0 if user_to_edit['Role'] == "User" else 1, key=f"er_{target_email}")
                    edit_status = st.selectbox("Status", ["Active", "Suspended"], index=0 if user_to_edit['Status'] == "Active" else 1, key=f"es_{target_email}")
                    col_upd, col_del = st.columns(2)
                    if col_upd.button("Update User Profile", key=f"update_btn_{target_email}"):
                        users_df.at[target_idx, 'Name'] = edit_name
                        users_df.at[target_idx, 'Password'] = edit_pass
                        users_df.at[target_idx, 'Role'] = edit_role
                        users_df.at[target_idx, 'Status'] = edit_status
                        users_df.to_csv(USERS_DB_FILE, index=False)
                        st.success(f"Account updated successfully!")
                        st.rerun()
                    if col_del.button("🗑️ Delete User", key=f"del_btn_{target_email}"):
                        if target_email.lower() == "mohamedhatem@kk.com":
                            st.error("Cannot delete the Super Admin account!")
                        else:
                            users_df = users_df.drop(target_idx)
                            users_df.to_csv(USERS_DB_FILE, index=False)
                            st.success(f"User deleted permanently!")
                            st.rerun()
            with tab_backup:
                if os.path.exists(USERS_DB_FILE):
                    with open(USERS_DB_FILE, "rb") as f:
                        st.download_button("📥 Download Users DB", data=f, file_name="users_db_backup.csv", mime="text/csv", use_container_width=True)
                uploaded_db = st.file_uploader("📤 Restore Users DB", type="csv")
                if uploaded_db is not None:
                    restored_df = pd.read_csv(uploaded_db)
                    restored_df.to_csv(USERS_DB_FILE, index=False)
                    st.success("Users Restored Successfully!")
                    st.rerun()
            st.markdown("#### System Access Logs")
            logs_df = pd.read_csv(LOGIN_LOGS_FILE)
            st.dataframe(logs_df.tail(10), use_container_width=True)
            
    st.sidebar.divider()

    st.sidebar.markdown("### 📁 1. Data Source")
    data_source = st.sidebar.selectbox("Connection Type:", ["Local CSV Upload", "Live SQL Database (Pending)"])

    with st.sidebar.expander("🗄️ History Database Backup"):
        st.markdown("<span style='font-size:12px; color:#d1d5da;'>Because cloud servers reset daily, save your history before leaving and restore it tomorrow.</span>", unsafe_allow_html=True)
        history_upload = st.file_uploader("1. Restore History Log", type="csv")
        if history_upload is not None:
            restored_df = pd.read_csv(history_upload)
            restored_df.to_csv(HistoryManager.FILE_NAME, index=False)
            st.success("✅ History Restored!")
        if os.path.exists(HistoryManager.FILE_NAME):
            with open(HistoryManager.FILE_NAME, "rb") as f:
                st.download_button(label="2. Download Backup 💾", data=f, file_name=f"history_backup_{datetime.now(EGYPT_TZ).strftime('%Y%m%d')}.csv", mime="text/csv", use_container_width=True)
    
    st.sidebar.divider()

    uploaded_file = None
    if data_source == "Local CSV Upload":
        uploaded_file = st.sidebar.file_uploader("Upload your Project Log (CSV) 📂", type="csv")

    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
        df.columns = df.columns.str.strip() 
        
        if 'Test Type' in df.columns: df['Test Type'] = df['Test Type'].str.strip().str.upper()
        if 'Date ( test)' in df.columns: df['Date ( test)'] = pd.to_datetime(df['Date ( test)'], errors='coerce', dayfirst=True)
        if 'Date( SUB)' in df.columns: df['Date( SUB)'] = pd.to_datetime(df['Date( SUB)'], errors='coerce', dayfirst=True)

        total_rows = len(df)
        missing_dates = df['Date ( test)'].isnull().sum() if 'Date ( test)' in df.columns else 0
        missing_status = df['sample status'].isnull().sum() if 'sample status' in df.columns else 0
        duplicate_serials = df['serial'].duplicated().sum() if 'serial' in df.columns else 0
        total_errors = missing_dates + missing_status + duplicate_serials
        health_score = max(0, 100 - (total_errors / (total_rows+1) * 100)) if total_rows > 0 else 0
        health_color = "#2ecc71" if health_score >= 95 else ("#f1c40f" if health_score >= 80 else "#e74c3c")
        health_icon = "✅" if health_score >= 95 else ("⚠️" if health_score >= 80 else "🚨")
        
        error_details = []
        if missing_dates > 0: error_details.append(f"{missing_dates} Missing Dates")
        if missing_status > 0: error_details.append(f"{missing_status} Missing Status")
        if duplicate_serials > 0: error_details.append(f"{duplicate_serials} Duplicate Serials")
        scanned_msg = f"<span style='color:#00d2ff; font-weight:bold;'>Scanned {total_rows:,} Rows</span>"
        error_str = f"{scanned_msg} &rarr; " + " | ".join(error_details) if error_details else f"{scanned_msg} &rarr; Data is 100% clean and structured."
        
        st.markdown(f"""
            <div class="health-card" style="border-left: 5px solid {health_color};">
                <div>
                    <h4 style="margin: 0; color: #d1d5da; font-size: 14px; text-transform: uppercase;">{health_icon} Data Integrity Inspector</h4>
                    <p style="margin: 5px 0 0 0; color: #8da3b9; font-size: 13px;">{error_str}</p>
                </div>
                <div>
                    <h2 style="margin: 0; color: {health_color}; text-shadow: 0 0 10px {health_color};">{health_score:.1f}%</h2>
                </div>
            </div>
        """, unsafe_allow_html=True)

        st.sidebar.markdown("### 🎯 2. Smart Filters")
        global_search = st.sidebar.text_input("🔍 Global Search:", placeholder="Keyword (Serial, Date)...")
        if global_search:
            mask = df.astype(str).apply(lambda x: x.str.contains(global_search, case=False, na=False)).any(axis=1)
            df = df[mask]
            st.sidebar.success(f"🎯 Found {len(df)} records matching '{global_search}'")
            
        companies = df['Company Name'].dropna().unique() if 'Company Name' in df.columns else []
        selected_companies = st.sidebar.multiselect("🏢 Select Contractor:", options=companies, default=companies)
        statuses = df['sample status'].dropna().unique() if 'sample status' in df.columns else []
        selected_statuses = st.sidebar.multiselect("📊 Sample Status:", options=statuses, default=statuses)

        st.sidebar.markdown("### 🧠 3. AI & Simulation")
        sim_days_saved = st.sidebar.slider("🎛️ Simulate Delay Reduction (Days):", min_value=0, max_value=10, value=0, step=1)
        curr_avg_dpl = pd.to_numeric(df['AVERAGE VALUE'], errors='coerce').mean() if 'AVERAGE VALUE' in df.columns else 0
        curr_avg_dur = pd.to_numeric(df['DURATION'], errors='coerce').mean() if 'DURATION' in df.columns else 0
        user_question = st.sidebar.text_input("🤖 Ask AI about any log issue:")
        if user_question:
            summary = {"avg_dpl": round(curr_avg_dpl, 2), "avg_duration": round(curr_avg_dur, 1)}
            st.sidebar.info(f"AI Response: {ai_assistant(user_question, summary)}")

        filtered_df = df.copy()
        if len(companies) > 0: filtered_df = filtered_df[filtered_df['Company Name'].isin(selected_companies)]
        if len(statuses) > 0: filtered_df = filtered_df[filtered_df['sample status'].isin(selected_statuses)]

        num_tests_col = next((c for c in filtered_df.columns if 'NUM' in c.upper() and 'TEST' in c.upper()), None)
        if num_tests_col: filtered_df[num_tests_col] = pd.to_numeric(filtered_df[num_tests_col], errors='coerce').fillna(0)
        if 'DURATION' in filtered_df.columns: filtered_df['DURATION'] = pd.to_numeric(filtered_df['DURATION'], errors='coerce')

        total_requests_count = len(filtered_df)
        total_tests_count = int(filtered_df[num_tests_col].sum() if num_tests_col else 0)
        avg_dpl_value = round(pd.to_numeric(filtered_df['AVERAGE VALUE'], errors='coerce').mean() if 'AVERAGE VALUE' in filtered_df.columns else 0, 2)
        avg_duration_value = round(filtered_df['DURATION'].mean(), 1) if 'DURATION' in filtered_df.columns else 0
        page_col_name = next((c for c in filtered_df.columns if 'PAGE' in c.upper()), None)
        total_paperwork_pages = int(pd.to_numeric(filtered_df[page_col_name], errors='coerce').fillna(0).sum()) if page_col_name else 0

        current_metrics = {
            "File_Name": uploaded_file.name, 
            "Total_Requests": total_requests_count,
            "Total_Tests": total_tests_count,
            "Avg_DPL": avg_dpl_value,
            "Avg_Duration": avg_duration_value,
            "Total_Paperwork": total_paperwork_pages
        }
        
        overall_acc = len(filtered_df[filtered_df['sample status'].astype(str).str.upper().isin(['ACCEPTED', 'APPROVED AS NOTED'])]) if 'sample status' in filtered_df.columns else 0
        overall_rate = (overall_acc / total_requests_count * 100) if total_requests_count > 0 else 0

        rejected_count = len(filtered_df[filtered_df['sample status'].isin(['REJECTED', 'REVISE'])]) if 'sample status' in filtered_df.columns else 0
        ticker_html = f"""
        <div class="ticker-wrap">
            <div class="ticker">
                <div class="ticker-item">🚀 <b>Total Logged Submittals:</b> <span>{total_requests_count:,}</span></div>
                <div class="ticker-item">✅ <b>Current Global Yield:</b> <span>{overall_rate:.1f}%</span></div>
                <div class="ticker-item">⏱️ <b>Sector Avg Delay:</b> <span>{avg_duration_value} Days</span></div>
                <div class="ticker-item">🚨 <b>Pending Rejections:</b> <span>{rejected_count}</span></div>
                <div class="ticker-item">🧪 <b>Total Field Tests:</b> <span>{total_tests_count:,}</span></div>
            </div>
        </div>
        """
        st.markdown(ticker_html, unsafe_allow_html=True)
        worst_office_name = "N/A"
        worst_office_delay = 0
        if 'Done BY' in filtered_df.columns and 'DURATION' in filtered_df.columns:
            office_delays = filtered_df.dropna(subset=['DURATION']).groupby('Done BY')['DURATION'].mean().reset_index()
            if not office_delays.empty:
                worst_office = office_delays.loc[office_delays['DURATION'].idxmax()]
                worst_office_name = worst_office['Done BY']
                worst_office_delay = round(worst_office['DURATION'], 1)

        st.markdown(f"""
            <div class="alert-banner">
                <div>
                    <h3 style="margin:0; font-size:22px;">🚨 Command Center Live Alerts</h3>
                    <p style="margin:5px 0 0 0; font-size:14px; opacity:0.9;">Top issues requiring immediate management attention today.</p>
                </div>
                <div style="text-align:right;">
                    <div style="background:rgba(0,0,0,0.2); padding:8px 15px; border-radius:8px; margin-bottom:5px;"><b>Worst Delay Node:</b> {worst_office_name} ({worst_office_delay} Days)</div>
                    <div style="background:rgba(0,0,0,0.2); padding:8px 15px; border-radius:8px;"><b>Critical Rejections:</b> {rejected_count} Submittals pending</div>
                </div>
            </div>
        """, unsafe_allow_html=True)

        st.markdown(f"**📂 Active Data Source:** `{uploaded_file.name}`")
        col_btn, col_msg = st.columns([0.2, 0.8])
        with col_btn:
            if st.button("💾 Save to BI History"):
                HistoryManager.save_metrics(current_metrics)
                st.success("✅ Logged Successfully!")
                st.rerun() 

        st.markdown("### 📊 Executive Key Performance Indicators")
        col1, col2, col3, col4, col5 = st.columns(5)
        t_req = 1000; t_test = 5000; t_dpl = 20; t_dur = 10
        d1 = HistoryManager.get_delta_html(current_metrics["Total_Requests"], "Total_Requests", uploaded_file.name)
        create_card(col1, "Total Submittals", current_metrics["Total_Requests"], delta_html=d1, progress=min(100, (current_metrics["Total_Requests"]/t_req)*100 if current_metrics["Total_Requests"] else 0))
        d2 = HistoryManager.get_delta_html(current_metrics["Total_Tests"], "Total_Tests", uploaded_file.name)
        create_card(col2, "Total Tests", current_metrics["Total_Tests"], delta_html=d2, progress=min(100, (current_metrics["Total_Tests"]/t_test)*100 if current_metrics["Total_Tests"] else 0))
        d3 = HistoryManager.get_delta_html(current_metrics["Avg_DPL"], "Avg_DPL", uploaded_file.name)
        create_card(col3, "Avg DPL Value", current_metrics["Avg_DPL"], delta_html=d3, progress=min(100, (current_metrics["Avg_DPL"]/t_dpl)*100 if current_metrics["Avg_DPL"] else 0))
        d4 = HistoryManager.get_delta_html(current_metrics["Avg_Duration"], "Avg_Duration", uploaded_file.name)
        dur_prog = max(0, 100 - (current_metrics["Avg_Duration"]/t_dur * 100)) if current_metrics["Avg_Duration"] else 100
        create_card(col4, "Avg. Dur (Days)", current_metrics["Avg_Duration"], delta_html=d4, progress=dur_prog)
        d5 = HistoryManager.get_delta_html(current_metrics["Total_Paperwork"], "Total_Paperwork", uploaded_file.name)
        create_card(col5, "Total Paperwork", current_metrics["Total_Paperwork"], delta_html=d5)

        g_col, s_col = st.columns([0.4, 0.6])
        with g_col:
            fig_gauge = go.Figure(go.Indicator(
                mode="gauge+number", value=overall_rate,
                title={'text': "Overall Approval Index", 'font': {'size': 20, 'color': 'white'}},
                number={'suffix': "%", 'font': {'size': 40, 'color': 'white'}},
                gauge={'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "rgba(255,255,255,0.2)"}, 'bar': {'color': "#ffffff", 'thickness': 0.25}, 'bgcolor': "rgba(255,255,255,0.05)", 'steps': [{'range': [0, 60], 'color': "#e74c3c"}, {'range': [60, 85], 'color': "#f1c40f"}, {'range': [85, 100], 'color': "#2ecc71"}]}
            ))
            fig_gauge.update_layout(paper_bgcolor="rgba(0,0,0,0)", height=250, margin=dict(l=20, r=20, t=40, b=20), font={'family': 'Montserrat'})
            st.plotly_chart(fig_gauge, use_container_width=True)

        with s_col:
            if sim_days_saved > 0:
                total_time_recovered = sim_days_saved * total_requests_count
                st.markdown(f"""
                    <div class="simulator-card">
                        <h4 style="color: #2ecc71; margin: 0; text-transform: uppercase; font-size: 16px; letter-spacing: 1px;">✨ Simulated Optimization Impact</h4>
                        <p style="font-size: 38px; font-weight: 800; color: #ffffff; margin: 5px 0;">{total_time_recovered:,} <span style="font-size:16px; color:#d1d5da; font-weight:500;">Project Days Saved</span></p>
                        <p style="font-size: 14px; color: #a0aec0; margin: 0; line-height: 1.6;">Reducing paperwork cycle times by {sim_days_saved} days across all active submittals accelerates overall sector handovers.</p>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.markdown("""
                    <div class="simulator-card" style="border-color: rgba(255,255,255,0.1); background: rgba(10, 20, 33, 0.5);">
                        <h4 style="color: #8da3b9; margin: 0; font-size: 18px;">🎛️ Optimization Simulator Inactive</h4>
                        <p style="font-size: 14px; color: #8da3b9; margin-top: 15px;">Use the slider in the sidebar to simulate the impact of reducing administrative delays.</p>
                    </div>
                    """, unsafe_allow_html=True)

        st.markdown('<div class="gradient-divider"></div>', unsafe_allow_html=True)

        st.markdown("#### 📝 AI Executive Auto-Narrative")
        narrative = f"The dataset encompasses <b>{total_requests_count:,}</b> submittals involving <b>{total_tests_count:,}</b> field tests. The current overall approval index stands at <b>{overall_rate:.1f}%</b>, with an average turnaround time of <b>{avg_duration_value} days</b>. "
        if worst_office_name != "N/A":
            narrative += f"Attention is required for <b>{worst_office_name}</b>, which currently flags the highest processing delays across the logged sectors."
        st.markdown(f"<div style='font-size: 15px; color: #8da3b9; line-height: 1.6; background: rgba(0,210,255,0.05); padding: 20px; border-radius: 10px; border-left: 4px solid #00d2ff; margin-bottom: 25px;'>{narrative}</div>", unsafe_allow_html=True)

        st.markdown('<div class="bi-title">🤖 Live Anomaly & Root Cause Detector</div>', unsafe_allow_html=True)
        anomalies = []
        if 'Company Name' in filtered_df.columns and 'DURATION' in filtered_df.columns:
            comp_dur = filtered_df.groupby('Company Name')['DURATION'].mean()
            for comp, dur in comp_dur.items():
                if dur > avg_duration_value + 5:
                    anomalies.append(f"⚠️ <b>Anomaly Detected:</b> <b>{comp}</b> is showing severe delays ({dur:.1f} days) compared to the global average ({avg_duration_value:.1f} days).")
        if 'sample status' in filtered_df.columns and 'Test Type' in filtered_df.columns:
            rejections_df = filtered_df[filtered_df['sample status'].isin(['REJECTED', 'REVISE'])]
            if not rejections_df.empty:
                top_fail_test = rejections_df['Test Type'].value_counts().idxmax()
                top_fail_comp = rejections_df['Company Name'].value_counts().idxmax() if 'Company Name' in rejections_df.columns else "Unknown"
                fail_pct = (len(rejections_df) / total_requests_count * 100) if total_requests_count > 0 else 0
                if fail_pct > 10:
                    anomalies.append(f"🔍 <b>Root Cause Insight:</b> Global rejection rate is high ({fail_pct:.1f}%). The primary contributor is the <b>{top_fail_test}</b> test, most frequently failing under contractor <b>{top_fail_comp}</b>.")
        if anomalies:
            for anomaly in anomalies:
                st.markdown(f'<div style="background: rgba(231,76,60,0.1); border-left: 4px solid #e74c3c; padding: 15px; margin-bottom: 10px; border-radius: 8px; color: #d1d5da;">{anomaly}</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div style="background: rgba(46,204,113,0.1); border-left: 4px solid #2ecc71; padding: 15px; margin-bottom: 10px; border-radius: 8px; color: #d1d5da;">✅ No severe workflow anomalies or critical bottlenecks detected in the current data scope.</div>', unsafe_allow_html=True)

        st.markdown('<div class="gradient-divider"></div>', unsafe_allow_html=True)

        st.markdown('<div class="bi-title">🏆 Benchmark Engine</div>', unsafe_allow_html=True)
        if 'Company Name' in filtered_df.columns:
            bm_comp = st.selectbox("Select Contractor for Benchmarking against Global Averages:", companies, key="bm_engine")
            if bm_comp:
                bm_df = filtered_df[filtered_df['Company Name'] == bm_comp]
                bm_acc = len(bm_df[bm_df['sample status'].isin(['ACCEPTED', 'APPROVED AS NOTED'])]) if 'sample status' in bm_df.columns else 0
                bm_yield = (bm_acc / len(bm_df) * 100) if len(bm_df) > 0 else 0
                bm_dur = bm_df['DURATION'].mean() if 'DURATION' in bm_df.columns else 0
                b1, b2 = st.columns(2)
                y_diff = bm_yield - overall_rate
                y_color = "#2ecc71" if y_diff >= 0 else "#e74c3c"
                y_icon = "▲" if y_diff >= 0 else "▼"
                b1.markdown(f"<div class='metric-card'><h4>Yield vs Sector Avg</h4><h2 style='color:white;'>{bm_yield:.1f}%</h2><p style='color:{y_color}; font-weight:bold;'>{y_icon} {abs(y_diff):.1f}% vs Global ({overall_rate:.1f}%)</p></div>", unsafe_allow_html=True)
                d_diff = bm_dur - avg_duration_value
                d_color = "#e74c3c" if d_diff > 0 else "#2ecc71" 
                d_icon = "▲" if d_diff > 0 else "▼"
                b2.markdown(f"<div class='metric-card'><h4>Delay vs Sector Avg</h4><h2 style='color:white;'>{bm_dur:.1f} Days</h2><p style='color:{d_color}; font-weight:bold;'>{d_icon} {abs(d_diff):.1f} Days vs Global ({avg_duration_value:.1f})</p></div>", unsafe_allow_html=True)
        else:
            st.info("Company Name column is required for benchmarking.")

        st.markdown('<div class="gradient-divider"></div>', unsafe_allow_html=True)

        st.markdown('<div class="bi-title">⚔️ Head-to-Head: Contractor vs Contractor</div>', unsafe_allow_html=True)
        if 'Company Name' in filtered_df.columns and len(companies) >= 2:
            cc1, cc2 = st.columns(2)
            c_a = cc1.selectbox("Select Contractor A", companies, index=0)
            c_b = cc2.selectbox("Select Contractor B", companies, index=1 if len(companies)>1 else 0)
            def get_c_stats(c_name):
                d = filtered_df[filtered_df['Company Name']==c_name]
                tot = len(d)
                acc = len(d[d['sample status'].astype(str).str.upper().isin(['ACCEPTED', 'APPROVED AS NOTED'])]) if 'sample status' in d.columns else 0
                rate = (acc/tot*100) if tot>0 else 0
                dur = round(d['DURATION'].mean(), 1) if 'DURATION' in d.columns else 0
                return tot, rate, dur
            tot_a, r_a, d_a = get_c_stats(c_a)
            tot_b, r_b, d_b = get_c_stats(c_b)
            st.markdown(f"""
            <div style="display:flex; justify-content:space-between; text-align:center; background:rgba(10,20,33,0.8); padding:20px; border-radius:15px; border:1px solid #ffaa00; box-shadow: 0 5px 15px rgba(0,0,0,0.4);">
                <div style="width:45%; border-right:1px solid rgba(255,255,255,0.1);"><h3 style="color:#00d2ff; margin-top:0;">{c_a}</h3><p style="font-size:32px; font-weight:800; color:white; margin:0;">{r_a:.1f}% Yield</p><p style="color:#8da3b9; font-size:14px; margin-top:5px;">{tot_a} Submittals | {d_a} Days Avg Delay</p></div>
                <div style="width:10%; align-self:center; font-size:30px; font-weight:900; color:#ffaa00; text-shadow: 0 0 10px rgba(255,170,0,0.5);">VS</div>
                <div style="width:45%; border-left:1px solid rgba(255,255,255,0.1);"><h3 style="color:#e74c3c; margin-top:0;">{c_b}</h3><p style="font-size:32px; font-weight:800; color:white; margin:0;">{r_b:.1f}% Yield</p><p style="color:#8da3b9; font-size:14px; margin-top:5px;">{tot_b} Submittals | {d_b} Days Avg Delay</p></div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.info("Requires 'Company Name' column and at least 2 contractors to enable Head-to-Head comparison.")

        st.markdown('<div class="gradient-divider"></div>', unsafe_allow_html=True)

        st.markdown('<div class="bi-title">🧪 Monthly Test Volume & Deficit Analysis</div>', unsafe_allow_html=True)
        if 'Date ( test)' in filtered_df.columns and 'Test Type' in filtered_df.columns:
            v_df = filtered_df.dropna(subset=['Date ( test)', 'Test Type']).copy()
            v_df['Month_Sort'] = v_df['Date ( test)'].dt.to_period('M')
            v_df['Month'] = v_df['Date ( test)'].dt.strftime('%b %Y')
            monthly_summary = v_df.groupby(['Month_Sort', 'Month', 'Test Type']).size().reset_index(name='Volume')
            monthly_summary = monthly_summary.sort_values('Month_Sort')
            fig_vol = px.bar(monthly_summary, x='Month', y='Volume', color='Test Type', barmode='group', title="Testing Intensity & Production Coverage per Month", color_discrete_sequence=NEON_COLORS)
            fig_vol.update_traces(hovertemplate='<b>Month:</b> %{x}<br><b>Volume:</b> %{y} Submittals')
            fig_vol = style_3d_glassy(fig_vol, chart_type="bar")
            ch_col, txt_col = st.columns([0.7, 0.3])
            ch_col.plotly_chart(fig_vol, use_container_width=True)
            with txt_col:
                st.markdown("#### 💡 AI Production Insights")
                if not monthly_summary.empty:
                    top_row = monthly_summary.loc[monthly_summary['Volume'].idxmax()]
                    st.info(f"📊 **Peak Activity:**\nIn **{top_row['Month']}**, the highest utilized test was **{top_row['Test Type']}** with **{top_row['Volume']}** submittals logged.")
                    months_ordered = monthly_summary['Month_Sort'].drop_duplicates().sort_values().tolist()
                    if len(months_ordered) > 1:
                        last_month_sort = months_ordered[-1]
                        prev_month_sort = months_ordered[-2]
                        last_month_name = last_month_sort.strftime('%b %Y')
                        prev_month_name = prev_month_sort.strftime('%b %Y')
                        last_count = v_df[v_df['Month_Sort'] == last_month_sort].shape[0]
                        prev_count = v_df[v_df['Month_Sort'] == prev_month_sort].shape[0]
                        if last_count < prev_count:
                            st.warning(f"⚠️ **Coverage Alert:**\nTotal log volume dropped from **{prev_count}** in {prev_month_name} to **{last_count}** in {last_month_name}. Verify potential field testing deficits.")
                        else:
                            st.success(f"✅ **Stable Volume:**\nTesting coverage is expanding smoothly from {prev_month_name} into {last_month_name}.")
                else:
                    st.text("No data available for tracking.")

        if 'Date ( test)' in filtered_df.columns:
            st.markdown('<div class="bi-title">🗓️ Activity Heatmap Calendar</div>', unsafe_allow_html=True)
            cal_df = filtered_df.dropna(subset=['Date ( test)']).copy()
            cal_df['Day'] = cal_df['Date ( test)'].dt.day
            cal_df['Month_Name'] = cal_df['Date ( test)'].dt.strftime('%b %Y')
            hm_data = cal_df.groupby(['Month_Name', 'Day']).size().reset_index(name='Submittals')
            fig_hm = px.density_heatmap(hm_data, x="Day", y="Month_Name", z="Submittals", color_continuous_scale="Viridis", title="Daily Activity Intensity (GitHub Style)", labels={'Day': 'Day of Month', 'Month_Name': 'Month'})
            fig_hm.update_traces(hovertemplate='<b>Date:</b> %{y} %{x}<br><b>Activity:</b> %{z} Tests Logged')
            fig_hm = style_3d_glassy(fig_hm, chart_type="heatmap")
            st.plotly_chart(fig_hm, use_container_width=True)

        st.markdown('<div class="gradient-divider"></div>', unsafe_allow_html=True)

        st.markdown("### 📈 Timeline Analysis")
        time_col1, time_col2 = st.columns(2)
        with time_col1:
            if 'Date ( test)' in filtered_df.columns:
                tl_df = filtered_df.copy()
                tl_df['Month_Plot'] = tl_df['Date ( test)'].dt.to_period('M').astype(str)
                monthly_data = tl_df.groupby('Month_Plot').size().reset_index(name='Count')
                fig_m = px.line(monthly_data.sort_values('Month_Plot'), x='Month_Plot', y='Count', markers=True, title="Monthly Workload Trend 📅", color_discrete_sequence=['#00d2ff'])
                fig_m = style_3d_glassy(fig_m, chart_type="line")
                st.plotly_chart(fig_m, use_container_width=True)

        with time_col2:
            if 'Date( SUB)' in filtered_df.columns and 'sample status' in filtered_df.columns:
                gap_df = filtered_df.dropna(subset=['Date( SUB)']).copy()
                gap_df['Month_Plot'] = gap_df['Date( SUB)'].dt.to_period('M').astype(str)
                total_sub = gap_df.groupby('Month_Plot').size().reset_index(name='Total Submitted')
                accepted_mask = gap_df['sample status'].str.upper().isin(['ACCEPTED', 'APPROVED AS NOTED'])
                accepted_sub = gap_df[accepted_mask].groupby('Month_Plot').size().reset_index(name='Accepted')
                rejected_mask = gap_df['sample status'].str.upper().isin(['REJECTED', 'REVISE'])
                rejected_sub = gap_df[rejected_mask].groupby('Month_Plot').size().reset_index(name='Rejected')
                merged_gap = total_sub.merge(accepted_sub, on='Month_Plot', how='left').merge(rejected_sub, on='Month_Plot', how='left').fillna(0)
                melted_gap = merged_gap.melt(id_vars='Month_Plot', value_vars=['Total Submitted', 'Accepted', 'Rejected'], var_name='Status', value_name='Count')
                fig_gap = px.bar(
                    melted_gap.sort_values('Month_Plot'), 
                    x='Month_Plot', y='Count', color='Status', barmode='group',
                    color_discrete_map={'Total Submitted': '#00d2ff', 'Accepted': '#2ecc71', 'Rejected': '#ff007f'},
                    title="Monthly Quality Yield (Based on Submission Date) 🎯"
                )
                fig_gap = style_3d_glassy(fig_gap, chart_type="bar")
                st.plotly_chart(fig_gap, use_container_width=True)

        st.markdown('<div class="gradient-divider"></div>', unsafe_allow_html=True)

        st.markdown('<div class="bi-title">🤖 Predictive Risk Forecasting</div>', unsafe_allow_html=True)
        if 'Date ( test)' in filtered_df.columns and 'DURATION' in filtered_df.columns:
            pred_df = filtered_df.dropna(subset=['Date ( test)', 'DURATION']).sort_values('Date ( test)')
            pred_df['7-Day Trend'] = pred_df['DURATION'].rolling(window=7, min_periods=1).mean()
            fig_pred = px.line(pred_df, x='Date ( test)', y=['DURATION', '7-Day Trend'], title="Duration Forecasting & Trendline Tracking", color_discrete_sequence=['#ffaa00', '#00d2ff'])
            fig_pred = style_3d_glassy(fig_pred, chart_type="line")
            latest_trend = pred_df['7-Day Trend'].iloc[-1] if not pred_df.empty else 0
            p1, p2 = st.columns([0.7, 0.3])
            p1.plotly_chart(fig_pred, use_container_width=True)
            with p2:
                st.info("**AI Risk Assessment:**")
                if latest_trend > current_metrics["Avg_Duration"]:
                    st.error(f"🚨 **Warning:** The recent workflow trend is rising ({latest_trend:.1f} days) compared to the overall average. Bottlenecks are forming.")
                else:
                    st.success(f"✅ **Stable:** Workflow trend is improving or stable at {latest_trend:.1f} days.")

        st.markdown('<div class="bi-title">🗺️ Sector Performance Heat Map</div>', unsafe_allow_html=True)
        if 'Classification' in filtered_df.columns and 'Company Name' in filtered_df.columns and 'sample status' in filtered_df.columns:
            tree_df = filtered_df.copy()
            tree_df[['Classification', 'Company Name', 'sample status']] = tree_df[['Classification', 'Company Name', 'sample status']].fillna('Unknown')
            status_weights = {'ACCEPTED': 100, 'APPROVED AS NOTED': 80, 'REVISE': 40, 'REJECTED': 0, 'Unknown': 50}
            tree_df['Heat_Score'] = tree_df['sample status'].map(status_weights).fillna(50)
            fig_tree = px.treemap(tree_df, path=['Classification', 'Company Name', 'sample status'], color='Heat_Score', color_continuous_scale='RdYlGn', title="Project Hierarchy Heat Map (Green = High Approval, Red = Bottleneck/Rejections)")
            fig_tree.update_traces(hovertemplate='<b>%{label}</b><br>Score: %{color:.1f}')
            fig_tree = style_3d_glassy(fig_tree, chart_type="treemap")
            st.plotly_chart(fig_tree, use_container_width=True)

        st.markdown('<div class="bi-title">🖨️ Smart PDF Executive Report</div>', unsafe_allow_html=True)
        st.info("💡 **CEO Feature:** Click the button below to download a styled HTML report. When opened, it can be easily saved as a perfectly formatted PDF for your Daily/Weekly Briefing!")
        html_report = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <title>Executive Report - {uploaded_file.name}</title>
            <style>
                body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; padding: 40px; color: #333; }}
                .header {{ border-bottom: 3px solid #1e3d59; padding-bottom: 20px; margin-bottom: 30px; display: flex; justify-content: space-between; align-items: center; }}
                .header h1 {{ color: #1e3d59; margin: 0; font-size: 32px; text-transform: uppercase; }}
                .header p {{ margin: 5px 0 0 0; color: #7f8c8d; }}
                .score-card {{ background: #f8f9fa; border-left: 5px solid #2ecc71; padding: 20px; margin-bottom: 30px; border-radius: 5px; }}
                .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 30px; }}
                .box {{ border: 1px solid #ecf0f1; padding: 20px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }}
                .box h3 {{ margin-top: 0; color: #e67e22; border-bottom: 1px solid #ecf0f1; padding-bottom: 10px; }}
                table {{ width: 100%; border-collapse: collapse; margin-top: 15px; }}
                th, td {{ padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }}
                th {{ background-color: #1e3d59; color: white; }}
            </style>
        </head>
        <body onload="window.print()">
            <div class="header">
                <div>
                    <h1>Executive Intelligence Briefing</h1>
                    <p><strong>System:</strong> Mega Infrastructure BI Portal</p>
                    <p><strong>Dataset:</strong> {uploaded_file.name}</p>
                    <p><strong>Generated On:</strong> {datetime.now(EGYPT_TZ).strftime("%Y-%m-%d at %I:%M %p")}</p>
                </div>
                <div style="font-size: 50px;">🏛️</div>
            </div>
            <div class="score-card">
                <h2 style="margin:0; color: #2c3e50;">Project Health Index: {overall_rate:.1f}% Approval Rate</h2>
                <p style="margin:5px 0 0 0;">Evaluating {total_requests_count} total submittals to date.</p>
            </div>
            <div class="grid">
                <div class="box">
                    <h3>📊 Key Performance Metrics</h3>
                    <table>
                        <tr><td>Total Submittals</td><td><strong>{current_metrics["Total_Requests"]}</strong></td></tr>
                        <tr><td>Total Field Tests</td><td><strong>{current_metrics["Total_Tests"]}</strong></td></tr>
                        <tr><td>Average Duration</td><td><strong>{current_metrics["Avg_Duration"]} Days</strong></td></tr>
                        <tr><td>Average DPL Score</td><td><strong>{current_metrics["Avg_DPL"]}</strong></td></tr>
                        <tr><td>Total Paperwork Pages</td><td><strong>{current_metrics["Total_Paperwork"]}</strong></td></tr>
                    </table>
                </div>
                <div class="box">
                    <h3>⚠️ Risk & Bottleneck Analysis</h3>
                    <table>
                        <tr><td>Rejected/Revise Count</td><td><strong style="color: #e74c3c;">{rejected_count} Submittals</strong></td></tr>
                        <tr><td>Critical Bottleneck Node</td><td><strong>{worst_office_name}</strong></td></tr>
                        <tr><td>Max Department Delay</td><td><strong style="color: #e74c3c;">{worst_office_delay} Days Average</strong></td></tr>
                        <tr><td>Data Integrity Score</td><td><strong>{health_score:.1f}%</strong></td></tr>
                    </table>
                </div>
            </div>
            <p style="text-align: center; color: #95a5a6; font-size: 12px; margin-top: 50px;">Confidential Document - Generated Automatically by the AI BI Framework</p>
        </body>
        </html>
        """
        b64 = base64.b64encode(html_report.encode()).decode()
        href = f'<a href="data:text/html;base64,{b64}" download="Executive_Report_{datetime.now(EGYPT_TZ).strftime("%Y%m%d")}.html" style="background-color:#ffaa00; color:#1e3d59; padding:12px 24px; text-decoration:none; font-weight:bold; border-radius:8px; display:inline-block; transition:0.3s; box-shadow: 0 4px 15px rgba(255, 170, 0, 0.4);">📄 Download PDF-Ready Report</a>'
        st.markdown(href, unsafe_allow_html=True)

        st.markdown('<div class="gradient-divider"></div>', unsafe_allow_html=True)

        global_history_df = HistoryManager.load_history()
        if not global_history_df.empty:
            if 'File_Name' not in global_history_df.columns:
                global_history_df['File_Name'] = uploaded_file.name
            file_trend_df = global_history_df[global_history_df['File_Name'] == uploaded_file.name].copy()
            if len(file_trend_df) > 1:
                st.markdown(f"### 🚀 KPI Daily Growth Trend for `{uploaded_file.name}`")
                file_trend_df['Added_Requests'] = file_trend_df['Total_Requests'].diff().fillna(0)
                file_trend_df['Growth_Rate_%'] = ((file_trend_df['Total_Requests'].diff() / file_trend_df['Total_Requests'].shift(1)) * 100).fillna(0)
                file_trend_df['Date_Time'] = pd.to_datetime(file_trend_df['Timestamp']).dt.strftime('%m-%d %H:%M')
                col_t1, col_t2 = st.columns(2)
                with col_t1:
                    fig_added = px.bar(file_trend_df.iloc[1:], x='Date_Time', y='Added_Requests', title="Daily Added Submittals Trend", text_auto=True, color_discrete_sequence=['#00d2ff'])
                    fig_added = style_3d_glassy(fig_added, chart_type="bar")
                    st.plotly_chart(fig_added, use_container_width=True)
                with col_t2:
                    fig_rate = px.line(file_trend_df.iloc[1:], x='Date_Time', y='Growth_Rate_%', title="Growth Rate Trend Percentage (%)", markers=True, color_discrete_sequence=['#2ecc71'])
                    fig_rate = style_3d_glassy(fig_rate, chart_type="line")
                    st.plotly_chart(fig_rate, use_container_width=True)
                with st.expander("🖨️ View & Export History Log for this File"):
                    export_df = file_trend_df[['Timestamp', 'Total_Requests', 'Added_Requests', 'Growth_Rate_%', 'Avg_DPL', 'Avg_Duration']].copy()
                    export_df.rename(columns={'Added_Requests': '+ Added', 'Growth_Rate_%': 'Growth %'}, inplace=True)
                    st.dataframe(export_df.round(2), use_container_width=True)
                st.markdown('<div class="gradient-divider"></div>', unsafe_allow_html=True)

        if num_tests_col and 'Test Type' in filtered_df.columns:
            st.markdown("### 🧪 Detailed Test Counts by Type")
            test_summary = filtered_df.groupby('Test Type')[num_tests_col].sum().reset_index()
            t_cols = st.columns(len(test_summary))
            for i, row in test_summary.iterrows():
                create_card(t_cols[i], row['Test Type'], int(row[num_tests_col]))
            st.markdown('<div class="gradient-divider"></div>', unsafe_allow_html=True)

        st.markdown("### 📈 Quality Metrics Distribution (DPL & Average Values)")
        if 'AVERAGE VALUE' in filtered_df.columns:
            dpl_df = filtered_df.dropna(subset=['AVERAGE VALUE']).copy()
            dpl_df['AVERAGE VALUE'] = pd.to_numeric(dpl_df['AVERAGE VALUE'], errors='coerce')
            dpl_df = dpl_df.dropna(subset=['AVERAGE VALUE'])
            if not dpl_df.empty:
                fig_dpl = px.histogram(dpl_df, x='AVERAGE VALUE', color='Test Type' if 'Test Type' in dpl_df.columns else None, marginal='box', title="Statistical Distribution & Outlier Detection for Test Values", nbins=30, color_discrete_sequence=NEON_COLORS)
                fig_dpl = style_3d_glassy(fig_dpl, chart_type="histogram")
                st.plotly_chart(fig_dpl, use_container_width=True)
        st.markdown('<div class="gradient-divider"></div>', unsafe_allow_html=True)

        st.markdown("### 💡 Strategic Insights & Recommendations")
        ins_col1, ins_col2 = st.columns(2)
        with ins_col1:
            st.success("✅ **Quality Improvement:**\n* Maintain tight oversight on duration KPIs.\n* Stable DPL curves confirm materials testing compliance.")
        with ins_col2:
            st.warning("⚠️ **Risk Mitigation:**\n* Closely audit moisture metrics for failed trials.\n* Intervene in lagging workflow review desks.")

        st.markdown('<div class="gradient-divider"></div>', unsafe_allow_html=True)

        chart_col1, chart_col2 = st.columns(2)
        with chart_col1:
            if 'Company Name' in filtered_df.columns and 'Test Type' in filtered_df.columns:
                if num_tests_col:
                    c1_df = filtered_df.groupby(['Company Name', 'Test Type'])[num_tests_col].sum().reset_index(name='Count')
                    c1_title = "Workload per Contractor (Total Test Points)"
                else:
                    c1_df = filtered_df.groupby(['Company Name', 'Test Type']).size().reset_index(name='Count')
                    c1_title = "Workload per Contractor (Total Submittals)"
                    
                fig_c1 = px.bar(c1_df, x='Company Name', y='Count', color='Test Type', title=c1_title, color_discrete_sequence=NEON_COLORS)
                fig_c1.update_traces(hovertemplate='<b>%{x}</b><br>Test: %{data.name}<br>Count: %{y}')
                fig_c1 = style_3d_glassy(fig_c1, chart_type="bar")
                st.plotly_chart(fig_c1, use_container_width=True)
                
            if 'Done BY' in filtered_df.columns and 'Test Type' in filtered_df.columns:
                if num_tests_col:
                    c2_df = filtered_df.groupby(['Done BY', 'Test Type'])[num_tests_col].sum().reset_index(name='Count')
                    c2_title = "Office Performance Analysis (Total Test Points)"
                else:
                    c2_df = filtered_df.groupby(['Done BY', 'Test Type']).size().reset_index(name='Count')
                    c2_title = "Office Performance Analysis (Total Submittals)"
                    
                fig_c2 = px.bar(c2_df, x='Done BY', y='Count', color='Test Type', title=c2_title, color_discrete_sequence=NEON_COLORS)
                fig_c2.update_traces(hovertemplate='<b>Office:</b> %{x}<br>Test: %{data.name}<br>Count: %{y}')
                fig_c2 = style_3d_glassy(fig_c2, chart_type="bar")
                st.plotly_chart(fig_c2, use_container_width=True)

        with chart_col2:
            if 'sample status' in filtered_df.columns:
                fig_p1 = px.pie(filtered_df, names='sample status', hole=0.4, title="Sample Status Distribution", color_discrete_map={'ACCEPTED':'#2ecc71', 'REJECTED':'#ff007f', 'REVISE':'#f1c40f', 'APPROVED AS NOTED':'#00d2ff'})
                fig_p1.update_traces(hovertemplate='<b>Status:</b> %{label}<br>Count: %{value} (%{percent})')
                fig_p1 = style_3d_glassy(fig_p1, chart_type="pie")
                st.plotly_chart(fig_p1, use_container_width=True)
            if 'Classification' in filtered_df.columns:
                class_df = filtered_df.dropna(subset=['Classification']).copy()
                if not class_df.empty:
                    fig_p2 = px.pie(class_df, names='Classification', title="Sample Classification Distribution", color_discrete_sequence=NEON_COLORS)
                    fig_p2 = style_3d_glassy(fig_p2, chart_type="pie")
                    st.plotly_chart(fig_p2, use_container_width=True)

        st.markdown('<div class="gradient-divider"></div>', unsafe_allow_html=True)

        st.markdown('<div class="bi-title">🏗️ Contractor Materials & Sourcing Analysis</div>', unsafe_allow_html=True)
        if 'Company Name' in filtered_df.columns and 'sample status' in filtered_df.columns:
            comp_stats = []
            for comp in filtered_df['Company Name'].dropna().unique():
                cdf = filtered_df[filtered_df['Company Name'] == comp]
                c_total = len(cdf)
                c_acc = len(cdf[cdf['sample status'].astype(str).str.upper().isin(['ACCEPTED', 'APPROVED AS NOTED'])])
                rate = (c_acc / c_total * 100) if c_total > 0 else 0
                comp_stats.append({'Company': comp, 'Total': c_total, 'Rate': rate})
            c_df = pd.DataFrame(comp_stats)
            if not c_df.empty:
                valid_c_df = c_df[c_df['Total'] >= 5] if len(c_df[c_df['Total'] >= 5]) > 0 else c_df
                best_comp = valid_c_df.loc[valid_c_df['Rate'].idxmax()]
                worst_comp = valid_c_df.loc[valid_c_df['Rate'].idxmin()]
                l_col1, l_col2 = st.columns(2)
                l_col1.markdown(f"""
                    <div class="leaderboard-card" style="border-left-color: #2ecc71;">
                        <h4 style="margin:0; color:#2ecc71; text-transform: uppercase; font-size: 14px;">🏆 Top Performer Contractor</h4>
                        <h2 style="margin:8px 0; color:white; font-size: 28px;">{best_comp['Company']}</h2>
                        <span style="color:#8da3b9;">Approval Rate: <b style="color:#2ecc71; font-size: 18px;">{best_comp['Rate']:.1f}%</b> (from {best_comp['Total']} submittals)</span>
                    </div>
                """, unsafe_allow_html=True)
                l_col2.markdown(f"""
                    <div class="leaderboard-card" style="border-left-color: #e74c3c;">
                        <h4 style="margin:0; color:#e74c3c; text-transform: uppercase; font-size: 14px;">⚠️ Needs Attention</h4>
                        <h2 style="margin:8px 0; color:white; font-size: 28px;">{worst_comp['Company']}</h2>
                        <span style="color:#8da3b9;">Approval Rate: <b style="color:#e74c3c; font-size: 18px;">{worst_comp['Rate']:.1f}%</b> (from {worst_comp['Total']} submittals)</span>
                    </div>
                """, unsafe_allow_html=True)

        if 'Company Name' in filtered_df.columns and 'Sampling Location' in filtered_df.columns:
            mat_df = filtered_df.copy()
            mat_df['Sampling_Lower'] = mat_df['Sampling Location'].astype(str).str.lower()
            def categorize_location(loc):
                if 'stock' in loc or 'مشون' in loc: return 'Stockpile'
                elif 'bottom' in loc or 'قاع' in loc: return 'Bottom of Excavation'
                elif 'fill' in loc or 'ردم' in loc: return 'Fill'
                else: return 'Other'
            mat_df['Loc_Category'] = mat_df['Sampling_Lower'].apply(categorize_location)
            
            st.markdown("#### 📑 Consolidated Contractors Summary (Ready for Print)")
            summary_pivot = pd.crosstab(mat_df['Company Name'], mat_df['Loc_Category'], margins=True, margins_name="Total")
            cols_order = ['Stockpile', 'Bottom of Excavation', 'Fill', 'Other', 'Total']
            existing_cols = [c for c in cols_order if c in summary_pivot.columns]
            summary_pivot = summary_pivot[existing_cols]
            st.dataframe(summary_pivot, use_container_width=True)
            st.divider()
            
            # ==========================================
            # 🔥 BI INDIVIDUAL CONTRACTOR DEEP DIVE 🔥
            # ==========================================
            st.markdown("#### 🏢 Individual Contractor Deep Dive")
            comp_list = sorted([c for c in mat_df['Company Name'].unique() if str(c) != 'nan'])
            if comp_list:
                selected_comp = st.selectbox("Select a Contractor to Analyze:", comp_list)
                comp_df = mat_df[mat_df['Company Name'] == selected_comp]
                
                stock_df = comp_df[comp_df['Loc_Category'] == 'Stockpile']
                
                # 1. Use NUMBER OF TESTS for accuracy
                if num_tests_col:
                    stock_count = int(pd.to_numeric(stock_df[num_tests_col], errors='coerce').fillna(0).sum())
                    bottom_count = int(pd.to_numeric(comp_df[comp_df['Loc_Category'] == 'Bottom of Excavation'][num_tests_col], errors='coerce').fillna(0).sum())
                    fill_count = int(pd.to_numeric(comp_df[comp_df['Loc_Category'] == 'Fill'][num_tests_col], errors='coerce').fillna(0).sum())
                else:
                    stock_count = len(stock_df)
                    bottom_count = len(comp_df[comp_df['Loc_Category'] == 'Bottom of Excavation'])
                    fill_count = len(comp_df[comp_df['Loc_Category'] == 'Fill'])
                
                # 2. Avg 200 for Stockpile ONLY
                avg_200 = pd.to_numeric(stock_df['#200'], errors='coerce').mean() if '#200' in stock_df.columns else np.nan
                
                # Clean UI Text (English Only)
                cc1, cc2, cc3, cc4 = st.columns(4)
                create_card(cc1, "Stockpile Tests", stock_count)
                create_card(cc2, "Bottom Excavation Tests", bottom_count)
                create_card(cc3, "Fill Tests", fill_count)
                create_card(cc4, "Avg Sieve #200 (Stockpile)", f"{avg_200:.2f}%" if pd.notna(avg_200) else "N/A")
                
                # 3. Target vs Required & Overqualified Check
                req_qty = np.nan
                # Read from the original main 'df' where the lookup column 'Company' matches the selected_comp
                if 'Company' in df.columns and 'Required Quantity' in df.columns:
                    match_row = df[df['Company'].astype(str).str.strip() == selected_comp.strip()]
                    if not match_row.empty:
                        req_qty = pd.to_numeric(match_row['Required Quantity'], errors='coerce').max()
                
                # Fallback if 'Company' lookup column is missing but Required Quantity exists in comp_df
                if pd.isna(req_qty) and 'Required Quantity' in comp_df.columns:
                    req_qty = pd.to_numeric(comp_df['Required Quantity'], errors='coerce').max()

                if pd.notna(req_qty) and req_qty > 0:
                    req_qty_int = int(req_qty)
                    diff = stock_count - req_qty_int
                    if diff >= 0:
                        status_msg = f"<span style='color: #2ecc71;'>Target Exceeded (+{diff} Tests)</span>"
                        progress_pct = 100
                        prog_color = "linear-gradient(90deg, #2ecc71, #27ae60)"
                    else:
                        status_msg = f"<span style='color: #ffaa00;'>Missing {abs(diff)} Tests</span>"
                        progress_pct = min(100, (stock_count / req_qty_int) * 100)
                        prog_color = "linear-gradient(90deg, #00d2ff, #2ecc71)"
                    
                    st.markdown(f"""
                    <div style="background: rgba(10, 20, 33, 0.8); padding: 20px; border-radius: 15px; border-left: 5px solid #00d2ff; margin-top: 15px; margin-bottom: 25px; box-shadow: 0 4px 15px rgba(0,0,0,0.3);">
                        <h4 style="color: #00d2ff; margin-top: 0; margin-bottom: 15px;">🎯 Stockpile Target Achievement</h4>
                        <div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
                            <span style="color: #d1d5da; font-size: 15px;">Target Required: <b style="color: white; font-size: 18px;">{req_qty_int}</b></span>
                            <span style="color: #00d2ff; font-size: 15px;">Executed Tests: <b style="color: white; font-size: 18px;">{stock_count}</b></span>
                            <span style="font-size: 15px; font-weight: bold;">Status: {status_msg}</span>
                        </div>
                        <div class="prog-bg" style="height: 10px; background: rgba(255,255,255,0.05);"><div class="prog-fill" style="width: {progress_pct}%; background: {prog_color};"></div></div>
                    </div>
                    """, unsafe_allow_html=True)
                
                # 4. AI Engineer Recommendation based on Fill/Stockpile timing
                if 'Date ( test)' in comp_df.columns:
                    time_analysis_df = comp_df.dropna(subset=['Date ( test)']).copy()
                    time_analysis_df['Month'] = time_analysis_df['Date ( test)'].dt.strftime('%b %Y')
                    fill_by_month = time_analysis_df[time_analysis_df['Loc_Category'] == 'Fill'].groupby('Month').size()
                    stock_by_month = time_analysis_df[time_analysis_df['Loc_Category'] == 'Stockpile'].groupby('Month').size()

                    if not fill_by_month.empty:
                        peak_fill_month = fill_by_month.idxmax()
                        peak_fill_val = fill_by_month.max()
                        stock_in_peak = stock_by_month.get(peak_fill_month, 0)
                        
                        st.markdown(f"""
                        <div style="background: rgba(46, 204, 113, 0.1); border-left: 4px solid #2ecc71; padding: 15px; border-radius: 10px; margin-bottom: 20px;">
                            <h4 style="color: #2ecc71; margin: 0 0 5px 0;">🤖 AI Engineer Recommendation</h4>
                            <p style="color: #d1d5da; margin: 0; font-size: 14px; line-height: 1.6;">
                            <b>Analysis:</b> High filling activity (DPL/Fill) detected in <b>{peak_fill_month}</b> ({peak_fill_val} submittals logged). Correlating Stockpile test volume during this period is {stock_in_peak}. <br>
                            <b>Action:</b> Consider proactively scheduling more Stockpile source approvals ahead of such high-volume fill operations to maintain material quality buffers and prevent bottlenecks.
                            </p>
                        </div>
                        """, unsafe_allow_html=True)

                ch_col1, ch_col2 = st.columns(2)
                with ch_col1:
                    if 'Classification' in stock_df.columns and not stock_df.empty:
                        class_counts = stock_df['Classification'].value_counts().reset_index()
                        class_counts.columns = ['Classification', 'Count']
                        fig_class = px.pie(class_counts, names='Classification', values='Count', title=f"Stockpile Classifications for {selected_comp}", hole=0.3, color_discrete_sequence=NEON_COLORS)
                        fig_class.update_traces(textinfo='label+value')
                        fig_class = style_3d_glassy(fig_class, chart_type="pie")
                        st.plotly_chart(fig_class, use_container_width=True)
                    else:
                        st.info(f"No Stockpile classification data logged for {selected_comp}.")
                        
                with ch_col2:
                    if 'sample status' in stock_df.columns and not stock_df.empty:
                        fig_stock_status = px.pie(stock_df, names='sample status', title=f"Stockpile Approval/Rejection Rate", hole=0.3, color='sample status', color_discrete_map={'ACCEPTED':'#2ecc71', 'REJECTED':'#ff007f', 'REVISE':'#f1c40f', 'APPROVED AS NOTED':'#00d2ff'})
                        fig_stock_status.update_traces(textinfo='label+value')
                        fig_stock_status = style_3d_glassy(fig_stock_status, chart_type="pie")
                        st.plotly_chart(fig_stock_status, use_container_width=True)
                    else:
                        st.info(f"No Stockpile status data logged for {selected_comp}.")

                ch_col3, ch_col4 = st.columns(2)
                with ch_col3:
                    if 'Date ( test)' in stock_df.columns and not stock_df.empty:
                        time_df = stock_df.dropna(subset=['Date ( test)']).copy()
                        time_df['Month'] = time_df['Date ( test)'].dt.strftime('%b %Y')
                        time_df['Month_Sort'] = time_df['Date ( test)'].dt.to_period('M')
                        monthly_stock = time_df.groupby(['Month_Sort', 'Month']).size().reset_index(name='Count').sort_values('Month_Sort')
                        fig_timeline = px.bar(monthly_stock, x='Month', y='Count', title="Stockpile Tests Timeline", text_auto=True, color_discrete_sequence=['#ffaa00'])
                        fig_timeline = style_3d_glassy(fig_timeline, chart_type="bar")
                        st.plotly_chart(fig_timeline, use_container_width=True)
                    else:
                        st.info("No Date data available to show Stockpile timeline.")

                with ch_col4:
                    if 'sample status' in comp_df.columns and not comp_df.empty:
                        fig_status = px.pie(comp_df, names='sample status', title=f"Overall Approval Rate (All Tests) for {selected_comp}", hole=0.3, color='sample status', color_discrete_map={'ACCEPTED':'#2ecc71', 'REJECTED':'#ff007f', 'REVISE':'#f1c40f', 'APPROVED AS NOTED':'#00d2ff'})
                        fig_status.update_traces(textinfo='label+percent')
                        fig_status = style_3d_glassy(fig_status, chart_type="pie")
                        st.plotly_chart(fig_status, use_container_width=True)
                    else:
                        st.info(f"No overall status data logged for {selected_comp}.")

        st.markdown('<div class="gradient-divider"></div>', unsafe_allow_html=True)

        st.markdown('<div class="bi-title">🔍 Advanced Element Quality Auditor</div>', unsafe_allow_html=True)
        bh_col_name = next((col for col in filtered_df.columns if str(col).strip().upper() in ['ELEMENT', 'ELMENT', 'BH', 'LOCATION']), None)
        zone_col_name = next((col for col in filtered_df.columns if 'ZONE' in str(col).strip().upper() or 'AREA' in str(col).strip().upper()), None)
        if bh_col_name:
            filtered_df[bh_col_name] = filtered_df[bh_col_name].fillna('').astype(str).str.strip()
            bh_list = [bh for bh in filtered_df[bh_col_name].unique() if str(bh).upper() != 'NAN' and str(bh) != '']
            if len(bh_list) > 0:
                selected_bh = st.selectbox(f"Select an Element ({bh_col_name}) to investigate:", ["-- Select Element --"] + sorted(bh_list))
                if selected_bh != "-- Select Element --":
                    bh_df_raw = filtered_df[filtered_df[bh_col_name] == selected_bh].copy()
                    bh_df = None
                    if zone_col_name and bh_df_raw[zone_col_name].nunique() > 1:
                        available_zones = sorted([str(z) for z in bh_df_raw[zone_col_name].unique() if pd.notna(z) and str(z).strip() != ''])
                        st.warning(f"⚠️ **Attention:** Element `{selected_bh}` is present in multiple zones. Please select the required Zone:")
                        selected_zone = st.radio("📍 Select Zone:", available_zones, horizontal=True)
                        if selected_zone:
                            bh_df = bh_df_raw[bh_df_raw[zone_col_name].astype(str) == selected_zone].copy()
                            st.markdown(f"#### 🎯 Investigation Report: `{selected_bh}` <span style='color:#00d2ff; font-size:18px;'>[Zone: {selected_zone}]</span>", unsafe_allow_html=True)
                    else:
                        bh_df = bh_df_raw
                        st.markdown(f"#### 🎯 Investigation Report: `{selected_bh}`")
                    
                    if bh_df is not None:
                        if 'layer' in bh_df.columns:
                            bh_df['Layer_Num'] = bh_df['layer'].astype(str).str.extract(r'(\d+)').fillna(999).astype(int)
                            bh_df = bh_df.sort_values(['Layer_Num', 'Date ( test)'])
                        
                        bh_total_submittals = len(bh_df) 
                        num_tests_col_bh = next((c for c in bh_df.columns if 'NUMBER OF TESTS' in str(c).strip().upper() or 'NUM OF TEST' in str(c).strip().upper()), None)
                        bh_total_tests = int(pd.to_numeric(bh_df[num_tests_col_bh], errors='coerce').fillna(0).sum()) if num_tests_col_bh else bh_total_submittals 
                        bh_accepted = len(bh_df[bh_df['sample status'].astype(str).str.upper().isin(['ACCEPTED', 'APPROVED AS NOTED'])]) if 'sample status' in bh_df.columns else 0
                        bh_pass_rate = (bh_accepted / bh_total_submittals * 100) if bh_total_submittals > 0 else 0
                        bh_avg_dpl = pd.to_numeric(bh_df['AVERAGE VALUE'], errors='coerce').mean() if 'AVERAGE VALUE' in bh_df.columns else 0
                        start_date = bh_df['Date ( test)'].min().strftime('%Y-%m-%d') if 'Date ( test)' in bh_df.columns and not pd.isna(bh_df['Date ( test)'].min()) else "N/A"
                        end_date = bh_df['Date ( test)'].max().strftime('%Y-%m-%d') if 'Date ( test)' in bh_df.columns and not pd.isna(bh_df['Date ( test)'].max()) else "N/A"
                        
                        c1, c2, c3, c4 = st.columns(4)
                        create_card(c1, "Total Submittals", bh_total_submittals)
                        create_card(c2, "Total Tests", bh_total_tests)
                        create_card(c3, "First Test Date", start_date)
                        create_card(c4, "Last Test Date", end_date)
                        c5, c6, c7, c8 = st.columns(4)
                        create_card(c5, "Passed/Approved", bh_accepted)
                        create_card(c6, "Approval Rate (%)", f"{bh_pass_rate:.1f}%")
                        create_card(c7, "Avg DPL Value", f"{bh_avg_dpl:.2f}" if not pd.isna(bh_avg_dpl) else "N/A")
                        create_card(c8, "Rejected Submittals", bh_total_submittals - bh_accepted)

                        if 'Company Name' in bh_df.columns:
                            if 'Date ( test)' in bh_df.columns:
                                comp_stats = bh_df.dropna(subset=['Company Name']).groupby('Company Name')['Date ( test)'].agg(['min', 'max']).reset_index()
                                comp_details = [f"<span style='color:#2ecc71;'><b>{r['Company Name']}</b></span>: <span style='font-size:16px; color:#8da3b9;'>{r['min'].strftime('%Y-%m-%d') if pd.notna(r['min']) else 'N/A'} <b style='color:#ffaa00;'>&rarr;</b> {r['max'].strftime('%Y-%m-%d') if pd.notna(r['max']) else 'N/A'}</span>" for _, r in comp_stats.iterrows()]
                                companies_str = "<br>".join(comp_details) if comp_details else "N/A"
                            else:
                                companies_worked = bh_df['Company Name'].dropna().unique()
                                companies_str = " ، ".join(companies_worked) if len(companies_worked) > 0 else "N/A"
                            st.markdown(f"""
                                <div class="metric-card" style="margin-top: 5px; text-align: left; padding-left: 30px;">
                                    <div class="metric-label" style="color:#ffaa00; text-align: left; margin-bottom: 15px;">Contractors Timeline on this Element</div>
                                    <div class="metric-value" style="font-size: 18px; line-height: 2.0; font-weight: 500;">{companies_str}</div>
                                </div>
                                """, unsafe_allow_html=True)

                        if 'layer' in bh_df.columns and 'sample status' in bh_df.columns:
                            rejected_mask = bh_df['sample status'].astype(str).str.upper().isin(['REJECTED', 'REVISE'])
                            approved_mask = bh_df['sample status'].astype(str).str.upper().isin(['ACCEPTED', 'APPROVED AS NOTED'])
                            approved_layers = set(bh_df[approved_mask]['layer'].dropna().astype(str).unique())
                            unresolved_alerts = list(set([(str(row.get('layer', 'Unknown')), row.get('Test Type', 'N/A'), row.get('serial', 'N/A')) for _, row in bh_df[rejected_mask].iterrows() if str(row.get('layer', 'Unknown')) not in approved_layers]))
                            if unresolved_alerts:
                                st.markdown("#### 🚨 Critical Quality Alerts (Unresolved Submittals)")
                                alert_cols = st.columns(min(len(unresolved_alerts), 4) if len(unresolved_alerts) > 0 else 1)
                                for idx, alert in enumerate(unresolved_alerts[:8]): 
                                    l, t_type, ser = alert
                                    alert_cols[idx % 4].markdown(f"""
                                        <div style="background: rgba(231, 76, 60, 0.15); backdrop-filter: blur(5px); padding: 15px; border-radius: 15px; border: 1px solid #e74c3c; margin-bottom: 10px; box-shadow: 0 4px 15px rgba(231, 76, 60, 0.2);">
                                            <div style="color: #e74c3c; font-size: 16px; font-weight: bold; margin-bottom: 5px;">⚠️ Action Required</div>
                                            <div style="color: #ffffff; font-size: 14px; line-height: 1.6;">
                                                <b>Layer:</b> {l}<br><b>Test:</b> {t_type}<br><b>Serial No:</b> {ser}<br>
                                                <span style="font-size:12px; color:#ffcccc;">Status is REVISE/REJECTED with no subsequent approval found!</span>
                                            </div>
                                        </div>
                                        """, unsafe_allow_html=True)
                        st.divider()

                        if 'layer' in bh_df.columns and 'Date ( test)' in bh_df.columns:
                            st.markdown("#### 🧠 AI Engineering Sequence Inspector (Compaction Only)")
                            seq_df = bh_df.dropna(subset=['Date ( test)']).copy()
                            if 'Test Type' in seq_df.columns:
                                seq_df = seq_df[seq_df['Test Type'].astype(str).str.contains('SANDCONE|SAND CONE|DPL', case=False, na=False)]
                            seq_df['Layer_Int'] = seq_df['layer'].astype(str).str.extract(r'(\d+)').fillna(-1).astype(int)
                            seq_df = seq_df[seq_df['Layer_Int'] > 0]
                            if not seq_df.empty:
                                layer_timeline = seq_df.groupby('Layer_Int')['Date ( test)'].min().reset_index()
                                layer_timeline = layer_timeline.sort_values('Layer_Int')
                                logic_errors = []
                                missing_layers = []
                                min_layer = layer_timeline['Layer_Int'].min()
                                max_layer = layer_timeline['Layer_Int'].max()
                                expected_layers = set(range(min_layer, max_layer + 1))
                                actual_layers = set(layer_timeline['Layer_Int'])
                                missing_layers = sorted(list(expected_layers - actual_layers))
                                for i in range(len(layer_timeline) - 1):
                                    curr_L = layer_timeline.iloc[i]['Layer_Int']
                                    next_L = layer_timeline.iloc[i+1]['Layer_Int']
                                    curr_D = layer_timeline.iloc[i]['Date ( test)']
                                    next_D = layer_timeline.iloc[i+1]['Date ( test)']
                                    if curr_D > next_D:
                                        logic_errors.append(f"<b>Layer {curr_L}</b> was tested on <span style='color:#ffaa00;'>{curr_D.date()}</span>, which is AFTER <b>Layer {next_L}</b> tested on <span style='color:#ffaa00;'>{next_D.date()}</span>.")
                                if not missing_layers and not logic_errors:
                                    st.markdown("""
                                    <div style="background: rgba(46, 204, 113, 0.1); border-left: 4px solid #2ecc71; padding: 15px; border-radius: 10px; margin-bottom: 20px;">
                                        <h5 style="color: #2ecc71; margin: 0;">✅ Sequence Verified</h5>
                                        <p style="color: #d1d5da; margin: 5px 0 0 0; font-size: 14px;">All compaction layers are chronologically correct with no missing intermediate layers.</p>
                                    </div>
                                    """, unsafe_allow_html=True)
                                else:
                                    if missing_layers:
                                        missing_str = ", ".join([f"Layer {l}" for l in missing_layers])
                                        st.markdown(f"""
                                        <div style="background: rgba(241, 196, 15, 0.1); border-left: 4px solid #f1c40f; padding: 15px; border-radius: 10px; margin-bottom: 10px;">
                                            <h5 style="color: #f1c40f; margin: 0;">⚠️ Missing Compaction Layers Detected</h5>
                                            <p style="color: #d1d5da; margin: 5px 0 0 0; font-size: 14px;">Gap found in execution sequence. Missing: <b style="color:white;">{missing_str}</b></p>
                                        </div>
                                        """, unsafe_allow_html=True)
                                    if logic_errors:
                                        errors_html = "<br>".join([f"🚨 {err}" for err in logic_errors])
                                        st.markdown(f"""
                                        <div style="background: rgba(231, 76, 60, 0.1); border-left: 4px solid #e74c3c; padding: 15px; border-radius: 10px; margin-bottom: 20px;">
                                            <h5 style="color: #e74c3c; margin: 0;">🛑 Critical Chronological Illogic</h5>
                                            <p style="color: #d1d5da; margin: 5px 0 0 0; font-size: 14px; line-height:1.8;">{errors_html}</p>
                                        </div>
                                        """, unsafe_allow_html=True)
                            else:
                                st.info("No compaction tests (SANDCONE or DPL) found to evaluate sequence.")
                        st.divider()

                        if 'Sampling Location' in bh_df.columns:
                            st.markdown("#### ⛏️ Bottom of Excavation & Soil Quality")
                            boe_df = bh_df[bh_df['Sampling Location'].astype(str).str.contains('Bottom|Soil', case=False, na=False)]
                            if not boe_df.empty:
                                boe_count = len(boe_df)
                                st.info(f"📌 Found **{boe_count}** submittals related to Bottom of Excavation / Soil in this Element.")
                                if 'Classification' in boe_df.columns:
                                    class_counts = boe_df['Classification'].value_counts().reset_index()
                                    class_counts.columns = ['Classification', 'Count']
                                    fig_sc = px.bar(class_counts, x='Classification', y='Count', title="Soil Classifications", color='Classification', text_auto=True, color_discrete_sequence=NEON_COLORS)
                                    fig_sc = style_3d_glassy(fig_sc, chart_type="bar")
                                    st.plotly_chart(fig_sc, use_container_width=True)
                            else:
                                st.success("No 'Bottom of Excavation' specific issues or tests logged for this Element.")
                        st.divider()

                        if 'Test Type' in bh_df.columns and 'Done BY' in bh_df.columns:
                            layer_col = bh_df['layer'] if 'layer' in bh_df.columns else pd.Series([''] * len(bh_df), index=bh_df.index)
                            samp_loc = bh_df['Sampling Location'] if 'Sampling Location' in bh_df.columns else pd.Series(['General Location'] * len(bh_df), index=bh_df.index)
                            bh_df['Execution_Node'] = np.where(layer_col.astype(str).str.contains(r'\d'), layer_col, samp_loc)
                            bh_df['Execution_Node'] = bh_df['Execution_Node'].replace(r'^\s*$', 'General Location', regex=True).fillna('General Location')
                            fig_matrix = px.treemap(bh_df, path=['Done BY', 'Test Type', 'Execution_Node'], title=f"Who did What & Where in {selected_bh}", color='Done BY', color_discrete_sequence=NEON_COLORS)
                            fig_matrix.update_traces(textinfo="label+value")
                            fig_matrix = style_3d_glassy(fig_matrix, chart_type="treemap")
                            st.plotly_chart(fig_matrix, use_container_width=True)
                        st.divider()

                        b_col1, b_col2 = st.columns(2)
                        with b_col1:
                            if 'sample status' in bh_df.columns:
                                fig_ep = px.pie(bh_df, names='sample status', title=f"Status Breakdown for {selected_bh}", hole=0.4, color_discrete_map={'ACCEPTED':'#2ecc71', 'REJECTED':'#ff007f', 'REVISE':'#f1c40f', 'APPROVED AS NOTED':'#00d2ff'})
                                fig_ep = style_3d_glassy(fig_ep, chart_type="pie")
                                st.plotly_chart(fig_ep, use_container_width=True)
                        with b_col2:
                            if 'layer' in bh_df.columns:
                                layer_reqs = bh_df.groupby('layer').size().reset_index(name='Submittals')
                                layer_reqs['Layer_Num'] = layer_reqs['layer'].astype(str).str.extract(r'(\d+)').fillna(999).astype(int)
                                layer_reqs = layer_reqs.sort_values('Layer_Num')
                                fig_eb = px.bar(layer_reqs, x='layer', y='Submittals', title="Number of Submittals per Layer (Sorted)", text_auto=True, color_discrete_sequence=['#ffaa00'])
                                fig_eb = style_3d_glassy(fig_eb, chart_type="bar")
                                st.plotly_chart(fig_eb, use_container_width=True)

                        if 'Date ( test)' in bh_df.columns and 'AVERAGE VALUE' in bh_df.columns and 'layer' in bh_df.columns:
                            trend_df = bh_df.dropna(subset=['Date ( test)', 'AVERAGE VALUE'])
                            if not trend_df.empty:
                                fig_el = px.line(trend_df, x='Date ( test)', y='AVERAGE VALUE', color='layer', markers=True, title=f"DPL Values Trend across Layers over time for {selected_bh}", color_discrete_sequence=NEON_COLORS)
                                fig_el = style_3d_glassy(fig_el, chart_type="line")
                                st.plotly_chart(fig_el, use_container_width=True)
                        
                        with st.expander(f"📂 View Raw Detailed Audit Log for `{selected_bh}`"):
                            st.dataframe(bh_df.drop(columns=['Layer_Num', 'Execution_Node'], errors='ignore'), use_container_width=True)
        else:
            st.warning("⚠️ **Column Not Found:** Could not locate an 'Element' column in your uploaded file to enable Deep Dive Analysis.")

        st.markdown('<div class="gradient-divider"></div>', unsafe_allow_html=True)
        with st.expander("📂 View Complete Operational Records (Raw Data)"):
            st.dataframe(filtered_df, use_container_width=True)

    else:
        st.info("👈 Please connect a Data Source or Upload a CSV to activate the Enterprise Engine.")

# ==========================================
# 8. Main Application Execution
# ==========================================
def main():
    init_auth_system()
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False

    if not st.session_state["authenticated"]:
        render_login_screen()
    else:
        render_dashboard()

if __name__ == "__main__":
    main()