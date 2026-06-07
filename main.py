import streamlit as st
import pandas as pd
import numpy as np
import easyocr
from PIL import Image
import re

st.set_page_config(page_title="ماسح تقارير التربة المطور", layout="wide")

@st.cache_resource
def load_ocr():
    return easyocr.Reader(['en'])

reader = load_ocr()

st.title("🏗️ نظام تحليل Evd الذكي")
picture = st.camera_input("صور الجدول بوضوح")

if picture:
    img = Image.open(picture)
    results = reader.readtext(np.array(img))
    
    raw_data = []
    for (bbox, text, prob) in results:
        # 1. تنظيف النص من أي حروف أو رموز غريبة
        clean_text = re.sub(r'[^\d.,]', '', text)
        clean_text = clean_text.replace(',', '.')
        
        try:
            val = float(clean_text)
            # 2. منطق تصحيح العلامة العشرية (لو الرقم أكبر من 150 مثلاً يبقى أكيد محتاج علامة)
            if val > 150:
                val = val / 100
            
            # 3. التأكد إننا بناخد الأرقام المنطقية لعمود الـ Evd فقط
            if 10 < val < 100:
                raw_data.append(round(val, 2))
        except:
            continue

    if raw_data:
        # عرض النتائج في جدول
        df = pd.DataFrame({"القيم المصححة (Evd)": raw_data})
        
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("📋 الجدول بعد التصحيح")
            st.dataframe(df, use_container_width=True)
            
        with col2:
            st.subheader("📊 التحليل الإحصائي")
            st.metric("المتوسط (Mean)", f"{np.mean(raw_data):.2f}")
            st.metric("الانحراف المعياري (Std)", f"{np.std(raw_data):.2f}")
            st.metric("المجموع (Total)", f"{sum(raw_data):.2f}")

        # تصدير إكسيل احترافي
        csv = df.to_csv(index=False).encode('utf-8-sig')
        st.download_button("📥 تحميل النتائج كـ Excel", data=csv, file_name="soil_report.csv")
    else:
        st.error("لم يتم العثور على أرقام واضحة. حاول تقريب الكاميرا من العمود الثاني.")