FROM python:3.9

USER root

RUN apt-get update && apt-get install -y sudo

RUN sudo apt-get update && sudo apt-get install -y bash

USER appuser

COPY requirements.txt /app/

RUN pip install -r /app/requirements.txt

COPY . /app

WORKDIR /app
RUN chmod +x /app/my_script.sh  
CMD ["bash", "sirta_command.py"]
