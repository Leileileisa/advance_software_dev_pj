FROM python:3.7
MAINTAINER liuli
EXPOSE 4001

WORKDIR app
COPY ./requirements.txt /requirements.txt
COPY * /app/
RUN apt-get update -y && \
    apt-get install -y python3-pip python3-dev
RUN pip3 install -r requirements.txt
CMD python app.py
