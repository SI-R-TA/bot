# استخدام الصورة الرسمية لـ Python 3.9
FROM python:3.9

# تعيين المستخدم root مؤقتًا لتثبيت الحزم
USER root

# تحديث الحزم وتثبيت sudo و bash (بدون أخطاء إملائية)
RUN apt-get update && apt-get install -y sudo bash

# إنشاء مستخدم جديد وإعداد مجلد التطبيق مع الصلاحيات
RUN useradd -ms /bin/bash appuser && \
    mkdir -p /app && \
    chown -R appuser:appuser /app  # منح appuser صلاحيات كاملة على /app

# التبديل إلى المستخدم appuser
USER appuser

# نسخ ملف المتطلبات وتثبيتها
COPY requirements.txt /app/
RUN pip install --user -r /app/requirements.txt

# نسخ كود التطبيق إلى مجلد /app
COPY . /app

# تعيين مجلد العمل الرئيسي
WORKDIR /app
EXPOSE 8080
# الأمر الذي يُنفَّذ عند تشغيل الحاوية
CMD ["python", "MI.PY"]
