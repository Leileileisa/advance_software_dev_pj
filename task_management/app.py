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
app = Flask(__name__)
DATABASE = 'database.db'
BOOT_STRAP_SERVERS='kafka:9092'
@app.route("/")
def index():
  page_html="""
  <h1>hello task_management!!!!</h1>
  """
  return page_html

@app.route('/see')
def see():
    db=get_db()
    cur = db.execute('select * from user')
    rv = cur.fetchall()
    cur.close()
    return str(rv)
@app.route('/register')
def register():
    password=request.args.get('password',None)
    if password is None:
        return f'fail! input your password!'
    db=get_db()
    try:
        sql_insert='insert into user (password) values (\''+password+'\')'
        cur=db.execute(sql_insert)
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
def register_kafka_listener(topic, listener):
# Poll kafka
    def poll():
        # Initialize consumer Instance
        consumer = KafkaConsumer(topic, bootstrap_servers=BOOT_STRAP_SERVERS)
        consumer.subscribe(topics=[topic])
        print("About to start polling for topic:", topic)
        consumer.poll(timeout_ms=6000)
        print("Started Polling for topic:", topic)
        for msg in consumer:
            print("Entered the loop\nKey: ",msg.key.decode()," Value:", msg.value.decode())
            with app.app_context():
                db=get_db()
                sql_insert = 'insert into user (password) values (\'' + 'leisa'+ '\')'
                cur = db.execute(sql_insert)
                db.commit()
                cur.close()
            kafka_listener(msg)
    print("About to register listener to topic:", topic)
    t1 = threading.Thread(target=poll)
    t1.start()
    print("started a background thread")

def kafka_listener(data):
    print("Image Ratings:\n", data.value.decode("utf-8"))

if __name__ == "__main__":
    init_db()
    register_kafka_listener('register_employee',kafka_listener)
    app.run(debug=True, host='0.0.0.0',port=5001)