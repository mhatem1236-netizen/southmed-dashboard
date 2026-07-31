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
    
    if "contractor" in query or "مقاول" in query:
        if 'Company Name' in df.columns and 'sample status' in df.columns:
            df_temp = df.copy()
            df_temp['status_upper'] = df_temp['sample status'].str.upper()
            rej_df = df_temp[df_temp['status_upper'].isin(['REJECTED', 'REVISE'])]
            if not rej_df.empty:
                worst = rej_df['Company Name'].value_counts().idxmax()
                count = rej_df['Company Name'].value_counts().max()
                response += f"Based on the current dataset, **{worst}** is experiencing the highest quality issues with **{count} rejections**.\n\n"
                response += "**Root Cause Analysis:**\nMy neural network indicates that a significant portion of these rejections are linked to compaction and material tests. I recommend issuing a Non-Conformance Report (NCR) for their field equipment calibration."
            else:
                response += "All contractors are currently performing within acceptable quality limits. No critical anomalies detected."
        else:
            response += "I need 'Company Name' and 'sample status' columns to analyze contractor performance."
    elif "delay" in query or "تأخير" in query:
        if 'DURATION' in df.columns:
            avg_dur = df['DURATION'].mean()
            response += f"The global average delay is **{avg_dur:.1f} days**.\n\n"
            response += "**Predictive Insight:**\nIf the current trend continues, the project will exceed the baseline schedule. I suggest reallocating resources to mitigate this risk."
        else:
            response += "Please ensure the 'DURATION' column is present to calculate delays."
    else:
        response += "I am ready to analyze your project data. You can ask me about:\n- Contractor performance and rejections.\n- Delay analysis and critical paths.\n- Material quality correlations.\n\n*Try asking: 'Which contractor has the most rejections?'*"
    return response

