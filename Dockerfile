# استخدام نسخة Alpine المستقرة والآمنة جداً
FROM python:3.10-alpine

# تحديد مجلد العمل داخل الحاوية
WORKDIR /app

# نسخ ملف المتطلبات
COPY requirements.txt .

# تثبيت مكتبة Flask مباشرة دون الحاجة لأدوات بناء إضافية
RUN pip install --no-cache-dir -r requirements.txt

# نسخ بقية ملفات المشروع
COPY . .

# منفذ الاتصال
EXPOSE 5000

# أمر التشغيل
CMD ["python", "app.py"]