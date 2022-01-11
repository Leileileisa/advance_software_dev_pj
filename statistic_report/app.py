from flask import Flask
from flask import request
from markupsafe import escape
from flask import current_app, g
from flask import make_response
from flask import jsonify
import click
import sqlite3
import sys
from kafka import KafkaProducer
from kafka import KafkaConsumer
from kafka.errors import kafka_errors
import traceback
import threading
import json

app = Flask(__name__)
DATABASE = 'database.db'
BOOT_STRAP_SERVERS = 'kafka:9092'
# KAFKA_TOPIC = 'change__department'
@app.route("/")
def index(page_html="""
  <h1>hello statistic report</h1>
  """):
    return page_html


@app.route('/report')
def report():
    print('report!')
    # name = request.args.get('name',None)
    # department = request.args.get('department', None)
    db = get_db()
    sql = 'select department, sum(task_unfinished) from report group by department '
    rs = db.execute(sql)
    return rs.fetchall().__str__()


@app.route('/insert/<string:user>/<string:department>/<int:task_unfinished>')
def insert(user, department, task_unfinished):
    db = get_db()
    rs = db.execute('insert into task(user, department, task_unfinished) values ("{}", "{}", "{}")'.format(user, department, task_unfinished))
    db.commit()
    rs.close()
    rs = db.execute('select * from report')
    return rs.fetchall().__str__()


@app.route('/delete/<int:id>')
def delete(id):
    request.args.get('department', None)
    db = get_db()
    rs = db.execute('delete from report where id={}'.format(id))
    db.commit()
    rs.close()
    rs = db.execute('select * from report')
    rs.close()
    return rs.fetchall()


@app.route('/testSend/<string:user>/<string:old_department>/<string:new_department>')
def send(user, old_department, new_department):
    # sendMessage(KAFKA_TOPIC, {'user': user, 'old_department': old_department, 'new_department': new_department})
    return 'send!'


@app.route('/see')
def see():
    db = get_db()
    cur = db.execute('select * from employee')
    rv = cur.fetchall()
    cur.close()
    return str(rv)


@app.route('/transfer')
def transfer():
    name = request.args.get('name', None)
    department = request.args.get('department', None)
    if name is None:
        return f'fail! input your name!'
    if department is None:
        return f'fail!input your department!'
    db = get_db()
    try:
        sql_insert = 'update employee set department=' + '\'' + department + '\'' + 'where name=' + '\'' + name + '\''
        cur = db.execute(sql_insert)
        db.commit()
        cur.close()
        return f'create successfully! your Name: {escape(name)} your department:{escape(department)}'
    except:
        return f'fail! this name dont exist.'


def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


def init_db():
    with app.app_context():
        db = get_db()
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()


def sendMessage(topic, msg):
    try:
        producer = KafkaProducer(bootstrap_servers=BOOT_STRAP_SERVERS,
                                 api_version=(0, 10, 2),
                                 key_serializer=lambda k: json.dumps(k).encode('utf-8'),
                                 value_serializer=lambda v: json.dumps(v).encode('utf-8'))
        print("开始发送")
        future = producer.send(topic=topic, value=msg)
        print("发送结束")
        future.get(timeout=1000)  # 监控是否发送成功
    except kafka_errors:  # 发送失败抛出kafka_errors
        return traceback.format_exc()
    except Exception as e:
        return e


# def register_kafka_listener(topic, listener):
# # Poll kafka
#     def poll():
#         # Initialize consumer Instance
#         consumer = KafkaConsumer(topic, bootstrap_servers=BOOT_STRAP_SERVERS, api_version=(0, 10))
#         consumer.subscribe(topics=[topic])
#         print("About to start polling for topic:", topic)
#         consumer.poll(timeout_ms=6000)
#         print("Started Polling for topic:", topic)
#         for msg in consumer:
#             print("Entered the loop\nKey: ", msg.key.decode(), " Value:", msg.value.decode())
#             with app.app_context():
#                 db = get_db()
#                 msg_json = eval(msg.value.decode())
#                 sql = 'update report set department="{}" where `user`="{}" ;'\
#                     .format(msg_json['department'], msg_json['user'])
#                 print(sql)
#                 cur = db.execute(sql)
#                 db.commit()
#                 cur.close()
#             kafka_listener(msg)
#         # rs = db.execute('select * from report')
#         # return rs.fetchall().__str__()
#
#     print("About to register listener to topic:", topic)
#     t1 = threading.Thread(target=poll)
#     t1.start()
#     print("started a background thread")


def register_kafka_employee():
    topic = 'register_employee'
    # Poll kafka
    def poll():
        # Initialize consumer Instance
        consumer = KafkaConsumer(topic, bootstrap_servers=BOOT_STRAP_SERVERS, api_version=(0, 10))
        consumer.subscribe(topics=[topic])
        print("About to start polling for topic:", topic)
        consumer.poll(timeout_ms=6000)
        print("Started Polling for topic:", topic)
        for msg in consumer:
            print("Entered the loop\nKey: ", msg.key.decode(), " Value:", msg.value.decode())
            with app.app_context():
                msg_json = eval(msg.value.decode())
                insert(msg_json['name'], msg_json['department'], 1)
                # sql = 'update report set department="{}" where department="{}" and `user`="{}" ;'\
                #     .format(msg_json['new_department'], msg_json['old_department'], msg_json['user'])
                # print(sql)
            kafka_listener(msg)
        # rs = db.execute('select * from report')
        # return rs.fetchall().__str__()

    print("About to register listener to topic:", topic)
    t1 = threading.Thread(target=poll)
    t1.start()
    print("started a background thread")


def kafka_listener(data):
    print("Image Ratings:\n", data.value.decode("utf-8"))


if __name__ == "__main__":
    init_db()
    # register_kafka_listener(KAFKA_TOPIC, kafka_listener)
    app.run(debug=True, host='0.0.0.0', port=4001)
