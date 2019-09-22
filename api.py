from __future__ import unicode_literals

from flask import Flask, request
import json
import logging

app = Flask(__name__)

storage = {}


class Dialog:
    storage = {}

    def __init__(self):
        self.response = {
            'session': request.json['session'],
            'version': request.json['version'],
            'response': {
                'end_session': False
            }
        }

    def greeting(self):
        self.response['response']['text'] = 'Привет! Хотите посмотреть правила или будем играть сразу?'

    def handle_first_step(self, tokens, user_id):
        if {'правила'}.intersection(tokens):
            self.response['response']['text'] = ''  # ЗДЕСЬ МОГЛИ БЫТЬ ВАШИ ПРАВИЛА, НО ИХ НЕ ЗАВЕЗЛИ
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
