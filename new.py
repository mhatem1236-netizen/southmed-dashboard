import streamlit as st
import pandas as pd
import plotly.express as px
import os
import json
from datetime import datetime

# ==========================================
# 1. Configuration Layer (طبقة الإعدادات)
# ==========================================
class ConfigManager:
    @staticmethod
    def load_config():
        try:
            with open('config.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            # إعدادات افتراضية لو الملف مش موجود
            return {
                "project_name": "South Med QC Dashboard",
                "consulting_office": "Engineering Office",
                "logo_filename": "شششششششش.JPG",
                "cover_filename": "5.jpg",
                "primary_color": "#1e3d59",
                "history_file": "analysis_history.csv"
            }

CONFIG = ConfigManager.load_config()

# ==========================================
# 2. Data & Logic Layer (طبقة معالجة البيانات)
# ==========================================
class DataProcessor:
    def __init__(self, df):
        self.raw_df = df
        self.clean_df = self._clean_data()
        self.num_tests_col = next((c for c in self.clean_df.columns if 'NUM' in c.upper() and 'TEST' in c.upper()), None)

    def _clean_data(self):
        df = self.raw_df.copy()
        df.columns = df.columns.str.strip()
        if 'Test Type' in df.columns: df['Test Type'] = df['Test Type'].str.strip().str.upper()
        if 'Date ( test)' in df.columns: df['Date ( test)'] = pd.to_datetime(df['Date ( test)'], errors='coerce')
        if 'Date( SUB)' in df.columns: df['Date( SUB)'] = pd.to_datetime(df['Date( SUB)'], errors='coerce')
        return df

    def filter_data(self, companies, statuses):
        df = self.clean_df.copy()
        if companies: df = df[df['Company Name'].isin(companies)]
        if statuses: df = df[df['sample status'].isin(statuses)]
        if self.num_tests_col: df[self.num_tests_col] = pd.to_numeric(df[self.num_tests_col], errors='coerce').fillna(0)
        return df

class HistoryTracker:
    @staticmethod
    def save_snapshot(metrics_dict):
        history_file = CONFIG["history_file"]
        metrics_dict['timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        history_df = pd.concat([pd.read_csv(history_file), pd.DataFrame([metrics_dict])], ignore_index=True) if os.path.exists(history_file) else pd.DataFrame([metrics_dict])
        history_df.to_csv(history_file, index=False)
        return history_df

    @staticmethod
    def get_history():
        return pd.read_csv(CONFIG["history_file"]) if os.path.exists(CONFIG["history_file"]) else None

# ==========================================
# 3. UI Presentation Layer (طبقة الواجهة)
# ==========================================
class DashboardUI:
    @staticmethod
    def apply_styles():
        st.markdown(f"""
            <style>
            .metric-card {{
                background-color: {CONFIG['primary_color']}; padding: 20px; border-radius: 10px;
                text-align: center; border: 1px solid #30363d; margin-bottom: 10px;
            }}
            .metric-label {{ color: #d1d5da; font-size: 16px; font-weight: bold; margin-bottom: 5px; }}
            .metric-value {{ color: #ffffff !important; font-size: 28px; font-weight: bold; }}
            .delta-pos {{ color: #28a745 !important; font-size: 14px; font-weight: bold; }}
            .delta-neg {{ color: #dc3545 !important; font-size: 14px; font-weight: bold; }}
            </style>
            """, unsafe_allow_html=True)

    @staticmethod
    def render_header():
        st.set_page_config(page_title=CONFIG['project_name'], layout="wide")
        DashboardUI.apply_styles()
        try: st.image(CONFIG['cover_filename'], use_container_width=True)
        except: pass
        col_h1, col_h2 = st.columns([0.8, 0.2])
        col_h1.title(f"{CONFIG['project_name']} 🏗️🤖")
        try: col_h2.image(CONFIG['logo_filename'], width=120)
        except: pass

    @staticmethod
    def metric_card(col, label, value, history_df=None, metric_key=None):
        delta_html = ""
        if history_df is not None and metric_key and len(history_df) > 1:
            prev_val = history_df.iloc[-2][metric_key]
            if prev_val != 0:
                change = ((value - prev_val) / prev_val) * 100
                color, symbol = ("delta-pos", "▲") if change >= 0 else ("delta-neg", "▼")
                delta_html = f'<div class="{color}">{symbol} {abs(round(change, 1))}%</div>'

        col.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">{label}</div>
                <div class="metric-value">{value:,}</div>
                {delta_html}
            </div>""", unsafe_allow_html=True)

# ==========================================
# 4. Main Application Flow (طبقة التشغيل)
# ==========================================
def main():
    DashboardUI.render_header()
    uploaded_file = st.file_uploader("Upload QC Log (CSV)", type="csv")

    if uploaded_file:
        processor = DataProcessor(pd.read_csv(uploaded_file))
        
        # Sidebar
        try: st.sidebar.image(CONFIG['logo_filename'], use_container_width=True)
        except: pass
        st.sidebar.markdown(f"**{CONFIG['consulting_office']}**")
        st.sidebar.divider()

        comps = processor.clean_df['Company Name'].dropna().unique() if 'Company Name' in processor.clean_df.columns else []
        sel_comps = st.sidebar.multiselect("Contractor:", comps, default=comps)
        
        filtered_df = processor.filter_data(sel_comps, [])
        num_col = processor.num_tests_col

        # Calculate Globals
        t_req = len(filtered_df)
        t_tests = int(filtered_df[num_col].sum() if num_col else 0)
        a_dpl = round(pd.to_numeric(filtered_df['AVERAGE VALUE'], errors='coerce').mean(), 2)
        a_dur = round(pd.to_numeric(filtered_df['DURATION'], errors='coerce').mean(), 1)

        # History Actions
        if st.button("💾 Save Update & Compare Growth"):
            HistoryTracker.save_snapshot({"reqs": t_req, "tests": t_tests, "dpl": a_dpl, "dur": a_dur})
            st.success("History updated!")
        
        hist_df = HistoryTracker.get_history()

        # Render Metrics
        st.markdown("### 📊 Live Performance Metrics")
        k1, k2, k3, k4 = st.columns(4)
        DashboardUI.metric_card(k1, "Total Requests", t_req, hist_df, "reqs")
        DashboardUI.metric_card(k2, "Total Tests Sum", t_tests, hist_df, "tests")
        DashboardUI.metric_card(k3, "Avg. DPL Value", a_dpl, hist_df, "dpl")
        DashboardUI.metric_card(k4, "Avg. Duration", a_dur, hist_df, "dur")
        
        st.divider()

        # Render Charts
        c1, c2 = st.columns(2)
        with c1: st.plotly_chart(px.bar(filtered_df, x='Company Name', color='Test Type', title="Workload"), use_container_width=True)
        with c2: st.plotly_chart(px.pie(filtered_df, names='sample status', hole=0.4, title="Status"), use_container_width=True)

        if hist_df is not None:
            st.plotly_chart(px.line(hist_df, x='timestamp', y=['tests', 'reqs'], markers=True, title="Growth Over Time"), use_container_width=True)

        st.dataframe(filtered_df, use_container_width=True)
    else:
        st.info("Please upload the log file to start the engine.")

if __name__ == "__main__":
    main()