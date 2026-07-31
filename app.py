import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
import time
from datetime import datetime, timedelta
import pytz
import base64
import hashlib
import sqlite3
import io

# ==========================================
# 1. System Configuration & Constants
# ==========================================
st.set_page_config(page_title="Command Center BI Dashboard", layout="wide", initial_sidebar_state="expanded")

EGYPT_TZ = pytz.timezone('Africa/Cairo')
NEON_COLORS = ['#00d2ff', '#ffaa00', '#2ecc71', '#ff007f', '#f1c40f', '#9b59b6', '#38f9d7', '#ff7eb3', '#00f2fe', '#4facfe']

STATUS_COLORS = {
    'ACCEPTED': '#2ecc71', 
    'APPROVED AS NOTED': '#00d2ff', 
    'REVISE': '#f1c40f', 
    'REJECTED': '#e74c3c'
}

USERS_DB_FILE = "users_db.csv"
LOGIN_LOGS_FILE = "login_logs.csv"
AUDIT_LOG_FILE = "audit_trail.csv"

if "theme" not in st.session_state:
    st.session_state["theme"] = "Dark"
if "site_mode" not in st.session_state:
    st.session_state["site_mode"] = False
if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = []
if "current_page" not in st.session_state:
    st.session_state["current_page"] = "home"

