from __future__ import unicode_literals

from db_model import QuestionsModel

from flask import Flask, request
import json

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

    def greeting(self):
        self.response['response']['text'] += 'Привет! Хотите посмотреть правила или начнем играть?'

    def ask_what_did_you_say(self):
        self.response['response']['text'] += 'Я вас не понимаю. Скажите глупому боту подоходчивее.'

    def finish_game(self):
        self.response['response']['text'] += 'Пока!'
        self.response['response']['end_session'] = True

    def suggest_themes(self):
        themes = self.db.get_unique_random_themes(self.storage['used_themes'] + self.storage['played_themes'], 3)
        if not themes:  # If no themes which aren't played is available
            self.storage['played_themes'] = []
            themes = self.db.get_unique_random_themes(self.storage['used_themes'], 3)

        self.storage['chosen_themes'] = themes
        self.storage['used_themes'] += themes

        self.response['response']['text'] += 'Выпавшие темы: {}, {}, {}.'.format(*themes)

        if self.storage['times_swapped'] == 0:
            self.response['response']['text'] += ' Играем или хотите сменить темы?'

        elif self.storage['times_swapped'] == 1:
            self.response['response']['text'] += ' Можете играть с этими темами или сменить их последний раз.'

        elif self.storage['times_swapped'] == 2:
            self.storage['played_themes'] += self.storage['chosen_themes']
            self.storage['step'] = 3
            self.storage['quests'] = self.db.get_random_quests(self.storage['chosen_themes'], 2)
            self.response['response']['text'] += ' Вы не можете более сменить темы. Начиаем!\n'
            self.give_question()

    def give_question(self):
        try:
            self.storage['current_quest'] = self.storage['quests'][self.storage['quest_num']]

            if self.storage['current_quest']['sound_id'] is not None:
                self.response['response']['tts'] = self.storage['current_quest']['sound_id']

            if self.storage['current_quest']['image_id'] is not None:
                content, title = self.storage['current_quest']['content'].split('~')
                self.storage['current_quest']['content'] = self.storage['current_quest']['content'].replace('~', ' ')
                self.response['response']['card'] = {
                    'type': 'BigImage',
                    'image_id': self.storage['current_quest']['image_id'],
                    'title': title,
                    'description': self.response['response']['text'] + content
                }

            self.response['response']['text'] += 'Тема: {}. Вопрос за {}.\n {}'.format(
                *self.storage['current_quest'].values()
            )

            self.storage['quest_num'] += 1

        except IndexError:
            self.response['response']['text'] += 'Вы набрали {} очков. Хотите продолжить играть\
             или закончить и записать результат в свою самооценку?'.format(self.storage['score'])
            self.storage['step'] = 4

    def handle_first_step(self, tokens):
        if {'играть'}.intersection(tokens):
            self.storage['step'] = 2
            self.suggest_themes()
        else:
            self.ask_what_did_you_say()

    def handle_second_step(self, tokens):
        if {'сменить'}.intersection(tokens):
            self.storage['times_swapped'] += 1
            self.suggest_themes()

        elif {'играть'}.intersection(tokens):
            print(self.storage['chosen_themes'])
            self.storage['played_themes'] += self.storage['chosen_themes']
            self.response['response']['text'] += 'Начнем! '
            self.storage['step'] = 3
            self.storage['quests'] = self.db.get_random_quests(self.storage['chosen_themes'], 2)
            self.give_question()

        else:
            self.ask_what_did_you_say()

    def handle_third_step(self, tokens):
        answers = self.storage['current_quest']['answer'].split('|')
        command = ' '.join(tokens)

        if any([answer.lower() == command for answer in answers]):  # Correct
            self.storage['score'] += self.storage['current_quest']['cost']
            self.response['response']['text'] += 'Правильно! '

        else:  # Incorrect
            self.storage['score'] -= self.storage['current_quest']['cost'] // 2
            self.storage['score'] = max(self.storage['score'], 0)
            self.response['response']['text'] += 'Неверно. Правильный ответ {}. '.format(answers[0])

        self.response['response']['text'] += 'У вас {} очков.\n'.format(self.storage['score'])
        self.give_question()

    def handle_fourth_step(self, tokens):
        if {'играть'}.intersection(tokens):
            self.storage['step'] = 2
            self.suggest_themes()
        else:
            self.ask_what_did_you_say()

    @staticmethod
    def reset_storage(user_id, score, played_themes):
        Dialog.storage[user_id] = {
            'step': 1,
            'score': score,
            'chosen_themes': [],
            'used_themes': [],
            'played_themes': played_themes,
            'times_swapped': 0,
            'quests': [],
            'quest_num': 0,
            'current_quest': None
        }
        return Dialog(user_id)


@app.route('/', methods=['POST'])
def main():
    user_id = request.json['session']['user_id']
    tokens = request.json['request']['nlu']['tokens']

    if request.json['session']['new']:
        dialog = Dialog.reset_storage(user_id, 0, [])
        dialog.greeting()

    else:
        dialog = Dialog(user_id)

        if {'правила'}.intersection(tokens):
            dialog.tell_rules()
        elif {'закончить'}.intersection(tokens):
            dialog.finish_game()
        elif Dialog.storage[user_id]['step'] == 1:
            dialog.handle_first_step(tokens)
        elif Dialog.storage[user_id]['step'] == 2:
            dialog.handle_second_step(tokens)
        elif Dialog.storage[user_id]['step'] == 3:
            dialog.handle_third_step(tokens)
        elif Dialog.storage[user_id]['step'] == 4:
            dialog = Dialog.reset_storage(user_id, dialog.storage['score'], dialog.storage['played_themes'])
            dialog.handle_fourth_step(tokens)

    dialog.db.close_connection()
    return json.dumps(dialog.response)


if __name__ == '__main__':
    app.run()
