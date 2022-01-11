FROM python:3.7
MAINTAINER leisa "leileileisa@foxmail.com"
EXPOSE 5002

WORKDIR app
COPY ./requirements.txt /requirements.txt
COPY * /app/
RUN apt-get update -y && \
    apt-get install -y python3-pip python3-dev
RUN pip3 install -r requirements.txt
CMD python app.py
