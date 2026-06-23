import streamlit as st
import pandas as pd
import numpy as np
import easyocr
import cv2
from PIL import Image

# إعدادات الصفحة
st.set_page_config(page_title="ماسح Evd الدقيق", layout="wide")

@st.cache_resource
def load_ocr():
    # تحميل الموديل مرة واحدة فقط لتوفير الوقت والرامات
    return easyocr.Reader(['en'], gpu=False) # جرب False لو الجهاز بيهنج، True لو عندك كارت شاشة قوي

reader = load_ocr()

st.title("🏗️ نظام قراءة عمود Evd الحصري")
st.write("صور الجدول، والبرنامج هيقص العمود الثاني ويحلله تلقائياً.")

picture = st.camera_input("صور الجدول بوضوح تام")

if picture:
    # 1. تحويل الصورة لتنسيق OpenCV
    file_bytes = np.asarray(bytearray(picture.read()), dtype=np.uint8)
    img = cv2.imdecode(file_bytes, 1)
    height, width, _ = img.shape

    # 2. تحديد منطقة عمود الـ Evd (القص - ROI)
    # بناءً على صورك، عمود الـ Evd بيبدأ تقريباً بعد 15% من عرض الصورة وبياخد حوالي 15% كمان.
    # والجدول بيبدأ من نص الورقة تقريباً (50% من الارتفاع) لحد آخرها.
    
    x_start = int(width * 0.15) # بداية القص أفقياً (15% من العرض)
    x_end = int(width * 0.30)   # نهاية القص أفقياً (30% من العرض)
    y_start = int(height * 0.45) # بداية القص رأسياً (من منتصف الجدول تقريباً)
    y_end = height              # نهاية القص رأسياً (لآخر الصورة)

    # عملية القص الفعلية
    cropped_img = img[y_start:y_end, x_start:x_end]

    # 3. معالجة الصورة المقصوصة لتحسين القراءة
    gray = cv2.cvtColor(cropped_img, cv2.COLOR_BGR2GRAY)
    # زيادة التباين (Contrast) وتوضيح الأرقام
    enhanced_img = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]

    # عرض الصورة المقصوصة للتأكد إننا بنقرأ المكان الصح
    st.image(enhanced_img, caption="المنطقة التي تم قصها وقراءتها (عمود Evd فقط)", width=200)

    with st.spinner('جاري تحليل العمود الثاني بدقة...'):
        # 4. قراءة الأرقام من الصورة المقصوصة فقط
        results = reader.readtext(enhanced_img)
        
        evd_values = []
        for (bbox, text, prob) in results:
            # تنظيف النص من أي حروف أو فواصل غلط
            clean_text = text.replace(',', '.').strip()
            
            try:
                # التأكد إنه رقم
                val = float(clean_text)
                
                # منطق هندسي لتصحيح العلامة العشرية (بناءً على شغلك)
                if val > 150: # رقم كبير جداً (زي 4327)
                    val = val / 100
                elif val > 10 and val < 100: # رقم مظبوط (زي 43.27)
                    pass
                elif val < 10: # رقم صغير جداً (زي 4.32)
                    pass # ممكن يكون غلط في العلامة برضه بس هنسيبه
                
                # إضافة القيم المنطقية فقط لعمود Evd
                if val > 5: # فلتر بسيط لاستبعاد أرقام الاختبار الصغيرة (لو اتوجدت)
                    evd_values.append(val)
            except:
                continue

    if evd_values:
        # 5. عرض النتائج والعمليات الحسابية
        df = pd.DataFrame({"رقم الاختبار": range(1, len(evd_values)+1), "Evd [MN/m²]": evd_values})
        
        col1, col2 = st.columns([2, 1])
        with col1:
            st.subheader("📋 قيم Evd المستخرجة (العمود 2)")
            # خاصية التعديل اليدوي (للدقة النهائية)
            edited_df = st.data_editor(df, num_rows="dynamic", use_container_width=True)
            
        with col2:
            st.subheader("📊 الإحصاء النهائي")
            current_vals = edited_df["Evd [MN/m²]"].tolist()
            st.metric("المتوسط الحسابي (Mean)", f"{np.mean(current_vals):.2f}")
            st.metric("الانحراف المعياري (Std)", f"{np.std(current_vals):.2f}")
            st.metric("عدد العينات", len(current_vals))

        # تصدير إكسيل
        csv = edited_df.to_csv(index=False).encode('utf-8-sig')
        st.download_button("📥 تحميل التقرير (Excel)", data=csv, file_name="Evd_Report.csv")
    else:
        st.error("لم يتم العثور على أرقام في عمود Evd. تأكد من توجيه الكاميرا جيداً على الجدول.")