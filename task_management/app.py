import json
import traceback

from flask import Flask
from flask import request
from kafka.errors import kafka_errors
from markupsafe import escape
from flask import g
import sqlite3
from kafka import KafkaProducer
from kafka import KafkaConsumer
import threading

app = Flask(__name__)
DATABASE = 'database.db'
BOOT_STRAP_SERVERS = 'kafka:9092'


@app.route("/")
def index():
    page_html = """
  <h1>hello task_management!!!!</h1>
  """
    return page_html


@app.route('/see')
def see():
    db = get_db()
    cur = db.execute('select * from user')
    rv = cur.fetchall()
    cur.close()
    return str(rv)


@app.route('/register')
def register():
    password = request.args.get('password', None)
    if password is None:
        return f'fail! input your password!'
    db = get_db()
    try:
        sql_insert = 'insert into user (password) values (\'' + password + '\')'
        cur = db.execute(sql_insert)
        db.commit()
        cur.close()
        return f'create successfully! your password: {escape(password)}'
    except:
        return f'fail! illegal password!'


def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db


@app.teardown_appcontext
def close_connection(exception):
    print('close_connection')
    db = getattr(g, '_database', None)
    if db is not None:
        print('db close')
        db.close()


def init_db():
    with app.app_context():
        db = get_db()
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()


# 消费员工注册消息，产生一条未完成的任务
def register_kafka_employee(topic='register_employee'):
    # Poll kafka
    def poll():
        # Initialize consumer Instance
        consumer = KafkaConsumer(topic, bootstrap_servers=BOOT_STRAP_SERVERS)
        consumer.subscribe(topics=[topic])
        print("About to start polling for topic:", topic)
        consumer.poll(timeout_ms=6000)
        print("Started Polling for topic:", topic)
        for msg in consumer:
            print("Entered the loop\nKey: ", msg.key.decode(), " Value:", msg.value.decode())
            with app.app_context():
                msg_json = eval(msg.value.decode())
                insert_task(msg_json['name'], msg_json['department'], 1)
            kafka_listener(msg)

    print("About to register listener to topic:", topic)
    t1 = threading.Thread(target=poll)
    t1.start()
    print("started a background thread")


# 消费员工激活密码消息，更新 未完成的任务 为已完成
def kafka_change_password(topic='change_password'):
    # Poll kafka
    def poll():
        # Initialize consumer Instance
        consumer = KafkaConsumer(topic, bootstrap_servers=BOOT_STRAP_SERVERS)
        consumer.subscribe(topics=[topic])
        print("About to start polling for topic:", topic)
        consumer.poll(timeout_ms=6000)
        print("Started Polling for topic:", topic)
        for msg in consumer:
            print("Entered the loop\nKey: ", msg.key.decode(), " Value:", msg.value.decode())
            with app.app_context():
                msg_json = eval(msg.value.decode())
                activate_user(msg_json['name'])
            kafka_listener(msg)

    print("About to register listener to topic:", topic)
    t1 = threading.Thread(target=poll)
    t1.start()
    print("started a background thread")


# 消费员工更换部门消息，更新 任务的部门 为 新部门
def kafka_change_department(topic='change_department'):
    # Poll kafka
    def poll():
        # Initialize consumer Instance
        consumer = KafkaConsumer(topic, bootstrap_servers=BOOT_STRAP_SERVERS)
        consumer.subscribe(topics=[topic])
        print("About to start polling for topic:", topic)
        consumer.poll(timeout_ms=6000)
        print("Started Polling for topic:", topic)
        for msg in consumer:
            print("Entered the loop\nKey: ", msg.key.decode(), " Value:", msg.value.decode())
            with app.app_context():
                msg_json = eval(msg.value.decode())
                change_department(msg_json['department'], msg_json['name'])
            kafka_listener(msg)

    print("About to register listener to topic:", topic)
    t1 = threading.Thread(target=poll)
    t1.start()
    print("started a background thread")


def activate_user(user):
    db = get_db()
    sql = 'update task set task_unfinished=0 where and `user`="{}" ;' \
        .format(user)
    print(sql)
    cur = db.execute(sql)
    db.commit()
    cur.close()


@app.route('/changeDepartment/<string:user>/<string:department>')
def change_department(department, user):
    db = get_db()
    sql = 'update task set department="{}" where and `user`="{}" ;' \
        .format(department, user)
    print(sql)
    cur = db.execute(sql)
    db.commit()
    cur.close()


def kafka_listener(data):
    print("Image Ratings:\n", data.value.decode("utf-8"))


@app.route('/insert/<string:user>/<string:department>/<int:task_unfinished>')
def insert_task(user, department, task_unfinished):
    db = get_db()
    rs = db.execute(
        'insert into task(user, department, task_unfinished) values ("{}", "{}", "{}")'.format(user, department,
                                                                                               task_unfinished))
    db.commit()
    rs.close()
    rs = db.execute('select * from task')
    return rs.fetchall().__str__()


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


# 查询统计报表
@app.route('/report')
def report():
    print('report!')
    # name = request.args.get('name',None)
    # department = request.args.get('department', None)
    db = get_db()
    sql = 'select department, sum(task_unfinished) from task group by department '
    rs = db.execute(sql)
    return rs.fetchall().__str__()


# 测试change_password发消息
@app.route('/changePassword/<string:name>')
def changePassword(name):
    sendMessage('change_password', {'name': name})


if __name__ == "__main__":
    init_db()
    register_kafka_employee(topic='register_employee')
    kafka_change_password(topic='change_password')
    kafka_change_department(topic='change_department')
    app.run(debug=True, host='0.0.0.0', port=5001)
