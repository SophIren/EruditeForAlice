from __future__ import unicode_literals

from db_model import QuestionsModel

from flask import Flask, request
import sqlite3
import json
import logging

app = Flask(__name__)


class Dialog:
    storage = {}

    def __init__(self):
        self.db = QuestionsModel()

        self.response = {
            'session': request.json['session'],
            'version': request.json['version'],
            'response': {}
        }
        self.response['response']['end_session'] = False

    def tell_rules(self):
        self.response['response']['text'] = 'Сперва вам предлагаются 3 темы на вопросы. Сменить их вы можете \
                не более трех раз. Далее следуют 6 вопросов стоимостью 100 и 150 очков на выбранные темы. \
                При правильном ответе к вашим очкам прибавляется стоимость вопроса. При неверном отнимается \
                половина стоимости. При выборе новых тем ваши очки сохраняются.'
        # Правила могут ребаланснуться в любой момент времени

    def greeting(self):
        self.response['response']['text'] = 'Привет! Хотите посмотреть правила или начнем играть?'

    def suggest_themes(self, user_id):
        themes = self.db.get_unique_random_themes(Dialog.storage[user_id]['used_themes'], 3)
        Dialog.storage[user_id]['used_themes'] += themes

        self.response['response']['text'] = \
            'Выпавшие темы: {}, {}, {}. Играем или хотите сменить темы?'.format(*themes)

    def handle_first_step(self, tokens, user_id):
        if {'играть'}.intersection(tokens):
            self.suggest_themes(user_id)
            Dialog.storage[user_id]['step'] = 2
        else:
            self.response['response']['text'] = 'Я вас не понимаю. Скажите глупому боту подоходчивее.'

    def handle_second_step(self, tokens, user_id):
        if {'сменить'}.intersection(tokens):
            self.suggest_themes(user_id)


@app.route('/', methods=['POST'])
def main():
    dialog = Dialog()
    user_id = request.json['session']['user_id']
    tokens = request.json['request']['nlu']['tokens']

    if request.json['session']['new']:
        Dialog.storage[user_id] = {
            'step': 1,
            'used_themes': []
        }
        dialog.greeting()

    elif {'правила'}.intersection(tokens):
        dialog.tell_rules()

    elif Dialog.storage[user_id]['step'] == 1:
        dialog.handle_first_step(tokens, user_id)

    elif Dialog.storage[user_id]['step'] == 2:
        dialog.handle_second_step(tokens, user_id)

    # HERE WILL BE OTHER STEPS

    dialog.db.close_connection()
    return json.dumps(dialog.response)


if __name__ == '__main__':
    app.run()
