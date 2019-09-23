def set_empty_values_for_theme(theme, quests_num, costs, conn, cursor):
    costs_len = len(costs)

    if quests_num % costs_len != 0:
        raise ValueError

    k = quests_num // costs_len
    for i in range(quests_num):
        params = (i + 1, theme, '', '', costs[i // k])
        cursor.execute('INSERT INTO questions(id, theme, content, answer, cost) VALUES(?, ?, ?, ?, ?)', params)
        conn.commit()


if __name__ == "__main__":
    import sqlite3

    conn = sqlite3.connect("data.db")
    cursor = conn.cursor()
    THEMES = ['Биология']
    for theme in THEMES:
        set_empty_values_for_theme(theme, 33, [100, 125, 150], conn, cursor)
    conn.close()
