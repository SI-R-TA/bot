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

COPY my_database.db /app/my_database.db

RUN chown -R appuser:appuser /app

ENV PATH="/home/appuser/.local/bin:${PATH}"

EXPOSE 8080

CMD ["python", "MI.PY"]
