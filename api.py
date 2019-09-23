from __future__ import unicode_literals

from flask import Flask, request
import sqlite3
import json
import logging

app = Flask(__name__)


class QuestionsModel:
    def __init__(self):
        self.conn = sqlite3.connect('data.db')

    def close_connection(self):
        self.conn.close()


class Dialog:
    storage = {}

    def __init__(self):
        self.response = {
            'session': request.json['session'],
            'version': request.json['version'],
            'response': {}
        }
        self.response['response']['end_session'] = False

    def greeting(self):
        self.response['response']['text'] = 'Привет! Хотите посмотреть правила или начнем играть?'

    def handle_first_step(self, tokens, user_id):
        if {'правила'}.intersection(tokens):
            self.response['response']['text'] = 'Сперва вам предлагаются 3 темы на вопросы. Сменить их вы можете \
            не более трех раз. Далее следуют 6 вопросов стоимостью 100, 125 и 150 очков на выбранные темы. \
            При правильном ответе к вашим очкам прибавляется стоимость вопроса. При неверном отнимается \
            половина стоимости. При выборе новых тем ваши очки сохраняются.'
            # Правила могут ребаланснуться в любой момент времени
        elif {'играть'}.intersection(tokens):
            self.response['response']['text'] = ''  # ТРИ НЕЗАВЕЗЕННЫЕ ТЕМКИ
            Dialog.storage[user_id]['step'] = 2
        else:
            self.response['response']['text'] = 'Я вас не понимаю. Скажите глупому боту подоходчивее.'


@app.route('/', methods=['POST'])
def main():
    dialog = Dialog()
    user_id = request.json['session']['user_id']
    tokens = request.json['request']['nlu']['tokens']

    if request.json['session']['new']:
        Dialog.storage[user_id] = {
            'step': 1
        }
        dialog.greeting()

    elif Dialog.storage[user_id]['step'] == 1:
        dialog.handle_first_step(tokens, user_id)

    # HERE WILL BE OTHER STEPS

    return json.dumps(dialog.response)


if __name__ == '__main__':
    app.run()
