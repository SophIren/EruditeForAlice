from __future__ import unicode_literals

from db_model import QuestionsModel

from flask import Flask, request
import json
import re
import pymorphy2

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
                'buttons': [],
                'end_session': False
            }
        }
        self.user_id = user_id
        self.storage = Dialog.storage[user_id]

    def tell_rules(self):
        self.response['response']['text'] += 'Правила игры: \
        сперва вам предлагаются 3 темы на вопросы. Сменить их вы можете \
        не более двух раз. Далее следуют 6 вопросов разных стоимостей на выбранные темы. \
        При выборе новых трех тем ваши очки сохраняются.'
        self.use_last_phrase()

    def use_last_phrase(self):
        self.response['response']['text'] += '\n{}'.format(self.storage['last_phrase'])
        if self.storage['stage'] == 1 or self.storage['stage'] == 4:
            self.storage['stage'] = 0

    def help(self):
        if self.storage['stage'] == 1 or self.storage['stage'] == 0 or self.storage['stage'] == 4:
            self.tell_rules()
        elif self.storage['stage'] == 2:
            self.response['response']['text'] += 'На данном этапе вы можете выбрать выпавшие темы или сменить их. ' \
                                                 'Для полной информации посмотрите правила.'
            self.use_last_phrase()
        elif self.storage['stage'] == 3:
            self.response['response']['text'] += 'Ничего сложного. Сейчас вам просто нужно ответить на вопрос.'

    def tell_my_abilities(self):
        self.response['response']['text'] += 'Это очень просто. У меня две функции. РАЗвлечь и РАЗвить вас.'
        self.use_last_phrase()

    def greeting(self):
        self.response['response']['text'] += 'Добро пожаловать в "Кто хочет стать эрудитом"! ' \
                                             'Хотите посмотреть правила или начнем играть?'
        self.storage['last_phrase'] = 'Начнем играть?'

    def ask_what_did_you_say(self):
        self.response['response']['text'] += 'Я вас не понимаю. Скажите глупому боту подоходчивее.'
        self.use_last_phrase()

    def finish_game(self):
        self.response['response']['text'] += 'Всего хорошего!'
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
            self.storage['stage'] = 3
            self.storage['quests'] = self.db.get_random_quests(self.storage['chosen_themes'], 2)
            self.response['response']['text'] += ' Вы не можете более сменить темы. Начиаем!\n'
            self.give_question()

        self.storage['last_phrase'] = self.response['response']['text']

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
            self.response['response']['text'] += 'Хотите продолжить играть\
             или закончить и записать результат в свою самооценку?'.format(self.storage['score'])
            self.storage['last_phrase'] = 'Продолжим играть?'
            self.storage['stage'] = 4

    def handle_zero_stage(self, command):
        if self.check_phrase_fit(command, Dialog.key_phrases['play']) or 'да' in command:
            self.storage = Dialog.reset_storage(self.user_id, self.storage['score'], self.storage['played_themes'])
            self.storage['stage'] = 2
            self.suggest_themes()
        elif self.check_phrase_fit(command, Dialog.key_phrases['farewell']) or 'нет' in command:
            self.response['response']['text'] += 'Не хотите - как хотите. '
            self.finish_game()
        else:
            self.ask_what_did_you_say()

    def handle_first_stage(self, command):
        if self.check_phrase_fit(command, Dialog.key_phrases['play']):
            self.storage = Dialog.reset_storage(self.user_id, self.storage['score'], self.storage['played_themes'])
            self.storage['stage'] = 2
            self.suggest_themes()
        else:
            self.ask_what_did_you_say()

    def handle_second_stage(self, command):
        if self.check_phrase_fit(command, Dialog.key_phrases['change']):
            self.storage['times_swapped'] += 1
            self.suggest_themes()

        elif self.check_phrase_fit(command, Dialog.key_phrases['play']):
            self.storage['played_themes'] += self.storage['chosen_themes']
            self.response['response']['text'] += 'Начнем! '
            self.storage['last_phrase'] = ''
            self.storage['stage'] = 3
            self.storage['quests'] = self.db.get_random_quests(self.storage['chosen_themes'], 2)
            self.give_question()

        else:
            self.ask_what_did_you_say()

    def handle_third_stage(self, command):
        answers = self.storage['current_quest']['answer'].split('|')
        quest_content = list(map(lambda el: el.lower() + ' ', self.storage['current_quest']['content']
                                 .replace('~', ' ').replace('!', ' ').replace('?', ' ').
                                 replace('.', ' ').replace(',', ' ').split()))
        typicals = '|'.join(Dialog.TYP_PHRASES.split('|') + quest_content)

        typicals = ' |'.join(self.to_inf(typicals.split(' |')))
        inf_answers = self.to_inf(map(str.lower, answers))
        command = ' '.join(self.to_inf(command.split()))

        # Correct
        if re.match('({0})*({1})({0})*'.format(typicals + ' ', '|'.join(inf_answers)), command + ' '):
            self.storage['score'] += self.storage['current_quest']['cost']
            self.response['response']['text'] += 'Правильно! '

        else:  # Incorrect
            self.storage['score'] -= self.storage['current_quest']['cost'] // 2
            self.storage['score'] = max(self.storage['score'], 0)
            if 'не знать' in command:
                self.response['response']['text'] += 'Правильный ответ {}. '.format(answers[0])
            else:
                self.response['response']['text'] += 'Неверно. Правильный ответ {}. '.format(answers[0])

        self.response['response']['text'] += 'У вас {} очков.\n'.format(self.storage['score'])
        self.give_question()

    def add_button_hints(self):
        if self.storage['stage'] == 0:
            self.response['response']['buttons'] += [Dialog.buttons['rules_but'],
                                                     Dialog.buttons['yes_but'], Dialog.buttons['no_but']]
        elif self.storage['stage'] == 1:
            self.response['response']['buttons'] += [Dialog.buttons['rules_but'], Dialog.buttons['play_but']]
        elif self.storage['stage'] == 2:
            self.response['response']['buttons'] += [Dialog.buttons['change_but'], Dialog.buttons['play_but']]
        elif self.storage['stage'] == 3:
            self.response['response']['buttons'].append(Dialog.buttons['do_not_know_but'])
        elif self.storage['stage'] == 4:
            self.response['response']['buttons'] += [Dialog.buttons['continue_but'], Dialog.buttons['bye_but']]

    @staticmethod
    def to_inf(phrases):
        list2 = []
        infs = []
        for phrase in phrases:
            for word in phrase.split():
                infs.append(morph.parse(word)[0].normal_form)
            list2.append(' '.join(infs))
            infs.clear()
        return list2

    @staticmethod
    def reset_storage(user_id, score, played_themes):
        Dialog.storage[user_id] = {
            'stage': 1,
            'score': score,
            'chosen_themes': [],
            'used_themes': [],
            'played_themes': played_themes,
            'times_swapped': 0,
            'quests': [],
            'quest_num': 0,
            'current_quest': None,
            'last_phrase': ''
        }
        return Dialog.storage[user_id]

    @staticmethod
    def check_phrase_fit(command, key_phrases):
        return any([key_phrase in command for key_phrase in key_phrases])


