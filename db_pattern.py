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

        self.set_costs(self.costs)
        self.set_quests_nums(self.quests_nums)

    def close_connection(self):
        self.conn.close()

    def set_costs(self, new_costs):
        QuestionsModel.check_params(self.quests_nums, new_costs)

        new_costs_len = len(new_costs)

        for i in range(len(new_costs)):
            self.cursor.execute('UPDATE questions SET cost=? WHERE id%?-?=0',
                                (new_costs[i], new_costs_len, (i + 1) % new_costs_len))

        self.costs = new_costs
        self.write_prop_in_settings('costs', new_costs)

        self.conn.commit()

    def set_quests_nums(self, new_quests_nums):  # WiP
        QuestionsModel.check_params(new_quests_nums, self.costs)

        costs_len = len(self.costs)

        for theme in new_quests_nums:

            for i in range(new_quests_nums[theme] - self.quests_nums[theme]):  # Increase
                params = (theme, '', '', self.costs[i % costs_len])
                self.cursor.execute('INSERT INTO questions(theme, content, answer, cost) VALUES(?, ?, ?, ?)', params)

            if self.quests_nums[theme] - new_quests_nums[theme] > 0:  # Decrease
                dif = self.quests_nums[theme] - new_quests_nums[theme]
                ids = self.cursor.execute('SELECT id FROM questions WHERE theme=?', (theme,)).fetchall()[-dif:]
                ids = tuple(map(lambda x: x[0], ids))
                if self.cursor.execute('SELECT content FROM questions WHERE id IN ({})'.format(('?,' * len(ids))[:-1]),
                                       ids).fetchall() != [('',)] * len(ids):
                    raise ValueError
                self.cursor.execute('DELETE FROM questions WHERE id IN ({})'.format(('?,' * len(ids))[:-1]), ids)

            self.quests_nums[theme] = new_quests_nums[theme]

        self.write_prop_in_settings('quests_nums', self.quests_nums)

        self.conn.commit()

    def get_unique_random_themes(self, forbidden, num):
        themes = map(lambda el: el[0], self.cursor.execute('SELECT theme FROM questions').fetchall())

        filtered = []
        for theme in themes:
            if theme not in filtered and theme not in forbidden:
                filtered.append(theme)

        return [filtered.pop(random.randint(0, len(filtered) - 1)) for _ in range(num)]

    @staticmethod
    def check_params(quests_nums, costs):
        for theme in quests_nums:
            if quests_nums[theme] % len(costs) != 0:
                raise ValueError

    @staticmethod
    def read_settings():
        with open('data_settings.json', encoding='utf-8') as settings:
            return json.load(settings)

    def write_prop_in_settings(self, prop, value):
        self.settings[prop] = value
        with open('data_settings.json', mode='w', encoding='utf-8') as settings:
            return json.dump(self.settings, settings)


if __name__ == "__main__":
    q_model = QuestionsModel()

    q_model.set_quests_nums({
        'Операционные системы': 10,
        'Анатомия': 10,
        'Настольные игры': 10
    })

    q_model.set_costs([100, 150])

    print(q_model.get_unique_random_themes(['Анатомия'], 3))

    q_model.close_connection()
