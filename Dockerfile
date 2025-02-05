FROM python:3.9

USER root

RUN apt-get update && apt-get install -y sudo

RUN sudo apt-get update && sudo apt-get install -y bash

USER appuser

COPY requirements.txt /app/

RUN pip install -r /app/requirements.txt

COPY . /app  # Added a dot before the slash

WORKDIR /app

RUN chmod +x /app/sirta_command.py  # Added chmod instruction

CMD ["python", "sirta_command.py"]  # Changed CMD instruction