@app.route('/', methods=['POST'])
def main():
    user_id = request.json['session']['user_id']
    command = ' '.join(request.json['request']['nlu']['tokens'])

    if request.json['session']['new']:
        Dialog.reset_storage(user_id, 0, [])
        dialog = Dialog(user_id)
        dialog.greeting()

    else:
        dialog = Dialog(user_id)

        if Dialog.check_phrase_fit(command, Dialog.key_phrases['rules']) and Dialog.storage[user_id]['stage'] != 3:
            dialog.tell_rules()
        elif Dialog.check_phrase_fit(command, Dialog.key_phrases['what_can_you_do']):
            dialog.tell_my_abilities()
        elif Dialog.check_phrase_fit(command, Dialog.key_phrases['help']):
            dialog.help()
        elif Dialog.check_phrase_fit(command, Dialog.key_phrases['farewell']):
            dialog.finish_game()
        elif Dialog.storage[user_id]['stage'] == 0:
            dialog.handle_zero_stage(command)
        elif Dialog.storage[user_id]['stage'] == 1:
            dialog.handle_first_stage(command)
        elif Dialog.storage[user_id]['stage'] == 2:
            dialog.handle_second_stage(command)
        elif Dialog.storage[user_id]['stage'] == 3:
            dialog.handle_third_stage(command)
        elif Dialog.storage[user_id]['stage'] == 4:
            dialog.handle_first_stage(command)

    dialog.add_button_hints()

    dialog.db.close_connection()
    return json.dumps(dialog.response)


Dialog.buttons = {
    'rules_but': {
        'title': 'Расскажи правила',
        'hide': True
    },
    'play_but': {
        'title': 'Играем',
        'hide': True
    },
    'change_but': {
        'title': 'Сменить темы',
        'hide': True
    },
    'do_not_know_but': {
        'title': 'Не знаю',
        'hide': True
    },
    'continue_but': {
        'title': 'Продолжим',
        'hide': True
    },
    'yes_but': {
        'title': 'Да',
        'hide': True
    },
    'no_but': {
        'title': 'Нет',
        'hide': True
    },
    'bye_but': {
        'title': 'Пока',
        'hide': True
    }
}
Dialog.key_phrases = {
    'rules': {'правила'},
    'help': {'помощь', 'помоги', 'что делать'},
    'what_can_you_do': {'что ты умеешь'},
    'farewell': {'закончить', 'пока', 'до свидания', 'записать'},
    'play': {'играть', 'играем', 'продолжим', 'продолжить', 'продолжаем', 'начнем', 'начинаем'},
    'change': {'сменить', 'смени', 'убери'}
}

Dialog.TYP_PHRASES = r'я |думаю |это |что |скорее всего |считаю |предпологаю |наверно |надеюсь |то |определенно '

morph = pymorphy2.MorphAnalyzer()

if __name__ == '__main__':
    app.run()
