# استخدام نسخة Alpine المستقرة والآمنة جداً
FROM python:3.10-alpine

# تحديد مجلد العمل
WORKDIR /app

# نسخ ملف المتطلبات
COPY requirements.txt .

# خطوة أمنية: ترقية الأدوات والمكتبات المصابة إلى نسخ آمنة وخالية من الثغرات
RUN pip install --no-cache-dir --upgrade pip setuptools wheel jaraco.context

# تثبيت متطلبات مشروعك
RUN pip install --no-cache-dir -r requirements.txt

# نسخ بقية الملفات
COPY . .

EXPOSE 5000

CMD ["python", "app.py"]