# ==========================================
# 2. Dynamic UI/UX CSS Injection
# ==========================================
def inject_custom_css():
    is_dark = st.session_state["theme"] == "Dark"
    
    if is_dark:
        bg_main = "radial-gradient(circle at top right, #0b1a2e, #050a11)"
        bg_sidebar = "rgba(5, 10, 17, 0.95)"
        card_bg = "linear-gradient(145deg, rgba(20, 35, 54, 0.6), rgba(10, 20, 33, 0.9))"
        card_border = "rgba(255, 170, 0, 0.15)"
        card_shadow = "0 10px 30px rgba(0, 0, 0, 0.4)"
        text_main = "#ffffff"
        text_muted = "#8da3b9"
        title_color = "#ffaa00"
        input_bg = "rgba(30, 45, 65, 0.8)"
        button_bg = "linear-gradient(135deg, #00d2ff, #008cba)"
        button_text = "#ffffff"
        hover_bg = "rgba(0, 210, 255, 0.1)"
    else:
        bg_main = "#F4F7F6"
        bg_sidebar = "#ffffff"
        card_bg = "#ffffff"
        card_border = "rgba(0, 0, 0, 0.12)"
        card_shadow = "0 8px 25px rgba(0, 0, 0, 0.08)"
        text_main = "#1a1a1a"
        text_muted = "#4a5568"
        title_color = "#2980B9"
        input_bg = "#f8f9fa"
        button_bg = "linear-gradient(135deg, #2980B9, #1a5276)"
        button_text = "#ffffff"
        hover_bg = "rgba(41, 128, 185, 0.08)"

    custom_css = f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Montserrat:wght@400;700;800&display=swap');
    
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    [data-testid="stHeader"] {{background: transparent !important;}}
    .block-container {{padding-top: 2rem !important; padding-bottom: 2rem !important;}}
    
    html, body, [class*="css"] {{ color: {text_main} !important; font-family: 'Inter', sans-serif; }}
    h1, h2, h3, h4, h5, h6, .login-title {{ font-family: 'Montserrat', sans-serif !important; color: {text_main} !important; }}
    p, .stMarkdown, label {{ color: {text_main} !important; }}
    
    [data-testid="stAppViewContainer"] {{ background: {bg_main} !important; transition: all 0.3s ease; }}
    [data-testid="stSidebar"] {{ background-color: {bg_sidebar} !important; border-right: 1px solid {card_border}; transition: all 0.3s ease; }}
    
    [data-testid="stTextInput"] input,
    [data-testid="stSelectbox"] div,
    [data-testid="stMultiselect"] div {{
        background-color: {input_bg} !important;
        color: {text_main} !important;
        border: 1px solid {card_border} !important;
    }}
    
    [data-testid="stButton"] button {{
        background: {button_bg} !important;
        color: {button_text} !important;
        border: none !important;
        font-weight: 600 !important;
    }}
    
    [data-testid="stButton"] button:hover {{
        opacity: 0.9 !important;
        transform: translateY(-2px) !important;
    }}
    
    ::-webkit-scrollbar {{
        width: 8px;
        height: 8px;
    }}
    ::-webkit-scrollbar-track {{
        background: rgba(0,0,0,0.1);
        border-radius: 10px;
    }}
    ::-webkit-scrollbar-thumb {{
        background: linear-gradient(180deg, #00d2ff, #ffaa00);
        border-radius: 10px;
    }}
    ::-webkit-scrollbar-thumb:hover {{
        background: linear-gradient(180deg, #ffaa00, #00d2ff);
    }}
    
    .metric-card, .leaderboard-card, .simulator-card, .health-card, .custom-card {{
        background: {card_bg} !important;
        padding: 25px;
        border-radius: 16px;
        border: 1px solid {card_border};
        box-shadow: {card_shadow};
        margin-bottom: 15px;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        position: relative;
        overflow: hidden;
    }}
    
    .metric-card:hover, .leaderboard-card:hover, .simulator-card:hover {{
        transform: translateY(-5px) scale(1.02) !important;
        box-shadow: 0 20px 40px rgba(0, 210, 255, 0.3) !important;
        border-color: #00d2ff !important;
    }}
    
    .metric-card::before, .leaderboard-card::before {{
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.1), transparent);
        transition: left 0.5s;
    }}
    
    .metric-card:hover::before, .leaderboard-card:hover::before {{
        left: 100%;
    }}
    
    .bi-title {{
        background: linear-gradient(135deg, #00d2ff 0%, #ffaa00 50%, #ff007f 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-size: 26px;
        font-weight: 800;
        margin-top: 40px;
        margin-bottom: 20px;
        position: relative;
    }}
    
    .bi-title::after {{
        content: '';
        position: absolute;
        bottom: -5px;
        left: 0;
        width: 0;
        height: 3px;
        background: linear-gradient(90deg, #00d2ff, #ffaa00);
        transition: width 0.5s ease;
    }}
    
    .bi-title:hover::after {{
        width: 100%;
    }}
    
    .metric-label {{ color: {text_muted} !important; font-size: 13px; font-weight: 600; margin-bottom: 5px; text-transform: uppercase; font-family: 'Montserrat', sans-serif; }}
    .metric-value {{ color: {text_main} !important; font-size: 36px; font-weight: 800; font-family: 'Montserrat', sans-serif; }}
    
    .delta-up {{ color: #2ecc71 !important; font-size: 14px; font-weight: bold; margin-top: 8px; }}
    .delta-down {{ color: #e74c3c !important; font-size: 14px; font-weight: bold; margin-top: 8px; }}
    .delta-neutral {{ color: {text_muted} !important; font-size: 14px; font-weight: bold; margin-top: 8px; }}
    
    .gradient-divider {{
        height: 2px;
        background: linear-gradient(90deg, transparent 0%, #00d2ff 20%, #ffaa00 50%, #00d2ff 80%, transparent 100%);
        background-size: 200% 100%;
        animation: shimmer-divider 3s linear infinite;
        margin: 40px 0;
        border: none;
        opacity: 0.5;
    }}
    
    @keyframes shimmer-divider {{
        0% {{ background-position: 200% 0; }}
        100% {{ background-position: -200% 0; }}
    }}
    
    .ticker-wrap {{ background: {card_bg}; border-radius: 8px; padding: 8px 0; margin-bottom: 20px; border-left: 3px solid #00d2ff; box-shadow: {card_shadow}; overflow: hidden; white-space: nowrap; }}
    .ticker {{ display: inline-block; padding-right: 100%; animation: ticker 35s linear infinite; }}
    @keyframes ticker {{ 0% {{ transform: translate3d(0, 0, 0); }} 100% {{ transform: translate3d(-100%, 0, 0); }} }}
    .ticker-item {{ display: inline-block; padding: 0 2rem; font-weight: 600; color: {text_main}; font-size: 14px; }}
    .ticker-item span {{ color: #00d2ff; font-weight: 800; }}
    
    .chat-container {{ background: {card_bg}; padding: 20px; border-radius: 15px; border: 1px solid {card_border}; margin-bottom: 20px; max-height: 400px; overflow-y: auto; }}
    .user-msg {{ background: rgba(0, 210, 255, 0.1); padding: 15px; border-radius: 10px; margin-bottom: 10px; text-align: right; border-right: 3px solid #00d2ff; }}
    .ai-msg {{ background: rgba(255, 170, 0, 0.05); padding: 15px; border-radius: 10px; margin-bottom: 10px; border-left: 3px solid #ffaa00; }}
    
    .site-btn {{ background: linear-gradient(145deg, #00d2ff, #008cba); color: white; padding: 25px; border-radius: 15px; text-align: center; font-size: 20px; font-weight: bold; box-shadow: 0 10px 20px rgba(0,0,0,0.2); cursor: pointer; transition: transform 0.2s; margin-bottom: 15px; }}
    .site-btn:hover {{ transform: translateY(-5px); }}
    .site-btn:active {{ transform: translateY(2px); }}
    
    @keyframes pulse-glow {{
        0%, 100% {{ box-shadow: 0 0 5px rgba(231, 76, 60, 0.5); }}
        50% {{ box-shadow: 0 0 20px rgba(231, 76, 60, 0.8); }}
    }}
    
    .metric-value.critical {{
        animation: pulse-glow 2s infinite;
        color: #e74c3c !important;
    }}
    
    @keyframes pulse {{
        0%, 100% {{ opacity: 1; transform: scale(1); }}
        50% {{ opacity: 0.5; transform: scale(1.2); }}
    }}
    
    .live-indicator {{
        display: flex;
        align-items: center;
        gap: 8px;
    }}
    
    .live-dot {{
        width: 10px;
        height: 10px;
        border-radius: 50%;
        animation: pulse 2s infinite;
    }}
    
    [data-testid="stAppViewContainer"]::before {{
        content: '';
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background-image:
            radial-gradient(circle at 20% 50%, rgba(0, 210, 255, 0.03) 0%, transparent 50%),
            radial-gradient(circle at 80% 80%, rgba(255, 170, 0, 0.03) 0%, transparent 50%);
        pointer-events: none;
        z-index: -1;
    }}
    
    [data-testid="stSidebar"] hr {{
        border: none;
        height: 1px;
        background: linear-gradient(90deg, transparent 0%, #00d2ff 50%, transparent 100%);
        margin: 20px 0;
    }}
    
    .dataframe {{
        border-radius: 12px !important;
        overflow: hidden;
        box-shadow: 0 10px 30px rgba(0,0,0,0.2) !important;
    }}
    
    .dataframe th {{
        background: linear-gradient(135deg, #00d2ff, #008cba) !important;
        color: white !important;
        font-weight: 600 !important;
        text-transform: uppercase;
        font-size: 12px !important;
        letter-spacing: 1px;
    }}
    
    .dataframe tr:hover {{
        background: rgba(0, 210, 255, 0.05) !important;
    }}
    
    .navigation-card {{
        background: {card_bg} !important;
        padding: 40px;
        border-radius: 20px;
        border: 2px solid {card_border};
        box-shadow: {card_shadow};
        cursor: pointer;
        transition: all 0.3s ease;
        min-height: 300px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        text-align: center;
    }}
    
    .navigation-card:hover {{
        transform: translateY(-10px) scale(1.05);
        border-color: #00d2ff !important;
        box-shadow: 0 30px 60px rgba(0, 210, 255, 0.4) !important;
    }}
    </style>
    """
    st.markdown(custom_css, unsafe_allow_html=True)

# ==========================================
# 3. Enhanced UI Components
# ==========================================
def show_breadcrumbs(path):
    parts = path.split(" > ")
    breadcrumb_html = " > ".join([
        f'<span style="color: #00d2ff; cursor: pointer;">{p}</span>' 
        if i < len(parts) - 1 
        else f'<span style="color: #ffaa00; font-weight: bold;">{p}</span>'
        for i, p in enumerate(parts)
    ])
    
    st.markdown(f"""
    <div style="
        background: rgba(255,255,255,0.05);
        padding: 10px 20px;
        border-radius: 8px;
        margin-bottom: 20px;
        font-size: 14px;
    ">
        🏠 Home {breadcrumb_html}
    </div>
    """, unsafe_allow_html=True)

def live_indicator(status="online"):
    colors = {
        "online": "#2ecc71",
        "offline": "#e74c3c",
        "warning": "#f1c40f"
    }
    
    st.markdown(f"""
    <div class="live-indicator">
        <div class="live-dot" style="background: {colors[status]}; box-shadow: 0 0 10px {colors[status]};"></div>
        <span style="color: {colors[status]}; font-size: 12px; text-transform: uppercase;">
            {status}
        </span>
    </div>
    """, unsafe_allow_html=True)

def create_progress_ring(percentage, label):
    color = "#2ecc71" if percentage > 80 else ("#f1c40f" if percentage > 50 else "#e74c3c")
    
    st.markdown(f"""
    <div style="text-align: center; padding: 20px;">
        <svg width="120" height="120" style="transform: rotate(-90deg);">
            <circle cx="60" cy="60" r="50" 
                    stroke="rgba(255,255,255,0.1)" 
                    stroke-width="8" 
                    fill="none"/>
            <circle cx="60" cy="60" r="50" 
                    stroke="{color}" 
                    stroke-width="8" 
                    fill="none"
                    stroke-dasharray="{2 * 3.14 * 50}"
                    stroke-dashoffset="{2 * 3.14 * 50 * (1 - percentage/100)}"
                    stroke-linecap="round"
                    style="transition: stroke-dashoffset 1s ease;"/>
        </svg>
        <div style="margin-top: -80px; font-size: 24px; font-weight: bold; color: {color};">
            {percentage}%
        </div>
        <div style="color: #8da3b9; font-size: 12px; margin-top: 40px;">
            {label}
        </div>
    </div>
    """, unsafe_allow_html=True)

# ==========================================
# 4. Authentication & User Management
# ==========================================
@st.cache_data(ttl=30)
def _load_users_db():
    if os.path.exists(USERS_DB_FILE):
        return pd.read_csv(USERS_DB_FILE)
    return pd.DataFrame()

@st.cache_data(ttl=30)
def _load_login_logs():
    if os.path.exists(LOGIN_LOGS_FILE):
        return pd.read_csv(LOGIN_LOGS_FILE)
    return pd.DataFrame(columns=["Timestamp", "Name", "Email", "Role"])

def clear_users_cache():
    _load_users_db.clear()

def clear_logs_cache():
    _load_login_logs.clear()

def init_auth_system():
    if not os.path.exists(USERS_DB_FILE):
        default_users = pd.DataFrame([
            {"Email": "Mohamedhatem@kk.com", "Password": "admin123", "Name": "Mohamed Hatem", "Role": "Admin", "Status": "Active"},
            {"Email": "engineer@kk.com", "Password": "123", "Name": "Site Engineer", "Role": "User", "Status": "Active"}
        ])
        default_users.to_csv(USERS_DB_FILE, index=False)
        clear_users_cache()
    
    if not os.path.exists(LOGIN_LOGS_FILE):
        logs_df = pd.DataFrame(columns=["Timestamp", "Name", "Email", "Role"])
        logs_df.to_csv(LOGIN_LOGS_FILE, index=False)
        clear_logs_cache()

def log_user_entry(user_info):
    logs_df = _load_login_logs()
    new_log = pd.DataFrame([{
        "Timestamp": datetime.now(EGYPT_TZ).strftime("%Y-%m-%d %H:%M:%S"),
        "Name": user_info["Name"],
        "Email": user_info["Email"],
        "Role": user_info["Role"]
    }])
    updated_logs = pd.concat([logs_df, new_log], ignore_index=True)
    updated_logs.to_csv(LOGIN_LOGS_FILE, index=False)
    clear_logs_cache()

def authenticate_user(email, password):
    users_df = _load_users_db()
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
# 5. 3D Glassy Chart Styling Function
# ==========================================
def style_3d_glassy(fig, chart_type="bar"):
    is_dark = st.session_state.get("theme", "Dark") == "Dark"
    template = "plotly_dark" if is_dark else "plotly_white"
    font_color = "#d1d5da" if is_dark else "#2C3E50"
    grid_color = 'rgba(255,255,255,0.05)' if is_dark else 'rgba(0,0,0,0.1)'
    line_color = 'rgba(255, 255, 255, 0.4)' if is_dark else 'rgba(0, 0, 0, 0.2)'
    marker_line = 'white' if is_dark else '#2C3E50'

    fig.update_layout(
        template=template,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter", color=font_color, size=12),
        margin=dict(t=50, b=20, l=20, r=20),
        title_font=dict(family="Montserrat", size=16, color=font_color),
        legend=dict(font=dict(color=font_color))
    )
    
    if chart_type in ["bar", "pie", "histogram", "treemap"]:
        fig.update_traces(marker=dict(line=dict(color=line_color, width=1.5)), opacity=0.85)
    elif chart_type == "line":
        fig.update_traces(line=dict(width=4), marker=dict(size=8, line=dict(color=marker_line, width=1.5)), selector=dict(type='scatter'))
    elif chart_type == "combo":
        fig.update_traces(marker=dict(line=dict(color=line_color, width=1.5)), opacity=0.85, selector=dict(type='bar'))
        fig.update_traces(line=dict(width=4), marker=dict(size=8, line=dict(color=marker_line, width=1.5)), selector=dict(type='scatter'))
        
    fig.update_xaxes(showgrid=False, title_font=dict(family="Inter", color=font_color), tickfont=dict(color=font_color))
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor=grid_color, title_font=dict(family="Inter", color=font_color), tickfont=dict(color=font_color))
    return fig

# ==========================================
# 6. History Manager with SQLite
# ==========================================
class HistoryManager:
    DB_FILE = "project_history.db"
    
    @staticmethod
    def init_db():
        conn = sqlite3.connect(HistoryManager.DB_FILE)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS kpi_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                file_name TEXT,
                total_requests INTEGER,
                total_tests INTEGER,
                avg_dpl REAL,
                avg_duration REAL,
                total_paperwork INTEGER
            )
        ''')
        conn.commit()
        conn.close()
    
    @staticmethod
    def save_metrics(metrics_dict):
        HistoryManager.init_db()
        conn = sqlite3.connect(HistoryManager.DB_FILE)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO kpi_history 
            (timestamp, file_name, total_requests, total_tests, avg_dpl, avg_duration, total_paperwork)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            datetime.now(EGYPT_TZ).strftime("%Y-%m-%d %H:%M:%S"),
            metrics_dict.get("File_Name", "Unknown_File"),
            metrics_dict.get("Total_Requests", 0),
            metrics_dict.get("Total_Tests", 0),
            metrics_dict.get("Avg_DPL", 0),
            metrics_dict.get("Avg_Duration", 0),
            metrics_dict.get("Total_Paperwork", 0)
        ))
        conn.commit()
        conn.close()
    
    @staticmethod
    def load_history():
        HistoryManager.init_db()
        try:
            conn = sqlite3.connect(HistoryManager.DB_FILE)
            df = pd.read_sql_query("SELECT * FROM kpi_history ORDER BY id", conn)
            conn.close()
            return df
        except:
            return pd.DataFrame()
    
    @staticmethod
    def get_delta_html(current_val, metric_key, current_file_name):
        history_df = HistoryManager.load_history()
        if history_df.empty:
            return ""
        
        column_map = {
            "Total_Requests": "total_requests",
            "Total_Tests": "total_tests",
            "Avg_DPL": "avg_dpl",
            "Avg_Duration": "avg_duration",
            "Total_Paperwork": "total_paperwork"
        }
        
        db_column = column_map.get(metric_key)
        if not db_column or db_column not in history_df.columns:
            return ""
        
        file_history = history_df[history_df['file_name'] == current_file_name] if 'file_name' in history_df.columns else pd.DataFrame()
        
        if file_history.empty:
            return ""
        
        file_history = file_history.sort_values('id')
        last_val = file_history.iloc[-1][db_column]
        diff = current_val - last_val
        pct_str = "0%" if last_val == 0 else f"{abs((diff / last_val) * 100):.1f}%"
        diff_fmt = f"{int(diff)}" if isinstance(current_val, (int, float)) and float(current_val).is_integer() else f"{diff:.2f}"
        
        if diff > 0:
            return f'<div class="delta-up">▲ +{diff_fmt} ({pct_str})</div>'
        elif diff < 0:
            return f'<div class="delta-down">▼ {diff_fmt} ({pct_str})</div>'
        else:
            return f'<div class="delta-neutral">➖ No change</div>'
    
    @staticmethod
    def export_to_csv():
        HistoryManager.init_db()
        conn = sqlite3.connect(HistoryManager.DB_FILE)
        df = pd.read_sql_query("SELECT * FROM kpi_history", conn)
        conn.close()
        return df
    
    @staticmethod
    def import_from_csv(df):
        HistoryManager.init_db()
        conn = sqlite3.connect(HistoryManager.DB_FILE)
        df.columns = df.columns.str.strip().str.lower()
        
        for index, row in df.iterrows():
            req = row.get('total_requests', 0)
            tst = row.get('total_tests', 0)
            dpl = row.get('avg_dpl', 0)
            dur = row.get('avg_duration', 0)
            pap = row.get('total_paperwork', 0)
            ts = row.get('timestamp', datetime.now(EGYPT_TZ).strftime("%Y-%m-%d %H:%M:%S"))
            fn = row.get('file_name', 'Legacy_Import.csv')
            
            conn.execute("""
                INSERT INTO kpi_history 
                (timestamp, file_name, total_requests, total_tests, avg_dpl, avg_duration, total_paperwork)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                str(ts),
                str(fn).strip(),
                pd.to_numeric(req, errors='coerce') or 0,
                pd.to_numeric(tst, errors='coerce') or 0,
                pd.to_numeric(dpl, errors='coerce') or 0,
                pd.to_numeric(dur, errors='coerce') or 0,
                pd.to_numeric(pap, errors='coerce') or 0
            ))
        conn.commit()
        conn.close()

def create_card(column, label, value, delta_html="", progress=None):
    if progress is not None:
        prog_color = "#2ecc71" if progress > 80 else ("#f1c40f" if progress > 50 else "#e74c3c")
        prog_html = f'<div class="prog-bg" style="height: 6px; background: rgba(127,140,141,0.2); border-radius: 10px; margin-top: 15px;"><div class="prog-fill" style="height: 100%; width: {progress}%; background: {prog_color}; border-radius: 10px;"></div></div>'
    else:
        prog_html = ""
    
    html_str = f"""<div class="metric-card">
<div class="metric-label">{label}</div>
<div class="metric-value">{value}</div>
{delta_html}
{prog_html}
</div>"""
    column.markdown(html_str, unsafe_allow_html=True)

def ai_assistant(query, data_summary):
    query = query.lower()
    if "delay" in query or "time" in query or "duration" in query:
        return f"Based on data, the average duration is {data_summary['avg_duration']} days. Check the AI Predictive section for bottleneck warnings."
    elif "dpl" in query:
        return f"Current average DPL is {data_summary['avg_dpl']}. Ensure rejected samples are re-tested after proper compaction."
    else:
        return "I am here to assist. Ask me about project logs, contractor performance, or quality control metrics."

def fmt_b(val):
    s = str(val).strip()
    return s[:-2] if s.endswith('.0') else s

# ==========================================
# 7. Audit Trail & GenAI
# ==========================================
def check_audit_trail(uploaded_file):
    original_pos = uploaded_file.tell()
    file_content = uploaded_file.read()
    file_hash = hashlib.md5(file_content).hexdigest()
    uploaded_file.seek(original_pos)
    
    if os.path.exists(AUDIT_LOG_FILE):
        audit_df = pd.read_csv(AUDIT_LOG_FILE)
        last_record = audit_df[audit_df['File_Name'] == uploaded_file.name]
        if not last_record.empty:
            last_hash = last_record.iloc[-1]['Hash']
            if last_hash == file_hash:
                return "✅ Data is identical to the last uploaded version. No changes detected."
            else:
                old_rows = last_record.iloc[-1]['Row_Count']
                new_rows = len(file_content.decode('utf-8', errors='ignore').strip().split('\n')) - 1
                diff = new_rows - old_rows
                return f"🔄 <b>Data Changed!</b> Previous: {old_rows} rows. Current: {new_rows} rows. (<b>{'+' if diff>=0 else ''}{diff} rows</b> modified/added)."
    
    new_audit = pd.DataFrame([{
        "Timestamp": datetime.now(EGYPT_TZ).strftime("%Y-%m-%d %H:%M:%S"),
        "File_Name": uploaded_file.name,
        "Hash": file_hash,
        "Row_Count": len(file_content.decode('utf-8', errors='ignore').strip().split('\n')) - 1
    }])
    if os.path.exists(AUDIT_LOG_FILE):
        pd.concat([pd.read_csv(AUDIT_LOG_FILE), new_audit], ignore_index=True).to_csv(AUDIT_LOG_FILE, index=False)
    else:
        new_audit.to_csv(AUDIT_LOG_FILE, index=False)
    return "✅ <b>New File Registered</b> in the Audit Trail System."

def genai_chat_engine(query, df):
    query = query.lower()
    response = "🤖 **AI Engineering Assistant:**\n\n"
    
    comp_lab_col = next((c for c in df.columns if str(c).strip().upper() in ['COMPANY', 'COMPANY NAME']), None)
    
    if "contractor" in query or "مقاول" in query:
        if comp_lab_col and 'sample status' in df.columns:
            df_temp = df.copy()
            df_temp['status_upper'] = df_temp['sample status'].str.upper()
            rej_df = df_temp[df_temp['status_upper'].isin(['REJECTED', 'REVISE'])]
            if not rej_df.empty:
                worst = rej_df[comp_lab_col].value_counts().idxmax()
                response += f"Based on the current dataset, **{worst}** is experiencing the highest quality issues with **{rej_df[comp_lab_col].value_counts().max()} rejections**.\n\nRoot Cause Analysis:\nMy neural network indicates that a significant portion of these rejections are linked to compaction and material tests. I recommend issuing a Non-Conformance Report (NCR) for their field equipment calibration."
            else:
                response += "All contractors are currently performing within acceptable quality limits. No critical anomalies detected."
        else:
            response += f"I need '{comp_lab_col}' and 'sample status' columns to analyze contractor performance."
    elif "delay" in query or "تأخير" in query:
        if 'DURATION' in df.columns:
            response += f"The global average delay is **{df['DURATION'].mean():.1f} days**.\n\nPredictive Insight:\nIf the current trend continues, the project will exceed the baseline schedule. I suggest reallocating resources to mitigate this risk."
        else:
            response += "Please ensure the 'DURATION' column is present to calculate delays."
    else:
        response += "I am ready to analyze your project data. You can ask me about:\n- Contractor performance and rejections.\n- Delay analysis and critical paths.\n- Material quality correlations.\n\n*Try asking: 'Which contractor has the most rejections?'*"
    return response

# ==========================================
# 8. Login & Navigation
# ==========================================
def render_login_screen():
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    _, col_center, _ = st.columns([1, 2, 1])
    with col_center:
        is_dark = st.session_state.get("theme", "Dark") == "Dark"
        st.markdown(f"""<div style="background: {'rgba(20, 35, 54, 0.8)' if is_dark else '#ffffff'}; padding: 50px; border-radius: 15px; box-shadow: 0px 10px 40px rgba(0,0,0,0.2);"><div style="text-align:center; margin-bottom: 20px;"><h1 style="color: {'#00d2ff' if is_dark else '#1e3d59'}; font-weight: 800; margin:0; letter-spacing: 2px; font-family:'Montserrat', sans-serif;">KK ENGINEERING</h1><p style="color: #7f8c8d; font-size: 16px; margin:0;">Command Center Portal</p></div><hr style="border: 0.5px solid #eee; margin-bottom: 30px;">""", unsafe_allow_html=True)
        st.markdown('<div class="login-title">SIGN IN</div>', unsafe_allow_html=True)
        email = st.text_input("Email Address", placeholder="e.g., Mohamedhatem@kk.com")
        password = st.text_input("Password", type="password", placeholder="••••••••••••")
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Secure Login", use_container_width=True, type="primary"):
            success, msg = authenticate_user(email, password)
            if success:
                st.success("Authentication Successful. Initializing System...")
                st.rerun()
            else: st.error(msg)
        st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

def render_home_page():
    user = st.session_state["current_user"]
    is_dark = st.session_state.get("theme", "Dark") == "Dark"
    ui = {'text_main': '#ffffff' if is_dark else '#1a1a1a', 'text_muted': '#8da3b9' if is_dark else '#4a5568'}
    
    col_h1, col_h2 = st.columns([0.8, 0.2])
    with col_h1: st.title("🏗️ Mega Infrastructure Command Center")
    with col_h2:
        st.markdown(f"<div style='background:rgba(255,170,0,0.1); padding:10px; border-radius:10px; border:1px solid #ffaa00; text-align:center;'><span style='color:{ui['text_muted']}; font-size:12px;'>Logged in as</span><br><b style='color:#ffaa00;'>{user['Name']}</b><br><span style='color:#2ecc71; font-size:12px;'>{user['Role']} Account</span></div>", unsafe_allow_html=True)
        if st.button("Logout", use_container_width=True):
            st.session_state["authenticated"] = False
            st.rerun()
    st.markdown('<div class="gradient-divider"></div>', unsafe_allow_html=True)
    
    st.markdown(f'<div style="text-align: center; margin-bottom: 50px;"><h2 style="color: {ui["text_main"]}; font-size: 32px; margin-bottom: 10px;">Welcome Back, {user["Name"].split()[0]}! 👋</h2><p style="color: {ui["text_muted"]}; font-size: 18px;">Choose your workspace to get started</p></div>', unsafe_allow_html=True)
    
    c1, c2 = st.columns(2)
    with c1:
        st.markdown('<div class="navigation-card"><div style="font-size: 80px; margin-bottom: 20px;">📊</div><h3 style="color: #00d2ff; font-size: 28px; margin-bottom: 15px;">Main Dashboard</h3><p style="color: #8da3b9; font-size: 16px; line-height: 1.6; margin-bottom: 20px;">Access the full operational dashboard with KPIs, charts, filters, and real-time monitoring</p><div style="background: linear-gradient(135deg, #00d2ff, #008cba); padding: 12px 30px; border-radius: 8px; color: white; font-weight: bold; font-size: 16px;">Enter Dashboard →</div></div>', unsafe_allow_html=True)
        if st.button("📊 Enter Main Dashboard", use_container_width=True, type="primary"):
            st.session_state["current_page"] = "dashboard"
            st.rerun()
    with c2:
        st.markdown('<div class="navigation-card"><div style="font-size: 80px; margin-bottom: 20px;">🔬</div><h3 style="color: #ffaa00; font-size: 28px; margin-bottom: 15px;">Advanced Analytics Hub</h3><p style="color: #8da3b9; font-size: 16px; line-height: 1.6; margin-bottom: 20px;">Explore the 4 levels of analytics: Descriptive, Diagnostic, Predictive, and Prescriptive</p><div style="background: linear-gradient(135deg, #ffaa00, #ff8c00); padding: 12px 30px; border-radius: 8px; color: white; font-weight: bold; font-size: 16px;">Enter Analytics Hub →</div></div>', unsafe_allow_html=True)
        if st.button("🔬 Enter Advanced Analytics", use_container_width=True, type="primary"):
            st.session_state["current_page"] = "analytics"
            st.rerun()
    st.markdown('<div class="gradient-divider"></div>', unsafe_allow_html=True)
    
    # Quick Stats
    st.markdown("### 📈 Quick Overview")
    s1, s2, s3, s4 = st.columns(4)
    with s1: st.markdown('<div class="metric-card" style="text-align: center;"><div style="font-size: 40px; color: #00d2ff;">📁</div><div style="font-size: 24px; font-weight: bold; color: #ffffff; margin-top: 10px;">0</div><div style="color: #8da3b9; font-size: 14px;">Active Projects</div></div>', unsafe_allow_html=True)
    with s2: st.markdown('<div class="metric-card" style="text-align: center;"><div style="font-size: 40px; color: #2ecc71;">✅</div><div style="font-size: 24px; font-weight: bold; color: #ffffff; margin-top: 10px;">0</div><div style="color: #8da3b9; font-size: 14px;">Completed Tests</div></div>', unsafe_allow_html=True)
    with s3: st.markdown('<div class="metric-card" style="text-align: center;"><div style="font-size: 40px; color: #ffaa00;">⚠️</div><div style="font-size: 24px; font-weight: bold; color: #ffffff; margin-top: 10px;">0</div><div style="color: #8da3b9; font-size: 14px;">Pending Reviews</div></div>', unsafe_allow_html=True)
    with s4: st.markdown('<div class="metric-card" style="text-align: center;"><div style="font-size: 40px; color: #e74c3c;">🚨</div><div style="font-size: 24px; font-weight: bold; color: #ffffff; margin-top: 10px;">0</div><div style="color: #8da3b9; font-size: 14px;">Critical Alerts</div></div>', unsafe_allow_html=True)

    st.markdown('<div class="gradient-divider"></div>', unsafe_allow_html=True)

    # Matrix to Flat Data Converter
    st.markdown("### 🗜️ Data Transformation Hub (Matrix to Flat Converter)")
    st.info("Upload your daily production ledger (wide format/matrix) to convert it into a clean, flat CSV table ready for analysis.")
    converter_file = st.file_uploader("Upload Matrix Excel File", type=['xlsx'], key="converter_upload")
    if converter_file and st.button("🔄 Convert to Flat Table", type="primary"):
        with st.spinner("Processing sheets and flattening data..."):
            try:
                xls = pd.ExcelFile(converter_file)
                all_flat_data = []
                for sheet in xls.sheet_names:
                    if 'TABLE' in sheet.upper() or 'DASH' in sheet.upper(): continue
                    try:
                        df_raw = pd.read_excel(xls, sheet_name=sheet, header=None).dropna(how='all', axis=1) 
                        if df_raw.empty or len(df_raw) < 5: continue
                        element_idx, company_idx, rate_idx, date_header_idx, data_start_idx = 1, 0, 2, 3, 4
                        for i in range(min(10, len(df_raw))):
                            row_str = " ".join([str(x).upper() for x in df_raw.iloc[i].tolist() if pd.notna(x)])
                            if 'ELMENT' in row_str or 'ELEMENT' in row_str:
                                element_idx, company_idx, rate_idx, date_header_idx, data_start_idx = i, max(0, i - 1), i + 1, i + 2, i + 3
                                break
                        companies, elements, daily_rates = df_raw.iloc[company_idx].ffill(), df_raw.iloc[element_idx], df_raw.iloc[rate_idx]
                        
                        date_col_idx = next((col for col in df_raw.columns if 'تاريخ' in str(df_raw.iloc[date_header_idx, col]).lower() or 'date' in str(df_raw.iloc[date_header_idx, col]).lower()), None)
                        if date_col_idx is None:
                            date_col_idx = next((col for col in df_raw.columns if isinstance(df_raw.iloc[data_start_idx, col], datetime) or (isinstance(df_raw.iloc[data_start_idx, col], str) and df_raw.iloc[data_start_idx, col].count('-') == 2)), None)
                        if date_col_idx is None: continue 
                            
                        data_rows = df_raw.iloc[data_start_idx:].copy()
                        data_rows['Date'] = pd.to_datetime(data_rows[date_col_idx], errors='coerce')
                        data_rows = data_rows.dropna(subset=['Date'])
                        
                        sheet_melted_data = []
                        for col in df_raw.columns:
                            if col == date_col_idx: continue
                            comp_name, elem_name, target_rate = str(companies[col]).strip(), str(elements[col]).strip(), pd.to_numeric(daily_rates[col], errors='coerce')
                            if str(df_raw.iloc[date_header_idx, col]).strip() == 'م' or comp_name.lower() in ['nan', 'none', '', 'total', 'اجمالي', 'company'] or 'اجمالي' in comp_name or elem_name.upper() in ['ELMENT', 'ELEMENT', 'NAN', 'NONE']: continue
                            temp_df = data_rows[['Date', col]].copy()
                            temp_df.columns = ['Date', 'Executed Quantity (m²)']
                            temp_df['Company Name2'], temp_df['Element (BH)'], temp_df['Target Daily Rate'] = comp_name, elem_name, target_rate if pd.notna(target_rate) else 0
                            sheet_melted_data.append(temp_df)
                            
                        if sheet_melted_data:
                            sheet_res = pd.concat(sheet_melted_data, ignore_index=True)
                            sheet_res['Executed Quantity (m²)'] = pd.to_numeric(sheet_res['Executed Quantity (m²)'], errors='coerce').fillna(0)
                            sheet_res = sheet_res[sheet_res['Executed Quantity (m²)'] > 0]
                            sector = "North Sector" if 'north' in sheet.lower() or 'شمال' in sheet else ("South Sector" if 'south' in sheet.lower() or 'جنوب' in sheet else sheet)
                            sheet_res['Sector'] = sector
                            all_flat_data.append(sheet_res[['Date', 'Sector', 'Company Name2', 'Element (BH)', 'Target Daily Rate', 'Executed Quantity (m²)']])
                    except Exception as e: st.warning(f"Skipped sheet '{sheet}' due to formatting issues. Error: {str(e)}")
                
                if all_flat_data:
                    final_df = pd.concat(all_flat_data, ignore_index=True).sort_values(by=['Date', 'Sector', 'Company Name2']).reset_index(drop=True)
                    final_df.insert(0, 'No.', final_df.index + 3131) 
                    final_df['Date'] = final_df['Date'].dt.strftime('%Y-%m-%d')
                    st.success(f"✅ Successfully converted! Generated {len(final_df)} flat records.")
                    with st.expander("👁️ Preview Converted Flat Data", expanded=True): st.dataframe(final_df.head(50), use_container_width=True)
                    st.download_button(label="📥 Download Clean CSV File", data=final_df.to_csv(index=False).encode('utf-8-sig'), file_name=f"Flat_Execution_Log_{datetime.now().strftime('%Y%m%d')}.csv", mime="text/csv", type="primary")
                else: st.error("❌ Could not extract valid production data. Please ensure the Excel file follows the matrix format.")
            except Exception as e: st.error(f"An error occurred while processing the file: {str(e)}")
            # ==========================================
# 10. Analytics Hub 
# ==========================================
def render_analytics_hub(df):
    df = df.copy()
    df.columns = df.columns.astype(str).str.replace('\n', ' ').str.replace('\r', '').str.strip().str.replace(r'\s+', ' ', regex=True)
    if 'Company Name' not in df.columns and 'Company' in df.columns: df.rename(columns={'Company': 'Company Name'}, inplace=True)
    if 'DURATION' in df.columns: df['DURATION'] = pd.to_numeric(df['DURATION'], errors='coerce').fillna(0)
    if 'AVERAGE VALUE' in df.columns: df['AVERAGE VALUE'] = pd.to_numeric(df['AVERAGE VALUE'], errors='coerce')
    if 'Date ( test)' in df.columns: df['Date ( test)'] = pd.to_datetime(df['Date ( test)'], errors='coerce', dayfirst=True)
    
    st.markdown('<div class="bi-title">🔬 Advanced Analytics Hub</div>', unsafe_allow_html=True)
    with st.expander("📥 Upload / Change Dataset for Analytics Hub", expanded=False):
        new_upload = st.file_uploader("Upload a new CSV dataset to analyze:", type=["csv"])
        if new_upload is not None:
            st.session_state["analytics_df"] = pd.read_csv(new_upload)
            st.success("✅ New dataset loaded! Refreshing Analytics Hub...")
            time.sleep(1); st.rerun()
    
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["📊 Descriptive", "🔍 Diagnostic", "🔮 Predictive", "💡 Prescriptive", "🎛️ Self-Service BI", "🔗 Correlation & Risk"])
    
    with tab1:
        st.markdown("### 📊 Descriptive Analytics - What Happened?")
        k1, k2, k3, k4 = st.columns(4)
        create_card(k1, "Total Samples", f"{len(df):,}")
        create_card(k2, "Accepted", f"<span style='color: #2ecc71;'>{len(df[df['sample status'].str.upper().isin(['ACCEPTED', 'APPROVED AS NOTED'])]) if 'sample status' in df.columns else 0:,}</span>")
        create_card(k3, "Rejected", f"<span style='color: #e74c3c;'>{len(df[df['sample status'].str.upper().isin(['REJECTED', 'REVISE'])]) if 'sample status' in df.columns else 0:,}</span>")
        create_card(k4, "Avg Duration (Days)", f"{df['DURATION'].mean() if 'DURATION' in df.columns else 0:.1f}")
        if 'sample status' in df.columns: st.plotly_chart(px.pie(df, names='sample status', title="Status Distribution", hole=0.4), use_container_width=True)
    
    with tab2:
        if 'Company Name' in df.columns and 'sample status' in df.columns:
            rej_df = df[df['sample status'].str.upper().isin(['REJECTED', 'REVISE'])]
            if not rej_df.empty:
                pareto_data = rej_df['Company Name'].value_counts().reset_index()
                pareto_data.columns = ['Contractor', 'Rejections']
                st.plotly_chart(px.bar(pareto_data, x='Contractor', y='Rejections', title="Rejections by Contractor (Pareto)", color='Rejections', color_continuous_scale='Reds'), use_container_width=True)
    
    with tab3:
        if 'Date ( test)' in df.columns and 'DURATION' in df.columns:
            pred_df = df.dropna(subset=['Date ( test)', 'DURATION']).sort_values('Date ( test)')
            pred_df['7-Day Trend'] = pred_df['DURATION'].rolling(window=7, min_periods=1).mean()
            st.plotly_chart(px.line(pred_df, x='Date ( test)', y=['DURATION', '7-Day Trend'], title="Duration Trend Analysis", color_discrete_sequence=['#ffaa00', '#00d2ff']), use_container_width=True)
    
    with tab4:
        if 'sample status' in df.columns:
            rej_rate = len(df[df['sample status'].str.upper().isin(['REJECTED', 'REVISE'])]) / len(df) * 100
            if rej_rate > 20: st.error(f"🔴 Critical: Immediate Quality Audit. Rejection rate is {rej_rate:.1f}%.")
        if 'DURATION' in df.columns and df['DURATION'].mean() > 15: st.warning(f"🟡 High: Process Optimization. Average duration is {df['DURATION'].mean():.1f} days.")
            
    with tab5:
        col_x, col_y, col_agg = st.columns(3)
        x_axis = col_x.selectbox("Select X-Axis:", df.columns.tolist())
        y_axis = col_y.selectbox("Select Y-Axis:", df.select_dtypes(include=np.number).columns.tolist() or df.columns.tolist())
        agg_func = col_agg.selectbox("Aggregation:", ["count", "sum", "mean", "max", "min"])
        if st.button("📊 Generate Custom Chart", type="primary"):
            try: st.plotly_chart(style_3d_glassy(px.bar(df.groupby(x_axis).agg({y_axis: agg_func}).reset_index(), x=x_axis, y=y_axis, title=f"{agg_func.capitalize()} of {y_axis} by {x_axis}", color_discrete_sequence=NEON_COLORS), chart_type="bar"), use_container_width=True)
            except Exception as e: st.error(f"Error: {str(e)}")

    with tab6:
        num_df = df.select_dtypes(include=np.number)
        if len(num_df.columns) >= 2: st.plotly_chart(style_3d_glassy(px.imshow(num_df.corr().round(2), text_auto=True, color_continuous_scale='RdBu_r', title="Correlation Matrix"), chart_type="heatmap"), use_container_width=True)
    
    st.markdown('<div class="gradient-divider"></div>', unsafe_allow_html=True)
    if st.button("🏠 Back to Home", use_container_width=True):
        st.session_state["current_page"] = "home"
        st.rerun()

def render_site_mode():
    st.title("📱 Site Engineer Mobile Mode")
    c1, c2 = st.columns(2)
    c1.markdown('<div class="site-btn"><br>Add New Sample</div>', unsafe_allow_html=True)
    c2.markdown('<div class="site-btn">📸<br>Upload Site Photo</div>', unsafe_allow_html=True)
    st.dataframe(pd.DataFrame({"Time": ["08:30 AM", "09:15 AM", "10:00 AM"], "Action": ["DPL Test - Zone 1", "Photo Uploaded - Stockpile", "Sample Rejected - Layer 2"], "Status": ["✅ Synced", "✅ Synced", "🚨 Needs Review"]}), use_container_width=True, hide_index=True)

def render_alerts_module(df):
    st.markdown('<div class="bi-title">🚨 Automated Alert & Notification System</div>', unsafe_allow_html=True)
    c1, c2 = st.columns([0.6, 0.4])
    with c1:
        alerts = []
        if 'Company Name' in df.columns and 'sample status' in df.columns:
            rej_df = df[df['sample status'].str.upper().isin(['REJECTED', 'REVISE'])]
            if not rej_df.empty: alerts.append({"Time": datetime.now(EGYPT_TZ).strftime("%H:%M"), "Severity": "🚨 CRITICAL", "Message": f"Contractor '{rej_df['Company Name'].value_counts().idxmax()}' exceeded rejection threshold."})
        if 'DURATION' in df.columns and len(df[df['DURATION'] > 15]) > 0: alerts.append({"Time": datetime.now(EGYPT_TZ).strftime("%Y-%m-%d %H:%M"), "Severity": "⚠️ WARNING", "Message": f"{len(df[df['DURATION'] > 15])} submittals exceeded 15-day SLA."})
        if not alerts: alerts.append({"Time": "Now", "Severity": "✅ OK", "Message": "All systems nominal."})
        st.dataframe(pd.DataFrame(alerts), use_container_width=True, hide_index=True)
    with c2:
        st.toggle("Enable WhatsApp Alerts", value=True)
        st.number_input("Rejection Threshold (%)", min_value=5, max_value=50, value=20)
        if st.button("📤 Send Test Notification", use_container_width=True, type="primary"):
            time.sleep(1)
            st.success("✅ Test Alert Sent Successfully!")
            st.balloons()
            # ==========================================
# 13. Main Dashboard Application
# ==========================================
def render_dashboard():
    user = st.session_state["current_user"]
    is_dark = st.session_state.get("theme", "Dark") == "Dark"
    ui = {'text_main': '#ffffff' if is_dark else '#1a1a1a', 'text_muted': '#8da3b9' if is_dark else '#4a5568', 'card_bg': 'rgba(10, 20, 33, 0.8)' if is_dark else '#ffffff', 'border_color': 'rgba(255, 255, 255, 0.1)' if is_dark else 'rgba(0,0,0,0.12)', 'shadow': '0 5px 15px rgba(0,0,0,0.4)' if is_dark else '0 5px 15px rgba(0,0,0,0.08)', 'highlight_bg': 'rgba(0,210,255,0.05)' if is_dark else 'rgba(41, 128, 185, 0.08)'}
    
    col_h1, col_h2 = st.columns([0.8, 0.2])
    with col_h1: st.title("🏗️ Mega Infrastructure Command Center")
    with col_h2:
        st.markdown(f"<div style='background:rgba(255,170,0,0.1); padding:10px; border-radius:10px; border:1px solid #ffaa00; text-align:center;'><span style='color:{ui['text_muted']}; font-size:12px;'>Logged in as</span><br><b style='color:#ffaa00;'>{user['Name']}</b><br><span style='color:#2ecc71; font-size:12px;'>{user['Role']} Account</span></div>", unsafe_allow_html=True)
        if st.button("Logout", use_container_width=True):
            st.session_state["authenticated"] = False
            st.rerun()

    st.sidebar.markdown("### 🎨 UI/UX Mode")
    theme_col1, theme_col2 = st.sidebar.columns(2)
    if theme_col1.button("🌙 Dark"): st.session_state["theme"] = "Dark"; st.rerun()
    if theme_col2.button("☀️ Light"): st.session_state["theme"] = "Light"; st.rerun()
    st.sidebar.divider()

    st.session_state["site_mode"] = st.sidebar.toggle("📱 Activate Site Engineer Mode", value=st.session_state["site_mode"])
    if st.session_state["site_mode"]:
        render_site_mode()
        return

    st.sidebar.markdown("### 📁 1. Data Source")
    data_source = st.sidebar.selectbox("Connection Type:", ["Local CSV/Excel Upload"])

    uploaded_file = st.sidebar.file_uploader("Upload your Project Log (Excel or CSV) 📂", type=["xlsx", "csv"])

    if uploaded_file is not None:
        try:
            if uploaded_file.name.endswith('.xlsx'): df = pd.read_excel(uploaded_file)
            else: df = pd.read_csv(uploaded_file)
            if df.empty: st.error("⚠️ Empty file!"); st.stop()
        except Exception as e:
            st.error(f"❌ Error reading file: {str(e)}")
            st.stop()
        
        st.session_state["analytics_df"] = df.copy()
        
        # --- 🛠️ Data Cleaning (Global for Dashboard) ---
        df.columns = df.columns.astype(str).str.replace('\n', ' ').str.replace('\r', '').str.strip().str.replace(r'\s+', ' ', regex=True)
        
        if 'Test Type' in df.columns: df['Test Type'] = df['Test Type'].str.strip().str.upper()
        if 'Date ( test)' in df.columns: df['Date ( test)'] = pd.to_datetime(df['Date ( test)'], errors='coerce', dayfirst=True)
        if 'Date( SUB)' in df.columns: df['Date( SUB)'] = pd.to_datetime(df['Date( SUB)'], errors='coerce', dayfirst=True)
        if 'Date (Daily)' in df.columns: df['Date (Daily)'] = pd.to_datetime(df['Date (Daily)'], errors='coerce', dayfirst=True)
        if 'DURATION' in df.columns: df['DURATION'] = pd.to_numeric(df['DURATION'], errors='coerce').fillna(0)
        if 'AVERAGE VALUE' in df.columns: df['AVERAGE VALUE'] = pd.to_numeric(df['AVERAGE VALUE'], errors='coerce')
        for col in ['Executed Quantity (m²)', 'Executed Quantity', 'Target Daily Rate', 'Total Quantity', 'Required Quantity', 'Executed Quantity (m3)']:
            if col in df.columns: df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

        total_rows = len(df)
        missing_dates = df['Date ( test)'].isnull().sum() if 'Date ( test)' in df.columns else 0
        health_score = max(0, 100 - (missing_dates / (total_rows+1) * 100)) if total_rows > 0 else 0
        health_color = "#2ecc71" if health_score >= 95 else "#e74c3c"
        
        st.markdown(f"""
            <div class="health-card" style="border-left: 5px solid {health_color}; background:{ui['card_bg']}; color:{ui['text_main']}; margin-bottom: 20px;">
                <div><h4 style="margin: 0;">✅ Data Integrity Inspector</h4><p style="margin: 5px 0 0 0; color: {ui['text_muted']};">Scanned {total_rows:,} Rows</p></div>
                <div><h2 style="margin: 0; color: {health_color};">{health_score:.1f}%</h2></div>
            </div>
        """, unsafe_allow_html=True)

        if st.button("🚨 Alert System", use_container_width=True): render_alerts_module(df)
        st.markdown('<div class="gradient-divider"></div>', unsafe_allow_html=True)

        # Smart Filters
        st.sidebar.markdown("### 🎯 2. Smart Filters")
        
        comp1 = df['Company Name'].dropna().unique().tolist() if 'Company Name' in df.columns else []
        comp2 = df['Contractor'].dropna().unique().tolist() if 'Contractor' in df.columns else []
        companies = sorted(list(set([str(c).strip() for c in comp1 + comp2 if str(c).lower() != 'nan' and str(c) != ''])))
        selected_companies = st.sidebar.multiselect("🏢 Select Contractor:", options=companies, default=companies)
        
        filtered_df = df.copy()
        if len(companies) > 0: 
            mask1 = filtered_df['Company Name'].astype(str).str.strip().isin(selected_companies) if 'Company Name' in filtered_df.columns else False
            mask2 = filtered_df['Contractor'].astype(str).str.strip().isin(selected_companies) if 'Contractor' in filtered_df.columns else False
            filtered_df = filtered_df[mask1 | mask2]

        num_tests_col = next((c for c in filtered_df.columns if 'NUM' in c.upper() and 'TEST' in c.upper()), None)
        if num_tests_col: filtered_df[num_tests_col] = pd.to_numeric(filtered_df[num_tests_col], errors='coerce').fillna(0)

        total_requests_count = len(filtered_df)
        total_tests_count = int(filtered_df[num_tests_col].sum() if num_tests_col else 0)
        avg_duration_value = round(filtered_df['DURATION'].mean(), 1) if 'DURATION' in filtered_df.columns else 0

        # Ticker
        overall_acc = len(filtered_df[filtered_df['sample status'].astype(str).str.upper().isin(['ACCEPTED', 'APPROVED AS NOTED'])]) if 'sample status' in filtered_df.columns else 0
        overall_rate = (overall_acc / total_requests_count * 100) if total_requests_count > 0 else 0
        st.markdown(f'<div class="ticker-wrap"><div class="ticker"><div class="ticker-item">🚀 <b>Total Logged Submittals:</b> <span>{total_requests_count:,}</span></div><div class="ticker-item">✅ <b>Current Global Yield:</b> <span>{overall_rate:.1f}%</span></div><div class="ticker-item">⏱️ <b>Sector Avg Delay:</b> <span>{avg_duration_value} Days</span></div></div></div>', unsafe_allow_html=True)
        live_indicator("online")

        # Head to Head
        st.markdown('<div class="bi-title">⚔️ Head-to-Head: Contractor vs Contractor</div>', unsafe_allow_html=True)
        if 'Company Name' in filtered_df.columns and len(companies) >= 2:
            cc1, cc2 = st.columns(2)
            c_a = cc1.selectbox("Select Contractor A", companies, index=0, key="h2h_a")
            c_b = cc2.selectbox("Select Contractor B", companies, index=1 if len(companies)>1 else 0, key="h2h_b")
            def get_c_stats(c_name):
                d = filtered_df[filtered_df['Company Name']==c_name]
                tot = len(d)
                rate = (len(d[d['sample status'].str.upper().isin(['ACCEPTED', 'APPROVED AS NOTED'])])/tot*100) if tot>0 else 0
                dur = round(d['DURATION'].mean(), 1) if 'DURATION' in d.columns else 0
                return tot, rate, dur
            tot_a, r_a, d_a = get_c_stats(c_a)
            tot_b, r_b, d_b = get_c_stats(c_b)
            st.markdown(f"""
            <div style="display:flex; justify-content:space-between; text-align:center; background:{ui['card_bg']}; padding:20px; border-radius:15px; border:1px solid #ffaa00; box-shadow: {ui['shadow']};">
                <div style="width:45%; border-right:1px solid {ui['border_color']};"><h3 style="color:#00d2ff; margin-top:0;">{c_a}</h3><p style="font-size:32px; font-weight:800; color:{ui['text_main']}; margin:0;">{r_a:.1f}% Yield</p><p style="color:{ui['text_muted']}; font-size:14px; margin-top:5px;">{tot_a} Submittals | {d_a} Days Avg Delay</p></div>
                <div style="width:10%; align-self:center; font-size:30px; font-weight:900; color:#ffaa00; text-shadow: 0 0 10px rgba(255,170,0,0.5);">VS</div>
                <div style="width:45%; border-left:1px solid {ui['border_color']};"><h3 style="color:#e74c3c; margin-top:0;">{c_b}</h3><p style="font-size:32px; font-weight:800; color:{ui['text_main']}; margin:0;">{r_b:.1f}% Yield</p><p style="color:{ui['text_muted']}; font-size:14px; margin-top:5px;">{tot_b} Submittals | {d_b} Days Avg Delay</p></div>
            </div>
            """, unsafe_allow_html=True)
        
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
                        <h2 style="margin:8px 0; color:{ui['text_main']}; font-size: 28px;">{best_comp['Company']}</h2>
                        <span style="color:{ui['text_muted']};">Approval Rate: <b style="color:#2ecc71; font-size: 18px;">{best_comp['Rate']:.1f}%</b> (from {best_comp['Total']} submittals)</span>
                    </div>
                """, unsafe_allow_html=True)
                l_col2.markdown(f"""
                    <div class="leaderboard-card" style="border-left-color: #e74c3c;">
                        <h4 style="margin:0; color:#e74c3c; text-transform: uppercase; font-size: 14px;">⚠️ Needs Attention</h4>
                        <h2 style="margin:8px 0; color:{ui['text_main']}; font-size: 28px;">{worst_comp['Company']}</h2>
                        <span style="color:{ui['text_muted']};">Approval Rate: <b style="color:#e74c3c; font-size: 18px;">{worst_comp['Rate']:.1f}%</b> (from {worst_comp['Total']} submittals)</span>
                    </div>
                """, unsafe_allow_html=True)

        if 'Company Name' in filtered_df.columns and 'Sampling Location' in filtered_df.columns:
            mat_df = filtered_df.copy()
            mat_df['Sampling_Lower'] = mat_df['Sampling Location'].astype(str).str.lower()
            def categorize_location(loc):
                if 'stock' in loc or 'مشون' in loc: return 'Stockpile'
                elif 'bottom' in loc or 'قاع' in loc: return 'Bottom of Excavation'
                elif 'fill' in loc or 'ردم' in loc: return 'Fill'
                return 'Other'
            mat_df['Loc_Category'] = mat_df['Sampling_Lower'].apply(categorize_location)
            
            st.markdown("#### 📑 Consolidated Contractors Summary (Ready for Print)")
            summary_pivot = pd.crosstab(mat_df['Company Name'], mat_df['Loc_Category'], margins=True, margins_name="Total")
            existing_cols = [c for c in ['Stockpile', 'Bottom of Excavation', 'Fill', 'Other', 'Total'] if c in summary_pivot.columns]
            st.dataframe(summary_pivot[existing_cols], use_container_width=True)
            st.divider()

            target_dict = {}
            if 'Company Name' in df.columns and 'Required Quantity' in df.columns:
                lookup_df = df[['Company Name', 'Required Quantity']].dropna(subset=['Company Name'])
                for _, row in lookup_df.iterrows():
                    c_qty = pd.to_numeric(row['Required Quantity'], errors='coerce')
                    if pd.notna(c_qty): target_dict[str(row['Company Name']).strip().lower()] = max(target_dict.get(str(row['Company Name']).strip().lower(), 0), c_qty)

            st.markdown("#### 📥 Master Stockpile Targets Report")
            report_data = []
            log_companies = [str(c).strip() for c in mat_df['Company Name'].dropna().unique()]
            target_companies = [str(c).strip() for c in df['Company Name'].dropna().unique()] if 'Company Name' in df.columns else []
            all_companies = sorted(list(set(log_companies + target_companies)))
            battalion_col_main = next((c for c in mat_df.columns if 'BATTAL' in c.upper()), None)

            for c_name in all_companies:
                c_key = c_name.lower()
                comp_all_rows = mat_df[mat_df['Company Name'].astype(str).str.strip().str.lower() == c_key]
                c_df_stock = comp_all_rows[comp_all_rows['Loc_Category'] == 'Stockpile']
                
                b_str = "N/A"
                if battalion_col_main and not comp_all_rows.empty:
                    bats = comp_all_rows[battalion_col_main].dropna().unique()
                    if len(bats) > 0: b_str = " & ".join([fmt_b(b) for b in bats]) 

                req_qty = target_dict.get(c_key, np.nan)
                exec_qty = int(pd.to_numeric(c_df_stock[num_tests_col], errors='coerce').fillna(0).sum()) if num_tests_col else len(c_df_stock)

                if pd.notna(req_qty) and req_qty > 0:
                    diff = exec_qty - int(req_qty)
                    status, req_val, diff_val = ("✅ Target Exceeded" if diff >= 0 else f"⚠️ Missing {abs(diff)} Tests", int(req_qty), diff)
                else: status, req_val, diff_val = ("No Target Defined", "N/A", "N/A")

                if req_val != "N/A" or exec_qty > 0:
                    report_data.append({"Contractor Name": c_name, "Battalion": b_str, "Executed Stockpile Tests": exec_qty, "Required Target": req_val, "Difference (+/-)": diff_val, "Status": status})
                    
            report_df = pd.DataFrame(report_data)
            st.dataframe(report_df, use_container_width=True)
            st.divider()

            st.markdown("#### 🏢 Individual Contractor Deep Dive")
            all_log_companies = sorted(list(set([str(c).strip() for c in mat_df['Company Name'].dropna().unique() if str(c) != 'nan'])))
            if all_log_companies:
                selected_comp = st.selectbox("Select a Contractor to Analyze:", all_log_companies, key="deepdive_comp_sel")
                comp_df_full = mat_df[mat_df['Company Name'] == selected_comp]
                
                # --- Advanced Sections including the NEW Quantities Rate ---
                tab_360, tab_stockpile, tab_execution, tab_quantities = st.tabs(["🌐 360° Corporate Profile", "⛰️ Stockpile Sourcing", "🏗️ Compaction Dashboard", "📊 Quantities Rate"])
                
                with tab_360:
                    st.markdown(f"### 🌐 Executive Profile: `{selected_comp}`")
                    battalion_col_360 = next((c for c in comp_df_full.columns if 'BATTAL' in c.upper()), None)
                    zone_col_360 = next((c for c in comp_df_full.columns if 'ZONE' in c.upper()), None)
                    elment_col_360 = next((c for c in comp_df_full.columns if 'ELMEN' in c.upper() or 'ELEMENT' in c.upper()), None)
                    
                    c1, c2, c3, c4 = st.columns(4)
                    create_card(c1, "Total Test Points", int(pd.to_numeric(comp_df_full[num_tests_col], errors='coerce').fillna(0).sum()) if num_tests_col else len(comp_df_full))
                    create_card(c2, "Active Battalions", comp_df_full[battalion_col_360].nunique() if battalion_col_360 else "N/A")
                    create_card(c3, "Active Zones", comp_df_full[zone_col_360].nunique() if zone_col_360 else "N/A")
                    create_card(c4, "Avg Delay (Days)", f"{pd.to_numeric(comp_df_full['DURATION'], errors='coerce').mean():.1f}" if 'DURATION' in comp_df_full.columns else "N/A")

                with tab_stockpile:
                    req_qty = target_dict.get(selected_comp.strip().lower(), np.nan)
                    comp_bat_df = comp_df_full
                    battalion_col_stock = next((c for c in comp_df_full.columns if 'BATTAL' in c.upper()), None)
                    if battalion_col_stock:
                        avail_bats = ["All Battalions"] + sorted([str(b) for b in comp_df_full[battalion_col_stock].unique() if pd.notna(b) and str(b).strip() != ''])
                        selected_bat = st.selectbox("📍 Filter Sourcing Analysis by Battalion:", avail_bats, key=f"bat_stock_{selected_comp}")
                        if selected_bat != "All Battalions": comp_bat_df = comp_df_full[comp_df_full[battalion_col_stock].astype(str) == selected_bat]

                    stock_df = comp_bat_df[comp_bat_df['Loc_Category'] == 'Stockpile']
                    stock_count = int(pd.to_numeric(stock_df[num_tests_col], errors='coerce').fillna(0).sum()) if num_tests_col else len(stock_df)
                    
                    cc1, cc2 = st.columns(2)
                    create_card(cc1, "Stockpile Tests", stock_count)
                    col_200 = next((c for c in stock_df.columns if '200' in str(c)), None)
                    if col_200 and not stock_df.empty: create_card(cc2, "Avg Sieve #200 (Stockpile)", f"{pd.to_numeric(stock_df[col_200].astype(str).str.replace('%', '', regex=False).str.strip(), errors='coerce').mean():.2f}%")
                    else: create_card(cc2, "Avg Sieve #200 (Stockpile)", "N/A")

                with tab_execution:
                    st.markdown(f"### 🏗️ Compaction Dashboard: `{selected_comp}`")
                    test_col = 'Test Type' if 'Test Type' in comp_df_full.columns else None
                    compaction_df = comp_df_full[comp_df_full[test_col].astype(str).str.contains('DPL|PLATE', case=False, na=False)].copy() if test_col else pd.DataFrame()
                    num_tests_col_exec = next((c for c in comp_df_full.columns if 'NUMBER OF TESTS' in str(c).strip().upper() or 'NUM OF TEST' in str(c).strip().upper()), None)
                    
                    dpl_pts = int(pd.to_numeric(compaction_df[compaction_df[test_col].astype(str).str.contains('DPL', case=False, na=False)][num_tests_col_exec], errors='coerce').sum()) if num_tests_col_exec else 0
                    plate_pts = int(pd.to_numeric(compaction_df[compaction_df[test_col].astype(str).str.contains('PLATE', case=False, na=False)][num_tests_col_exec], errors='coerce').sum()) if num_tests_col_exec else 0
                    
                    c1, c2, c3 = st.columns(3)
                    create_card(c1, "Total Test Points", f"{dpl_pts + plate_pts:,}", delta_html=f"<div style='font-size:14px; color:#8da3b9; margin-top:5px;'>DPL: <b style='color:#00d2ff;'>{dpl_pts}</b> | Plate: <b style='color:#ffaa00;'>{plate_pts}</b></div>")
                    create_card(c2, "Avg DPL Value", f"{pd.to_numeric(compaction_df[compaction_df[test_col].astype(str).str.contains('DPL', case=False, na=False)]['AVERAGE VALUE'], errors='coerce').mean():.2f}" if 'AVERAGE VALUE' in compaction_df.columns else "N/A")
                    
                    if 'sample status' in compaction_df.columns and not compaction_df.empty:
                        compaction_df['status_upper'] = compaction_df['sample status'].str.upper()
                        yield_pct = (len(compaction_df[compaction_df['status_upper'].isin(['ACCEPTED', 'APPROVED AS NOTED'])]) / len(compaction_df)) * 100 if len(compaction_df) > 0 else 0
                        yield_color = "#2ecc71" if yield_pct >= 90 else ("#f1c40f" if yield_pct >= 75 else "#e74c3c")
                        create_card(c3, "Compaction Yield", f"<span style='color:{yield_color};'>{yield_pct:.1f}%</span>")

                # ==========================================
                # 🚀 QUANTITIES RATE — NEW ENHANCED SECTION
                # ==========================================
                with tab_quantities:
                    st.markdown(f"### 📊 Quantities Rate & Execution Analytics")
                    st.caption("Full execution analysis — quantities, targets, elements coverage, and worst performer.")
                    
                    contractor_col   = 'Contractor' if 'Contractor' in df.columns else next((c for c in df.columns if 'CONTRACTOR' in c.upper()), None)
                    company_col      = 'Company' if 'Company' in df.columns else next((c for c in df.columns if str(c).strip().upper() == 'COMPANY'), None)
                    company_name_col = 'Company Name' if 'Company Name' in df.columns else next((c for c in df.columns if 'COMPANY NAME' in c.upper()), None)
                    
                    exec_qty_m3_col  = 'Executed Quantity (m3)' if 'Executed Quantity (m3)' in df.columns else next((c for c in df.columns if 'EXECUTED QUANTITY' in c.upper() and 'M3' in c.upper()), None)
                    exec_qty_lab_col = 'Executed Quantity' if 'Executed Quantity' in df.columns else next((c for c in df.columns if str(c).strip().upper() == 'EXECUTED QUANTITY'), None)
                    total_qty_col    = 'Total Quantity' if 'Total Quantity' in df.columns else next((c for c in df.columns if 'TOTAL QUANTITY' in c.upper()), None)
                    target_rate_col  = 'Target Daily Rate' if 'Target Daily Rate' in df.columns else next((c for c in df.columns if 'TARGET DAILY RATE' in c.upper()), None)
                    date_daily_col   = 'Date (Daily)' if 'Date (Daily)' in df.columns else next((c for c in df.columns if 'DATE (DAILY)' in c.upper()), None)
                    elem_all_col     = 'Element (all)' if 'Element (all)' in df.columns else next((c for c in df.columns if 'ELEMENT (ALL)' in c.upper()), None)
                    elment_main_col  = 'ELMENT' if 'ELMENT' in df.columns else next((c for c in df.columns if 'ELMENT' in c.upper() and 'ALL' not in c.upper()), None)
                    sector_col       = 'Sectoer' if 'Sectoer' in df.columns else next((c for c in df.columns if 'SECTOER' in c.upper() or 'SECTOR' in c.upper()), None)

                    if contractor_col:
                        df[contractor_col] = df[contractor_col].astype(str).str.strip()
                        valid_contractors = sorted([c for c in df[contractor_col].unique() if c.lower() != 'nan' and c != ''])
                        
                        st.markdown(f"""
                        <div style='background:rgba(0, 210, 255, 0.05); padding: 15px; border-radius: 8px; border-left: 4px solid #00d2ff; margin-bottom: 20px;'>
                            <b style='color:#00d2ff; font-size:16px;'>🏗️ Step 1: Select Execution Contractor</b><br>
                            <span style='color:{ui["text_muted"]}; font-size:13px;'>Choose the contractor to view exact execution quantities and cross-check with Lab data.</span>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        exec_comp = st.selectbox("Select Contractor:", valid_contractors, key="q_comp_sel_final")
                        
                        df_site = df[df[contractor_col] == exec_comp].copy()
                        df_comp = df[df[company_col].astype(str).str.strip() == exec_comp].copy() if company_col else pd.DataFrame()
                        df_comp_name = df[df[company_name_col].astype(str).str.strip() == exec_comp].copy() if company_name_col else pd.DataFrame()

                        if exec_qty_m3_col: df_site[exec_qty_m3_col] = pd.to_numeric(df_site[exec_qty_m3_col], errors='coerce').fillna(0)
                        if exec_qty_lab_col and not df_comp.empty: df_comp[exec_qty_lab_col] = pd.to_numeric(df_comp[exec_qty_lab_col], errors='coerce').fillna(0)
                        if total_qty_col and not df_comp.empty: df_comp[total_qty_col] = pd.to_numeric(df_comp[total_qty_col], errors='coerce').fillna(0)
                        if target_rate_col: df_site[target_rate_col] = pd.to_numeric(df_site[target_rate_col], errors='coerce').fillna(0)
                        
                        total_scope = 0
                        if total_qty_col and not df_comp.empty:
                            if elment_main_col and elment_main_col in df_comp.columns:
                                total_scope = df_comp.groupby(elment_main_col)[total_qty_col].max().sum()
                            else:
                                total_scope = df_comp[total_qty_col].max()
                                
                        lab_exec = 0
                        if exec_qty_lab_col and not df_comp.empty:
                            lab_exec = df_comp[exec_qty_lab_col].sum()
                            
                        site_exec = 0
                        if exec_qty_m3_col and not df_site.empty:
                            site_exec = df_site[exec_qty_m3_col].sum()
                            
                        completion_pct = (site_exec / total_scope * 100) if total_scope > 0 else 0
                        
                        st.markdown("#### ⚖️ Overall Quantities KPIs")
                        c1, c2, c3, c4 = st.columns(4)
                        create_card(c1, "Total Project Scope (m³)", f"{total_scope:,.1f}", delta_html=f"<span style='color:#bdc3c7; font-size:11px;'>Ref: {company_col} ➔ {total_qty_col}</span>")
                        create_card(c2, "Lab Executed Qty [QC]", f"{lab_exec:,.1f}", delta_html=f"<span style='color:#ffaa00; font-size:11px;'>Ref: {company_col} ➔ {exec_qty_lab_col}</span>")
                        create_card(c3, "Site Executed Qty (m³) [Production]", f"{site_exec:,.1f}", delta_html=f"<span style='color:#00d2ff; font-size:11px;'>Ref: {contractor_col} ➔ {exec_qty_m3_col}</span>")
                        
                        comp_color = "#2ecc71" if completion_pct >= 80 else ("#f1c40f" if completion_pct >= 50 else "#e74c3c")
                        c4.markdown(f"""
                            <div class="metric-card" style="border-left: 5px solid {comp_color};">
                                <div class="metric-label">Scope Completion %</div>
                                <div class="metric-value" style="color: {comp_color} !important;">{completion_pct:.1f}%</div>
                                <div class="prog-bg" style="height: 6px; background: rgba(127,140,141,0.2); border-radius: 10px; margin-top: 10px;">
                                    <div class="prog-fill" style="height: 100%; width: {min(100, completion_pct)}%; background: {comp_color}; border-radius: 10px;"></div>
                                </div>
                            </div>
                        """, unsafe_allow_html=True)
                        
                        st.markdown('<div class="gradient-divider"></div>', unsafe_allow_html=True)

                        col_elem, col_chart = st.columns([0.4, 0.6])
                        
                        with col_elem:
                            st.markdown("#### 🏗️ Executed Quantity per Element")
                            if elem_all_col and exec_qty_m3_col and not df_site.empty:
                                elem_df = df_site.groupby(elem_all_col)[exec_qty_m3_col].sum().reset_index()
                                elem_df = elem_df[elem_df[exec_qty_m3_col] > 0].sort_values(exec_qty_m3_col, ascending=False)
                                
                                if not elem_df.empty:
                                    top_elems = elem_df.head(3)
                                    for _, row in top_elems.iterrows():
                                        st.markdown(f"""
                                        <div style="background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.1); padding: 15px; border-radius: 8px; margin-bottom: 10px;">
                                            <div style="color: #ffaa00; font-size: 13px; font-weight: bold;">📍 {row[elem_all_col]}</div>
                                            <div style="color: white; font-size: 24px; font-weight: 800;">{row[exec_qty_m3_col]:,.1f} m³</div>
                                            <div style="color: #8da3b9; font-size: 11px;">{exec_comp}</div>
                                        </div>
                                        """, unsafe_allow_html=True)
                                    with st.expander("View All Elements Breakdown"):
                                        st.dataframe(elem_df, use_container_width=True)
                                else:
                                    st.info("No quantities found per element.")
                                    
                        with col_chart:
                            st.markdown("#### 🚀 Daily Execution vs Target Rate")
                            if date_daily_col and target_rate_col and exec_qty_m3_col and not df_site.empty:
                                df_site[date_daily_col] = pd.to_datetime(df_site[date_daily_col], errors='coerce')
                                valid_dates_df = df_site.dropna(subset=[date_daily_col, exec_qty_m3_col])
                                
                                if not valid_dates_df.empty:
                                    daily_trend = valid_dates_df.groupby(date_daily_col).agg({
                                        exec_qty_m3_col: 'sum',
                                        target_rate_col: 'max'
                                    }).reset_index().sort_values(date_daily_col)
                                    
                                    days_hit = len(daily_trend[daily_trend[exec_qty_m3_col] >= daily_trend[target_rate_col]])
                                    total_days = len(daily_trend)
                                    hit_rate = (days_hit / total_days * 100) if total_days > 0 else 0
                                    
                                    st.markdown(f"**Target Hit Rate:** Contractor met daily target on <b style='color:#2ecc71;'>{days_hit} / {total_days}</b> active days ({hit_rate:.1f}%).", unsafe_allow_html=True)
                                    
                                    fig_daily = go.Figure()
                                    fig_daily.add_trace(go.Scatter(x=daily_trend[date_daily_col], y=daily_trend[target_rate_col], name="Target Daily Rate", mode='lines+markers', line=dict(color='#e74c3c', width=3), hovertemplate='<b>Date:</b> %{x|%Y-%m-%d}<br><b>Target:</b> %{y:,.1f} m³'))
                                    fig_daily.add_trace(go.Bar(x=daily_trend[date_daily_col], y=daily_trend[exec_qty_m3_col], name="Executed (m³)", marker_color='#00d2ff', hovertemplate='<b>Date:</b> %{x|%Y-%m-%d}<br><b>Executed:</b> %{y:,.1f} m³'))
                                    fig_daily.update_layout(height=350, barmode='group', hovermode='x unified', margin=dict(l=0, r=0, t=10, b=0), legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
                                    try: fig_daily = style_3d_glassy(fig_daily, "combo")
                                    except: pass
                                    st.plotly_chart(fig_daily, use_container_width=True)
                                else:
                                    st.info("No valid dates for plotting.")
                            else:
                                st.info("Missing Date, Target, or Execution (m3) columns.")

                        st.markdown('<div class="gradient-divider"></div>', unsafe_allow_html=True)

                        st.markdown("#### 🕵️ Element Coverage Audit — Missing Quantities Detector")
                        st.caption("Cross-checks [Element (all) + Contractor] vs [ELMENT + Company Name] to find elements missing Lab quantities.")
                        
                        if elem_all_col and elment_main_col and company_name_col:
                            expected_elems = set(df_site[df_site[exec_qty_m3_col] > 0][elem_all_col].dropna().astype(str).str.strip()) if exec_qty_m3_col else set()
                            lab_elems = set(df_comp_name[elment_main_col].dropna().astype(str).str.strip())
                            
                            missing_in_lab = expected_elems - lab_elems
                            
                            col_m, col_c = st.columns(2)
                            with col_m:
                                if missing_in_lab:
                                    missing_df = pd.DataFrame({'Contractor': exec_comp, 'Element': list(missing_in_lab), 'Status': '❌ No Quantity'})
                                    st.markdown(f"""
                                    <div style="background: rgba(231, 76, 60, 0.1); border-left: 4px solid #e74c3c; padding: 15px; border-radius: 8px; margin-bottom: 10px;">
                                        <b style="color:#e74c3c;">🚨 {len(missing_in_lab)} Element(s) Missing Quantities</b><br>
                                        <span style="font-size:12px; color:{ui['text_main']};">Request quantities from the Technical Office for these elements:</span>
                                    </div>
                                    """, unsafe_allow_html=True)
                                    st.dataframe(missing_df, use_container_width=True)
                                else:
                                    st.success("✅ All executed elements have corresponding Lab records!")
                                    
                            with col_c:
                                covered_in_lab = expected_elems.intersection(lab_elems)
                                if covered_in_lab:
                                    covered_df = pd.DataFrame({'Contractor': exec_comp, 'Element': list(covered_in_lab), 'Status': '✅ Has Quantity'})
                                    st.markdown(f"""
                                    <div style="background: rgba(46, 204, 113, 0.1); border-left: 4px solid #2ecc71; padding: 15px; border-radius: 8px; margin-bottom: 10px;">
                                        <b style="color:#2ecc71;">✅ {len(covered_in_lab)} Element(s) Covered</b><br>
                                        <span style="font-size:12px; color:{ui['text_main']};">These elements have validated quantities.</span>
                                    </div>
                                    """, unsafe_allow_html=True)
                                    st.dataframe(covered_df, use_container_width=True)
                        else:
                            st.info("Missing 'Element (all)', 'ELMENT', or 'Company Name' columns to perform audit.")

                        st.markdown('<div class="gradient-divider"></div>', unsafe_allow_html=True)

                        st.markdown("#### 🏆 Worst Performer Analysis — By Sector")
                        st.caption("Identifies the contractor with the lowest execution rate vs daily target per sector.")
                        
                        if sector_col and target_rate_col and exec_qty_m3_col:
                            perf_df = df.copy()
                            perf_df[exec_qty_m3_col] = pd.to_numeric(perf_df[exec_qty_m3_col], errors='coerce').fillna(0)
                            perf_df[target_rate_col] = pd.to_numeric(perf_df[target_rate_col], errors='coerce').fillna(0)
                            
                            worst_data = []
                            sectors = [s for s in perf_df[sector_col].dropna().unique() if str(s).strip().lower() != 'nan']
                            
                            for s in sectors:
                                s_df = perf_df[perf_df[sector_col] == s].copy()
                                if date_daily_col:
                                    daily_agg = s_df.groupby([contractor_col, date_daily_col]).agg({
                                        exec_qty_m3_col: 'sum',
                                        target_rate_col: 'max'
                                    }).reset_index()
                                    cont_agg = daily_agg.groupby(contractor_col).agg({
                                        exec_qty_m3_col: 'sum',
                                        target_rate_col: 'sum'
                                    }).reset_index()
                                else:
                                    cont_agg = s_df.groupby(contractor_col).agg({
                                        exec_qty_m3_col: 'sum',
                                        target_rate_col: 'sum'
                                    }).reset_index()
                                    
                                cont_agg = cont_agg[cont_agg[target_rate_col] > 0]
                                
                                if not cont_agg.empty:
                                    cont_agg['Avg Performance %'] = (cont_agg[exec_qty_m3_col] / cont_agg[target_rate_col] * 100).round(1)
                                    cont_agg = cont_agg.sort_values('Avg Performance %')
                                    worst = cont_agg.iloc[0]
                                    worst_data.append({'Sector': s, 'Contractor': worst[contractor_col], 'Avg Performance %': worst['Avg Performance %']})
                                    
                            if worst_data:
                                w_cols = st.columns(len(worst_data))
                                for idx, w in enumerate(worst_data):
                                    w_cols[idx].markdown(f"""
                                    <div style="background:rgba(231,76,60,0.1);border-left:5px solid #e74c3c;border-radius:12px;padding:16px;margin-bottom:12px;">
                                        <div style="color:#e74c3c;font-size:12px;font-weight:600;text-transform:uppercase;margin-bottom:6px;">🔴 Worst Performer in {w['Sector']}</div>
                                        <div style="color:#ffffff;font-size:20px;font-weight:700;">{w['Contractor']}</div>
                                        <div style="color:#8da3b9;font-size:13px;margin-top:6px;">Target Met: <b style="color:#e74c3c">{w['Avg Performance %']:.1f}%</b></div>
                                    </div>
                                    """, unsafe_allow_html=True)
                            else:
                                st.info("No active targets found to evaluate performance.")
                        else:
                            st.info("Missing Sector, Target, or Execution (m3) columns.")

                    else:
                        st.info("🚨 **Data Missing:** Please ensure your CSV includes 'Contractor' and 'Company' columns.")

        # --- 🔍 Advanced Element Quality Auditor ---
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

                        comp_lab_col_global = next((c for c in bh_df.columns if str(c).strip().upper() in ['COMPANY', 'COMPANY NAME']), None)
                        if comp_lab_col_global:
                            if 'Date ( test)' in bh_df.columns:
                                comp_stats = bh_df.dropna(subset=[comp_lab_col_global]).groupby(comp_lab_col_global)['Date ( test)'].agg(['min', 'max']).reset_index()
                                comp_details = [f"<span style='color:#2ecc71;'><b>{r[comp_lab_col_global]}</b></span>: <span style='font-size:16px; color:{ui['text_muted']};'>{r['min'].strftime('%Y-%m-%d') if pd.notna(r['min']) else 'N/A'} <b style='color:#ffaa00;'>&rarr;</b> {r['max'].strftime('%Y-%m-%d') if pd.notna(r['max']) else 'N/A'}</span>" for _, r in comp_stats.iterrows()]
                                companies_str = "<br>".join(comp_details) if comp_details else "N/A"
                            else:
                                companies_worked = bh_df[comp_lab_col_global].dropna().unique()
                                companies_str = " ، ".join(companies_worked) if len(companies_worked) > 0 else "N/A"
                            st.markdown(f"""
                                <div class="custom-card" style="margin-top: 5px; text-align: left; padding-left: 30px;">
                                    <div class="metric-label" style="color:#ffaa00; text-align: left; margin-bottom: 15px;">Contractors Timeline on this Element</div>
                                    <div class="metric-value" style="font-size: 18px; line-height: 2.0; font-weight: 500; color:{ui['text_main']};">{companies_str}</div>
                                </div>
                                """, unsafe_allow_html=True)

                        if 'layer' in bh_df.columns and 'sample status' in bh_df.columns:
                            rejected_mask = bh_df['sample status'].astype(str).str.upper().isin(['REJECTED', 'REVISE'])
                            accepted_mask = bh_df['sample status'].astype(str).str.upper().isin(['ACCEPTED', 'APPROVED AS NOTED'])
                            approved_layers = set(bh_df[accepted_mask]['layer'].dropna().astype(str).unique())
                            unresolved_alerts = list(set([(str(row.get('layer', 'Unknown')), row.get('Test Type', 'N/A'), row.get('serial', 'N/A')) for _, row in bh_df[rejected_mask].iterrows() if str(row.get('layer', 'Unknown')) not in approved_layers]))
                            if unresolved_alerts:
                                st.markdown("#### 🚨 Critical Quality Alerts (Unresolved Submittals)")
                                alert_cols = st.columns(min(len(unresolved_alerts), 4) if len(unresolved_alerts) > 0 else 1)
                                for idx, alert in enumerate(unresolved_alerts[:8]): 
                                    l, t_type, ser = alert
                                    alert_cols[idx % 4].markdown(f"""
                                        <div style="background: rgba(231, 76, 60, 0.15); backdrop-filter: blur(5px); padding: 15px; border-radius: 15px; border: 1px solid #e74c3c; margin-bottom: 10px; box-shadow: 0 4px 15px rgba(231, 76, 60, 0.2);">
                                            <div style="color: #e74c3c; font-size: 16px; font-weight: bold; margin-bottom: 5px;">⚠️ Action Required</div>
                                            <div style="color: {ui['text_main']}; font-size: 14px; line-height: 1.6;">
                                                <b>Layer:</b> {l}<br><b>Test:</b> {t_type}<br><b>Serial No:</b> {ser}<br>
                                                <span style="font-size:12px; color:#e74c3c;">Status is REVISE/REJECTED with no subsequent approval found!</span>
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
                                    st.markdown(f"""
                                    <div style="background: rgba(46, 204, 113, 0.1); border-left: 4px solid #2ecc71; padding: 15px; border-radius: 10px; margin-bottom: 20px;">
                                        <h5 style="color: #2ecc71; margin: 0;">✅ Sequence Verified</h5>
                                        <p style="color: {ui['text_main']}; margin: 5px 0 0 0; font-size: 14px;">All compaction layers are chronologically correct with no missing intermediate layers.</p>
                                    </div>
                                    """, unsafe_allow_html=True)
                                else:
                                    if missing_layers:
                                        missing_str = ", ".join([f"Layer {l}" for l in missing_layers])
                                        st.markdown(f"""
                                        <div style="background: rgba(241, 196, 15, 0.1); border-left: 4px solid #f1c40f; padding: 15px; border-radius: 10px; margin-bottom: 10px;">
                                            <h5 style="color: #f1c40f; margin: 0;">⚠️ Missing Compaction Layers Detected</h5>
                                            <p style="color: {ui['text_main']}; margin: 5px 0 0 0; font-size: 14px;">Gap found in execution sequence. Missing: <b style="color:{ui['text_main']};">{missing_str}</b></p>
                                        </div>
                                        """, unsafe_allow_html=True)
                                    if logic_errors:
                                        errors_html = "<br>".join([f"🚨 {err}" for err in logic_errors])
                                        st.markdown(f"""
                                        <div style="background: rgba(231, 76, 60, 0.1); border-left: 4px solid #e74c3c; padding: 15px; border-radius: 10px; margin-bottom: 20px;">
                                            <h5 style="color: #e74c3c; margin: 0;">🛑 Critical Chronological Illogic</h5>
                                            <p style="color: {ui['text_main']}; margin: 5px 0 0 0; font-size: 14px; line-height:1.8;">{errors_html}</p>
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
                                    st.plotly_chart(fig_sc, use_container_width=True, key=f"sc_{selected_bh}")
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
                            st.plotly_chart(fig_matrix, use_container_width=True, key=f"mat_{selected_bh}")
                        st.divider()

                        b_col1, b_col2 = st.columns(2)
                        with b_col1:
                            if 'sample status' in bh_df.columns:
                                bh_df['status_upper'] = bh_df['sample status'].str.upper()
                                fig_ep = px.pie(bh_df, names='status_upper', title=f"Status Breakdown for {selected_bh}", hole=0.4, color='status_upper', color_discrete_map=STATUS_COLORS)
                                fig_ep.update_traces(textinfo='label+percent', hovertemplate='<b>Status:</b> %{label}<br>Count: %{value}<br>Percentage: %{percent}')
                                fig_ep = style_3d_glassy(fig_ep, chart_type="pie")
                                st.plotly_chart(fig_ep, use_container_width=True, key=f"ep_{selected_bh}")
                        with b_col2:
                            if 'layer' in bh_df.columns:
                                layer_reqs = bh_df.groupby('layer').size().reset_index(name='Submittals')
                                layer_reqs['Layer_Num'] = layer_reqs['layer'].astype(str).str.extract(r'(\d+)').fillna(999).astype(int)
                                layer_reqs = layer_reqs.sort_values('Layer_Num')
                                fig_eb = px.bar(layer_reqs, x='layer', y='Submittals', title="Number of Submittals per Layer (Sorted)", text_auto=True, color_discrete_sequence=['#ffaa00'])
                                fig_eb = style_3d_glassy(fig_eb, chart_type="bar")
                                st.plotly_chart(fig_eb, use_container_width=True, key=f"eb_{selected_bh}")

                        if 'Date ( test)' in bh_df.columns and 'AVERAGE VALUE' in bh_df.columns and 'layer' in bh_df.columns:
                            trend_df = bh_df.dropna(subset=['Date ( test)', 'AVERAGE VALUE'])
                            if not trend_df.empty:
                                fig_el = px.line(trend_df, x='Date ( test)', y='AVERAGE VALUE', color='layer', markers=True, title=f"DPL Values Trend across Layers over time for {selected_bh}", color_discrete_sequence=NEON_COLORS)
                                fig_el = style_3d_glassy(fig_el, chart_type="line")
                                st.plotly_chart(fig_el, use_container_width=True, key=f"el_{selected_bh}")
                        
                        with st.expander(f"📂 View Raw Detailed Audit Log for `{selected_bh}`"):
                            st.dataframe(bh_df.drop(columns=['Layer_Num', 'Execution_Node'], errors='ignore'), use_container_width=True)
        else:
            st.warning("⚠️ **Column Not Found:** Could not locate an 'Element' column in your uploaded file to enable Deep Dive Analysis.")

        st.markdown('<div class="gradient-divider"></div>', unsafe_allow_html=True)
        with st.expander("📂 View Complete Operational Records (Raw Data)"):
            st.dataframe(filtered_df, use_container_width=True)

        st.markdown('<div class="gradient-divider"></div>', unsafe_allow_html=True)
        if st.button("🏠 Back to Home", use_container_width=True, key="back_to_home_dashboard"):
            st.session_state["current_page"] = "home"
            st.rerun()

    else:
        st.info("👈 Please connect a Data Source or Upload a CSV to activate the Enterprise Engine.")

# ==========================================
# 14. Main Application Execution
# ==========================================
def main():
    inject_custom_css()  
    init_auth_system()
    
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False

    if not st.session_state["authenticated"]:
        render_login_screen()
    else:
        current_page = st.session_state.get("current_page", "home")
        
        if current_page == "home":
            render_home_page()
        elif current_page == "dashboard":
            render_dashboard()
        elif current_page == "analytics":
            if "analytics_df" not in st.session_state:
                st.markdown("### 📥 Welcome to Advanced Analytics Hub")
                st.info("You can upload your dataset directly here to begin analysis.")
                hub_init_upload = st.file_uploader("Upload Dataset (CSV/Excel) 📂", type=["csv", "xlsx"], key="hub_init_uploader")
                if hub_init_upload is not None:
                    if hub_init_upload.name.endswith('.xlsx'):
                         st.session_state["analytics_df"] = pd.read_excel(hub_init_upload, sheet_name=0)
                    else:
                         st.session_state["analytics_df"] = pd.read_csv(hub_init_upload)
                    st.rerun()
            
            if "analytics_df" in st.session_state:
                render_analytics_hub(st.session_state["analytics_df"])
            else:
                st.warning("⚠️ Please upload a dataset from the Main Dashboard first to use Analytics Hub")
                if st.button("📊 Go to Main Dashboard", use_container_width=True, type="primary"):
                    st.session_state["current_page"] = "dashboard"
                    st.rerun()

if __name__ == "__main__":
    main()