import sqlite3

from aiogram.dispatcher.filters.builtin import Command
from aiogram.types import user


conn = sqlite3.connect("./weather_radar.db")


def select_users_id():
    command = f"SELECT DISTINCT user_id FROM following_cities"
    curs = conn.cursor()
    curs.execute(command)
    ids_list = curs.fetchall()
    ids = []
    for id in ids_list:
        ids.append(id[0])
    return ids


def select_cities_coords(user_id):
    command = f"SELECT city_coords, notification_time, id FROM following_cities WHERE user_id = {user_id}"
    curs = conn.cursor()
    curs.execute(command)
    data = curs.fetchall()
    if len(data) == 0:
        return
    follow_data = []
    for i in range(0, len(data)):
        city_coords = (data[i][0]).split(";")
        follow_data.append([{"lat": city_coords[0], "lon": city_coords[1]}, data[i][1], data[i][2]])
    return follow_data


def select_follow_cities(user_id):
    command = f"SELECT city_address FROM following_cities WHERE user_id = {user_id}"
    curs = conn.cursor()
    curs.execute(command)
    cities_list = curs.fetchall()
    cities = []
    if len(cities_list) > 0:
        for city in cities_list:
            cities.append(city[0])
    return cities


def select_city_coords(user_id, city_address=None):
    command = f"SELECT city_coords FROM following_cities WHERE (user_id = {user_id}) AND (city_address = '{city_address}')"
    curs = conn.cursor()
    curs.execute(command)
    coords_list = (curs.fetchone()[0]).split(";")
    coords = {"lat": coords_list[0], "lon": coords_list[1]}
    return coords


def select_notification_time(user_id, city_address = None, city_number = -1):
    command = ""
    if city_address and city_number == -1:
        command = f"SELECT notification_time FROM following_cities WHERE (city_address = '{city_address}') AND (user_id = {user_id})"
    elif city_number != -1 and not city_address:
        command = f"SELECT notification_time FROM following_cities WHERE (id = '{city_number}') AND (user_id = {user_id})"
    curs = conn.cursor()
    curs.execute(command)
    time = curs.fetchone()[0]
    return time


def select_city_number(user_id, city_address):
    command = f"SELECT id FROM following_cities WHERE (user_id = {user_id} AND city_address = '{city_address}')"
    curs = conn.cursor()
    curs.execute(command)
    city_number = curs.fetchone()[0]
    return city_number


def select_city_address(user_id, city_number):
    command = f"SELECT city_address FROM following_cities WHERE (user_id = {user_id}) AND (id = {city_number})"
    curs = conn.cursor()
    curs.execute(command)
    city_address = curs.fetchone()[0]
    return city_address


def delete_subscription_city(user_id, city_number):
    command = f"DELETE FROM following_cities WHERE (user_id = {user_id}) AND (id = {city_number})"
    curs = conn.cursor()
    curs.execute(command)
    conn.commit()
    print(f"Пользователь {user_id} удалил из отслеживаемых город {city_number}")


def update_notification_time(user_id, city_number, notification_time):
    command = f"UPDATE following_cities SET notification_time = {notification_time} WHERE (user_id = {user_id} AND id = {city_number})"
    curs = conn.cursor()
    curs.execute(command)
    conn.commit()
    print(f"Пользователь {user_id} обновил время города {city_number} на {notification_time}:00")


def select_count_following_cities(user_id):
    command = f"SELECT COUNT (id) FROM following_cities WHERE user_id = {user_id}"
    curs = conn.cursor()
    curs.execute(command)
    city_count = curs.fetchone()[0]
    return city_count


def select_max_id_following_cities():
    command = f"SELECT MAX (id) FROM following_cities"
    curs = conn.cursor()
    curs.execute(command)
    city_number = curs.fetchone()[0]
    return city_number


def insert_follow_city(user_id, user_name, city_address, city_coords, notification_time=12):
    command = f"INSERT INTO following_cities (user_id, user_name, city_address, city_coords, notification_time) VALUES ({user_id}, '{user_name}', '{city_address}', '{city_coords}', '{notification_time}')"
    curs = conn.cursor()
    curs.execute(command)
    conn.commit()

    print(f"Пользователь {user_name}({user_id}) теперь отслеживает погоду в {city_address}")
    city_number = select_max_id_following_cities()
    return city_number


def create_table(table_name, columns: list, types: list):
    columns_and_types = []

    for i in range(0, len(columns)):
        columns_and_types.append(f"{columns[i]} {types[i]}")

    columns_and_types = ', '.join(columns_and_types)

    command = f"CREATE TABLE {table_name} ({columns_and_types})"
    curs = conn.cursor()
    curs.execute(command)
    conn.commit()

    print(f"Таблица {table_name} создана")


def drop_table(table_name):
    command = f"DROP TABLE {table_name}"
    curs = conn.cursor()
    curs.execute(command)
    conn.commit()

    print(f"Таблица {table_name} удалена")


def delete_data(table_name):
    command = f"DELETE FROM {table_name} WHERE user_id = 759409190"
    curs = conn.cursor()
    curs.execute(command)
    conn.commit()

    print(f"Данные из таблицы {table_name} удалены")

#delete_data('following_cities')


def select_feedbacks(count = 3):
    command = f"SELECT id, user_id, username, fb_text, action FROM feedbacks WHERE action = 'send'"
    curs = conn.cursor()
    curs.execute(command)
    fb = curs.fetchall()
    fb_count = len(fb)
    feedbacks = []
    if len(fb) > count:
        feedbacks.clear()
        for i in range(0, count):
            feedbacks.append(fb[i])
    else:
        feedbacks = fb
    return feedbacks, fb_count


def insert_feedback(user_id, username, fb_text, action):
    command = f"INSERT INTO feedbacks (user_id, username, fb_text, action) VALUES ({user_id}, '{username}', '{fb_text}', '{action}')"
    curs = conn.cursor()
    curs.execute(command)
    conn.commit()
    print(f"Фидбек от {username} ({user_id}) был записан.")


def delete_feedback(id):
    command = f"DELETE FROM feedbacks WHERE id = {id}"
    curs = conn.cursor()
    curs.execute(command)
    conn.commit()
    print(f"Фидбек {id} был удален.")


#insert_feedback(111, 'bca', 'saf', 'send')
#drop_table('following_cities')
#create_table("feedbacks", ['id', 'user_id', 'username', 'fb_text', 'action'], ['INTEGER PRIMARY KEY', 'INTEGER', 'TEXT', 'TEXT', 'TEXT'])
#create_table("following_cities", ['id', 'user_id', 'user_name', 'city_address', 'city_coords', 'notification_time'], ['INTEGER PRIMARY KEY', 'INTEGER', 'TEXT', 'TEXT', 'TEXT', 'INTEGER'])