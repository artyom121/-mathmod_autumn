# save this as app.py
import time
from pydantic import *
import flask
from flask import Flask, abort
import datetime

app = Flask(__name__)
db = []
db.append({
    'name': 'Artyom',
    'time': time.time(),
    'text': 'hello world'
})

@app.route("/")
def hello():
    return "Hello, World!"


class Slovarb(BaseModel):
    slovarb: dict


class Strocka(BaseModel):
    strocka: str



@app.route("/send", methods= ['POST'])
def send_message():
    '''
    функция для отправки нового сообщения пользователем
    :return:
    '''
    # TODO
    # проверить, является ли присланное пользователем правильным json-объектом
    # проверить, есть ли там имя и текст
    # Добавить сообщение в базу данных db
    value = ValueError
    try:
        data = Slovarb(slovarb=flask.request.json)
    except value:
        return abort(400)


    key_data = data.slovarb.keys()
    if 'name' not in key_data or \
        'text' not in key_data:
        return abort(400)
    try:
        text = Strocka(strocka=data.slovarb['text'])
        name = Strocka(strocka=data.slovarb['name'])

    except value:
        return abort(400)
    if len(data.slovarb['name']) == 0 or len(data.slovarb['text']) == 0:
        return abort(400)


    message = {
        'text': text.strocka,
        'name': name.strocka,
        'time': time.time()
    }
    db.append(message)

    if '/day_of_week' in data.slovarb['text']:
        week = {
            '1':'пн',
            '2': 'вт',
            '3': 'ср',
            '4': 'чт',
            '5': 'пт',
            '6': 'сб',
            '7': 'вс',
        }
        message = {
            'text': week[str(datetime.datetime.today().weekday())],
            'name': 'bot',
            'time': time.time()
        }
        db.append(message)

    if '/count_of_users' in data.slovarb['text']:
        listusers = []
        for i in range(len(db)):
            if db[i]['name'] not in listusers:
                listusers.append(db[i]['name'])
        message = {
            'text': 'число пользователей сейчас: ' + str(len(listusers)),
            'name': 'bot',
            'time': time.time()
        }
        db.append(message)

    return {'ok': True}

@app.route("/messages")
def get_messages():
    try:
        after = float(flask.request.args['after'])
    except:
        abort(400)
    db_after = []
    for message in db:
        if message['time'] > after:
            db_after.append(message)
    return {'messages': db_after}

@app.route("/status")
def print_status():
    countmessengers = str(len(db))
    listusers = []
    for i in range(len(db)):
        if db[i]['name'] not in listusers:
            listusers.append(db[i]['name'])
    countusers = str(len(listusers))
    return {
       'time': time.time(),
        'count messangers': countmessengers,
        'count users': countusers,
        'list users': listusers,
    }

@app.route('/index')
def lionel(): 
    return flask.render_template('index.html')


app.run()