from flask import Flask
from flask import request
from markupsafe import escape
from flask import current_app,g
from flask import make_response
from flask import jsonify
import sqlite3
from kafka import KafkaProducer
from kafka import KafkaConsumer
import  threading
import json
app = Flask(__name__)
DATABASE = 'database.db'
BOOT_STRAP_SERVERS='kafka:9092'
@app.route("/")
def index():
  page_html="""
  <h1>hello task_management!!!!helloworldwwwwwwwwwww</h1>
  """
  return page_html

@app.route('/see')
def see():
    db=get_db()
    cur = db.execute('select * from task')
    rv = cur.fetchall()
    cur.close()
    return str(rv)


@app.route('/task')
def task():
    id = request.args.get('id',None)
    if id is None:
        return f'fail! input your id!'
    db = get_db()
    cur = db.execute('select content, isover from task where userid = '+str(id))
    rv = cur.fetchall()
    cur.close()
    return str(rv)

@app.route('/report')
def report():
    department = request.args.get('department',None)
    if department is None:
        return f'fail! input department!'
    db = get_db()
    sql_query=" select count(*) from task where department= '"+str(department)+" ' and isover=1"
    cur = db.execute(sql_query)
    rv = cur.fetchall()
    cur.close()
    return str(department)+":"+str(rv)


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

def register_kafka_listener(topic, listener):
# Poll kafka
    def poll():
        # Initialize consumer Instance
        consumer = KafkaConsumer(topic, bootstrap_servers=BOOT_STRAP_SERVERS,
                                 auto_offset_reset='earliest',
                                 enable_auto_commit=True,
                                 auto_commit_interval_ms=100,
                                 group_id='task')
        print("Started Polling for topic:", topic)
        for msg in consumer:
            msg=json.loads(msg.value.decode('utf-8'))
            userid=msg['userid']
            department=msg['department']
            with app.app_context():
                db=get_db()
                cur=db.cursor()
                sql_insert="insert into task (userid,department,content, isover) values('"\
                           + str(userid) + " ',"+" '"+str(department)+" ',"+"'updatepasswd','0')"
                cur.execute(sql_insert)
                db.commit()
            kafka_listener(msg)


    print("About to register listener to topic:", topic)
    t1 = threading.Thread(target=poll)
    t1.start()
    print("started a background thread")

def kafka_listener_update_passwd(topic, listener):
    def poll():
        consumer = KafkaConsumer(topic, bootstrap_servers=BOOT_STRAP_SERVERS,
                                 auto_offset_reset='earliest',
                                 enable_auto_commit=True,
                                 auto_commit_interval_ms=100,
                                 group_id='task')
        print("Started Polling for topic:", topic)
        for msg in consumer:
            msg=json.loads(msg.value.decode('utf-8'))
            userid=msg['userid']
            with app.app_context():
                db=get_db()
                cur=db.cursor()
                sql_insert="update task set isover= 1 where userid="+str(userid)
                cur.execute(sql_insert)
                db.commit()
            kafka_listener(msg)


    print("About to register listener to topic:", topic)
    t1 = threading.Thread(target=poll)
    t1.start()
    print("started a background thread")
def kafka_listener_update_department(topic, listener):
    def poll():
        consumer = KafkaConsumer(topic, bootstrap_servers=BOOT_STRAP_SERVERS,
                                 auto_offset_reset='earliest',
                                 enable_auto_commit=True,
                                 auto_commit_interval_ms=100,
                                 group_id='task')
        print("Started Polling for topic:", topic)
        for msg in consumer:
            msg=json.loads(msg.value.decode('utf-8'))
            userid=msg['userid']
            department=msg['department']
            with app.app_context():
                db=get_db()
                cur=db.cursor()
                sql_insert="update task set department= '"+str(department)+"' where userid="+str(userid)
                cur.execute(sql_insert)
                db.commit()
            kafka_listener(msg)

    print("About to register listener to topic:", topic)
    t1 = threading.Thread(target=poll)
    t1.start()
    print("started a background thread")
def kafka_listener(data):
    print("kafka_listener")

if __name__ == "__main__":
    # init_db()
    register_kafka_listener('register_user',kafka_listener)
    kafka_listener_update_passwd('update_passwd', kafka_listener)
    kafka_listener_update_department('update_department', kafka_listener)
    app.run(debug=False, host='0.0.0.0',port=5010)