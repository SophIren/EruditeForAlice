from __future__ import unicode_literals

from db_model import QuestionsModel

from flask import Flask, request
import json
import logging

app = Flask(__name__)


class Dialog:
    storage = {}

    def __init__(self, user_id):
        self.db = QuestionsModel()

        self.response = {
            'session': request.json['session'],
            'version': request.json['version'],
            'response': {
                'text': '',
                'end_session': False
            }
        }
        self.storage = Dialog.storage[user_id]

    def tell_rules(self):
        self.response['response']['text'] += 'Сперва вам предлагаются 3 темы на вопросы. Сменить их вы можете \
                не более двух раз. Далее следуют 6 вопросов стоимостью 100 и 150 очков на выбранные темы. \
                При правильном ответе к вашим очкам прибавляется стоимость вопроса. При неверном отнимается \
                половина стоимости. При выборе новых тем ваши очки сохраняются.'
        # Правила могут ребаланснуться в любой момент времени

    def greeting(self):
        self.response['response']['text'] += 'Привет! Хотите посмотреть правила или начнем играть?'

    def ask_what_did_you_say(self):
        self.response['response']['text'] += 'Я вас не понимаю. Скажите глупому боту подоходчивее.'

    def suggest_themes(self):
        themes = self.db.get_unique_random_themes(self.storage['used_themes'], 3)
        self.storage['themes'] = themes
        self.storage['used_themes'] += themes

        self.response['response']['text'] += 'Выпавшие темы: {}, {}, {}.'.format(*themes)

        if self.storage['swapped_times'] == 0:
            self.response['response']['text'] += ' Играем или хотите сменить темы?'
        elif self.storage['swapped_times'] == 1:
            self.response['response']['text'] += ' Можете играть с этими темами или сменить их последний раз.'
        elif self.storage['swapped_times'] == 2:
            self.storage['step'] = 3
            self.storage['quests'] = self.db.get_random_quests(self.storage['themes'])
            self.response['response']['text'] = 'Вы не можете более сменить темы. Начиаем!\n'
            self.give_question()

    def give_question(self):
        self.response['response']['text'] += 'Тема: {}. Вопрос за {}. {}'.format(
            *self.storage['quests'][self.storage['quest_num']]
        )

    def handle_first_step(self, tokens):
        if {'играть'}.intersection(tokens):
            self.storage['step'] = 2
            self.suggest_themes()
        else:
            self.ask_what_did_you_say()

    def handle_second_step(self, tokens):
        if {'сменить'}.intersection(tokens):
            self.storage['swapped_times'] += 1
            self.suggest_themes()
        elif {'играть'}.intersection(tokens):
            self.storage['step'] = 3
            self.storage['quests'] = self.db.get_random_quests(self.storage['themes'])
            self.give_question()
        else:
            self.ask_what_did_you_say()

    def handle_third_step(self, tokens):
        pass


@app.route('/', methods=['POST'])
def main():
    user_id = request.json['session']['user_id']
    tokens = request.json['request']['nlu']['tokens']

    if request.json['session']['new']:
        Dialog.storage[user_id] = {
            'step': 1,
            'themes': [],
            'used_themes': [],
            'swapped_times': 0,
            'quests': [],
            'quest_num': 0
        }
        dialog = Dialog(user_id)
        dialog.greeting()

    else:
        dialog = Dialog(user_id)

        if {'правила'}.intersection(tokens):
            dialog.tell_rules()

        elif Dialog.storage[user_id]['step'] == 1:
            dialog.handle_first_step(tokens)

        elif Dialog.storage[user_id]['step'] == 2:
            dialog.handle_second_step(tokens)

        elif Dialog.storage[user_id]['step'] == 3:
            dialog.handle_third_step(tokens)

        # HERE WILL BE OTHER STEPS

    dialog.db.close_connection()
    return json.dumps(dialog.response)


if __name__ == '__main__':
    app.run()
