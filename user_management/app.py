from flask import Flask
from flask import request
from markupsafe import escape
from flask import g
import sqlite3
from kafka import KafkaProducer
from kafka import KafkaConsumer
from kafka.errors import kafka_errors
import traceback
import threading
import json

app = Flask(__name__)
DATABASE = 'database.db'
BOOT_STRAP_SERVERS = 'kafka:9092'

text = []


@app.route("/")
def index():
    page_html = """
  <h1>hello user_management!!!!wwwwwww</h1>
  """
    return page_html + str(text)


@app.route('/see')
def see():
    db = get_db()
    cur = db.cursor()
    cur.execute('select * from user')
    rv = cur.fetchall()
    cur.close()
    return str(rv)


@app.route('/new_password')
def new_password():
    id = request.args.get('id', None)
    password = request.args.get('password', None)
    new_password = request.args.get('new_password', None)
    if id is None:
        return f'fail! input your id!'
    if password is None:
        return f'fail! input your password!'
    if new_password is None:
        return f'fail! input your new_password!'
    db = get_db()
    cur = db.cursor()
    text.append(new_password)
    try:
        sql_insert = 'update user set password =\'' + str(new_password) + '\' where id = ' + str(id)
        text.append(sql_insert)
        cur.execute(sql_insert)
        db.commit()
        try:
            producer = KafkaProducer(bootstrap_servers=BOOT_STRAP_SERVERS,
                                     api_version=(0, 10, 2),
                                     key_serializer=lambda k: json.dumps(k).encode('utf-8'),
                                     value_serializer=lambda v: json.dumps(v).encode('utf-8'))
            future = producer.send('update_passwd', {'name': id})
            future.get(timeout=10)  # 监控是否发送成功
        except kafka_errors:  # 发送失败抛出kafka_errors
            return traceback.format_exc()
        except Exception as e:
            return e

        return f'create new password successfully! your new_password: {escape(new_password)}'
    except:
        return f'fail! illegal password!'


def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db


@app.route('/login')
def login():
    id = request.args.get('id', None)
    password = request.args.get('password', None)
    if id is None:
        return f'fail! input your id!'
    if password is None:
        return f'fail! input your password!'
    db = get_db()
    cur = db.cursor()
    sql_select = "select * from user where id=" + str(id) + " and password= '" + str(password) + "'"
    try:
        cur.execute(sql_select)
        rv = cur.fetchall()
        if len(rv) == 0:
            return f'fail!'
        return f'success!'
    except:
        return f'fail!'


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


def register_kafka_listener(topic, listener):
    # Poll kafka
    def poll():
        # Initialize consumer Instance
        consumer = KafkaConsumer(topic, bootstrap_servers=BOOT_STRAP_SERVERS,
                                 auto_offset_reset='earliest',
                                 enable_auto_commit=True,
                                 auto_commit_interval_ms=100,
                                 group_id='user')
        print("About to start polling for topic:", topic)
        # consumer.poll(timeout_ms=6000)
        print("Started Polling for topic:", topic)
        with app.app_context():
            db = get_db()
            for msg in consumer:
                text.append(msg.value)
                id = json.loads(msg.value.decode('utf-8'))['id']
                passwd = json.loads(msg.value.decode('utf-8'))['name']
                text.append(passwd)
                text.append(id)
                text.append(msg.offset)
                cur = db.cursor()
                sql_insert = 'insert into user (id,password) values (' \
                             '\'' + str(id) + '\', \'' + str(123456) + '\')'
                cur.execute(sql_insert)
                db.commit()

        consumer.close()

    print("About to register listener to topic:", topic)
    t1 = threading.Thread(target=poll)
    t1.start()
    print("started a background thread")


def kafka_listener(data):
    print("Image Ratings:\n", data.value.decode("utf-8"))


if __name__ == '__main__':
    # init_db()
    register_kafka_listener('register_employee', kafka_listener)
    app.run(debug=False, host='0.0.0.0', port=6002)
