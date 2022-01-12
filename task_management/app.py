import json
import sqlite3
import threading

from flask import Flask
from flask import g
from flask import request
from kafka import KafkaConsumer

app = Flask(__name__)
DATABASE = 'database.db'
BOOT_STRAP_SERVERS = 'kafka:9092'


@app.route("/")
def index():
    page_html = """
  <h1>hello task_management!!!!helloworldwwwwwwwwwww</h1>
  """
    return page_html


@app.route('/see')
def see():
    db = get_db()
    cur = db.execute('select * from task')
    rv = cur.fetchall()
    cur.close()
    return str(rv)


@app.route('/task')
def task():
    id = request.args.get('id', None)
    if id is None:
        return f'fail! input your id!'
    db = get_db()
    cur = db.execute('select content, isover from task where userid = ' + str(id))
    rv = cur.fetchall()
    cur.close()
    return str(rv)


@app.route('/report')
def report():
    print('report!')
    # name = request.args.get('name',None)
    # department = request.args.get('department', None)
    db = get_db()
    sql = 'select department, sum(task_unfinished) from task group by department '
    rs = db.execute(sql)
    return rs.fetchall().__str__()

def kafka_listener(data):
    print(data)

# def report():
#     department = request.args.get('department', None)
#     if department is None:
#         return f'fail! input department!'
#     db = get_db()
#     sql_query = " select count(*) from task where department= '" + str(department) + " ' and isover=1"
#     cur = db.execute(sql_query)
#     rv = cur.fetchall()
#     cur.close()
#     return str(department) + ":" + str(rv)


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
def register_kafka_employee(topic='register_task', listener=kafka_listener):
    # Poll kafka
    def poll():
        # Initialize consumer Instance
        consumer = KafkaConsumer(topic, bootstrap_servers=BOOT_STRAP_SERVERS, api_version=(0, 10, 2),
                                 auto_offset_reset='earliest',
                                 enable_auto_commit=True,
                                 auto_commit_interval_ms=100,
                                 group_id='task')
        print("About to start polling for topic:", topic)
        print("Started Polling for topic:", topic)
        for msg in consumer:
            print("Entered the loop\nKey: ", msg.key.decode(), " Value:", msg.value.decode())
            with app.app_context():
                msg_json = eval(msg.value.decode())
                insert_task(msg_json['name'], msg_json['department'], 1)
            listener(msg)

    print("About to register listener to topic:", topic)
    t1 = threading.Thread(target=poll)
    t1.start()
    print("started a background thread")


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


# 消费员工激活密码消息，更新 未完成的任务 为已完成
def kafka_change_password(topic='update_passwd', listener=kafka_listener):
    # Poll kafka
    def poll():
        # Initialize consumer Instance
        consumer = KafkaConsumer(topic, bootstrap_servers=BOOT_STRAP_SERVERS, api_version=(0, 10, 2),
                                 auto_offset_reset='earliest',
                                 enable_auto_commit=True,
                                 auto_commit_interval_ms=100,
                                 group_id='task')
        print("About to start polling for topic:", topic)
        print("Started Polling for topic:", topic)
        for msg in consumer:
            print("Entered the loop\nKey: ", msg.key.decode(), " Value:", msg.value.decode())
            with app.app_context():
                msg_json = eval(msg.value.decode())
                activate_user(msg_json['name'])
            listener(msg)

    print("About to register listener to topic:", topic)
    t1 = threading.Thread(target=poll)
    t1.start()
    print("started a background thread")


# 消费员工更换部门消息，更新 任务的部门 为 新部门
def kafka_change_department(topic='update_department', listener=kafka_listener):
    # Poll kafka
    def poll():
        # Initialize consumer Instance
        consumer = KafkaConsumer(topic, bootstrap_servers=BOOT_STRAP_SERVERS, api_version=(0, 10, 2),
                                 auto_offset_reset='earliest',
                                 enable_auto_commit=True,
                                 auto_commit_interval_ms=100,
                                 group_id='task'
                                 )
        print("About to start polling for topic:", topic)
        print("Started Polling for topic:", topic)
        for msg in consumer:
            print("Entered the loop\nKey: ", msg.key.decode(), " Value:", msg.value.decode())
            with app.app_context():
                msg_json = eval(msg.value.decode())
                change_department(msg_json['department'], msg_json['name'])
            listener(msg)

    print("About to register listener to topic:", topic)
    t1 = threading.Thread(target=poll)
    t1.start()
    print("started a background thread")


def activate_user(user):
    db = get_db()
    sql = 'update task set task_unfinished=0 where `user`="{}" '.format(user)
    print(sql)
    cur = db.execute(sql)
    db.commit()
    cur.close()


def change_department(department, user):
    db = get_db()
    sql = 'update task set department="{}" where `user`="{}" '.format(department, user)
    print(sql)
    cur = db.execute(sql)
    db.commit()
    cur.close()


if __name__ == "__main__":
    # init_db()
    register_kafka_employee(topic='register_task', listener=kafka_listener)  # {'name':'', 'department':''}
    kafka_change_password(topic='update_passwd', listener=kafka_listener)  # {'name':''}
    kafka_change_department(topic='update_department', listener=kafka_listener)  # {'name':'', 'department':''}
    app.run(debug=False, host='0.0.0.0', port=6003)
