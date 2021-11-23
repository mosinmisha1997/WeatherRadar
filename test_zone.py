import sqlite3

conn = sqlite3.connect("./weather_radar.db")


def add_column():
    command = "ALTER TABLE following_cities ADD COLUMN city_number INTEGER"
    curs = conn.cursor()
    curs.execute(command)
    conn.commit()

add_column()