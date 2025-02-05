FROM python:3.9

USER root

RUN apt-get update && apt-get install -y sudo

RUN sudo apt-get update && sudo apt-get install -y bash

USER appuser

COPY . /app

WORKDIR /app

CMD ["python", "sirta_command.py"]
