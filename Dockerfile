FROM python:3.9  # أو الصورة الأساسية التي تفضلها

USER root  # التبديل إلى مستخدم الجذر

RUN apt-get update && apt-get install -y bash

USER appuser  # التبديل مرة أخرى إلى مستخدم غير جذر (مهم للأمان)

COPY . /app
WORKDIR /app

CMD ["bash", "start"]
