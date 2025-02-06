FROM python:3.9

USER root

RUN apt-get update && apt-get install -y sudo

RUN sudo apt-get update && sudo apt-get install -y bash

RUN useradd -ms /bin/bash appuser

USER appuser

COPY requirements.txt /app/

RUN pip install --user -r /app/requirements.txt

COPY . /app

WORKDIR /app

# تغيير ملكية المجلد الذي يحتوي على قاعدة البيانات
RUN chown -R appuser:appuser /app/db  
# تأكد من أن المسار صحيح

# نسخ ملف قاعدة البيانات
COPY db/your_database.db /app/db/your_database.db 
# استبدل your_database.db باسم ملفك

ENV PATH="/home/appuser/.local/bin:${PATH}"

EXPOSE 8080

CMD ["python", "MI.PY"]
