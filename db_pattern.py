class QuestionsModel:
    def __init__(self, costs, quests_nums):  # В аргументы - актуальные данные БД! (пока нет файла сеттинга БД)
        self.conn = sqlite3.connect('data.db')

        self.costs = costs
        self.quests_nums = quests_nums

    def close_connection(self):
        self.conn.close()

    def fix_costs(self, new_costs):
        QuestionsModel.check_params(self.quests_nums, new_costs)

        cursor = self.conn.cursor()
        new_costs_len = len(new_costs)

        for i in range(len(new_costs)):
            cursor.execute('UPDATE questions SET cost=? WHERE id%?-?=0',
                           (new_costs[i], new_costs_len, (i + 1) % new_costs_len))

        self.costs = new_costs
        self.conn.commit()

    def set_quests_nums(self, new_quests_nums):  # WiP
        QuestionsModel.check_params(new_quests_nums, self.costs)

        cursor = self.conn.cursor()
        costs_len = len(self.costs)

        for theme in new_quests_nums:

            for i in range(new_quests_nums[theme] - self.quests_nums[theme]):  # Increase
                params = (theme, '', '', self.costs[i % costs_len])
                cursor.execute('INSERT INTO questions(theme, content, answer, cost) VALUES(?, ?, ?, ?)', params)

            if self.quests_nums[theme] - new_quests_nums[theme] > 0:  # Decrease
                dif = self.quests_nums[theme] - new_quests_nums[theme]
                ids = cursor.execute('SELECT id FROM questions WHERE theme=?', (theme,)).fetchall()[-dif:]
                ids = tuple(map(lambda x: x[0], ids))
                if cursor.execute('SELECT content FROM questions WHERE id IN ({})'.format(('?,' * len(ids))[:-1]),
                                  ids).fetchall() != [('',)] * len(ids):
                    raise ValueError
                cursor.execute('DELETE FROM questions WHERE id IN ({})'.format(('?,' * len(ids))[:-1]), ids)

        self.conn.commit()

    @staticmethod
    def check_params(quests_nums, costs):
        for theme in quests_nums:
            if quests_nums[theme] % len(costs) != 0:
                raise ValueError


if __name__ == "__main__":
    import sqlite3

    quests_nums = {
        'Операционные системы': 14,
        'Анатомия': 16,
        'Авторы произведений': 10,
        'Настольные игры': 8
    }
    q_model = QuestionsModel([100, 150], quests_nums)

    q_model.set_quests_nums({
        'Операционные системы': 14,
        'Анатомия': 16,
        'Настольные игры': 8
    })

    # q_model.fix_costs([100, 175, 200, 1000])

    q_model.close_connection()
