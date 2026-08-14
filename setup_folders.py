import os

# الفولدرات اللي محتاجينها
folders = ['utils', 'modules', 'data']

# الملفات اللي جوه كل فولدر
files = [
    'utils/__init__.py', 'utils/config.py', 'utils/ui_styles.py', 
    'utils/db_manager.py', 'utils/ai_engine.py', 'utils/export_tools.py',
    'modules/__init__.py', 'modules/auth.py', 'modules/home.py', 
    'modules/analytics_hub.py', 'modules/site_mobile.py', 'modules/main_dashboard.py'
]

# كود الإنشاء
for folder in folders:
    os.makedirs(folder, exist_ok=True)

for file in files:
    with open(file, 'w') as f:
        pass

print("✅ تم إنشاء جميع المجلدات والملفات بنجاح!")