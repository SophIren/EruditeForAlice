def set_empty_values_for_theme(theme, quests_num, costs, conn, cursor):
    costs_len = len(costs)

    if quests_num % costs_len != 0:
        raise ValueError

    for i in range(quests_num):
        try:
            cursor.execute('SELECT content FROM questions WHERE theme=?', (theme,)).fetchall()[i]
        except IndexError:
            params = (theme, '', '', costs[i % costs_len])
            cursor.execute('INSERT INTO questions(theme, content, answer, cost) VALUES(?, ?, ?, ?)', params)
            conn.commit()


if __name__ == "__main__":
    import sqlite3

    conn = sqlite3.connect("data.db")
    cursor = conn.cursor()
    THEMES = ['Операционные системы', 'Анатомия', 'Авторы произведений']
    for theme in THEMES:
        set_empty_values_for_theme(theme, 10, [100, 150], conn, cursor)
    conn.close()
