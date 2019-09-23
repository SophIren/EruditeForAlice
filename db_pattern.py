def set_empty_values_for_theme(theme, quests_num, costs, conn, cursor):
    costs_len = len(costs)

    if quests_num % costs_len != 0:
        raise ValueError

    for i in range(quests_num):
        params = (i + 1, theme, '', '', costs[i % costs_len])
        try:
            cursor.execute('INSERT INTO questions(id, theme, content, answer, cost) VALUES(?, ?, ?, ?, ?)', params)
        except sqlite3.IntegrityError:
            return
        conn.commit()


if __name__ == "__main__":
    import sqlite3

    conn = sqlite3.connect("data.db")
    cursor = conn.cursor()
    THEMES = ['Биология']
    for theme in THEMES:
        set_empty_values_for_theme(theme, 30, [100, 150], conn, cursor)
    conn.close()
