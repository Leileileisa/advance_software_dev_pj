from flask import Flask
from flask import request
from markupsafe import escape
from flask import current_app,g
from flask import make_response
from flask import jsonify
import click
import sqlite3
import sys
from kafka import KafkaProducer
from kafka import KafkaConsumer
from kafka.errors import  kafka_errors
import traceback
import threading
import json
app = Flask(__name__)
DATABASE = 'database.db'
BOOT_STRAP_SERVERS='kafka:9092'
@app.route("/")
def index():
  page_html="""
  <h1>hello employee_management!!!!wwww</h1>
  """
  page_html+='hi'
  return page_html

@app.route('/register')
def register():
    print('register!')
    name=request.args.get('name',None)
    department=request.args.get('department',None)
    if name is None:
        return f'fail! input your name!'
    if department is None:
        return f'fail!input your department!'
    db=get_db()
    try:
        sql_insert='insert into employee (name,department) values (\''+name+'\',\''+department+'\')'
        cur=db.execute(sql_insert)
        db.commit()
        cur.close()
    except:
        return f'fail! this name already exists.'
    try:
        producer = KafkaProducer(bootstrap_servers=BOOT_STRAP_SERVERS,
                                 key_serializer=lambda k: json.dumps(k).encode('utf-8'),
                                 value_serializer=lambda v: json.dumps(v).encode('utf-8'))
        future = producer.send('register_employee', {'name': name, 'department': department})
        future.get(timeout=10)  # 监控是否发送成功
    except kafka_errors:  # 发送失败抛出kafka_errors
        return traceback.format_exc()
    except Exception as e:
        return e
    print('kafka')
    return f'create successfully! your Name: {escape(name)} your department:{escape(department)}'
@app.route('/see')
def see():
    db=get_db()
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
        sql_insert = 'update employee set department=' + '\''+department +'\''+ 'where name='+'\'' +name+'\''
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

if __name__ == "__main__":
    init_db()
    app.run(debug=True, host='0.0.0.0')