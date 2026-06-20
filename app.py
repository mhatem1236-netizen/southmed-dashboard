معاك حق 100% يا هندسة، بعتذر لك جداً على الاختصار في الرد اللي فات. السيستم كبر وموديولاته كترت، ولازم الكود يكون "قطعة واحدة" عشان يشتغل معاك فوراً من غير ما يحصل أي Error في الدمج.

جمعتلك **كل الأسطر البرمجية**، من أول سطر لآخر سطر (بما فيها خريطة الـ 3D Site Navigator، والفلاتر الذكية للـ Zones، والطباعة، واللغة الإنجليزية الكاملة، ومفتش الداتا).

انسخ **الكود المستقر النهائي (Master Code V22 - Enterprise Full Edition)** بالكامل من هنا:

```python
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
# 1. Timezone and Colors Configuration
# ==========================================
EGYPT_TZ = pytz.timezone('Africa/Cairo')
NEON_COLORS = ['#00d2ff', '#ffaa00', '#2ecc71', '#ff007f', '#f1c40f', '#9b59b6', '#38f9d7', '#ff7eb3', '#00f2fe', '#4facfe']

# ==========================================
# 2. 3D Glassy Chart Styling Function
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
        fig.update_traces(
            marker=dict(line=dict(color='rgba(255, 255, 255, 0.4)', width=1.5)),
            opacity=0.85
        )
    elif chart_type == "line":
        fig.update_traces(line=dict(width=4), marker=dict(size=8, line=dict(color='white', width=1.5)))
        
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='rgba(255,255,255,0.05)')
    return fig

# ==========================================
# 3. History Manager
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
# 4. Page Config & Advanced CSS Styling (Including PDF Print)
# ==========================================
st.set_page_config(page_title="Infrastructure BI Dashboard", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@300;500;700;800&family=Tajawal:wght@400;700&display=swap');

    html, body, [class*="css"] { font-family: 'Montserrat', sans-serif !important; }

    [data-testid="stAppViewContainer"] { background: radial-gradient(circle at top right, #0b1a2e, #050a11) !important; }
    
    [data-testid="stSidebar"] { background-color: rgba(5, 10, 17, 0.95) !important; border-right: 1px solid rgba(255, 170, 0, 0.1); }

    .metric-card { 
        background: linear-gradient(145deg, rgba(20, 35, 54, 0.6), rgba(10, 20, 33, 0.9));
        backdrop-filter: blur(15px); -webkit-backdrop-filter: blur(15px);
        padding: 25px; border-radius: 20px; text-align: center; 
        border: 1px solid rgba(255, 170, 0, 0.15); border-left: 4px solid #ffaa00;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.4); margin-bottom: 15px; 
        transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
    }
    .metric-card:hover { transform: translateY(-8px) scale(1.02); border-left: 4px solid #00d2ff; box-shadow: 0 15px 35px rgba(0, 210, 255, 0.25); }
    
    .metric-label { color: #8da3b9; font-size: 14px; font-weight: 500; margin-bottom: 5px; text-transform: uppercase; letter-spacing: 1.5px;}
    .metric-value { color: #ffffff !important; font-size: 38px; font-weight: 800; background: -webkit-linear-gradient(#ffffff, #a0aec0); -webkit-background-clip: text; -webkit-text-fill-color: transparent;}
    
    .stDataFrame { border: 1px solid rgba(255, 255, 255, 0.05); border-radius: 12px; overflow: hidden; }
    .delta-up { color: #2ecc71; font-size: 14px; font-weight: bold; margin-top: 8px; text-shadow: 0 0 10px rgba(46, 204, 113, 0.4);}
    .delta-down { color: #e74c3c; font-size: 14px; font-weight: bold; margin-top: 8px; text-shadow: 0 0 10px rgba(231, 76, 60, 0.4);}
    .delta-neutral { color: #95a5a6; font-size: 14px; font-weight: bold; margin-top: 8px; }
    
    .bi-title { color: #ffaa00; font-size: 28px; font-weight: 800; margin-top: 40px; margin-bottom: 20px; text-shadow: 0px 0px 15px rgba(255, 170, 0, 0.3);}
    .gradient-divider { height: 2px; background: linear-gradient(90deg, transparent 0%, rgba(255,170,0,0.8) 50%, transparent 100%); margin-top: 40px; margin-bottom: 40px; border: none; opacity: 0.6;}
    
    .simulator-card { background: linear-gradient(135deg, rgba(14, 36, 57, 0.7), rgba(46, 204, 113, 0.1)); backdrop-filter: blur(12px); padding: 25px; border-radius: 20px; border: 1px solid rgba(46, 204, 113, 0.4); text-align: center; margin-top: 15px; box-shadow: 0 8px 25px rgba(46, 204, 113, 0.15);}
    .leaderboard-card { background: rgba(10, 20, 33, 0.7); padding: 25px; border-radius: 20px; border-left: 5px solid; margin-bottom: 15px; box-shadow: 0 8px 20px rgba(0,0,0,0.3);}
    
    .health-card { background: rgba(10, 20, 33, 0.8); backdrop-filter: blur(10px); padding: 15px 25px; border-radius: 15px; border: 1px solid rgba(255, 255, 255, 0.1); display: flex; align-items: center; justify-content: space-between; margin-bottom: 25px; box-shadow: 0 5px 15px rgba(0,0,0,0.3);}
    .visual-frame { border: 2px solid #ffaa00; border-radius: 20px; padding: 10px; background: rgba(0,0,0,0.4); margin-bottom: 20px; }

    ::-webkit-scrollbar { width: 8px; height: 8px; }
    ::-webkit-scrollbar-track { background: #050a11; }
    ::-webkit-scrollbar-thumb { background: rgba(255, 170, 0, 0.5); border-radius: 10px; }
    ::-webkit-scrollbar-thumb:hover { background: rgba(255, 170, 0, 0.8); }

    /* 🔥 CSS for Professional PDF Export (Ctrl+P) 🔥 */
    @media print {
        * { -webkit-print-color-adjust: exact !important; print-color-adjust: exact !important; }
        body, [data-testid="stAppViewContainer"] { background: #050a11 !important; }
        [data-testid="stSidebar"], .stFileUploader, .stButton, header, footer, [data-testid="stSidebarCollapsedControl"] { display: none !important; }
        .main .block-container { max-width: 100% !important; padding: 5mm !important; margin: 0 !important; }
        .metric-card, .simulator-card, .leaderboard-card, .health-card, div[data-testid="stPlotlyChart"], .visual-frame { page-break-inside: avoid !important; background: #0b1a2e !important; border: 1px solid rgba(255, 170, 0, 0.4) !important; }
        .metric-value, .bi-title { -webkit-text-fill-color: white !important; color: white !important; }
        h1, h2, h3, h4, p, span, .metric-label { color: #d1d5da !important; }
        .gradient-divider { display: none !important; }
    }
    </style>
    """, unsafe_allow_html=True)

def create_card(column, label, value, delta_html=""):
    column.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">{label}</div>
            <div class="metric-value">{value}</div>
            {delta_html}
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
# 5. App Header
# ==========================================
try: st.image("5.jpg", use_container_width=True)
except: pass

col_h1, col_h2 = st.columns([0.8, 0.2])
with col_h1: st.title("Mega Infrastructure BI & Intelligence System 🏗️🧠")
with col_h2:
    try: st.image("شششششششش.JPG", width=120)
    except: pass

# ==========================================
# 6. Sidebar: Database, Filters & Simulator
# ==========================================
try:
    st.sidebar.image("شششششششش.JPG", use_container_width=True)
    st.sidebar.divider()
except: pass

st.sidebar.markdown("### 🔌 Data Source Connection")
data_source = st.sidebar.selectbox("Connection Type:", ["Local CSV Upload", "Live SQL Database (Pending)"])

uploaded_file = None
if data_source == "Local CSV Upload":
    uploaded_file = st.sidebar.file_uploader("Upload your Project Log (CSV) 📂", type="csv")

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    df.columns = df.columns.str.strip() 
    
    if 'Test Type' in df.columns: df['Test Type'] = df['Test Type'].str.strip().str.upper()
    if 'Date ( test)' in df.columns: df['Date ( test)'] = pd.to_datetime(df['Date ( test)'], errors='coerce', dayfirst=True)
    if 'Date( SUB)' in df.columns: df['Date( SUB)'] = pd.to_datetime(df['Date( SUB)'], errors='coerce', dayfirst=True)

    # 🔥 6.1. Health Inspector (With Scanned Rows) 🔥
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

    # 🔥 6.2. Global Smart Search 🔥
    st.sidebar.divider()
    st.sidebar.markdown("### 🔍 Global Smart Search")
    global_search = st.sidebar.text_input("Search (Serial, Element, Date...):", placeholder="Type keyword to filter all...")
    
    if global_search:
        mask = df.astype(str).apply(lambda x: x.str.contains(global_search, case=False, na=False)).any(axis=1)
        df = df[mask]
        st.sidebar.success(f"🎯 Found {len(df)} records matching '{global_search}'")

    st.sidebar.divider()
    st.sidebar.header("🎯 BI Filters & AI Chat")
    
    curr_avg_dpl = pd.to_numeric(df['AVERAGE VALUE'], errors='coerce').mean() if 'AVERAGE VALUE' in df.columns else 0
    curr_avg_dur = pd.to_numeric(df['DURATION'], errors='coerce').mean() if 'DURATION' in df.columns else 0
    
    user_question = st.sidebar.text_input("Ask AI about any log issue:")
    if user_question:
        summary = {"avg_dpl": round(curr_avg_dpl, 2), "avg_duration": round(curr_avg_dur, 1)}
        st.sidebar.info(f"AI Response: {ai_assistant(user_question, summary)}")
    
    st.sidebar.divider()
    
    companies = df['Company Name'].dropna().unique() if 'Company Name' in df.columns else []
    selected_companies = st.sidebar.multiselect("Select Contractor:", options=companies, default=companies)
    
    statuses = df['sample status'].dropna().unique() if 'sample status' in df.columns else []
    selected_statuses = st.sidebar.multiselect("Sample Status:", options=statuses, default=statuses)

    # What-If Simulator
    st.sidebar.divider()
    st.sidebar.header("🎛️ What-If Optimization Simulator")
    sim_days_saved = st.sidebar.slider("Simulate Admin Delay Reduction (Days):", min_value=0, max_value=10, value=0, step=1)

    # Backup & Restore
    st.sidebar.divider()
    with st.sidebar.expander("🗄️ History Database Backup"):
        st.markdown("<span style='font-size:12px; color:#d1d5da;'>Save your history before leaving to restore tomorrow.</span>", unsafe_allow_html=True)
        
        history_upload = st.file_uploader("1. Restore History Log", type="csv")
        if history_upload is not None:
            restored_df = pd.read_csv(history_upload)
            restored_df.to_csv(HistoryManager.FILE_NAME, index=False)
            st.success("✅ History Restored!")
            
        if os.path.exists(HistoryManager.FILE_NAME):
            with open(HistoryManager.FILE_NAME, "rb") as f:
                st.download_button(
                    label="2. Download Backup 💾",
                    data=f,
                    file_name=f"history_backup_{datetime.now(EGYPT_TZ).strftime('%Y%m%d')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )

    filtered_df = df.copy()
    if len(companies) > 0: filtered_df = filtered_df[filtered_df['Company Name'].isin(selected_companies)]
    if len(statuses) > 0: filtered_df = filtered_df[filtered_df['sample status'].isin(selected_statuses)]

    num_tests_col = next((c for c in filtered_df.columns if 'NUM' in c.upper() and 'TEST' in c.upper()), None)
    if num_tests_col:
        filtered_df[num_tests_col] = pd.to_numeric(filtered_df[num_tests_col], errors='coerce').fillna(0)
    
    if 'DURATION' in filtered_df.columns:
        filtered_df['DURATION'] = pd.to_numeric(filtered_df['DURATION'], errors='coerce')

    # Data Calculations
    total_requests_count = len(filtered_df)
    total_tests_count = int(filtered_df[num_tests_col].sum() if num_tests_col else 0)
    avg_dpl_value = round(pd.to_numeric(filtered_df['AVERAGE VALUE'], errors='coerce').mean() if 'AVERAGE VALUE' in filtered_df.columns else 0, 2)
    avg_duration_value = round(filtered_df['DURATION'].mean(), 1) if 'DURATION' in filtered_df.columns else 0
    total_paperwork_pages = int(filtered_df[next((c for c in filtered_df.columns if 'PAGE' in c.upper()), None)].sum() if next((c for c in filtered_df.columns if 'PAGE' in c.upper()), None) else 0)

    current_metrics = {
        "File_Name": uploaded_file.name, 
        "Total_Requests": total_requests_count,
        "Total_Tests": total_tests_count,
        "Avg_DPL": avg_dpl_value,
        "Avg_Duration": avg_duration_value,
        "Total_Paperwork": total_paperwork_pages
    }

    st.markdown(f"**📂 Active Data Source:** `{uploaded_file.name}`")
    col_btn, col_msg = st.columns([0.2, 0.8])
    with col_btn:
        if st.button("💾 Save to BI History"):
            HistoryManager.save_metrics(current_metrics)
            st.success("✅ Logged Successfully!")
            st.rerun() 

    # ==========================================
    # 7. Core KPIs Section
    # ==========================================
    st.markdown("### 📊 Executive Key Performance Indicators")
    col1, col2, col3, col4, col5 = st.columns(5)
    
    d1 = HistoryManager.get_delta_html(current_metrics["Total_Requests"], "Total_Requests", uploaded_file.name)
    create_card(col1, "Total Submittals", current_metrics["Total_Requests"], delta_html=d1)
    
    d2 = HistoryManager.get_delta_html(current_metrics["Total_Tests"], "Total_Tests", uploaded_file.name)
    create_card(col2, "Total Tests", current_metrics["Total_Tests"], delta_html=d2)
    
    d3 = HistoryManager.get_delta_html(current_metrics["Avg_DPL"], "Avg_DPL", uploaded_file.name)
    create_card(col3, "Avg DPL Value", current_metrics["Avg_DPL"], delta_html=d3)

    d4 = HistoryManager.get_delta_html(current_metrics["Avg_Duration"], "Avg_Duration", uploaded_file.name)
    create_card(col4, "Avg. Dur (Days)", current_metrics["Avg_Duration"], delta_html=d4)
    
    d5 = HistoryManager.get_delta_html(current_metrics["Total_Paperwork"], "Total_Paperwork", uploaded_file.name)
    create_card(col5, "Total Paperwork", current_metrics["Total_Paperwork"], delta_html=d5)

    # --- Speedometer & Simulator Row ---
    g_col, s_col = st.columns([0.4, 0.6])
    with g_col:
        overall_acc = len(filtered_df[filtered_df['sample status'].astype(str).str.upper().isin(['ACCEPTED', 'APPROVED AS NOTED'])]) if 'sample status' in filtered_df.columns else 0
        overall_rate = (overall_acc / total_requests_count * 100) if total_requests_count > 0 else 0
        
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number", value=overall_rate,
            title={'text': "Overall Approval Index", 'font': {'size': 20, 'color': 'white'}},
            number={'suffix': "%", 'font': {'size': 40, 'color': 'white'}},
            gauge={
                'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "rgba(255,255,255,0.2)"},
                'bar': {'color': "#ffffff", 'thickness': 0.25},
                'bgcolor': "rgba(255,255,255,0.05)",
                'steps': [{'range': [0, 60], 'color': "#e74c3c"}, {'range': [60, 85], 'color': "#f1c40f"}, {'range': [85, 100], 'color': "#2ecc71"}],
            }
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

    # ==========================================
    # 🔥 8. NEW: VISUAL SITE NAVIGATOR (3D View Prototype) 🔥
    # ==========================================
    st.markdown('<div class="bi-title">🗺️ Visual Site Navigator (Interactive Layout)</div>', unsafe_allow_html=True)
    
    col_map, col_info = st.columns([0.7, 0.3])
    
    with col_map:
        st.markdown('<div class="visual-frame">', unsafe_allow_html=True)
        
        bh_col_name = next((col for col in filtered_df.columns if str(col).strip().upper() in ['ELEMENT', 'ELMENT', 'BH', 'LOCATION']), None)
        
        if bh_col_name:
            unique_elements = filtered_df[bh_col_name].dropna().unique()
            # Generate dummy coordinates for demonstration
            map_data = pd.DataFrame({
                'Element': unique_elements,
                'x': np.random.uniform(10, 90, size=len(unique_elements)),
                'y': np.random.uniform(10, 90, size=len(unique_elements))
            })

            fig_map = go.Figure()

            # Placeholder for actual background image (Will be replaced with real layout URL later)
            # fig_map.add_layout_image(dict(source="URL_TO_YOUR_IMAGE.jpg", x=0, y=100, sizex=100, sizey=100, sizing="stretch", opacity=0.5, layer="below"))

            fig_map.add_trace(go.Scatter(
                x=map_data['x'], y=map_data['y'],
                mode='markers+text',
                marker=dict(size=15, color='#ffaa00', symbol='hexagon', line=dict(color='white', width=2)),
                text=map_data['Element'],
                textposition="top center",
                hovertemplate="<b>Element:</b> %{text}<br>Click to filter dashboard<extra></extra>"
            ))

            fig_map.update_layout(
                title="Interactive Project Layout (Prototype)",
                xaxis=dict(showgrid=False, zeroline=False, visible=False, range=[0, 100]),
                yaxis=dict(showgrid=False, zeroline=False, visible=False, range=[0, 100]),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                height=400,
                margin=dict(l=0, r=0, t=40, b=0)
            )
            
            st.plotly_chart(fig_map, use_container_width=True)
        else:
            st.info("Element/Location column not found to generate the map.")
            
        st.markdown('</div>', unsafe_allow_html=True)

    with col_info:
        st.info("💡 **Instructions:** This map represents your site layout. Clicking a node will instantly focus the analytics on that specific villa/element (Coming Soon).")
        st.markdown("""
        **Map Legends:**
        - 🟠 Hexagon: Active Element
        - 🟢 Green Glow: Approved Status
        - 🔴 Red Glow: Pending/Rejected
        """)

    st.markdown('<div class="gradient-divider"></div>', unsafe_allow_html=True)

    # ==========================================
    # 9. Monthly Volume & Deficit Analysis
    # ==========================================
    st.markdown('<div class="bi-title">🧪 Monthly Test Volume & Deficit Analysis</div>', unsafe_allow_html=True)
    if 'Date ( test)' in filtered_df.columns and 'Test Type' in filtered_df.columns:
        v_df = filtered_df.dropna(subset=['Date ( test)', 'Test Type']).copy()
        
        v_df['Month_Sort'] = v_df['Date ( test)'].dt.to_period('M')
        v_df['Month'] = v_df['Date ( test)'].dt.strftime('%b %Y')
        
        monthly_summary = v_df.groupby(['Month_Sort', 'Month', 'Test Type']).size().reset_index(name='Volume')
        monthly_summary = monthly_summary.sort_values('Month_Sort')
        
        fig_vol = px.bar(monthly_summary, x='Month', y='Volume', color='Test Type', barmode='group',
                         title="Testing Intensity & Production Coverage per Month",
                         color_discrete_sequence=NEON_COLORS)
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

    # ==========================================
    # 10. Workflow & Delay Risk Analysis
    # ==========================================
    st.markdown('<div class="bi-title">⏱️ Workflow & Delay Risk Analysis</div>', unsafe_allow_html=True)
    
    rejected_count = len(filtered_df[filtered_df['sample status'].isin(['REJECTED', 'REVISE'])]) if 'sample status' in filtered_df.columns else 0
    worst_office_name = "N/A"
    worst_office_delay = 0

    if 'Done BY' in filtered_df.columns and 'DURATION' in filtered_df.columns:
        office_delays = filtered_df.dropna(subset=['DURATION']).groupby('Done BY')['DURATION'].mean().reset_index()
        if not office_delays.empty:
            worst_office = office_delays.loc[office_delays['DURATION'].idxmax()]
            worst_office_name = worst_office['Done BY']
            worst_office_delay = round(worst_office['DURATION'], 1)

    r1, r2, r3 = st.columns(3)
    r1.error(f"**Rejected/Revise Samples:** {rejected_count} submittals")
    r2.warning(f"**Highest Delay Office:** {worst_office_name}")
    r3.warning(f"**Avg Delay for this Office:** {worst_office_delay} Days")

    if worst_office_name != "N/A":
        st.markdown("#### 📧 Administrative Action Center")
        if st.button("Generate Official Warning Memo"):
            memo_text = f"""SUBJECT: URGENT: Action Required - Escalating Turnaround Delays
TO: Management Team of [{worst_office_name}]
DATE: {datetime.now(EGYPT_TZ).strftime("%Y-%m-%d")}

This is an automated notification from the Project Quality BI System.

Our data analytics framework indicates a critical workflow bottleneck originating from your department. Currently, your average processing duration is [{worst_office_delay} Days], which significantly exceeds acceptable project execution constraints.

Immediate corrective action is required to expedite all pending documentation. Please submit a mitigation and recovery schedule within 24 hours.

Best Regards,
Project Quality Management Office"""
            
            st.code(memo_text, language="markdown")
            
            with st.expander(f"📋 View Audit Trail: All Log Records for [{worst_office_name}]"):
                worst_office_data = filtered_df[filtered_df['Done BY'] == worst_office_name]
                st.dataframe(worst_office_data, use_container_width=True)

    # ==========================================
    # 11. AI Predictive Analytics & Geospatial
    # ==========================================
    st.markdown('<div class="bi-title">🤖 Predictive Risk Forecasting</div>', unsafe_allow_html=True)
    if 'Date ( test)' in filtered_df.columns and 'DURATION' in filtered_df.columns:
        pred_df = filtered_df.dropna(subset=['Date ( test)', 'DURATION']).sort_values('Date ( test)')
        pred_df['7-Day Trend'] = pred_df['DURATION'].rolling(window=7, min_periods=1).mean()
        
        fig_pred = px.line(pred_df, x='Date ( test)', y=['DURATION', '7-Day Trend'], 
                           title="Duration Forecasting & Trendline Tracking",
                           color_discrete_sequence=['#ffaa00', '#00d2ff'])
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

    st.markdown('<div class="bi-title">🗺️ Sector / Zone Performance Map</div>', unsafe_allow_html=True)
    if 'Classification' in filtered_df.columns and 'Company Name' in filtered_df.columns and 'sample status' in filtered_df.columns:
        tree_df = filtered_df.copy()
        tree_df[['Classification', 'Company Name', 'sample status']] = tree_df[['Classification', 'Company Name', 'sample status']].fillna('Unknown')
        fig_tree = px.treemap(tree_df, path=['Classification', 'Company Name', 'sample status'], 
                              title="Project Hierarchy Breakdown (Click to Drill Down)",
                              color='sample status',
                              color_discrete_map={'ACCEPTED':'#2ecc71', 'REJECTED':'#ff007f', 'REVISE':'#f1c40f', 'APPROVED AS NOTED':'#00d2ff'})
        fig_tree = style_3d_glassy(fig_tree, chart_type="treemap")
        st.plotly_chart(fig_tree, use_container_width=True)

    # ==========================================
    # 🔥 12. Automated Smart PDF Executive Report 🔥
    # ==========================================
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

    # ==========================================
    # 13. KPI Trend Tracker (Historical Growth)
    # ==========================================
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

    # ==========================================
    # 14. Test Type Breakdown & Quality Distributions
    # ==========================================
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

    # ==========================================
    # 15. Strategic Insights & Recommendation Charts
    # ==========================================
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
            c1_df = filtered_df.groupby(['Company Name', 'Test Type']).size().reset_index(name='Count')
            fig_c1 = px.bar(c1_df, x='Company Name', y='Count', color='Test Type', title="Workload per Contractor 🏢", color_discrete_sequence=NEON_COLORS)
            fig_c1 = style_3d_glassy(fig_c1, chart_type="bar")
            st.plotly_chart(fig_c1, use_container_width=True)
            
        if 'Done BY' in filtered_df.columns and 'Test Type' in filtered_df.columns:
            c2_df = filtered_df.groupby(['Done BY', 'Test Type']).size().reset_index(name='Count')
            fig_c2 = px.bar(c2_df, x='Done BY', y='Count', color='Test Type', title="Office Performance Analysis (Done BY) 👨‍💼", color_discrete_sequence=NEON_COLORS)
            fig_c2 = style_3d_glassy(fig_c2, chart_type="bar")
            st.plotly_chart(fig_c2, use_container_width=True)

    with chart_col2:
        if 'sample status' in filtered_df.columns:
            fig_p1 = px.pie(filtered_df, names='sample status', hole=0.4, title="Sample Status Distribution 🟢🔴", color_discrete_map={'ACCEPTED':'#2ecc71', 'REJECTED':'#ff007f', 'REVISE':'#f1c40f', 'APPROVED AS NOTED':'#00d2ff'})
            fig_p1 = style_3d_glassy(fig_p1, chart_type="pie")
            st.plotly_chart(fig_p1, use_container_width=True)
        
        if 'Classification' in filtered_df.columns:
            class_df = filtered_df.dropna(subset=['Classification']).copy()
            if not class_df.empty:
                fig_p2 = px.pie(class_df, names='Classification', title="Sample Classification Distribution 📑", color_discrete_sequence=NEON_COLORS)
                fig_p2 = style_3d_glassy(fig_p2, chart_type="pie")
                st.plotly_chart(fig_p2, use_container_width=True)

    st.markdown('<div class="gradient-divider"></div>', unsafe_allow_html=True)

    # ==========================================
    # 16. Contractor Materials & Sourcing Analysis
    # ==========================================
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
        
        st.markdown("#### 🏢 Individual Contractor Deep Dive")
        comp_list = sorted([c for c in mat_df['Company Name'].unique() if str(c) != 'nan'])
        
        if comp_list:
            selected_comp = st.selectbox("Select a Contractor to Analyze:", comp_list)
            comp_df = mat_df[mat_df['Company Name'] == selected_comp]
            
            stock_count = len(comp_df[comp_df['Loc_Category'] == 'Stockpile'])
            bottom_count = len(comp_df[comp_df['Loc_Category'] == 'Bottom of Excavation'])
            fill_count = len(comp_df[comp_df['Loc_Category'] == 'Fill'])
            
            cc1, cc2, cc3 = st.columns(3)
            create_card(cc1, "Stockpile Samples", stock_count)
            create_card(cc2, "Bottom Excavation", bottom_count)
            create_card(cc3, "Fill Samples", fill_count)
            
            ch_col1, ch_col2 = st.columns(2)
            
            with ch_col1:
                stock_df = comp_df[comp_df['Loc_Category'] == 'Stockpile']
                if 'Classification' in stock_df.columns and not stock_df.empty:
                    fig_class = px.pie(stock_df, names='Classification', title=f"Stockpile Classifications for {selected_comp}", hole=0.3, color_discrete_sequence=NEON_COLORS)
                    fig_class = style_3d_glassy(fig_class, chart_type="pie")
                    st.plotly_chart(fig_class, use_container_width=True)
                else:
                    st.info(f"No Stockpile classification data logged for {selected_comp}.")
                    
            with ch_col2:
                if 'sample status' in comp_df.columns and not comp_df.empty:
                    fig_status = px.pie(comp_df, names='sample status', title=f"Overall Approval/Rejection Rate for {selected_comp}", hole=0.3,
                                        color='sample status',
                                        color_discrete_map={'ACCEPTED':'#2ecc71', 'REJECTED':'#ff007f', 'REVISE':'#f1c40f', 'APPROVED AS NOTED':'#00d2ff'})
                    fig_status = style_3d_glassy(fig_status, chart_type="pie")
                    st.plotly_chart(fig_status, use_container_width=True)
                else:
                    st.info(f"No status data logged for {selected_comp}.")

    st.markdown('<div class="gradient-divider"></div>', unsafe_allow_html=True)

    # ==========================================
    # 17. Timeline Analysis
    # ==========================================
    st.markdown("### 📈 Timeline Analysis")
    time_col1, time_col2 = st.columns(2)
    
    with time_col1:
        if 'Date ( test)' in filtered_df.columns:
            filtered_df['Month_Plot'] = filtered_df['Date ( test)'].dt.to_period('M').astype(str)
            monthly_data = filtered_df.groupby('Month_Plot').size().reset_index(name='Count')
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

    # ==========================================
    # 🔥 18. ADVANCED Element Quality Auditor (Zone-Aware) 🔥
    # ==========================================
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
                
                # Smart Zone Filter (Radio Buttons)
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

                    st.markdown("#### 👨‍🔧 Office & Execution Matrix")
                    if 'Test Type' in bh_df.columns and 'Done BY' in bh_df.columns:
                        bh_df['Execution_Node'] = np.where(bh_df['layer'].astype(str).str.contains(r'\d'), bh_df['layer'], bh_df['Sampling Location'])
                        bh_df['Execution_Node'] = bh_df['Execution_Node'].fillna('General Location')
                        
                        fig_matrix = px.treemap(bh_df, path=['Done BY', 'Test Type', 'Execution_Node'], 
                                              title=f"Who did What & Where in {selected_bh}",
                                              color='Done BY', color_discrete_sequence=NEON_COLORS)
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

    # ==========================================
    # 19. Complete Operational Records
    # ==========================================
    with st.expander("📂 View Complete Operational Records (Raw Data)"):
        st.dataframe(filtered_df, use_container_width=True)

else:
    st.info("👈 Please connect a Data Source or Upload a CSV to activate the Enterprise Engine.")

```