import sqlite3
import random
import json


class QuestionsModel:
    def __init__(self):
        self.conn = sqlite3.connect('data.db')
        self.cursor = self.conn.cursor()

        self.settings = QuestionsModel.read_settings()
        self.costs = self.settings['costs']
        self.quests_nums = self.settings['quests_nums']

    def close_connection(self):
        self.conn.close()

    def set_costs(self, new_costs):
        if not all([cost % 2 == 0 for cost in new_costs]):
            raise ValueError
        QuestionsModel.check_params(self.quests_nums, new_costs)

        new_costs_len = len(new_costs)

        for i in range(len(new_costs)):
            self.cursor.execute('UPDATE questions SET cost=? WHERE id%?-?=0',
                                (new_costs[i], new_costs_len, (i + 1) % new_costs_len))

        self.costs = new_costs
        self.write_prop_in_settings('costs', new_costs)

        self.conn.commit()

    def set_quests_nums(self, new_quests_nums):
        QuestionsModel.check_params(new_quests_nums, self.costs)
        costs_len = len(self.costs)

        for theme in new_quests_nums:
            if theme not in self.quests_nums:
                self.quests_nums[theme] = 0

            for i in range(new_quests_nums[theme] - self.quests_nums[theme]):  # Increase
                params = (theme, '', '', self.costs[i % costs_len])
                self.cursor.execute('INSERT INTO questions(theme, content, answer, cost) VALUES(?, ?, ?, ?)', params)

            if self.quests_nums[theme] - new_quests_nums[theme] > 0:  # Decrease
                dif = self.quests_nums[theme] - new_quests_nums[theme]
                ids = self.cursor.execute('SELECT id FROM questions WHERE theme=?', (theme,)).fetchall()[-dif:]
                ids = tuple(map(lambda x: x[0], ids))

                sql_quests = ('?,' * len(ids))[:-1]

                if self.cursor.execute(
                        'SELECT content FROM questions WHERE id IN ({})'.format(sql_quests,), ids
                ).fetchall() != [('',)] * len(ids):
                    raise ValueError

                self.cursor.execute('DELETE FROM questions WHERE id IN ({})'.format(sql_quests,), ids)

            self.quests_nums[theme] = new_quests_nums[theme]

        self.write_prop_in_settings('quests_nums', self.quests_nums)
        self.conn.commit()

    def change_theme_name(self, old_name, new_name):
        self.cursor.execute('UPDATE questions SET theme=? WHERE theme=?', (new_name, old_name))

        self.quests_nums[new_name] = self.quests_nums[old_name]
        self.quests_nums[old_name] = 0
        self.write_prop_in_settings('quests_nums', self.quests_nums)

        self.conn.commit()

    @staticmethod
    def check_params(quests_nums, costs):
        for theme in quests_nums:
            if quests_nums[theme] % len(costs) != 0:
                raise ValueError

    def get_unique_random_themes(self, forbidden, num):
        themes = map(lambda el: el[0], self.cursor.execute('SELECT theme FROM questions').fetchall())

        filtered = []
        for theme in themes:
            if theme not in filtered and theme not in forbidden:
                filtered.append(theme)

        return [filtered.pop(random.randint(0, len(filtered) - 1)) for _ in range(num)]

    def get_random_quests(self, themes):
        res = []

        for theme in themes:
            for cost in self.costs:
                quests = self.cursor.execute(
                    'SELECT theme, cost, content, answer FROM questions WHERE theme=? AND cost=? AND content != \'\'',
                    (theme, cost)
                ).fetchall()
                rand_quest = quests[random.randint(0, len(quests) - 1)]
                res.append({
                    'theme': rand_quest[0],
                    'cost': rand_quest[1],
                    'content': rand_quest[2],
                    'answer': rand_quest[3]
                })

        return res

    @staticmethod
    def read_settings():
        with open('data_settings.json', encoding='utf-8') as settings:
            return json.load(settings)

    def write_prop_in_settings(self, prop, value):  # Записываются темы с 0 вопросами!!!
        self.settings[prop] = value
        with open('data_settings.json', mode='w', encoding='utf-8') as settings:
            return json.dump(self.settings, settings)


if __name__ == "__main__":
    q_model = QuestionsModel()

    q_model.set_quests_nums({
        'Операционные системы': 10,
        'Анатомия': 10,
        'Отечественная война': 10,
        'Золотой век литературы': 10,
        'Пословицы': 10,
        'Поговорки': 10,
        'Первое оружие': 10,
        'Добро пожаловать в Рим!': 10
    })

    q_model.change_theme_name('Добро пожаловать в Рим!', 'Добро пожаловать в Рим')

    print(q_model.get_random_quests(['Операционные системы', 'Анатомия']))

    q_model.close_connection()
