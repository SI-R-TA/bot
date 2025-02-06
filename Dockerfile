# المرحلة الأولى: بناء التطبيق وتغيير ملكية الملفات
FROM python:3.9-slim-buster AS builder

WORKDIR /app

# نسخ ملفات المتطلبات وتثبيتها
COPY requirements.txt /app/
RUN pip install --user -r /app/requirements.txt

# نسخ باقي ملفات التطبيق
COPY . /app

# تغيير ملكية الملفات إلى المستخدم appuser
RUN chown -R appuser:appuser /app

# المرحلة الثانية: إنشاء الصورة النهائية
FROM python:3.9-slim-buster

WORKDIR /app

# نسخ الملفات من المرحلة الأولى
COPY --from=builder /app /app

# نسخ قاعدة البيانات
COPY my_database.db /app/my_database.db

# تعيين متغير البيئة PATH
ENV PATH="/home/appuser/.local/bin:${PATH}"

# تعريض المنفذ
EXPOSE 8080

# تشغيل التطبيق
CMD ["python", "MI.PY"]
