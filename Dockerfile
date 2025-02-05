FROM python:3.9  # أو الصورة الأساسية التي تستخدمها

USER root

# تحديث وتثبيت sudo و bash
RUN apt-get update && apt-get install -y sudo
RUN sudo apt-get update && sudo apt-get install -y bash

USER appuser

# نسخ ملف requirements.txt وتثبيت التبعيات
COPY requirements.txt /app/
RUN pip install -r /app/requirements.txt

# نسخ باقي ملفات المشروع
COPY . /app

# تعيين مجلد العمل
WORKDIR /app

# الأمر الذي سيتم تشغيله عند بدء تشغيل الحاوية
CMD ["python", "sirta_command.py"]  # أو الأمر المناسب لتشغيل تطبيقك