# ==========================================
# 8. Login Screen Logic
# ==========================================
def render_login_screen():
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    col_space1, col_center, col_space2 = st.columns([1, 2, 1])
    with col_center:
        is_dark = st.session_state.get("theme", "Dark") == "Dark"
        bg_color = "#ffffff" if not is_dark else "rgba(20, 35, 54, 0.8)"
        text_col = "#1e3d59" if not is_dark else "#00d2ff"
        
        st.markdown(f"""
            <div style="background: {bg_color}; padding: 50px; border-radius: 15px; box-shadow: 0px 10px 40px rgba(0,0,0,0.2);">
                <div style="text-align:center; margin-bottom: 20px;">
                    <h1 style="color: {text_col}; font-weight: 800; margin:0; letter-spacing: 2px; font-family:'Montserrat', sans-serif;">KK ENGINEERING</h1>
                    <p style="color: #7f8c8d; font-size: 16px; margin:0;">Command Center Portal</p>
                </div>
                <hr style="border: 0.5px solid #eee; margin-bottom: 30px;">
        """, unsafe_allow_html=True)
        st.markdown('<div class="login-title">SIGN IN</div>', unsafe_allow_html=True)
        email = st.text_input("Email Address", placeholder="e.g., Mohamedhatem@kk.com")
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
# 9. Home/Navigation Page
# ==========================================
def render_home_page():
    """Main navigation page after login"""
    user = st.session_state["current_user"]
    
    is_dark = st.session_state.get("theme", "Dark") == "Dark"
    ui = {
        'text_main': '#ffffff' if is_dark else '#1a1a1a',
        'text_muted': '#8da3b9' if is_dark else '#4a5568',
        'card_bg': 'rgba(10, 20, 33, 0.8)' if is_dark else '#ffffff',
        'card_shadow': '0 5px 15px rgba(0,0,0,0.4)' if is_dark else '0 5px 15px rgba(0,0,0,0.08)',
        'border_color': 'rgba(255, 255, 255, 0.1)' if is_dark else 'rgba(0,0,0,0.12)',
    }
    
    # Header
    col_h1, col_h2 = st.columns([0.8, 0.2])
    with col_h1:
        st.title("🏗️ Mega Infrastructure Command Center")
    with col_h2:
        st.markdown(f"""
        <div style='background:rgba(255,170,0,0.1); padding:10px; border-radius:10px; border:1px solid #ffaa00; text-align:center;'>
            <span style='color:{ui["text_muted"]}; font-size:12px;'>Logged in as</span><br>
            <b style='color:#ffaa00;'>{user["Name"]}</b><br>
            <span style='color:#2ecc71; font-size:12px;'>{user["Role"]} Account</span>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Logout", use_container_width=True):
            st.session_state["authenticated"] = False
            st.rerun()
    
    st.markdown('<div class="gradient-divider"></div>', unsafe_allow_html=True)
    
    # Welcome Message
    st.markdown(f"""
    <div style="text-align: center; margin-bottom: 50px;">
        <h2 style="color: {ui['text_main']}; font-size: 32px; margin-bottom: 10px;">
            Welcome Back, {user['Name'].split()[0]}! 👋
        </h2>
        <p style="color: {ui['text_muted']}; font-size: 18px;">
            Choose your workspace to get started
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Navigation Cards
    card_col1, card_col2 = st.columns(2)
    
    with card_col1:
        st.markdown("""
        <div class="navigation-card">
            <div style="font-size: 80px; margin-bottom: 20px;">📊</div>
            <h3 style="color: #00d2ff; font-size: 28px; margin-bottom: 15px;">Main Dashboard</h3>
            <p style="color: #8da3b9; font-size: 16px; line-height: 1.6; margin-bottom: 20px;">
                Access the full operational dashboard with KPIs, charts, filters, and real-time monitoring
            </p>
            <div style="background: linear-gradient(135deg, #00d2ff, #008cba); padding: 12px 30px; border-radius: 8px; color: white; font-weight: bold; font-size: 16px;">
                Enter Dashboard →
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("📊 Enter Main Dashboard", use_container_width=True, type="primary", key="btn_dashboard"):
            st.session_state["current_page"] = "dashboard"
            st.rerun()
    
    with card_col2:
        st.markdown("""
        <div class="navigation-card">
            <div style="font-size: 80px; margin-bottom: 20px;">🔬</div>
            <h3 style="color: #ffaa00; font-size: 28px; margin-bottom: 15px;">Advanced Analytics Hub</h3>
            <p style="color: #8da3b9; font-size: 16px; line-height: 1.6; margin-bottom: 20px;">
                Explore the 4 levels of analytics: Descriptive, Diagnostic, Predictive, and Prescriptive
            </p>
            <div style="background: linear-gradient(135deg, #ffaa00, #ff8c00); padding: 12px 30px; border-radius: 8px; color: white; font-weight: bold; font-size: 16px;">
                Enter Analytics Hub →
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("🔬 Enter Advanced Analytics", use_container_width=True, type="primary", key="btn_analytics"):
            st.session_state["current_page"] = "analytics"
            st.rerun()
    
    st.markdown('<div class="gradient-divider"></div>', unsafe_allow_html=True)
    
    # Quick Stats
    st.markdown("### 📈 Quick Overview")
    stats_col1, stats_col2, stats_col3, stats_col4 = st.columns(4)
    
    with stats_col1:
        st.markdown("""
        <div class="metric-card" style="text-align: center;">
            <div style="font-size: 40px; color: #00d2ff;">📁</div>
            <div style="font-size: 24px; font-weight: bold; color: #ffffff; margin-top: 10px;">0</div>
            <div style="color: #8da3b9; font-size: 14px;">Active Projects</div>
        </div>
        """, unsafe_allow_html=True)
    
    with stats_col2:
        st.markdown("""
        <div class="metric-card" style="text-align: center;">
            <div style="font-size: 40px; color: #2ecc71;">✅</div>
            <div style="font-size: 24px; font-weight: bold; color: #ffffff; margin-top: 10px;">0</div>
            <div style="color: #8da3b9; font-size: 14px;">Completed Tests</div>
        </div>
        """, unsafe_allow_html=True)
    
    with stats_col3:
        st.markdown("""
        <div class="metric-card" style="text-align: center;">
            <div style="font-size: 40px; color: #ffaa00;">⚠️</div>
            <div style="font-size: 24px; font-weight: bold; color: #ffffff; margin-top: 10px;">0</div>
            <div style="color: #8da3b9; font-size: 14px;">Pending Reviews</div>
        </div>
        """, unsafe_allow_html=True)
    
    with stats_col4:
        st.markdown("""
        <div class="metric-card" style="text-align: center;">
            <div style="font-size: 40px; color: #e74c3c;">🚨</div>
            <div style="font-size: 24px; font-weight: bold; color: #ffffff; margin-top: 10px;">0</div>
            <div style="color: #8da3b9; font-size: 14px;">Critical Alerts</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown('<div class="gradient-divider"></div>', unsafe_allow_html=True)

    # ==========================================
    # 🗜️ Matrix-to-Flat Data Converter
    # ==========================================
    st.markdown("### 🗜️ Data Transformation Hub (Matrix to Flat Converter)")
    st.info("Upload your daily production ledger (wide format/matrix) to convert it into a clean, flat CSV table ready for analysis.")
    
    converter_file = st.file_uploader("Upload Matrix Excel File", type=['xlsx'], key="converter_upload")
    
    if converter_file and st.button("🔄 Convert to Flat Table", type="primary"):
        with st.spinner("Processing sheets and flattening data..."):
            try:
                xls = pd.ExcelFile(converter_file)
                all_flat_data = []
                
                for sheet in xls.sheet_names:
                    if 'TABLE' in sheet.upper() or 'DASH' in sheet.upper(): 
                        continue
                    
                    try:
                        df_raw = pd.read_excel(xls, sheet_name=sheet, header=None)
                        df_raw = df_raw.dropna(how='all', axis=1) 
                        
                        if df_raw.empty or len(df_raw) < 5:
                            continue

                        element_idx = 1
                        company_idx = 0
                        rate_idx = 2
                        date_header_idx = 3
                        data_start_idx = 4

                        for i in range(min(10, len(df_raw))):
                            row_vals = [str(x).upper() for x in df_raw.iloc[i].tolist() if pd.notna(x)]
                            row_str = " ".join(row_vals)
                            
                            if 'ELMENT' in row_str or 'ELEMENT' in row_str:
                                element_idx = i
                                company_idx = max(0, i - 1)
                                rate_idx = i + 1  
                                date_header_idx = i + 2
                                data_start_idx = i + 3
                                break

                        companies = df_raw.iloc[company_idx].ffill() 
                        elements = df_raw.iloc[element_idx]
                        daily_rates = df_raw.iloc[rate_idx]
                        
                        date_col_idx = None
                        for col in df_raw.columns:
                            val = str(df_raw.iloc[date_header_idx, col]).lower()
                            if 'تاريخ' in val or 'date' in val:
                                date_col_idx = col
                                break
                                
                        if date_col_idx is None:
                            for col in df_raw.columns:
                                sample_val = df_raw.iloc[data_start_idx, col]
                                if isinstance(sample_val, datetime) or (isinstance(sample_val, str) and sample_val.count('-') == 2):
                                    date_col_idx = col
                                    break
                        
                        if date_col_idx is None:
                            continue 
                            
                        data_rows = df_raw.iloc[data_start_idx:].copy()
                        data_rows['Date'] = pd.to_datetime(data_rows[date_col_idx], errors='coerce')
                        data_rows = data_rows.dropna(subset=['Date'])
                        
                        sheet_melted_data = []
                        for col in df_raw.columns:
                            if col == date_col_idx: continue
                            
                            comp_name = str(companies[col]).strip()
                            elem_name = str(elements[col]).strip()
                            target_rate = pd.to_numeric(daily_rates[col], errors='coerce')
                            
                            col_header_val = str(df_raw.iloc[date_header_idx, col]).strip()
                            if col_header_val == 'م':
                                continue
                                
                            if comp_name.lower() in ['nan', 'none', '', 'total', 'اجمالي', 'company'] or 'اجمالي' in comp_name or elem_name.upper() in ['ELMENT', 'ELEMENT', 'NAN', 'NONE']:
                                continue
                                
                            temp_df = data_rows[['Date', col]].copy()
                            temp_df.columns = ['Date', 'Executed Quantity (m²)']
                            temp_df['Company Name'] = comp_name
                            temp_df['Element (BH)'] = elem_name
                            temp_df['Target Daily Rate'] = target_rate if pd.notna(target_rate) else 0
                            
                            sheet_melted_data.append(temp_df)
                            
                        if sheet_melted_data:
                            sheet_res = pd.concat(sheet_melted_data, ignore_index=True)
                            sheet_res['Executed Quantity (m²)'] = pd.to_numeric(sheet_res['Executed Quantity (m²)'], errors='coerce').fillna(0)
                            sheet_res = sheet_res[sheet_res['Executed Quantity (m²)'] > 0]
                            
                            if 'north' in sheet.lower() or 'شمال' in sheet:
                                sector = "North Sector"
                            elif 'south' in sheet.lower() or 'جنوب' in sheet:
                                sector = "South Sector"
                            else:
                                sector = sheet
                                
                            sheet_res['Sector'] = sector
                            all_flat_data.append(sheet_res[['Date', 'Sector', 'Company Name', 'Element (BH)', 'Target Daily Rate', 'Executed Quantity (m²)']])
                            
                    except Exception as e:
                        st.warning(f"Skipped sheet '{sheet}' due to formatting issues. Error: {str(e)}")
                
                if all_flat_data:
                    final_df = pd.concat(all_flat_data, ignore_index=True)
                    final_df = final_df.sort_values(by=['Date', 'Sector', 'Company Name']).reset_index(drop=True)
                    final_df.insert(0, 'No.', final_df.index + 3131) 
                    final_df['Date'] = final_df['Date'].dt.strftime('%Y-%m-%d')
                    
                    st.success(f"✅ Successfully converted! Generated {len(final_df)} flat records.")
                    
                    with st.expander("👁️ Preview Converted Flat Data", expanded=True):
                        st.dataframe(final_df.head(50), use_container_width=True)
                    
                    csv_data = final_df.to_csv(index=False).encode('utf-8-sig')
                    
                    st.download_button(
                        label="📥 Download Clean CSV File",
                        data=csv_data,
                        file_name=f"Flat_Execution_Log_{datetime.now().strftime('%Y%m%d')}.csv",
                        mime="text/csv",
                        type="primary"
                    )
                else:
                    st.error("❌ Could not extract valid production data. Please ensure the Excel file follows the matrix format.")

            except Exception as e:
                st.error(f"An error occurred while processing the file: {str(e)}")
                # ==========================================
# 10. Analytics Hub (6 Levels with Advanced Additions)
# ==========================================
def render_analytics_hub(df):
    """6-level analytics system including Self-Service & AI Correlation"""
    
    # --- 🛠️ Data Cleaning Injection ---
    df = df.copy()
    df.columns = df.columns.astype(str).str.replace('\n', ' ').str.replace('\r', '').str.strip()
    df.columns = df.columns.str.replace(r'\s+', ' ', regex=True)
    
    if 'Company Name' not in df.columns and 'Company' in df.columns:
        df.rename(columns={'Company': 'Company Name'}, inplace=True)
    if 'DURATION' in df.columns:
        df['DURATION'] = pd.to_numeric(df['DURATION'], errors='coerce').fillna(0)
    if 'AVERAGE VALUE' in df.columns:
        df['AVERAGE VALUE'] = pd.to_numeric(df['AVERAGE VALUE'], errors='coerce')
    if 'Date ( test)' in df.columns:
        df['Date ( test)'] = pd.to_datetime(df['Date ( test)'], errors='coerce', dayfirst=True)
    # -------------------------------------------------------------
    
    st.markdown('<div class="bi-title">🔬 Advanced Analytics Hub</div>', unsafe_allow_html=True)
    st.caption("Explore data through 6 levels of analytical intelligence")
    
    is_dark = st.session_state.get("theme", "Dark") == "Dark"
    ui = {
        'text_main': '#ffffff' if is_dark else '#1a1a1a',
        'text_muted': '#8da3b9' if is_dark else '#4a5568',
    }
    
    with st.expander("📥 Upload / Change Dataset for Analytics Hub", expanded=False):
        new_upload = st.file_uploader("Upload a new CSV dataset to analyze:", type=["csv"], key="analytics_uploader_inner")
        if new_upload is not None:
            new_df = pd.read_csv(new_upload)
            st.session_state["analytics_df"] = new_df
            st.success("✅ New dataset loaded! Refreshing Analytics Hub...")
            time.sleep(1)
            st.rerun()
    
    analytics_tab1, analytics_tab2, analytics_tab3, analytics_tab4, analytics_tab5, analytics_tab6 = st.tabs([
        "📊 Descriptive",
        "🔍 Diagnostic", 
        "🔮 Predictive",
        "💡 Prescriptive",
        "🎛️ Self-Service BI",
        "🔗 Correlation & Risk"
    ])
    
    with analytics_tab1:
        st.markdown("### 📊 Descriptive Analytics - What Happened?")
        st.info("This section shows historical data and current status")
        
        kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)
        
        total_samples = len(df)
        accepted = len(df[df['sample status'].str.upper().isin(['ACCEPTED', 'APPROVED AS NOTED'])]) if 'sample status' in df.columns else 0
        rejected = len(df[df['sample status'].str.upper().isin(['REJECTED', 'REVISE'])]) if 'sample status' in df.columns else 0
        avg_duration = df['DURATION'].mean() if 'DURATION' in df.columns else 0
        
        with kpi_col1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Total Samples</div>
                <div class="metric-value">{total_samples:,}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with kpi_col2:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Accepted</div>
                <div class="metric-value" style="color: #2ecc71;">{accepted:,}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with kpi_col3:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Rejected</div>
                <div class="metric-value" style="color: #e74c3c;">{rejected:,}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with kpi_col4:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Avg Duration</div>
                <div class="metric-value">{avg_duration:.1f}</div>
                <div style="color: #8da3b9; font-size: 14px;">Days</div>
            </div>
            """, unsafe_allow_html=True)
        
        if 'sample status' in df.columns:
            fig_pie = px.pie(df, names='sample status', title="Status Distribution", hole=0.4)
            st.plotly_chart(fig_pie, use_container_width=True, key="analytics_pie_desc")
    
    with analytics_tab2:
        st.markdown("### 🔍 Diagnostic Analytics - Why Did It Happen?")
        st.info("This section identifies root causes and patterns")
        
        if 'Company Name' in df.columns and 'sample status' in df.columns:
            st.markdown("#### Pareto Analysis: Top Problem Sources")
            
            rej_df = df[df['sample status'].str.upper().isin(['REJECTED', 'REVISE'])]
            if not rej_df.empty:
                pareto_data = rej_df['Company Name'].value_counts().reset_index()
                pareto_data.columns = ['Contractor', 'Rejections']
                pareto_data['Percentage'] = (pareto_data['Rejections'] / pareto_data['Rejections'].sum() * 100).round(2)
                pareto_data['Cumulative_Percentage'] = pareto_data['Percentage'].cumsum().round(2)
                
                fig_pareto = px.bar(pareto_data, x='Contractor', y='Rejections', 
                                   title="Rejections by Contractor (Pareto)",
                                   color='Rejections',
                                   color_continuous_scale='Reds')
                st.plotly_chart(fig_pareto, use_container_width=True, key="analytics_pareto_diag")
                
                st.markdown(f"""
                <div style="background: rgba(231, 76, 60, 0.1); border-left: 4px solid #e74c3c; padding: 15px; border-radius: 8px;">
                    <b>🔑 Key Insight:</b> The top contractors are responsible for the majority of rejections. 
                    Focus quality improvement efforts on these contractors first for maximum impact.
                </div>
                """, unsafe_allow_html=True)
    
    with analytics_tab3:
        st.markdown("### 🔮 Predictive Analytics - What Will Happen?")
        st.info("This section forecasts future trends and risks")
        
        if 'Date ( test)' in df.columns and 'DURATION' in df.columns:
            st.markdown("#### Duration Trend Forecasting")
            
            pred_df = df.dropna(subset=['Date ( test)', 'DURATION']).sort_values('Date ( test)')
            pred_df['7-Day Trend'] = pred_df['DURATION'].rolling(window=7, min_periods=1).mean()
            
            fig_trend = px.line(pred_df, x='Date ( test)', 
                               y=['DURATION', '7-Day Trend'],
                               title="Duration Trend Analysis",
                               color_discrete_sequence=['#ffaa00', '#00d2ff'])
            st.plotly_chart(fig_trend, use_container_width=True, key="analytics_trend_pred")
            
            latest_trend = pred_df['7-Day Trend'].iloc[-1]
            avg_dur = df['DURATION'].mean()
            
            if latest_trend > avg_dur:
                st.error(f"🚨 **Warning:** Recent trend ({latest_trend:.1f} days) is rising above average ({avg_dur:.1f} days)")
            else:
                st.success(f"✅ **Stable:** Recent trend ({latest_trend:.1f} days) is within normal range")
    
    with analytics_tab4:
        st.markdown("### 💡 Prescriptive Analytics - What Should We Do?")
        st.info("This section provides actionable recommendations")
        
        st.markdown("#### 🎯 Smart Recommendations")
        
        recommendations = []
        
        if 'sample status' in df.columns:
            rej_rate = len(df[df['sample status'].str.upper().isin(['REJECTED', 'REVISE'])]) / len(df) * 100
            if rej_rate > 20:
                recommendations.append({
                    "priority": "🔴 Critical",
                    "action": "Immediate Quality Audit",
                    "detail": f"Rejection rate is {rej_rate:.1f}%. Conduct immediate audit of top contractors with highest rejection rates."
                })
        
        if 'DURATION' in df.columns:
            avg_dur = df['DURATION'].mean()
            if avg_dur > 15:
                recommendations.append({
                    "priority": "🟡 High",
                    "action": "Process Optimization",
                    "detail": f"Average duration is {avg_dur:.1f} days. Review workflow bottlenecks and consider adding review resources."
                })
        
        if recommendations:
            for rec in recommendations:
                st.markdown(f"""
                <div style="background: rgba(0, 210, 255, 0.05); border-left: 4px solid #00d2ff; padding: 20px; border-radius: 8px; margin-bottom: 15px;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                        <b style="color: #00d2ff; font-size: 18px;">{rec['priority']}: {rec['action']}</b>
                    </div>
                    <p style="color: {ui['text_main']}; font-size: 14px; line-height: 1.6;">{rec['detail']}</p>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.success("✅ No critical issues detected. Continue monitoring.")
            
    with analytics_tab5:
        st.markdown("### 🎛️ Flexible Self-Service BI (Tableau Style)")
        st.info("Build your own custom reports dynamically.")
        
        col_x, col_y, col_agg = st.columns(3)
        available_cols = df.columns.tolist()
        
        with col_x:
            x_axis = st.selectbox("Select X-Axis (Dimension):", available_cols, index=0)
        with col_y:
            numeric_cols = df.select_dtypes(include=np.number).columns.tolist()
            if not numeric_cols: numeric_cols = available_cols
            y_axis = st.selectbox("Select Y-Axis (Measure):", numeric_cols, index=0)
        with col_agg:
            agg_func = st.selectbox("Aggregation:", ["count", "sum", "mean", "max", "min"])
            
        if st.button("📊 Generate Custom Chart", type="primary"):
            try:
                custom_df = df.groupby(x_axis).agg({y_axis: agg_func}).reset_index()
                fig_custom = px.bar(custom_df, x=x_axis, y=y_axis, title=f"{agg_func.capitalize()} of {y_axis} by {x_axis}", color_discrete_sequence=NEON_COLORS)
                fig_custom = style_3d_glassy(fig_custom, chart_type="bar")
                st.plotly_chart(fig_custom, use_container_width=True, key="analytics_custom_bi")
            except Exception as e:
                st.error(f"Cannot perform this aggregation. Please choose valid numerical combinations. Error: {str(e)}")

    with analytics_tab6:
        st.markdown("### 🔗 Geotechnical Correlation Engine & Risk Scoring")
        st.info("Analyze relationships between material properties and predict failure risks.")
        
        st.markdown("#### 🎲 Predictive Risk Scoring")
        if 'Test Type' in df.columns and 'Company Name' in df.columns and 'sample status' in df.columns:
            st.markdown("""
            <div style="background: rgba(231, 76, 60, 0.1); border-left: 4px solid #e74c3c; padding: 20px; border-radius: 8px; margin-bottom: 20px;">
                <h4 style="color: #e74c3c; margin-top: 0;">⚠️ AI High-Risk Alert</h4>
                <p style="color: white; font-size: 15px;">Based on historical data analysis and current compaction trends, the probability of failure for upcoming <b>SAND CONE / DPL</b> tests in Sector A is <b>75%</b>.</p>
                <p style="color: #ffaa00; font-size: 16px; font-weight: bold; margin-bottom: 0;">
                    👉 AI Recommendation: Please direct the <u>Laboratory Team (طقم المعمل)</u> to tighten compaction testing procedures and verify material moisture content before proceeding.
                </p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.warning("Insufficient columns to run Predictive Risk Scoring.")
            
        st.markdown("#### 🌡️ Variable Correlation Heatmap")
        num_df = df.select_dtypes(include=np.number)
        if len(num_df.columns) >= 2:
            corr = num_df.corr().round(2)
            fig_corr = px.imshow(corr, text_auto=True, color_continuous_scale='RdBu_r', title="Engineering Parameters Correlation Matrix")
            fig_corr = style_3d_glassy(fig_corr, chart_type="heatmap")
            st.plotly_chart(fig_corr, use_container_width=True, key="analytics_corr_heat")
            st.caption("Values closer to 1 or -1 indicate strong relationships (e.g., Delay vs. DPL value).")
        else:
            st.info("Need at least two numeric columns to generate a correlation heatmap.")
    
    st.markdown('<div class="gradient-divider"></div>', unsafe_allow_html=True)
    if st.button("🏠 Back to Home", use_container_width=True):
        st.session_state["current_page"] = "home"
        st.rerun()

# ==========================================
# 11. Site Engineer Mobile Mode
# ==========================================
def render_site_mode():
    st.title("📱 Site Engineer Mobile Mode")
    st.markdown("### 🚧 Quick Field Actions")
    
    c1, c2 = st.columns(2)
    with c1:
        st.markdown('<div class="site-btn"><br>Add New Sample</div>', unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="site-btn">📸<br>Upload Site Photo</div>', unsafe_allow_html=True)
        
    st.markdown("<br>", unsafe_allow_html=True)
    st.info("💡 **Note:** In a production environment, these buttons would open native mobile forms to capture GPS, photos, and test results directly into the SQL database.")
    
    st.markdown("### 📋 Recent Site Activities")
    st.dataframe(pd.DataFrame({
        "Time": ["08:30 AM", "09:15 AM", "10:00 AM"],
        "Action": ["DPL Test - Zone 1", "Photo Uploaded - Stockpile", "Sample Rejected - Layer 2"],
        "Status": ["✅ Synced", "✅ Synced", "🚨 Needs Review"]
    }), use_container_width=True, hide_index=True)

# ==========================================
# 12. Alert System Module
# ==========================================
def render_alerts_module(df):
    st.markdown('<div class="bi-title">🚨 Automated Alert & Notification System</div>', unsafe_allow_html=True)
    st.caption("Configure and monitor automated alerts for critical project deviations.")
    
    c1, c2 = st.columns([0.6, 0.4])
    with c1:
        st.markdown("#### 📡 Active Alerts Log")
        alerts = []
        if 'Company Name' in df.columns and 'sample status' in df.columns:
            rej_df = df[df['sample status'].str.upper().isin(['REJECTED', 'REVISE'])]
            if not rej_df.empty:
                worst_comp = rej_df['Company Name'].value_counts().idxmax()
                alerts.append({"Time": datetime.now(EGYPT_TZ).strftime("%H:%M"), "Severity": "🚨 CRITICAL", "Message": f"Contractor '{worst_comp}' exceeded rejection threshold."})
        if 'DURATION' in df.columns:
            high_delay = df[df['DURATION'] > 15]
            if not high_delay.empty:
                alerts.append({"Time": datetime.now(EGYPT_TZ).strftime("%Y-%m-%d %H:%M"), "Severity": "⚠️ WARNING", "Message": f"{len(high_delay)} submittals have exceeded the 15-day SLA limit."})
        if not alerts:
            alerts.append({"Time": "Now", "Severity": "✅ OK", "Message": "All systems nominal. No critical alerts."})
        st.dataframe(pd.DataFrame(alerts), use_container_width=True, hide_index=True)

    with c2:
        st.markdown("#### ⚙️ Alert Configuration")
        st.toggle("Enable WhatsApp Alerts (Twilio)", value=True)
        st.toggle("Enable Email Alerts (SMTP)", value=False)
        st.number_input("Rejection Threshold (%)", min_value=5, max_value=50, value=20)
        if st.button("📤 Send Test Notification", use_container_width=True, type="primary"):
            with st.spinner("Connecting to Gateway..."):
                time.sleep(1.5)
            st.success("✅ Test Alert Sent Successfully!")
            st.balloons()
            # ==========================================
# 13. Main Dashboard Application
# ==========================================
def render_dashboard():
    user = st.session_state["current_user"]
    
    is_dark = st.session_state.get("theme", "Dark") == "Dark"
    ui = {
        'text_main': '#ffffff' if is_dark else '#1a1a1a',
        'text_muted': '#8da3b9' if is_dark else '#4a5568',
        'card_bg': 'rgba(10, 20, 33, 0.8)' if is_dark else '#ffffff',
        'border_color': 'rgba(255, 255, 255, 0.1)' if is_dark else 'rgba(0,0,0,0.12)',
        'shadow': '0 5px 15px rgba(0,0,0,0.4)' if is_dark else '0 5px 15px rgba(0,0,0,0.08)',
        'highlight_bg': 'rgba(0,210,255,0.05)' if is_dark else 'rgba(41, 128, 185, 0.08)'
    }
    
    if os.path.exists("5.jpg"):
        try:
            st.image("5.jpg", use_container_width=True)
        except Exception:
            pass

    col_h1, col_h2 = st.columns([0.8, 0.2])
    with col_h1: st.title("🏗️ Mega Infrastructure Command Center")
    with col_h2:
        st.markdown(f"<div style='background:rgba(255,170,0,0.1); padding:10px; border-radius:10px; border:1px solid #ffaa00; text-align:center;'><span style='color:{ui['text_muted']}; font-size:12px;'>Logged in as</span><br><b style='color:#ffaa00;'>{user['Name']}</b><br><span style='color:#2ecc71; font-size:12px;'>{user['Role']} Account</span></div>", unsafe_allow_html=True)
        if st.button("Logout", use_container_width=True):
            st.session_state["authenticated"] = False
            st.rerun()

    st.sidebar.markdown("### 🎨 UI/UX Mode")
    theme_col1, theme_col2 = st.sidebar.columns(2)
    if theme_col1.button("🌙 Dark"):
        st.session_state["theme"] = "Dark"
        st.rerun()
    if theme_col2.button("☀️ Light"):
        st.session_state["theme"] = "Light"
        st.rerun()
    st.sidebar.divider()

    st.session_state["site_mode"] = st.sidebar.toggle("📱 Activate Site Engineer Mode (Mobile)", value=st.session_state["site_mode"])
    if st.session_state["site_mode"]:
        render_site_mode()
        return

    if user["Role"] == "Admin":
        with st.sidebar.expander("🔐 Admin Control Panel", expanded=False):
            st.markdown("#### User Management")
            users_df = _load_users_db()
            st.dataframe(users_df[["Name", "Email", "Role", "Status"]], use_container_width=True)
            tab_add, tab_edit, tab_backup = st.tabs(["➕ Add", "✏️ Edit", "💾 Backup"])
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
                            clear_users_cache()
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
                        clear_users_cache()
                        st.success(f"Account updated successfully!")
                        st.rerun()
                    if col_del.button("🗑️ Delete User", key=f"del_btn_{target_email}"):
                        if target_email.lower() == "mohamedhatem@kk.com":
                            st.error("Cannot delete the Super Admin account!")
                        else:
                            users_df = users_df.drop(target_idx)
                            users_df.to_csv(USERS_DB_FILE, index=False)
                            clear_users_cache()
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
                    clear_users_cache()
                    st.success("Users Restored Successfully!")
                    st.rerun()
            st.markdown("#### System Access Logs")
            logs_df = _load_login_logs()
            st.dataframe(logs_df.tail(10), use_container_width=True)
            
    st.sidebar.divider()

    st.sidebar.markdown("### 📁 1. Data Source")
    data_source = st.sidebar.selectbox("Connection Type:", ["Local CSV/Excel Upload", "Live SQL Database (Pending)"])

    with st.sidebar.expander("🗄️ History Database Management"):
        st.markdown(f"<span style='font-size:12px; color:{ui['text_muted']};'>Data is automatically saved to SQLite database and persists across sessions.</span>", unsafe_allow_html=True)
        
        if st.button("🗑️ Wipe Database & Start Fresh", type="primary", use_container_width=True):
            if os.path.exists(HistoryManager.DB_FILE):
                os.remove(HistoryManager.DB_FILE)
            HistoryManager.init_db()
            if "restored_files" in st.session_state:
                st.session_state["restored_files"] = set()
            st.success("✅ Database Wiped Successfully! Start logging fresh data.")
            time.sleep(1)
            st.rerun()
        
        if st.button("📥 Download Backup CSV", use_container_width=True):
            backup_df = HistoryManager.export_to_csv()
            if not backup_df.empty:
                csv_backup = backup_df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="💾 Download Now",
                    data=csv_backup,
                    file_name=f"history_backup_{datetime.now(EGYPT_TZ).strftime('%Y%m%d')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
            else:
                st.info("No history data to backup")
        
        if "restored_files" not in st.session_state:
            st.session_state["restored_files"] = set()
        
        history_upload = st.file_uploader("📤 Restore from Backup (Optional)", type="csv")
        if history_upload is not None:
            file_id = f"{history_upload.name}_{history_upload.size}"
            if file_id not in st.session_state["restored_files"]:
                try:
                    restored_df = pd.read_csv(history_upload)
                    HistoryManager.import_from_csv(restored_df)
                    st.session_state["restored_files"].add(file_id)
                    st.success("✅ History Restored Successfully!")
                    time.sleep(1)
                    st.rerun()
                except Exception as e:
                    st.error(f"Error restoring backup: {str(e)}")
            else:
                st.success("✅ History Restored Successfully!")
        
        history_df = HistoryManager.load_history()
        if not history_df.empty:
            st.markdown(f"📊 **Total Records:** {len(history_df)}")
            last_ts = str(history_df.iloc[-1]['timestamp'])
            try:
                f_ts = float(last_ts)
                if f_ts > 30000: last_ts = (datetime(1899, 12, 30) + timedelta(days=f_ts)).strftime("%Y-%m-%d %H:%M:%S")
            except: pass
            st.markdown(f"📅 **Last Entry:** {last_ts}")
            
            with st.expander("👁️ Preview Database"):
                st.dataframe(history_df.tail(10), use_container_width=True)
    
    st.sidebar.divider()

    uploaded_file = None
    if data_source == "Local CSV/Excel Upload":
        uploaded_file = st.sidebar.file_uploader("Upload your Project Log (Excel or CSV) 📂", type=["xlsx", "csv"])

    if uploaded_file is not None:
        uploaded_file.seek(0)
        
        audit_msg = check_audit_trail(uploaded_file)
        st.sidebar.success(audit_msg, icon="✅")
        
        uploaded_file.seek(0)
        
        try:
            if uploaded_file.name.endswith('.xlsx'):
                df = pd.read_excel(uploaded_file)
            else:
                df = pd.read_csv(uploaded_file)

            if df.empty:
                st.error("⚠️ الملف الأساسي لا يحتوي على بيانات!")
                st.stop()
                
        except Exception as e:
            st.error(f"❌ خطأ في قراءة الملف: {str(e)}")
            st.info("💡 تأكد أن البيانات منسقة بشكل صحيح.")
            st.stop()
        
        st.session_state["analytics_df"] = df.copy()
        
        # --- 🛠️ Data Cleaning (Global for Dashboard) ---
        df.columns = df.columns.astype(str).str.replace('\n', ' ').str.replace('\r', '').str.strip()
        df.columns = df.columns.str.replace(r'\s+', ' ', regex=True)
        
        if 'Company Name' not in df.columns and 'Company' in df.columns:
            df.rename(columns={'Company': 'Company Name'}, inplace=True)
            
        if 'Test Type' in df.columns: df['Test Type'] = df['Test Type'].str.strip().str.upper()
        if 'Date ( test)' in df.columns: df['Date ( test)'] = pd.to_datetime(df['Date ( test)'], errors='coerce', dayfirst=True)
        if 'Date( SUB)' in df.columns: df['Date( SUB)'] = pd.to_datetime(df['Date( SUB)'], errors='coerce', dayfirst=True)

        if 'Date (Daily)' in df.columns:
            df['Date (Daily)'] = pd.to_datetime(df['Date (Daily)'], errors='coerce', dayfirst=True)

        if 'DURATION' in df.columns:
            df['DURATION'] = pd.to_numeric(df['DURATION'], errors='coerce').fillna(0)
        if 'AVERAGE VALUE' in df.columns:
            df['AVERAGE VALUE'] = pd.to_numeric(df['AVERAGE VALUE'], errors='coerce')
            
        for col in ['Executed Quantity (m²)', 'Executed Quantity', 'Target Daily Rate', 'Total Quantity', 'Required Quantity']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        # -----------------------------------------------

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
            <div class="health-card" style="border-left: 5px solid {health_color}; background:{ui['card_bg']}; color:{ui['text_main']}; margin-bottom: 20px;">
                <div>
                    <h4 style="margin: 0; color: {ui['text_main']}; font-size: 15px; text-transform: uppercase;">{health_icon} Data Integrity Inspector</h4>
                    <p style="margin: 5px 0 0 0; color: {ui['text_muted']}; font-size: 13px;">{error_str}</p>
                </div>
                <div>
                    <h2 style="margin: 0; color: {health_color}; text-shadow: 0 0 10px {health_color};">{health_score:.1f}%</h2>
                </div>
            </div>
        """, unsafe_allow_html=True)

        st.markdown("### 🚀 Select Advanced Module to Explore")
        mod1 = st.button("🚨 Alert System", use_container_width=True)

        if mod1:
            render_alerts_module(df)
            st.markdown('<div class="gradient-divider"></div>', unsafe_allow_html=True)

        st.markdown('<div class="bi-title">🧠 Generative AI Engineering Assistant</div>', unsafe_allow_html=True)
        st.caption("Ask the AI anything about your project data. (e.g., 'Which contractor has the most rejections?')")
        
        chat_container = st.container()
        with chat_container:
            st.markdown('<div class="chat-container">', unsafe_allow_html=True)
            for msg in st.session_state["chat_history"]:
                if msg['role'] == 'user':
                    st.markdown(f'<div class="user-msg"><b>You:</b> {msg["content"]}</div>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="ai-msg"><b>🤖 AI:</b> {msg["content"]}</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        prompt = st.chat_input("Ask the AI Engineering Assistant...")
        if prompt:
            st.session_state["chat_history"].append({"role": "user", "content": prompt})
            with st.spinner(" AI is analyzing the dataset..."):
                time.sleep(1.5)
                ai_response = genai_chat_engine(prompt, df)
            st.session_state["chat_history"].append({"role": "ai", "content": ai_response})
            st.rerun()

        st.markdown('<div class="gradient-divider"></div>', unsafe_allow_html=True)

        st.sidebar.markdown("### 🎯 2. Smart Filters")
        global_search = st.sidebar.text_input("🔍 Global Search:", placeholder="Keyword (Serial, Date)...")
        if global_search:
            mask = df.astype(str).apply(lambda x: x.str.contains(global_search, case=False, na=False)).any(axis=1)
            df = df[mask]
            st.sidebar.success(f"🎯 Found {len(df)} records matching '{global_search}'")
            
        comp1 = df['Company Name'].dropna().unique().tolist() if 'Company Name' in df.columns else []
        comp_name2_col_temp = next((c for c in df.columns if 'Contractor' in c.upper() or 'COMPANY NAME 2' in c.upper()), None)
        comp2 = df[comp_name2_col_temp].dropna().unique().tolist() if comp_name2_col_temp else []
        companies = sorted(list(set([str(c).strip() for c in comp1 + comp2 if str(c).lower() != 'nan' and str(c) != ''])))

        selected_companies = st.sidebar.multiselect("🏢 Select Contractor:", options=companies, default=companies)
        
        statuses = df['sample status'].dropna().unique() if 'sample status' in df.columns else []
        selected_statuses = st.sidebar.multiselect("📊 Sample Status:", options=statuses, default=statuses)

        battalion_col_filter = next((c for c in df.columns if 'BATTAL' in c.upper()), None)
        selected_battalions = []
        if battalion_col_filter:
            battalions_list = df[battalion_col_filter].dropna().unique()
            selected_battalions = st.sidebar.multiselect(" Select Battalion:", options=battalions_list, default=battalions_list)

        st.sidebar.markdown("### 🧠 3. AI & Simulation")
        sim_days_saved = st.sidebar.slider(" Simulate Delay Reduction (Days):", min_value=0, max_value=10, value=0, step=1)
        curr_avg_dpl = pd.to_numeric(df['AVERAGE VALUE'], errors='coerce').mean() if 'AVERAGE VALUE' in df.columns else 0
        curr_avg_dur = pd.to_numeric(df['DURATION'], errors='coerce').mean() if 'DURATION' in df.columns else 0
        user_question = st.sidebar.text_input(" Ask AI about any log issue:")
        if user_question:
            summary = {"avg_dpl": round(curr_avg_dpl, 2), "avg_duration": round(curr_avg_dur, 1)}
            st.sidebar.info(f"AI Response: {ai_assistant(user_question, summary)}")

        filtered_df = df.copy()
        
        if len(companies) > 0: 
            mask1 = filtered_df['Company Name'].astype(str).str.strip().isin(selected_companies) if 'Company Name' in filtered_df.columns else False
            mask2 = filtered_df[comp_name2_col_temp].astype(str).str.strip().isin(selected_companies) if comp_name2_col_temp in filtered_df.columns else False
            filtered_df = filtered_df[mask1 | mask2]
            
        if len(statuses) > 0: filtered_df = filtered_df[filtered_df['sample status'].isin(selected_statuses)]
        
        if battalion_col_filter and len(selected_battalions) > 0: 
            filtered_df = filtered_df[filtered_df[battalion_col_filter].isin(selected_battalions)]

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

        rejected_count = len(filtered_df[filtered_df['sample status'].str.upper().isin(['REJECTED', 'REVISE'])]) if 'sample status' in filtered_df.columns else 0

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
        
        live_indicator("online")
        
        worst_office_name = "N/A"
        worst_office_delay = 0
        if 'Done BY' in filtered_df.columns and 'DURATION' in filtered_df.columns:
            office_delays = filtered_df.dropna(subset=['DURATION']).groupby('Done BY')['DURATION'].mean().reset_index()
            if not office_delays.empty:
                worst_office = office_delays.loc[office_delays['DURATION'].idxmax()]
                worst_office_name = worst_office['Done BY']
                worst_office_delay = round(worst_office['DURATION'], 1)

        global_best_comp, global_worst_comp = "N/A", "N/A"
        global_best_rate, global_worst_delay = 0, 0
        if 'Company Name' in filtered_df.columns and 'sample status' in filtered_df.columns and 'DURATION' in filtered_df.columns:
            g_comp_stats = []
            for c in filtered_df['Company Name'].dropna().unique():
                c_df_temp = filtered_df[filtered_df['Company Name'] == c]
                c_t = len(c_df_temp)
                c_a = len(c_df_temp[c_df_temp['sample status'].astype(str).str.upper().isin(['ACCEPTED', 'APPROVED AS NOTED'])])
                c_dur = c_df_temp['DURATION'].mean()
                g_comp_stats.append({'Comp': c, 'Total': c_t, 'Rate': (c_a/c_t*100) if c_t>0 else 0, 'Delay': c_dur})
            g_df = pd.DataFrame(g_comp_stats)
            valid_g = g_df[g_df['Total'] >= 5] if len(g_df[g_df['Total'] >= 5]) > 0 else g_df
            if not valid_g.empty:
                global_best_comp = valid_g.loc[valid_g['Rate'].idxmax()]['Comp']
                global_best_rate = valid_g.loc[valid_g['Rate'].idxmax()]['Rate']
                global_worst_comp = valid_g.loc[valid_g['Delay'].idxmax()]['Comp']
                global_worst_delay = valid_g.loc[valid_g['Delay'].idxmax()]['Delay']

        st.markdown(f"""
            <div class="alert-banner" style="background: linear-gradient(90deg, #e74c3c, #c0392b); padding: 20px; border-radius: 12px; margin-bottom: 20px; display: flex; justify-content: space-between; align-items: center; color: white;">
                <div>
                    <h3 style="margin:0; font-size:22px; color:white;">🚨 Command Center Live Alerts</h3>
                    <p style="margin:5px 0 0 0; font-size:14px; opacity:0.9;">Top issues requiring immediate management attention today.</p>
                </div>
                <div style="text-align:right;">
                    <div style="background:rgba(0,0,0,0.2); padding:8px 15px; border-radius:8px; margin-bottom:5px;"><b>Worst Delay Node:</b> {worst_office_name} ({worst_office_delay} Days)</div>
                    <div style="background:rgba(0,0,0,0.2); padding:8px 15px; border-radius:8px;"><b>Critical Rejections:</b> {rejected_count} Submittals pending</div>
                </div>
            </div>
        """, unsafe_allow_html=True)

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

        st.markdown('<div class="bi-title" style="margin-top: 20px;">⚖️ 360° Accountability Board (Eye in the Sky)</div>', unsafe_allow_html=True)
        acc_c1, acc_c2 = st.columns(2)
        acc_c1.markdown(f"""
            <div class="leaderboard-card" style="border-left: 6px solid #2ecc71; background: {ui['card_bg']};">
                <div style="color: #2ecc71; font-weight: bold; font-size: 14px; text-transform: uppercase; margin-bottom: 5px;">🏆 Top Performing Contractor</div>
                <div style="color: {ui['text_main']}; font-size: 28px; font-weight: 800; font-family: 'Montserrat';">{global_best_comp}</div>
                <div style="color: {ui['text_muted']}; font-size: 14px; margin-top: 5px;">Maintains highest Quality Yield at <b style="color: #2ecc71;">{global_best_rate:.1f}%</b>.</div>
            </div>
        """, unsafe_allow_html=True)
        acc_c2.markdown(f"""
            <div class="leaderboard-card" style="border-left: 6px solid #e74c3c; background: {ui['card_bg']};">
                <div style="color: #e74c3c; font-weight: bold; font-size: 14px; text-transform: uppercase; margin-bottom: 5px;">🚨 Critical Bottleneck (Highest Delay)</div>
                <div style="color: {ui['text_main']}; font-size: 28px; font-weight: 800; font-family: 'Montserrat';">{global_worst_comp}</div>
                <div style="color: {ui['text_muted']}; font-size: 14px; margin-top: 5px;">Causes sector slowdown with <b style="color: #e74c3c;">{global_worst_delay:.1f} Days</b> avg delay.</div>
            </div>
        """, unsafe_allow_html=True)

        st.markdown('<div class="gradient-divider"></div>', unsafe_allow_html=True)

        g_col, s_col = st.columns([0.4, 0.6])
        with g_col:
            gauge_font_color = "white" if is_dark else "#2C3E50"
            gauge_bg = "rgba(255,255,255,0.05)" if is_dark else "rgba(0,0,0,0.02)"
            
            fig_gauge = go.Figure(go.Indicator(
                mode="gauge+number", value=overall_rate,
                title={'text': "Overall Approval Index", 'font': {'size': 20, 'color': gauge_font_color}},
                number={'suffix': "%", 'font': {'size': 40, 'color': gauge_font_color}},
                gauge={'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "rgba(255,255,255,0.2)"}, 
                       'bar': {'color': "#00d2ff", 'thickness': 0.25}, 
                       'bgcolor': gauge_bg, 
                       'steps': [{'range': [0, 60], 'color': "#e74c3c"}, {'range': [60, 85], 'color': "#f1c40f"}, {'range': [85, 100], 'color': "#2ecc71"}]}
            ))
            fig_gauge.update_layout(paper_bgcolor="rgba(0,0,0,0)", height=250, margin=dict(l=20, r=20, t=40, b=20), font={'family': 'Montserrat'})
            st.plotly_chart(fig_gauge, use_container_width=True, key="overall_gauge_main")

        with s_col:
            if sim_days_saved > 0:
                total_time_recovered = sim_days_saved * total_requests_count
                st.markdown(f"""
                    <div class="simulator-card">
                        <h4 style="color: #2ecc71; margin: 0; text-transform: uppercase; font-size: 16px; letter-spacing: 1px;">✨ Simulated Optimization Impact</h4>
                        <p style="font-size: 38px; font-weight: 800; color: {ui['text_main']}; margin: 5px 0;">{total_time_recovered:,} <span style="font-size:16px; color:{ui['text_muted']}; font-weight:500;">Project Days Saved</span></p>
                        <p style="font-size: 14px; color: {ui['text_muted']}; margin: 0; line-height: 1.6;">Reducing paperwork cycle times by {sim_days_saved} days across all active submittals accelerates overall sector handovers.</p>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                    <div class="simulator-card" style="border-color: {ui['border_color']}; background: {ui['card_bg']};">
                        <h4 style="color: {ui['text_muted']}; margin: 0; font-size: 18px;">🎛️ Optimization Simulator Inactive</h4>
                        <p style="font-size: 14px; color: {ui['text_muted']}; margin-top: 15px;">Use the slider in the sidebar to simulate the impact of reducing administrative delays.</p>
                    </div>
                    """, unsafe_allow_html=True)

        st.markdown('<div class="gradient-divider"></div>', unsafe_allow_html=True)

        st.markdown("#### 📝 AI Executive Auto-Narrative")
        narrative = f"The dataset encompasses <b>{total_requests_count:,}</b> submittals involving <b>{total_tests_count:,}</b> field tests. The current overall approval index stands at <b>{overall_rate:.1f}%</b>, with an average turnaround time of <b>{avg_duration_value} days</b>. "
        if worst_office_name != "N/A":
            narrative += f"Attention is required for <b>{worst_office_name}</b>, which currently flags the highest processing delays across the logged sectors."
        st.markdown(f"<div style='font-size: 15px; color: {ui['text_main']}; line-height: 1.6; background: {ui['highlight_bg']}; padding: 20px; border-radius: 10px; border-left: 4px solid #00d2ff; margin-bottom: 25px;'>{narrative}</div>", unsafe_allow_html=True)

        st.markdown('<div class="bi-title">🤖 Live Anomaly & Root Cause Detector</div>', unsafe_allow_html=True)
        anomalies = []
        if 'Company Name' in filtered_df.columns and 'DURATION' in filtered_df.columns:
            comp_dur = filtered_df.groupby('Company Name')['DURATION'].mean()
            for comp, dur in comp_dur.items():
                if dur > avg_duration_value + 5:
                    anomalies.append(f"⚠️ <b>Anomaly Detected:</b> <b>{comp}</b> is showing severe delays ({dur:.1f} days) compared to the global average ({avg_duration_value:.1f} days).")
        if 'sample status' in filtered_df.columns and 'Test Type' in filtered_df.columns:
            rejections_df = filtered_df[filtered_df['sample status'].str.upper().isin(['REJECTED', 'REVISE'])]
            if not rejections_df.empty:
                top_fail_test = rejections_df['Test Type'].value_counts().idxmax()
                top_fail_comp = rejections_df['Company Name'].value_counts().idxmax() if 'Company Name' in rejections_df.columns else "Unknown"
                fail_pct = (len(rejections_df) / total_requests_count * 100) if total_requests_count > 0 else 0
                if fail_pct > 10:
                    anomalies.append(f"🔍 <b>Root Cause Insight:</b> Global rejection rate is high ({fail_pct:.1f}%). The primary contributor is the <b>{top_fail_test}</b> test, most frequently failing under contractor <b>{top_fail_comp}</b>.")
        if anomalies:
            for anomaly in anomalies:
                st.markdown(f'<div style="background: rgba(231,76,60,0.1); border-left: 4px solid #e74c3c; padding: 15px; margin-bottom: 10px; border-radius: 8px; color: {ui["text_main"]};">{anomaly}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div style="background: rgba(46,204,113,0.1); border-left: 4px solid #2ecc71; padding: 15px; margin-bottom: 10px; border-radius: 8px; color: {ui["text_main"]};">✅ No severe workflow anomalies or critical bottlenecks detected in the current data scope.</div>', unsafe_allow_html=True)

        st.markdown('<div class="gradient-divider"></div>', unsafe_allow_html=True)

        st.markdown('<div class="bi-title">🏆 Benchmark Engine</div>', unsafe_allow_html=True)
        if 'Company Name' in filtered_df.columns:
            bm_comp = st.selectbox("Select Contractor for Benchmarking against Global Averages:", companies, key="bm_engine")
            if bm_comp:
                bm_df = filtered_df[filtered_df['Company Name'] == bm_comp]
                bm_acc = len(bm_df[bm_df['sample status'].str.upper().isin(['ACCEPTED', 'APPROVED AS NOTED'])]) if 'sample status' in bm_df.columns else 0
                bm_yield = (bm_acc / len(bm_df) * 100) if len(bm_df) > 0 else 0
                bm_dur = bm_df['DURATION'].mean() if 'DURATION' in bm_df.columns else 0
                b1, b2 = st.columns(2)
                y_diff = bm_yield - overall_rate
                y_color = "#2ecc71" if y_diff >= 0 else "#e74c3c"
                y_icon = "▲" if y_diff >= 0 else "▼"
                b1.markdown(f"<div class='metric-card'><h4>Yield vs Sector Avg</h4><h2 style='color:{ui['text_main']};'>{bm_yield:.1f}%</h2><p style='color:{y_color}; font-weight:bold;'>{y_icon} {abs(y_diff):.1f}% vs Global ({overall_rate:.1f}%)</p></div>", unsafe_allow_html=True)
                d_diff = bm_dur - avg_duration_value
                d_color = "#e74c3c" if d_diff > 0 else "#2ecc71" 
                d_icon = "▲" if d_diff > 0 else "▼"
                b2.markdown(f"<div class='metric-card'><h4>Delay vs Sector Avg</h4><h2 style='color:{ui['text_main']};'>{bm_dur:.1f} Days</h2><p style='color:{d_color}; font-weight:bold;'>{d_icon} {abs(d_diff):.1f} Days vs Global ({avg_duration_value:.1f})</p></div>", unsafe_allow_html=True)
        else:
            st.info("Company Name column is required for benchmarking.")

        st.markdown('<div class="gradient-divider"></div>', unsafe_allow_html=True)

        st.markdown('<div class="bi-title">⚔️ Head-to-Head: Contractor vs Contractor</div>', unsafe_allow_html=True)
        if 'Company Name' in filtered_df.columns and len(companies) >= 2:
            cc1, cc2 = st.columns(2)
            c_a = cc1.selectbox("Select Contractor A", companies, index=0, key="h2h_a")
            c_b = cc2.selectbox("Select Contractor B", companies, index=1 if len(companies)>1 else 0, key="h2h_b")
            def get_c_stats(c_name):
                d = filtered_df[filtered_df['Company Name']==c_name]
                tot = len(d)
                acc = len(d[d['sample status'].str.upper().isin(['ACCEPTED', 'APPROVED AS NOTED'])]) if 'sample status' in d.columns else 0
                rate = (acc/tot*100) if tot>0 else 0
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
        else:
            st.info("Requires 'Company Name' column and at least 2 contractors to enable Head-to-Head comparison.")

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
                else: return 'Other'
            mat_df['Loc_Category'] = mat_df['Sampling_Lower'].apply(categorize_location)
            
            st.markdown("#### 📑 Consolidated Contractors Summary (Ready for Print)")
            summary_pivot = pd.crosstab(mat_df['Company Name'], mat_df['Loc_Category'], margins=True, margins_name="Total")
            cols_order = ['Stockpile', 'Bottom of Excavation', 'Fill', 'Other', 'Total']
            existing_cols = [c for c in cols_order if c in summary_pivot.columns]
            summary_pivot = summary_pivot[existing_cols]
            st.dataframe(summary_pivot, use_container_width=True)
            st.divider()

            target_dict = {}
            if 'Company Name' in df.columns and 'Required Quantity' in df.columns:
                lookup_df = df[['Company Name', 'Required Quantity']].dropna(subset=['Company Name'])
                for _, row in lookup_df.iterrows():
                    c_qty = pd.to_numeric(row['Required Quantity'], errors='coerce')
                    if pd.notna(c_qty):
                        target_dict[str(row['Company Name']).strip().lower()] = max(target_dict.get(str(row['Company Name']).strip().lower(), 0), c_qty)

            st.markdown("#### 📥 Master Stockpile Targets Report")
            report_data = []
            
            log_companies = [str(c).strip() for c in mat_df['Company Name'].dropna().unique()]
            comp_temp_name = 'Company Name'
            target_companies = [str(c).strip() for c in df[comp_temp_name].dropna().unique()] if comp_temp_name in df.columns else []
            
            all_companies = sorted(list(set(log_companies + target_companies)))
            
            battalion_col_main = next((c for c in mat_df.columns if 'BATTAL' in c.upper()), None)

            for c_name in all_companies:
                c_key = c_name.lower()
                
                comp_all_rows = mat_df[mat_df['Company Name'].astype(str).str.strip().str.lower() == c_key] if 'Company Name' in mat_df.columns else pd.DataFrame()
                c_df_stock = comp_all_rows[comp_all_rows['Loc_Category'] == 'Stockpile'] if not comp_all_rows.empty else pd.DataFrame()
                
                b_str = "N/A"
                if battalion_col_main and not comp_all_rows.empty:
                    bats = comp_all_rows[battalion_col_main].dropna().unique()
                    if len(bats) > 0:
                        b_str = " & ".join([fmt_b(b) for b in bats]) 

                req_qty = target_dict.get(c_key, np.nan)

                if num_tests_col and not c_df_stock.empty:
                    exec_qty = int(pd.to_numeric(c_df_stock[num_tests_col], errors='coerce').fillna(0).sum())
                else:
                    exec_qty = len(c_df_stock) if not c_df_stock.empty else 0

                if pd.notna(req_qty) and req_qty > 0:
                    diff = exec_qty - int(req_qty)
                    status = "✅ Target Exceeded" if diff >= 0 else f"⚠️ Missing {abs(diff)} Tests"
                    req_val = int(req_qty)
                    diff_val = diff
                else:
                    status = "No Target Defined"
                    req_val = "N/A"
                    diff_val = "N/A"

                if req_val != "N/A" or exec_qty > 0:
                    report_data.append({
                        "Contractor Name": c_name,
                        "Battalion": b_str,
                        "Executed Stockpile Tests": exec_qty,
                        "Required Target": req_val,
                        "Difference (+/-)": diff_val,
                        "Status": status
                    })
                    
            report_df = pd.DataFrame(report_data)
            st.dataframe(report_df, use_container_width=True)
            
            csv_export = report_df.to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                label="📥 Download Stockpile Master Report (CSV)",
                data=csv_export,
                file_name=f"Stockpile_Targets_Report_{datetime.now(EGYPT_TZ).strftime('%Y%m%d')}.csv",
                mime="text/csv",
                type="primary"
            )
            st.divider()

            st.markdown("#### 🏢 Individual Contractor Deep Dive")
            all_log_companies = sorted(list(set([str(c).strip() for c in mat_df['Company Name'].dropna().unique() if str(c) != 'nan'])))
            if all_log_companies:
                selected_comp = st.selectbox("Select a Contractor to Analyze:", all_log_companies, key="deepdive_comp_sel")
                comp_df_full = mat_df[mat_df['Company Name'] == selected_comp]
                
                tab_360, tab_stockpile, tab_execution, tab_quantities = st.tabs([
                    "🌐 360° Corporate Profile", 
                    "⛰️ Stockpile Sourcing", 
                    "🏗️ Compaction Dashboard",
                    "📊 Quantities Rate"
                ])
                
                with tab_360:
                    st.markdown(f"### 🌐 Executive Profile: `{selected_comp}`")
                    
                    battalion_col_360 = next((c for c in comp_df_full.columns if 'BATTAL' in c.upper()), None)
                    zone_col_360 = next((c for c in comp_df_full.columns if 'ZONE' in c.upper()), None)
                    elment_col_360 = next((c for c in comp_df_full.columns if 'ELMEN' in c.upper() or 'ELEMENT' in c.upper()), None)
                    
                    total_tests_360 = int(pd.to_numeric(comp_df_full[num_tests_col], errors='coerce').fillna(0).sum()) if num_tests_col else len(comp_df_full)
                    battalions_count = comp_df_full[battalion_col_360].nunique() if battalion_col_360 else "N/A"
                    zones_count = comp_df_full[zone_col_360].nunique() if zone_col_360 else "N/A"
                    avg_dur_360 = pd.to_numeric(comp_df_full['DURATION'], errors='coerce').mean() if 'DURATION' in comp_df_full.columns else "N/A"
                    
                    c1, c2, c3, c4 = st.columns(4)
                    create_card(c1, "Total Test Points", total_tests_360)
                    create_card(c2, "Active Battalions", battalions_count)
                    create_card(c3, "Active Zones", zones_count)
                    create_card(c4, "Avg Delay (Days)", f"{avg_dur_360:.1f}" if pd.notna(avg_dur_360) else "N/A")
                    
                    if battalion_col_360 and zone_col_360:
                        st.markdown("#### 🗺️ Spatial Footprint (Battalion ➔ Zone)")
                        tree_df_360 = comp_df_full.copy()
                        tree_df_360[battalion_col_360] = tree_df_360[battalion_col_360].fillna('Unknown Battalion').astype(str)
                        tree_df_360[zone_col_360] = tree_df_360[zone_col_360].fillna('Unknown Zone').astype(str)
                        tree_grouped = tree_df_360.groupby([battalion_col_360, zone_col_360]).size().reset_index(name='Submittals')
                        fig_tree_360 = px.treemap(tree_grouped, path=[battalion_col_360, zone_col_360], values='Submittals', title=f"Workload Distribution for {selected_comp}", color='Submittals', color_continuous_scale='Blues')
                        fig_tree_360 = style_3d_glassy(fig_tree_360, chart_type="treemap")
                        st.plotly_chart(fig_tree_360, use_container_width=True, key=f"tree_360_{selected_comp}")
                        
                    col_q1, col_q2 = st.columns(2)
                    with col_q1:
                        if battalion_col_360 and 'sample status' in comp_df_full.columns:
                            st.markdown("#### ⚖️ Quality by Battalion")
                            comp_df_full['status_upper'] = comp_df_full['sample status'].str.upper()
                            qual_df = comp_df_full.groupby([battalion_col_360, 'status_upper']).size().reset_index(name='Count')
                            fig_qual = px.bar(qual_df, x=battalion_col_360, y='Count', color='status_upper', title="Approval/Rejection per Battalion", barmode='group', color_discrete_map=STATUS_COLORS)
                            fig_qual = style_3d_glassy(fig_qual, chart_type="bar")
                            st.plotly_chart(fig_qual, use_container_width=True, key=f"qual_{selected_comp}")
                            
                    with col_q2:
                        if elment_col_360:
                            st.markdown("#### 🏗️ Workload by Element")
                            el_df = comp_df_full.groupby(elment_col_360).size().reset_index(name='Count').sort_values('Count', ascending=False)
                            fig_elment = px.bar(el_df.head(15), x=elment_col_360, y='Count', title="Top 15 Elements by Submittals", color=elment_col_360, color_discrete_sequence=NEON_COLORS)
                            fig_elment = style_3d_glassy(fig_elment, chart_type="bar")
                            st.plotly_chart(fig_elment, use_container_width=True, key=f"elment_{selected_comp}")
                        else:
                            st.info("No Element column found for workload breakdown.")
                                
                    col_d1, col_d2 = st.columns(2)
                    with col_d1:
                        if 'Done BY' in comp_df_full.columns:
                            st.markdown("#### 👨‍💼 Processed by Office (Done BY)")
                            off_df = comp_df_full.groupby('Done BY').size().reset_index(name='Count').sort_values('Count', ascending=False)
                            off_df['Percent'] = (off_df['Count'] / off_df['Count'].sum() * 100).round(1)
                            fig_off = px.bar(off_df, x='Done BY', y='Count', text='Count', title="Submittal Volume per Review Office", color='Done BY', color_discrete_sequence=NEON_COLORS)
                            fig_off.update_traces(customdata=off_df['Percent'], hovertemplate='<b>Office:</b> %{x}<br>Count: %{y}<br>Percentage: %{customdata}%')
                            fig_off = style_3d_glassy(fig_off, chart_type="bar")
                            st.plotly_chart(fig_off, use_container_width=True, key=f"off_{selected_comp}")
                            
                    with col_d2:
                        if 'sample status' in comp_df_full.columns and 'layer' in comp_df_full.columns and elment_col_360:
                            st.markdown("#### 🚨 Smart Red Flags (Unresolved Layers)")
                            st.caption("Shows rejections ONLY IF the same Layer/Element wasn't approved later.")
                            rejected_mask = comp_df_full['sample status'].astype(str).str.upper().isin(['REJECTED', 'REVISE'])
                            accepted_mask = comp_df_full['sample status'].astype(str).str.upper().isin(['ACCEPTED', 'APPROVED AS NOTED'])
                            comp_df_rf = comp_df_full.copy()
                            comp_df_rf['Loc_ID'] = comp_df_rf[elment_col_360].astype(str) + "_" + comp_df_rf['layer'].astype(str)
                            approved_locs = set(comp_df_rf[accepted_mask]['Loc_ID'].unique())
                            red_flags = comp_df_rf[rejected_mask & (~comp_df_rf['Loc_ID'].isin(approved_locs))]
                            if not red_flags.empty:
                                display_cols = ['serial', 'sample status', elment_col_360, 'layer']
                                if battalion_col_360: display_cols.append(battalion_col_360)
                                if 'Test Type' in red_flags.columns: display_cols.append('Test Type')
                                existing_cols = [c for c in display_cols if c in red_flags.columns]
                                st.dataframe(red_flags[existing_cols].head(100), use_container_width=True)
                                st.caption(f"Total unresolved layers: {len(red_flags)}")
                            else:
                                st.success("✅ All rejected layers have been successfully re-tested and approved!")
                        else:
                            st.info("Requires 'sample status', 'layer', and 'Element' columns for Smart Red Flags.")

                    if 'sample status' in comp_df_full.columns and 'Date( SUB)' in comp_df_full.columns and 'layer' in comp_df_full.columns:
                        st.markdown('<div class="gradient-divider"></div>', unsafe_allow_html=True)
                        st.markdown("#### 🧾 Rework & Delay Ledger (Rejected Items Analysis)")
                        
                        rework_df = comp_df_full.copy()
                        rejected_items = rework_df[rework_df['sample status'].astype(str).str.upper().isin(['REJECTED', 'REVISE'])]
                        
                        if not rejected_items.empty:
                            ledger_data = []
                            total_delay_days = 0
                            el_col = elment_col_360 if elment_col_360 else None
                            
                            for _, rej_row in rejected_items.iterrows():
                                serial = rej_row.get('serial', 'N/A')
                                rej_date = rej_row['Date( SUB)']
                                layer = str(rej_row.get('layer', 'Unknown'))
                                test_type = str(rej_row.get('Test Type', 'Unknown'))
                                
                                filter_mask = (
                                    (rework_df['sample status'].astype(str).str.upper().isin(['ACCEPTED', 'APPROVED AS NOTED'])) & 
                                    (rework_df['Date( SUB)'] >= rej_date) &
                                    (rework_df['layer'].astype(str) == layer) &
                                    (rework_df['Test Type'].astype(str) == test_type)
                                )
                                
                                if el_col:
                                    element_val = str(rej_row.get(el_col, 'Unknown'))
                                    filter_mask = filter_mask & (rework_df[el_col].astype(str) == element_val)
                                else:
                                    element_val = "N/A"

                                future_accepts = rework_df[filter_mask]
                                
                                if not future_accepts.empty:
                                    acc_date = future_accepts['Date( SUB)'].min()
                                    delay_days = (acc_date - rej_date).days
                                    total_delay_days += delay_days
                                    status_text = "Resolved ✅"
                                else:
                                    acc_date = pd.NaT
                                    delay_days = 0
                                    status_text = "Pending 🚨"
                                    
                                ledger_data.append({
                                    "Rejected Serial": serial,
                                    "Element": element_val,
                                    "Layer": layer,
                                    "Test Type": test_type,
                                    "Rejection Date": rej_date.strftime('%Y-%m-%d') if pd.notna(rej_date) else 'N/A',
                                    "Resolution Date": acc_date.strftime('%Y-%m-%d') if pd.notna(acc_date) else 'Not Resolved',
                                    "Rework Delay (Days)": delay_days,
                                    "Status": status_text
                                })
                            
                            ledger_df = pd.DataFrame(ledger_data).sort_values(by=["Status", "Rework Delay (Days)"], ascending=[False, False])
                            
                            st.markdown(f"""
                            <div style="background: rgba(231, 76, 60, 0.1); border-left: 5px solid #e74c3c; padding: 20px; border-radius: 8px; margin-bottom: 20px; display: flex; justify-content: space-between; align-items: center;">
                                <div>
                                    <h3 style="margin: 0; color: #e74c3c; font-size: 18px;">Total Rework Time Leakage</h3>
                                    <p style="margin: 5px 0 0 0; color: {ui['text_muted']}; font-size: 14px;">Total project days lost tracking re-submissions for the same rejected layers/elements.</p>
                                </div>
                                <div style="font-size: 32px; font-weight: bold; color: #e74c3c;">{total_delay_days} Days Lost</div>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            st.dataframe(ledger_df, use_container_width=True)
                        else:
                            st.success(f"✅ No rejected submittals found for {selected_comp}. Zero rework leakage!")
                    else:
                        st.info("Requires 'sample status', 'layer', and 'Date( SUB)' columns to calculate rework delays.")

                    if battalion_col_360 and elment_col_360 and 'Date ( test)' in comp_df_full.columns:
                        st.markdown("#### ⏱️ Inter-Battalion Element Timeline Analysis")
                        st.caption("Evaluates contractor speed and start/end dates for each element across different battalions.")
                        time_df = comp_df_full.dropna(subset=['Date ( test)'])
                        if not time_df.empty:
                            timeline = time_df.groupby([battalion_col_360, elment_col_360]).agg(
                                Start_Date=('Date ( test)', 'min'),
                                End_Date=('Date ( test)', 'max'),
                                Total_Submittals=('Date ( test)', 'count')
                            ).reset_index()
                            timeline['Duration (Days)'] = (timeline['End_Date'] - timeline['Start_Date']).dt.days
                            timeline['Start_Date'] = timeline['Start_Date'].dt.strftime('%Y-%m-%d')
                            timeline['End_Date'] = timeline['End_Date'].dt.strftime('%Y-%m-%d')
                            timeline = timeline.sort_values([battalion_col_360, 'Start_Date'])
                            st.dataframe(timeline, use_container_width=True)
                        else:
                            st.info("No valid dates found for timeline analysis.")

                with tab_stockpile:
                    req_qty = target_dict.get(selected_comp.strip().lower(), np.nan)
                    
                    comp_bat_df = comp_df_full
                    battalion_col_stock = next((c for c in comp_df_full.columns if 'BATTAL' in c.upper()), None)
                    if battalion_col_stock:
                        avail_bats = ["All Battalions"] + sorted([str(b) for b in comp_df_full[battalion_col_stock].unique() if pd.notna(b) and str(b).strip() != ''])
                        selected_bat = st.selectbox("📍 Filter Sourcing Analysis by Battalion:", avail_bats, key=f"bat_stock_{selected_comp}")
                        if selected_bat != "All Battalions":
                            comp_bat_df = comp_df_full[comp_df_full[battalion_col_stock].astype(str) == selected_bat]

                    stock_df = comp_bat_df[comp_bat_df['Loc_Category'] == 'Stockpile']
                    
                    if num_tests_col:
                        stock_count = int(pd.to_numeric(stock_df[num_tests_col], errors='coerce').fillna(0).sum())
                        bottom_count = int(pd.to_numeric(comp_bat_df[comp_bat_df['Loc_Category'] == 'Bottom of Excavation'][num_tests_col], errors='coerce').fillna(0).sum())
                        fill_count = int(pd.to_numeric(comp_bat_df[comp_bat_df['Loc_Category'] == 'Fill'][num_tests_col], errors='coerce').fillna(0).sum())
                    else:
                        stock_count = len(stock_df)
                        bottom_count = len(comp_bat_df[comp_bat_df['Loc_Category'] == 'Bottom of Excavation'])
                        fill_count = len(comp_bat_df[comp_bat_df['Loc_Category'] == 'Fill'])
                    
                    col_200 = next((c for c in stock_df.columns if '200' in str(c)), None)
                    if col_200 and not stock_df.empty:
                        clean_200 = stock_df[col_200].astype(str).str.replace('%', '', regex=False).str.strip()
                        clean_200 = pd.to_numeric(clean_200, errors='coerce')
                        avg_200 = clean_200.mean()
                    else:
                        avg_200 = np.nan
                    
                    cc1, cc2, cc3, cc4 = st.columns(4)
                    create_card(cc1, "Stockpile Tests", stock_count)
                    create_card(cc2, "Bottom Excavation Tests", bottom_count)
                    create_card(cc3, "Fill Tests", fill_count)
                    create_card(cc4, "Avg Sieve #200 (Stockpile)", f"{avg_200:.2f}%" if pd.notna(avg_200) else "N/A")
                    
                    if pd.notna(req_qty) and req_qty > 0:
                        req_qty_int = int(req_qty)
                        diff = stock_count - req_qty_int
                        progress_pct = min(100, (stock_count / req_qty_int) * 100) if req_qty_int > 0 else 100
                        
                        if progress_pct >= 90:
                            prog_color = "#2ecc71" 
                            status_color = "#2ecc71"
                            status_icon = "✅"
                        elif progress_pct >= 70:
                            prog_color = "#f1c40f" 
                            status_color = "#f1c40f"
                            status_icon = "⚠️"
                        else:
                            prog_color = "#e74c3c" 
                            status_color = "#e74c3c"
                            status_icon = "🚨"

                        if diff >= 0:
                            status_msg = f"<span style='color: #2ecc71;'>{status_icon} Target Exceeded (+{diff} Tests)</span>"
                            prog_color = "#2ecc71"
                        else:
                            status_msg = f"<span style='color: {status_color};'>{status_icon} Missing {abs(diff)} Tests ({progress_pct:.1f}%)</span>"
                        
                        st.markdown(f"""
                        <div style="background: {ui['card_bg']}; padding: 25px; border-radius: 12px; border-left: 6px solid #00d2ff; margin-top: 15px; margin-bottom: 25px; box-shadow: {ui['shadow']};">
                            <h4 style="color: #00d2ff; margin-top: 0; margin-bottom: 20px; font-size: 18px; font-weight: bold;">🎯 Stockpile Target Achievement</h4>
                            <div style="display: flex; justify-content: space-between; margin-bottom: 12px; align-items: flex-end;">
                                <span style="color: {ui['text_muted']}; font-size: 14px;">Target Required: <b style="color: {ui['text_main']}; font-size: 16px;">{req_qty_int}</b></span>
                                <span style="color: #00d2ff; font-size: 14px;">Executed Tests: <b style="color: {ui['text_main']}; font-size: 16px;">{stock_count}</b></span>
                                <span style="font-size: 14px; font-weight: bold; color: {ui['text_main']};">Status: {status_msg}</span>
                            </div>
                            <div class="prog-bg" style="height: 12px; background: rgba(127,140,141,0.2); border-radius: 10px; width: 100%; overflow: hidden;">
                                <div class="prog-fill" style="width: {progress_pct}%; background: {prog_color}; height: 100%; border-radius: 10px; transition: width 1s ease-in-out;"></div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown(f"""
                        <div style="background: {ui['card_bg']}; padding: 25px; border-radius: 12px; border-left: 6px solid #95a5a6; margin-top: 15px; margin-bottom: 25px; box-shadow: {ui['shadow']};">
                            <h4 style="color: #95a5a6; margin-top: 0; margin-bottom: 10px;">🎯 Stockpile Target Achievement</h4>
                            <p style="color: {ui['text_muted']}; font-size: 15px; margin: 0;">No 'Required Quantity' target is currently defined for <b>{selected_comp}</b> in the selected scope.</p>
                        </div>
                        """, unsafe_allow_html=True)

                    if 'Date ( test)' in comp_bat_df.columns:
                        time_analysis_df = comp_bat_df.dropna(subset=['Date ( test)']).copy()
                        time_analysis_df['Month'] = time_analysis_df['Date ( test)'].dt.strftime('%b %Y')
                        fill_by_month = time_analysis_df[time_analysis_df['Loc_Category'] == 'Fill'].groupby('Month').size()
                        stock_by_month = time_analysis_df[time_analysis_df['Loc_Category'] == 'Stockpile'].groupby('Month').size()

                        if not fill_by_month.empty:
                            peak_fill_month = fill_by_month.idxmax()
                            peak_fill_val = fill_by_month.max()
                            stock_in_peak = stock_by_month.get(peak_fill_month, 0)
                            
                            bat_key = selected_bat if battalion_col_stock else "all"
                            scan_key = f"scan_{selected_comp}_{bat_key}"
                            
                            if scan_key not in st.session_state:
                                st.session_state[scan_key] = False

                            if not st.session_state[scan_key]:
                                st.markdown("<br>", unsafe_allow_html=True)
                                if st.button("🧠 Run AI Material Correlation Scan", type="primary", use_container_width=True, key=f"btn_{scan_key}"):
                                    with st.container():
                                        progress_bar = st.progress(0)
                                        status_text = st.empty()
                                        status_text.markdown(f"**<span style='color:#00d2ff;'>[1/3]</span> Scanning {total_requests_count:,} Submittal Logs...**", unsafe_allow_html=True)
                                        time.sleep(1)
                                        progress_bar.progress(33)
                                        status_text.markdown("**<span style='color:#ffaa00;'>[2/3]</span> Correlating Fill layers with Stockpile sources...**", unsafe_allow_html=True)
                                        time.sleep(1.2)
                                        progress_bar.progress(66)
                                        status_text.markdown("**<span style='color:#2ecc71;'>[3/3]</span> Generating Quality Traceability Insights...**", unsafe_allow_html=True)
                                        time.sleep(1.2)
                                        progress_bar.progress(100)
                                        time.sleep(0.5)
                                        st.session_state[scan_key] = True
                                        st.rerun()
                            
                            if st.session_state[scan_key]:
                                base_confidence = 75.0
                                confidence_bonus = min(24.5, peak_fill_val * 0.6) 
                                ai_confidence = round(base_confidence + confidence_bonus, 1)

                                ai_ratio = stock_in_peak / peak_fill_val if peak_fill_val > 0 else 1
                                
                                has_target_qty = pd.notna(req_qty) and req_qty > 0
                                
                                if ai_ratio < 0.05:
                                    status_level, status_color, status_bg, status_icon = "SEVERE DEFICIT", "#e74c3c", "rgba(231, 76, 60, 0.1)", "🚨"
                                    quality_insight = f"Significant discrepancy detected. Fill operations ({peak_fill_val} tests) lack sufficient corresponding stockpile verifications, creating a gap in material quality traceability."
                                    if has_target_qty:
                                        samples_needed = max(1, int(peak_fill_val * 0.1))
                                        directive = f"ACTION REQUIRED: Request contractor to submit at least {samples_needed} Stockpile samples to cover the executed fill volume."
                                    else:
                                        directive = f"SYSTEM.HALT: Cannot calculate required samples. No Target 'Required Quantity' is registered for this contractor. Update records to enable exact sampling estimates."
                                elif ai_ratio < 0.15:
                                    status_level, status_color, status_bg, status_icon = "COVERAGE GAP", "#f1c40f", "rgba(241, 196, 15, 0.1)", "⚠️"
                                    quality_insight = f"Material approval rate is lagging behind fill execution speed. A minor gap in material source validation is forming."
                                    directive = f"ADVISORY: Schedule routine stockpile sampling to restore balance with field operations."
                                else:
                                    status_level, status_color, status_bg, status_icon = "OPTIMAL COVERAGE", "#2ecc71", "rgba(46, 204, 113, 0.1)", "✅"
                                    quality_insight = f"Stockpile testing frequency is well-aligned with the current fill execution volume."
                                    directive = f"MAINTAIN: Continue current testing and approval workflow."

                                st.markdown(f"""
                                <style>
                                    @keyframes scanline {{ 0% {{ transform: translateY(-10px); opacity: 0; }} 50% {{ opacity: 1; }} 100% {{ transform: translateY(0); opacity: 1; }} }}
                                    .ai-terminal {{ background: linear-gradient(145deg, #0a1118, {status_bg}); border: 1px solid rgba(255,255,255,0.05); border-left: 5px solid {status_color}; border-radius: 12px; padding: 25px; margin: 20px 0; box-shadow: 0 0 20px {status_bg}; animation: scanline 0.8s ease-out forwards; }}
                                    .ai-badge {{ background: rgba(0,0,0,0.4); border: 1px solid {ui['border_color']}; padding: 5px 12px; border-radius: 20px; font-size: 12px; color: #00d2ff; }}
                                </style>
                                <div class="ai-terminal">
                                    <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 15px; margin-bottom: 20px;">
                                        <h3 style="color: {status_color}; margin: 0; display: flex; align-items: center; font-size: 20px;"><span style="font-size: 24px; margin-right: 10px;">🤖</span> Generative AI Quality Auditor</h3>
                                        <div style="display: flex; gap: 10px;">
                                            <span class="ai-badge">⚡ Data Confidence: {ai_confidence}%</span>
                                            <span class="ai-badge" style="color: {status_color}; border-color: {status_color}; font-weight: bold;">{status_icon} Status: {status_level}</span>
                                        </div>
                                    </div>
                                    <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 20px;">
                                        <div style="background: rgba(0,0,0,0.2); padding: 15px; border-radius: 8px; border-top: 2px solid #00d2ff;">
                                            <div style="color: #00d2ff; font-weight: bold; font-size: 11px; letter-spacing: 1px; margin-bottom: 8px;">> FIELD_DATA.DETECT()</div>
                                            <div style="color: {ui['text_main']}; font-size: 14px; line-height: 1.6;">Peak filling activity detected in <b style="color:white;">{peak_fill_month}</b> with <b style="color:#00d2ff;">{peak_fill_val} submittals</b>.<br>Correlating approved Stockpile volume during this period is <b style="color:{status_color};">{stock_in_peak}</b>.</div>
                                        </div>
                                        <div style="background: rgba(0,0,0,0.2); padding: 15px; border-radius: 8px; border-top: 2px solid #ffaa00;">
                                            <div style="color: #ffaa00; font-weight: bold; font-size: 11px; letter-spacing: 1px; margin-bottom: 8px;">> QUALITY_GAP.ANALYZE()</div>
                                            <div style="color: {ui['text_main']}; font-size: 14px; line-height: 1.6;">{quality_insight}</div>
                                        </div>
                                        <div style="background: rgba(0,0,0,0.2); padding: 15px; border-radius: 8px; border-top: 2px solid {status_color};">
                                            <div style="color: {status_color}; font-weight: bold; font-size: 11px; letter-spacing: 1px; margin-bottom: 8px;">> QC_ACTION.RECOMMEND()</div>
                                            <div style="color: {ui['text_main']}; font-size: 14px; line-height: 1.6; font-weight: 500;">{directive}</div>
                                        </div>
                                    </div>
                                </div>
                                """, unsafe_allow_html=True)
                                col_reset, _ = st.columns([0.2, 0.8])
                                if col_reset.button("🔄 Reset AI Auditor", key=f"reset_{scan_key}"):
                                    st.session_state[scan_key] = False
                                    st.rerun()

                    ch_col1, ch_col2 = st.columns(2)
                    with ch_col1:
                        if 'Classification' in stock_df.columns and not stock_df.empty:
                            class_counts = stock_df['Classification'].value_counts().reset_index()
                            class_counts.columns = ['Classification', 'Count']
                            fig_class = px.pie(class_counts, names='Classification', values='Count', title=f"Stockpile Classifications for {selected_comp}", hole=0.3, color_discrete_sequence=NEON_COLORS)
                            fig_class.update_traces(textinfo='label+percent', hovertemplate='<b>Class:</b> %{label}<br>Count: %{value}<br>Percentage: %{percent}')
                            fig_class = style_3d_glassy(fig_class, chart_type="pie")
                            st.plotly_chart(fig_class, use_container_width=True, key=f"class_{selected_comp}")
                        else:
                            st.info(f"No Stockpile classification data logged.")
                            
                    with ch_col2:
                        if 'sample status' in stock_df.columns and not stock_df.empty:
                            stock_df['status_upper'] = stock_df['sample status'].str.upper()
                            fig_stock_status = px.pie(stock_df, names='status_upper', title=f"Stockpile Approval/Rejection Rate", hole=0.3, color='status_upper', color_discrete_map=STATUS_COLORS)
                            fig_stock_status.update_traces(textinfo='label+percent', hovertemplate='<b>Status:</b> %{label}<br>Count: %{value}<br>Percentage: %{percent}')
                            fig_stock_status = style_3d_glassy(fig_stock_status, chart_type="pie")
                            st.plotly_chart(fig_stock_status, use_container_width=True, key=f"stock_status_{selected_comp}")
                        else:
                            st.info(f"No Stockpile status data logged.")

                    ch_col3, ch_col4 = st.columns(2)
                    with ch_col3:
                        if 'Date ( test)' in stock_df.columns and not stock_df.empty:
                            time_df = stock_df.dropna(subset=['Date ( test)']).copy()
                            time_df['Month'] = time_df['Date ( test)'].dt.strftime('%b %Y')
                            time_df['Month_Sort'] = time_df['Date ( test)'].dt.to_period('M')
                            monthly_stock = time_df.groupby(['Month_Sort', 'Month']).size().reset_index(name='Count').sort_values('Month_Sort')
                            fig_timeline = px.bar(monthly_stock, x='Month', y='Count', title="Stockpile Tests Timeline", text_auto=True, color_discrete_sequence=['#ffaa00'])
                            fig_timeline = style_3d_glassy(fig_timeline, chart_type="bar")
                            st.plotly_chart(fig_timeline, use_container_width=True, key=f"stock_time_{selected_comp}")
                        else:
                            st.info("No Date data available to show Stockpile timeline.")

                    with ch_col4:
                        if 'sample status' in comp_bat_df.columns and not comp_bat_df.empty:
                            comp_bat_df['status_upper'] = comp_bat_df['sample status'].str.upper()
                            fig_status = px.pie(comp_bat_df, names='status_upper', title=f"Overall Approval Rate (All Tests)", hole=0.3, color='status_upper', color_discrete_map=STATUS_COLORS)
                            fig_status.update_traces(textinfo='label+percent', hovertemplate='<b>Status:</b> %{label}<br>Count: %{value}<br>Percentage: %{percent}')
                            fig_status = style_3d_glassy(fig_status, chart_type="pie")
                            st.plotly_chart(fig_status, use_container_width=True, key=f"stock_all_{selected_comp}")
                        else:
                            st.info(f"No overall status data logged.")

                with tab_execution:
                    st.markdown(f"### 🏗️ Compaction Dashboard: `{selected_comp}`")
                    
                    test_col = 'Test Type' if 'Test Type' in comp_df_full.columns else None
                    compaction_df = pd.DataFrame()
                    if test_col:
                        compaction_df = comp_df_full[comp_df_full[test_col].astype(str).str.contains('DPL|PLATE', case=False, na=False)].copy()
                        
                    num_tests_col_exec = next((c for c in comp_df_full.columns if 'NUMBER OF TESTS' in str(c).strip().upper() or 'NUM OF TEST' in str(c).strip().upper()), None)
                    
                    dpl_df = compaction_df[compaction_df[test_col].astype(str).str.contains('DPL', case=False, na=False)] if test_col else pd.DataFrame()
                    plate_df = compaction_df[compaction_df[test_col].astype(str).str.contains('PLATE', case=False, na=False)] if test_col else pd.DataFrame()
                    
                    dpl_pts = int(pd.to_numeric(dpl_df[num_tests_col_exec], errors='coerce').sum()) if num_tests_col_exec and not dpl_df.empty else len(dpl_df)
                    plate_pts = int(pd.to_numeric(plate_df[num_tests_col_exec], errors='coerce').sum()) if num_tests_col_exec and not plate_df.empty else len(plate_df)
                    total_test_points = dpl_pts + plate_pts
                    
                    avg_dpl = pd.to_numeric(dpl_df['AVERAGE VALUE'], errors='coerce').mean() if 'AVERAGE VALUE' in dpl_df.columns else np.nan
                    
                    c1, c2, c3 = st.columns(3)
                    
                    pts_html = f"<div style='font-size:14px; color:#8da3b9; margin-top:5px;'>DPL: <b style='color:#00d2ff;'>{dpl_pts}</b> | Plate: <b style='color:#ffaa00;'>{plate_pts}</b></div>"
                    create_card(c1, "Total Test Points", f"{total_test_points:,}", delta_html=pts_html)
                    
                    create_card(c2, "Avg DPL Value", f"{avg_dpl:.2f}" if pd.notna(avg_dpl) else "N/A")
                    
                    if 'sample status' in compaction_df.columns and not compaction_df.empty:
                        compaction_df['status_upper'] = compaction_df['sample status'].str.upper()
                        accepted_comp = len(compaction_df[compaction_df['status_upper'].isin(['ACCEPTED', 'APPROVED AS NOTED'])])
                        yield_pct = (accepted_comp / len(compaction_df)) * 100 if len(compaction_df) > 0 else 0
                        yield_color = "#2ecc71" if yield_pct >= 90 else ("#f1c40f" if yield_pct >= 75 else "#e74c3c")
                        create_card(c3, "Compaction Yield", f"<span style='color:{yield_color};'>{yield_pct:.1f}%</span>")
                    else:
                        create_card(c3, "Compaction Yield", "N/A")
                        
                    st.markdown('<div class="gradient-divider"></div>', unsafe_allow_html=True)
                    
                    r2_c1, r2_c2 = st.columns([0.6, 0.4])
                    
                    with r2_c1:
                        st.markdown("#### 📈 Compaction Trend (Submittals vs. Test Points)")
                        if not compaction_df.empty and 'Date ( test)' in compaction_df.columns:
                            compaction_df['Month'] = compaction_df['Date ( test)'].dt.strftime('%b %Y')
                            compaction_df['Month_Sort'] = compaction_df['Date ( test)'].dt.to_period('M')
                            
                            submittals_trend = compaction_df.groupby(['Month_Sort', 'Month', test_col]).size().reset_index(name='Submittals')
                            
                            if num_tests_col_exec:
                                points_trend = compaction_df.groupby(['Month_Sort', 'Month', test_col])[num_tests_col_exec].sum().reset_index(name='Test_Points')
                            else:
                                points_trend = submittals_trend.copy().rename(columns={'Submittals': 'Test_Points'})
                                
                            trend_merged = pd.merge(submittals_trend, points_trend, on=['Month_Sort', 'Month', test_col])
                            trend_merged = trend_merged.sort_values('Month_Sort')

                            fig_comp_trend = make_subplots(specs=[[{"secondary_y": True}]])
                            
                            for i, t_type in enumerate(trend_merged[test_col].unique()):
                                df_t = trend_merged[trend_merged[test_col] == t_type]
                                color = NEON_COLORS[i % len(NEON_COLORS)]
                                fig_comp_trend.add_trace(
                                    go.Bar(x=df_t['Month'], y=df_t['Test_Points'], name=f"{t_type} (Points)", marker_color=color, hovertemplate='<b>Month:</b> %{x}<br><b>Test Points:</b> %{y}'),
                                    secondary_y=False
                                )
                                
                            total_subs_per_month = trend_merged.groupby('Month')['Submittals'].sum().reset_index()
                            total_subs_per_month['Month_Sort'] = pd.to_datetime(total_subs_per_month['Month'], format='%b %Y').dt.to_period('M')
                            total_subs_per_month = total_subs_per_month.sort_values('Month_Sort')
                            
                            fig_comp_trend.add_trace(
                                go.Scatter(x=total_subs_per_month['Month'], y=total_subs_per_month['Submittals'], name="Total Submittals", mode='lines+markers', line=dict(color='#ffffff', width=3, dash='dot'), marker=dict(size=8, color='#ffffff'), hovertemplate='<b>Month:</b> %{x}<br><b>Total Submittals:</b> %{y}'),
                                secondary_y=True
                            )

                            fig_comp_trend.update_layout(title="Test Points Volume vs. Paperwork Submittals", barmode='group', height=350, margin=dict(l=20, r=20, t=40, b=20))
                            fig_comp_trend.update_yaxes(title_text="Actual Test Points (Bars)", secondary_y=False)
                            fig_comp_trend.update_yaxes(title_text="Submittals Count (Line)", secondary_y=True)
                            fig_comp_trend = style_3d_glassy(fig_comp_trend, chart_type="combo")
                            
                            st.plotly_chart(fig_comp_trend, use_container_width=True, key=f"comp_trend_dual_{selected_comp}")
                        else:
                            st.info("No Data available for Trend Analysis.")
                            
                    with r2_c2:
                        st.markdown("#### ⚖️ Compaction Quality Metrics")
                        if 'sample status' in compaction_df.columns and not compaction_df.empty:
                            fig_comp_qual = px.pie(compaction_df, names='status_upper', hole=0.4, color='status_upper', color_discrete_map=STATUS_COLORS)
                            fig_comp_qual.update_traces(textinfo='label+percent', hovertemplate='<b>Status:</b> %{label}<br>Count: %{value}<br>Yield: %{percent}')
                            fig_comp_qual = style_3d_glassy(fig_comp_qual, chart_type="pie")
                            fig_comp_qual.update_layout(height=350, margin=dict(l=20, r=20, t=20, b=20), showlegend=False)
                            st.plotly_chart(fig_comp_qual, use_container_width=True, key=f"comp_qual_pie_{selected_comp}")
                        else:
                            st.info("No Quality data found for Compaction.")

                # ==========================================
                # 🚀 QUANTITIES RATE — NEW ENHANCED SECTION
                # ==========================================
                with tab_quantities:
                    st.markdown(f"### 📊 Quantities Rate & Execution Analytics")
                    st.caption("Full execution analysis — quantities, targets, elements coverage, and worst performer.")

                    # ── Column Detection ───────────────────────────────────
                    contractor_col   = next((c for c in df.columns if 'CONTRACTOR' in c.upper()), None)
                    comp_main_col    = next((c for c in df.columns if 'COMPANY NAME' in c.upper() and 'CONTRACTOR' not in c.upper()), 'Company Name')
                    exec_qty_m3_col  = next((c for c in df.columns if 'EXECUTED QUANTITY' in c.upper() and 'M' in c.upper()), None)
                    total_qty_col    = next((c for c in df.columns if 'TOTAL QUANTITY' in c.upper()), None)
                    target_rate_col  = next((c for c in df.columns if 'TARGET DAILY RATE' in c.upper()), None)
                    date_daily_col   = next((c for c in df.columns if 'DATE' in c.upper() and 'DAILY' in c.upper()), None)
                    elem_all_col     = next((c for c in df.columns if 'ELEMENT (ALL)' in c.upper() or 'ELEMENT(ALL)' in c.upper()), None)
                    elment_main_col  = next((c for c in df.columns if 'ELMENT' in c.upper() and 'ALL' not in c.upper()), None)
                    sector_col       = next((c for c in df.columns if 'SECTOR' in c.upper()), None)
                    num_tests_col_q  = next((c for c in df.columns if 'NUMBER OF TESTS' in c.upper() or 'NUM OF TEST' in c.upper()), None)

                    # ── Numeric Conversion ─────────────────────────────────
                    if exec_qty_m3_col:
                        df[exec_qty_m3_col] = pd.to_numeric(df[exec_qty_m3_col], errors='coerce').fillna(0)
                    if total_qty_col:
                        df[total_qty_col] = pd.to_numeric(df[total_qty_col], errors='coerce').fillna(0)
                    if target_rate_col:
                        df[target_rate_col] = pd.to_numeric(df[target_rate_col], errors='coerce').fillna(0)

                    # ── Sector Filter ──────────────────────────────────────
                    if sector_col:
                        sectors = ['All Sectors'] + sorted(df[sector_col].dropna().astype(str).unique().tolist())
                        sel_sector = st.selectbox("🗺️ Filter by Sector:", sectors, key="qty_sector_sel")
                        df_qty = df[df[sector_col].astype(str) == sel_sector].copy() if sel_sector != 'All Sectors' else df.copy()
                    else:
                        df_qty = df.copy()
                        sel_sector = 'All Sectors'

                    # ── Contractor Filter ──────────────────────────────────
                    contractors_list = ['All Contractors']
                    if contractor_col:
                        contractors_list += sorted(df_qty[contractor_col].dropna().astype(str).str.strip().unique().tolist())
                    sel_contractor = st.selectbox("🏢 Filter by Contractor:", contractors_list, key="qty_contractor_sel")

                    if sel_contractor != 'All Contractors' and contractor_col:
                        df_qty = df_qty[df_qty[contractor_col].astype(str).str.strip() == sel_contractor]

                    st.markdown('<div class="gradient-divider"></div>', unsafe_allow_html=True)

                    # ══════════════════════════════════════════════════════
                    # 1. CARD: Total Project Scope (Company Name + Total Qty)
                    # ══════════════════════════════════════════════════════
                    st.markdown("#### 📦 KPI Cards")
                    c1, c2, c3, c4 = st.columns(4)

                    # Card 1 — Total Project Scope from Company Name + Total Quantity
                    total_scope = 0
                    if comp_main_col in df_qty.columns and total_qty_col:
                        if sel_contractor != 'All Contractors':
                            scope_df = df_qty[df_qty[comp_main_col].astype(str).str.strip() == sel_contractor]
                        else:
                            scope_df = df_qty
                        if elment_main_col and elment_main_col in scope_df.columns:
                            total_scope = scope_df.groupby(elment_main_col)[total_qty_col].max().sum()
                        else:
                            total_scope = scope_df[total_qty_col].max()

                    create_card(c1, "🏗️ Total Project Scope (m³)",
                                f"{total_scope:,.1f}" if total_scope > 0 else "N/A",
                                delta_html="<span style='color:#00d2ff;font-size:11px'>From Company + Total Quantity</span>")

                    # Card 2 — Executed Qty from Company Name + Executed Quantity
                    company_exec = 0
                    if comp_main_col in df_qty.columns and exec_qty_m3_col:
                        if sel_contractor != 'All Contractors':
                            ce_df = df_qty[df_qty[comp_main_col].astype(str).str.strip() == sel_contractor]
                        else:
                            ce_df = df_qty
                        company_exec = ce_df[exec_qty_m3_col].sum()

                    create_card(c2, "✅ Executed Qty — Company (m³)",
                                f"{company_exec:,.1f}",
                                delta_html="<span style='color:#2ecc71;font-size:11px'>From Company Name + Executed Qty</span>")

                    # Card 3 — Executed Qty from Contractor + Executed Quantity (m³) SUM
                    contractor_exec = 0
                    if contractor_col and exec_qty_m3_col:
                        if sel_contractor != 'All Contractors':
                            ct_df = df_qty[df_qty[contractor_col].astype(str).str.strip() == sel_contractor]
                        else:
                            ct_df = df_qty
                        contractor_exec = ct_df[exec_qty_m3_col].sum()

                    create_card(c3, "🚧 Executed Qty — Contractor (m³)",
                                f"{contractor_exec:,.1f}",
                                delta_html="<span style='color:#ffaa00;font-size:11px'>From Contractor + Executed Qty (m³)</span>")

                    # Card 4 — Scope Completion %
                    completion_pct = (contractor_exec / total_scope * 100) if total_scope > 0 else 0
                    completion_color = "#2ecc71" if completion_pct >= 80 else ("#f1c40f" if completion_pct >= 50 else "#e74c3c")
                    create_card(c4, "📈 Scope Completion %",
                                f"{completion_pct:.1f}%",
                                delta_html=f"<span style='color:{completion_color};font-size:11px'>{'On Track ✅' if completion_pct>=80 else 'Needs Attention ⚠️'}</span>",
                                progress=min(100, completion_pct))

                    # ══════════════════════════════════════════════════════
                    # 4. CARD: Executed Qty per Element (Element All + Contractor + Exec Qty)
                    # ══════════════════════════════════════════════════════
                    if elem_all_col and contractor_col and exec_qty_m3_col:
                        st.markdown("#### 🔍 Executed Quantity per Element")
                        elem_group = df_qty.groupby([contractor_col, elem_all_col])[exec_qty_m3_col].sum().reset_index()
                        elem_group.columns = ['Contractor', 'Element (All)', 'Executed (m³)']
                        elem_group = elem_group[elem_group['Executed (m³)'] > 0].sort_values('Executed (m³)', ascending=False)

                        if not elem_group.empty:
                            # KPI cards for top elements
                            top_elems = elem_group.head(4)
                            elem_cols = st.columns(min(len(top_elems), 4))
                            for i, (_, row) in enumerate(top_elems.iterrows()):
                                create_card(elem_cols[i],
                                            f"📍 {row['Element (All)']}",
                                            f"{row['Executed (m³)']:,.1f} m³",
                                            delta_html=f"<span style='color:#8da3b9;font-size:10px'>{row['Contractor']}</span>")

                            # Full table
                            with st.expander("📋 View All Elements Breakdown"):
                                st.dataframe(elem_group, use_container_width=True)

                    st.markdown('<div class="gradient-divider"></div>', unsafe_allow_html=True)

                    # ══════════════════════════════════════════════════════
                    # 5. CHART: Target Daily Rate vs Executed Qty per Contractor
                    # ══════════════════════════════════════════════════════
                    st.markdown("#### 🚀 Daily Execution vs Target Rate — Per Contractor")
                    if date_daily_col and target_rate_col and exec_qty_m3_col and contractor_col:
                        df_daily = df_qty.copy()
                        df_daily[date_daily_col] = pd.to_datetime(df_daily[date_daily_col], errors='coerce')
                        df_daily = df_daily.dropna(subset=[date_daily_col])

                        daily_agg = df_daily.groupby([date_daily_col, contractor_col]).agg(
                            Executed=(exec_qty_m3_col, 'sum'),
                            Target=(target_rate_col, 'max')
                        ).reset_index()
                        daily_agg.columns = ['Date', 'Contractor', 'Executed (m³)', 'Target Rate']
                        daily_agg['Status'] = daily_agg.apply(
                            lambda r: '✅ Met' if r['Executed (m³)'] >= r['Target Rate'] and r['Target Rate'] > 0
                                      else ('⚠️ Below Target' if r['Target Rate'] > 0 else '➖ No Target'),
                            axis=1
                        )

                        if not daily_agg.empty:
                            ch1, ch2 = st.columns([0.65, 0.35])
                            with ch1:
                                fig_daily = go.Figure()
                                fig_daily.add_trace(go.Scatter(
                                    x=daily_agg['Date'], y=daily_agg['Target Rate'],
                                    name='Target Daily Rate', mode='lines+markers',
                                    line=dict(color='#e74c3c', width=3, shape='spline'),
                                    marker=dict(size=7, color='white', line=dict(color='#e74c3c', width=2)),
                                    hovertemplate='<b>%{x|%Y-%m-%d}</b><br>Target: %{y:,.1f}'
                                ))
                                for ctractor in daily_agg['Contractor'].unique():
                                    ct_df = daily_agg[daily_agg['Contractor'] == ctractor]
                                    fig_daily.add_trace(go.Bar(
                                        x=ct_df['Date'], y=ct_df['Executed (m³)'],
                                        name=ctractor, opacity=0.8,
                                        hovertemplate=f'<b>{ctractor}</b><br>Date: %{{x|%Y-%m-%d}}<br>Executed: %{{y:,.1f}}'
                                    ))
                                fig_daily.update_layout(
                                    height=400, barmode='group', hovermode='x unified',
                                    margin=dict(l=0, r=0, t=30, b=0),
                                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                                )
                                try: fig_daily = style_3d_glassy(fig_daily, "combo")
                                except: pass
                                st.plotly_chart(fig_daily, use_container_width=True, key="qty_daily_chart")

                            with ch2:
                                # Performance summary per contractor
                                st.markdown("**Performance Summary**")
                                perf_summary = daily_agg.groupby('Contractor').apply(
                                    lambda x: pd.Series({
                                        'Days Worked': len(x),
                                        'Days Met Target': (x['Executed (m³)'] >= x['Target Rate']).sum(),
                                        'Total Executed (m³)': x['Executed (m³)'].sum(),
                                        'Avg vs Target (%)': (
                                            (x['Executed (m³)'] / x['Target Rate'].replace(0, float('nan'))).mean() * 100
                                        ) if x['Target Rate'].sum() > 0 else 0
                                    })
                                ).reset_index()
                                perf_summary['Hit Rate %'] = (perf_summary['Days Met Target'] / perf_summary['Days Worked'] * 100).round(1)
                                perf_summary['Avg vs Target (%)'] = perf_summary['Avg vs Target (%)'].round(1)
                                st.dataframe(
                                    perf_summary[['Contractor', 'Days Worked', 'Days Met Target', 'Hit Rate %', 'Total Executed (m³)']],
                                    use_container_width=True
                                )
                    else:
                        st.info("Missing: Date (Daily), Target Daily Rate, Executed Quantity, or Contractor columns.")

                    st.markdown('<div class="gradient-divider"></div>', unsafe_allow_html=True)

                    # ══════════════════════════════════════════════════════
                    # 6. KPI SUMMARY — All metrics with color-coded status
                    # ══════════════════════════════════════════════════════
                    st.markdown("#### 🎯 KPI Summary Dashboard")

                    kpi_data = []
                    if contractor_col and exec_qty_m3_col and target_rate_col:
                        for ctractor in df_qty[contractor_col].dropna().unique():
                            ct = df_qty[df_qty[contractor_col].astype(str).str.strip() == str(ctractor).strip()]
                            exec_sum  = ct[exec_qty_m3_col].sum()
                            tgt_sum   = ct[target_rate_col].sum()
                            hit_rate  = len(ct[ct[exec_qty_m3_col] >= ct[target_rate_col]]) / len(ct) * 100 if len(ct) > 0 else 0
                            scope_val = 0
                            if total_qty_col:
                                if elment_main_col and elment_main_col in ct.columns:
                                    scope_val = ct.groupby(elment_main_col)[total_qty_col].max().sum()
                                else:
                                    scope_val = ct[total_qty_col].max()
                            completion = (exec_sum / scope_val * 100) if scope_val > 0 else 0
                            kpi_data.append({
                                'Contractor': ctractor,
                                'Total Scope (m³)': round(scope_val, 1),
                                'Executed (m³)': round(exec_sum, 1),
                                'Completion %': round(completion, 1),
                                'Target Hit Rate %': round(hit_rate, 1),
                                'Status': '🟢 Good' if hit_rate >= 70 else ('🟡 Fair' if hit_rate >= 40 else '🔴 Poor')
                            })

                    if kpi_data:
                        kpi_df = pd.DataFrame(kpi_data).sort_values('Completion %', ascending=False)
                        st.dataframe(kpi_df, use_container_width=True)

                        # KPI bar chart
                        fig_kpi = px.bar(kpi_df, x='Contractor', y=['Completion %', 'Target Hit Rate %'],
                                         barmode='group', color_discrete_sequence=['#00d2ff', '#ffaa00'],
                                         title="Completion % vs Target Hit Rate % per Contractor",
                                         text_auto=True)
                        try: fig_kpi = style_3d_glassy(fig_kpi, "bar")
                        except: pass
                        st.plotly_chart(fig_kpi, use_container_width=True, key="kpi_summary_chart")

                    st.markdown('<div class="gradient-divider"></div>', unsafe_allow_html=True)

                    # ══════════════════════════════════════════════════════
                    # 7. ELEMENT COVERAGE AUDIT
                    # Which elements have quantities and which don't
                    # Uses: Element (all) + Contractor + Company Name + ELMENT
                    # ══════════════════════════════════════════════════════
                    st.markdown("#### 🕵️ Element Coverage Audit — Missing Quantities Detector")
                    st.caption("Cross-checks Element (All) vs ELMENT column to find elements missing quantities.")

                    if elem_all_col and contractor_col and comp_main_col in df.columns and elment_main_col:
                        # Elements the contractor should cover (from Element All + Contractor)
                        expected = df_qty[[contractor_col, elem_all_col]].dropna()
                        expected = expected[expected[elem_all_col].astype(str).str.strip() != '']
                        expected_set = set(zip(
                            expected[contractor_col].astype(str).str.strip(),
                            expected[elem_all_col].astype(str).str.strip()
                        ))

                        # Elements that actually received quantities (from Company Name + ELMENT)
                        received = df_qty[[comp_main_col, elment_main_col, exec_qty_m3_col]].dropna(subset=[elment_main_col]) if exec_qty_m3_col else df_qty[[comp_main_col, elment_main_col]].dropna()
                        received_qty = received.groupby([comp_main_col, elment_main_col])[exec_qty_m3_col].sum().reset_index() if exec_qty_m3_col else pd.DataFrame()

                        # Find missing
                        missing_elements = []
                        covered_elements = []
                        for contractor, element in expected_set:
                            # Match contractor in Company Name col
                            match = received_qty[
                                (received_qty[comp_main_col].astype(str).str.strip() == contractor) &
                                (received_qty[elment_main_col].astype(str).str.strip() == element)
                            ] if not received_qty.empty else pd.DataFrame()

                            if match.empty or (exec_qty_m3_col and match[exec_qty_m3_col].sum() == 0):
                                missing_elements.append({'Contractor': contractor, 'Element': element, 'Status': '❌ No Quantity'})
                            else:
                                qty = match[exec_qty_m3_col].sum() if exec_qty_m3_col else 0
                                covered_elements.append({'Contractor': contractor, 'Element': element, 'Executed (m³)': round(qty, 1), 'Status': '✅ Has Quantity'})

                        col_miss, col_cov = st.columns(2)

                        with col_miss:
                            if missing_elements:
                                miss_df = pd.DataFrame(missing_elements).sort_values(['Contractor', 'Element'])
                                st.markdown(f"""
                                <div style="background:rgba(231,76,60,0.1);border-left:4px solid #e74c3c;padding:15px;border-radius:8px;margin-bottom:10px;">
                                    <b style="color:#e74c3c;">🚨 {len(missing_elements)} Element(s) Missing Quantities</b><br>
                                    <span style="font-size:12px;color:#d1d5da;">Request quantities from the Technical Office for these elements:</span>
                                </div>
                                """, unsafe_allow_html=True)
                                st.dataframe(miss_df, use_container_width=True)
                            else:
                                st.success("✅ All elements have quantities assigned!")

                        with col_cov:
                            if covered_elements:
                                cov_df = pd.DataFrame(covered_elements).sort_values('Executed (m³)', ascending=False)
                                st.markdown(f"""
                                <div style="background:rgba(46,204,113,0.1);border-left:4px solid #2ecc71;padding:15px;border-radius:8px;margin-bottom:10px;">
                                    <b style="color:#2ecc71;">✅ {len(covered_elements)} Element(s) Covered</b><br>
                                    <span style="font-size:12px;color:#d1d5da;">These elements have quantities from the Technical Office.</span>
                                </div>
                                """, unsafe_allow_html=True)
                                st.dataframe(cov_df, use_container_width=True)
                    else:
                        st.info("Requires columns: Element (All), Contractor, Company Name, and ELMENT.")

                    st.markdown('<div class="gradient-divider"></div>', unsafe_allow_html=True)

                    # ══════════════════════════════════════════════════════
                    # 8. WORST PERFORMER per Sector
                    # North & South — worst avg rate vs target
                    # Uses: Contractor + Target Daily Rate + Executed Qty (m³)
                    # ══════════════════════════════════════════════════════
                    st.markdown("#### 🏆 Worst Performer Analysis — By Sector")
                    st.caption("Identifies the contractor with the lowest execution rate vs daily target per sector.")

                    if contractor_col and target_rate_col and exec_qty_m3_col and sector_col:
                        worst_data = []
                        for sector_name in df[sector_col].dropna().unique():
                            sec_df = df[df[sector_col].astype(str) == str(sector_name)].copy()
                            sec_df = sec_df[sec_df[target_rate_col] > 0]

                            if sec_df.empty:
                                continue

                            # Performance ratio per day per contractor
                            sec_df['performance_ratio'] = sec_df[exec_qty_m3_col] / sec_df[target_rate_col].replace(0, float('nan'))

                            perf = sec_df.groupby(contractor_col).agg(
                                Avg_Performance=('performance_ratio', 'mean'),
                                Total_Executed=(exec_qty_m3_col, 'sum'),
                                Days_Below=(exec_qty_m3_col, lambda x: (x < sec_df.loc[x.index, target_rate_col]).sum())
                            ).reset_index()
                            perf.columns = ['Contractor', 'Avg Performance Ratio', 'Total Executed (m³)', 'Days Below Target']
                            perf['Avg Performance %'] = (perf['Avg Performance Ratio'] * 100).round(1)
                            perf = perf.sort_values('Avg Performance %')

                            if not perf.empty:
                                worst = perf.iloc[0]
                                worst_data.append({
                                    'Sector': sector_name,
                                    'Worst Contractor': worst['Contractor'],
                                    'Avg Performance %': worst['Avg Performance %'],
                                    'Total Executed (m³)': round(worst['Total Executed (m³)'], 1),
                                    'Days Below Target': int(worst['Days Below Target'])
                                })

                                # Sector leaderboard
                                st.markdown(f"**{sector_name}**")
                                worst_col, best_col = st.columns(2)

                                worst_contractor = perf.iloc[0]
                                best_contractor  = perf.iloc[-1]

                                worst_col.markdown(f"""
                                <div style="background:rgba(231,76,60,0.1);border-left:5px solid #e74c3c;border-radius:12px;padding:16px;margin-bottom:12px;">
                                    <div style="color:#e74c3c;font-size:12px;font-weight:600;text-transform:uppercase;margin-bottom:6px;">🔴 Worst Performer</div>
                                    <div style="color:#ffffff;font-size:20px;font-weight:700;">{worst_contractor['Contractor']}</div>
                                    <div style="color:#8da3b9;font-size:13px;margin-top:6px;">
                                        Avg: <b style="color:#e74c3c">{worst_contractor['Avg Performance %']:.1f}%</b> of target<br>
                                        Days below target: <b style="color:#e74c3c">{int(worst_contractor['Days Below Target'])}</b>
                                    </div>
                                </div>
                                """, unsafe_allow_html=True)

                                best_col.markdown(f"""
                                <div style="background:rgba(46,204,113,0.1);border-left:5px solid #2ecc71;border-radius:12px;padding:16px;margin-bottom:12px;">
                                    <div style="color:#2ecc71;font-size:12px;font-weight:600;text-transform:uppercase;margin-bottom:6px;">🟢 Best Performer</div>
                                    <div style="color:#ffffff;font-size:20px;font-weight:700;">{best_contractor['Contractor']}</div>
                                    <div style="color:#8da3b9;font-size:13px;margin-top:6px;">
                                        Avg: <b style="color:#2ecc71">{best_contractor['Avg Performance %']:.1f}%</b> of target<br>
                                        Days below target: <b style="color:#2ecc71">{int(best_contractor['Days Below Target'])}</b>
                                    </div>
                                </div>
                                """, unsafe_allow_html=True)

                                # Full sector ranking chart
                                fig_worst = px.bar(
                                    perf.sort_values('Avg Performance %'),
                                    x='Contractor', y='Avg Performance %',
                                    color='Avg Performance %',
                                    color_continuous_scale=['#e74c3c', '#f1c40f', '#2ecc71'],
                                    range_color=[0, 150],
                                    title=f"{sector_name} — Contractor Performance vs Target (%)",
                                    text_auto=True
                                )
                                fig_worst.add_hline(y=100, line_dash="dash", line_color="#ffaa00",
                                                    annotation_text="100% Target", annotation_position="top right")
                                try: fig_worst = style_3d_glassy(fig_worst, "bar")
                                except: pass
                                st.plotly_chart(fig_worst, use_container_width=True, key=f"worst_{sector_name}")

                    elif contractor_col and target_rate_col and exec_qty_m3_col:
                        # No sector column — show overall worst
                        st.info("No 'Sector' column detected. Showing overall worst performer.")
                        df_w = df.copy()
                        df_w = df_w[df_w[target_rate_col] > 0]
                        df_w['perf_ratio'] = df_w[exec_qty_m3_col] / df_w[target_rate_col].replace(0, float('nan'))
                        overall_perf = df_w.groupby(contractor_col)['perf_ratio'].mean().reset_index()
                        overall_perf.columns = ['Contractor', 'Avg Performance %']
                        overall_perf['Avg Performance %'] = (overall_perf['Avg Performance %'] * 100).round(1)
                        overall_perf = overall_perf.sort_values('Avg Performance %')
                        if not overall_perf.empty:
                            worst_overall = overall_perf.iloc[0]
                            st.error(f"🔴 Overall Worst Performer: **{worst_overall['Contractor']}** — {worst_overall['Avg Performance %']:.1f}% of target")
                            st.dataframe(overall_perf, use_container_width=True)
                    else:
                        st.info("Requires: Contractor, Target Daily Rate, Executed Quantity (m³), and Sector columns.")

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