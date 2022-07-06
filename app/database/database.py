from datetime import datetime
from os import execvp
import sqlite3
from aiogram.types import user

from aiogram.types.user import User
from pytz import timezone

from app.scheduler.notifications import update_scheduler_status


conn = sqlite3.connect("./weather_radar.db")

########################
### START users_data ###

def select_user_id(user_id):
    command = f"SELECT user_id FROM users_data WHERE user_id = {user_id}"
    curs = conn.cursor()
    curs.execute(command)
    user_id = curs.fetchone()
    return user_id


def insert_users_data(user:User):
    user_id = select_user_id(user.id)
    if user_id:
        return

    date_of_register = datetime.now(tz=timezone("Europe/Moscow")).strftime("%d.%m.%Y %H:%M")
    command = f"INSERT INTO users_data (user_id, username, first_name, last_name, date_of_register) VALUES ({user.id}, '{user.username}', '{user.first_name}', '{user.last_name}', '{date_of_register}')"
    curs = conn.cursor()
    curs.execute(command)
    conn.commit()
    print(f"Приветствуем пользователя {user.username}[{user.id}]")
    update_units_settings(user_id=user.id)
    update_notifications_data(user_id=user.id)

### END users_data ###
######################


###########################
### START user_settings ###

def select_user_settings(user_id):
    """
    Return dict of user_settings \n
    lang_code - код языка локализации \n
    coords - координаты города \n
    \tlat, lon \n
    address - адрес города \n
    weather_units - единицы измерения
    """
    command = f"SELECT lang_code, city_coords, city_address, weather_units FROM user_settings WHERE user_id = {user_id}"
    curs = conn.cursor()
    curs.execute(command)
    settings = curs.fetchone()
    user_settings = None
    if settings:
        lang_code = settings[0]
        coords = settings[1].split(';')
        address = settings[2]
        weather_units = settings[3]
        user_settings = {
            'lang_code':lang_code,
            'coords':{'lat':coords[0], 'lon':coords[1]},
            'address':address,
            'weather_units':weather_units
        }
    return user_settings


def update_user_settings(user_id, address=None, coords=None, lang_code=None, weather_units=None):
    user_settings = select_user_settings(user_id)
    
    if user_settings:
        if not address:
            address = user_settings['address']
        if not coords:
            coords = f"{user_settings['coords']['lat']};{user_settings['coords']['lon']}"
        else:
            coords = f"{coords['lat']};{coords['lon']}"
        if not lang_code:
            lang_code = user_settings['lang_code']
        if not weather_units:
            weather_units = user_settings['weather_units']

        command = f"UPDATE user_settings SET city_address = '{address}', city_coords = '{coords}', lang_code = '{lang_code}', weather_units = '{weather_units}' WHERE user_id = {user_id}"
    else:
        if not lang_code:
            lang_code = 'RU'
        if not weather_units:
            weather_units = "speed:м/с;pressure:мм рт. ст.;temperature:℃;humidity:%;cloudy:%"
        coords = f"{coords['lat']};{coords['lon']}"
        command = f"INSERT INTO user_settings (user_id, city_address, city_coords, lang_code, weather_units) VALUES ({user_id}, '{address}', '{coords}', '{lang_code}', '{weather_units}')"
    curs = conn.cursor()
    curs.execute(command)
    conn.commit()
    print(f"Пользователь {user_id} изменил настройки")

### END user_settings ###
#########################


############################
### START units_settings ###

def select_units_settings(user_id):
    command = f"SELECT * FROM units_settings WHERE user_id = {user_id}"
    curs = conn.cursor()
    curs.execute(command)
    settings = curs.fetchone()
    if not settings:
        print(f"Настройки единиц измерения пользователя {user_id} не найдены")
        return
    
    units_settings = {
        'name':settings[1],
        'speed':settings[2],
        'pressure':settings[3],
        'temperature':settings[4],
        'humidity':settings[5],
        'cloudy':settings[6]
    }
    return units_settings


def update_units_settings(user_id, name=None, speed=None, pressure=None, temperature=None, humidity=None, cloudy=None):
    units_settings = select_units_settings(user_id=user_id)
    if units_settings:
        if not speed:
            speed = units_settings['speed']
        if not pressure:
            pressure = units_settings['pressure']
        if not temperature:
            temperature = units_settings['temperature']
        if not humidity:
            humidity = units_settings['humidity']
        if not cloudy:
            cloudy = units_settings['cloudy']
        if not name:
            if speed == 'м/с' and pressure == 'мм рт. ст.' and temperature == '°C':
                name = 'metric'
            elif speed == 'миль/ч' and pressure == 'дюйм рт. ст.' and temperature == '°F':
                name = 'imperial'
            else:
                name = 'custom'
        else:
            if name == 'metric':
                speed = 'м/с'
                pressure = 'мм рт. ст.'
                temperature = '°C'
                humidity = '%'
                cloudy = '%'
            elif name == 'imperial':
                speed = 'миль/ч'
                pressure = 'дюйм рт. ст.'
                temperature = '°F'
                humidity = '%'
                cloudy = '%'
        command = f"UPDATE units_settings SET name = '{name}', speed = '{speed}', pressure = '{pressure}', temperature = '{temperature}', humidity = '{humidity}', cloudy = '{cloudy}' WHERE user_id = {user_id}"
    else:
        if not speed:
            speed = 'м/с'
        if not pressure:
            pressure = 'мм рт. ст.'
        if not temperature:
            temperature = '°C'
        if not humidity:
            humidity = '%'
        if not cloudy:
            cloudy = '%'
        if not name:
            if speed == 'м/с' and pressure == 'мм рт. ст.' and temperature == '°C':
                name = 'metric'
            elif speed == 'миль/ч' and pressure == 'дюйм рт. ст.' and temperature == '°F':
                name = 'imperial'
            else:
                name = 'custom'
        command = f"INSERT INTO units_settings VALUES ({user_id}, '{name}', '{speed}', '{pressure}', '{temperature}', '{humidity}', '{cloudy}')"
    curs = conn.cursor()
    curs.execute(command)
    conn.commit()
    print(f"Пользователь {user_id} изменил настройки единиц измерения")


### END units_settings ###
##########################


###########################
### START NOTIFICATIONS ###


def select_notifications_time(user_id:int, fcast_type:str):
    """
    Returned user_id and list of notifications_time as dict
    keys: user_id, notifications_time
    """
    command = f"SELECT user_id, notifications_time FROM notifications_{fcast_type}_fcast WHERE user_id={user_id}"
    curs = conn.cursor()
    curs.execute(command)
    records = curs.fetchall()
    user_id = None
    notifications_time = None
    if records:
        user_id = records[0][0]
        notifications_time = records[0][1]
    return {'user_id':user_id, 'notifications_time':notifications_time}


def get_notifications_time(user_id:int, fcast_type:str):
    """
    Returned list of notifications_time
    """
    list_of_time = select_notifications_time(user_id=user_id, fcast_type=fcast_type)['notifications_time']
    if not list_of_time:
        return

    time_list = list_of_time.split(';')
    notifications_time = {}
    for time in time_list:
        hour = int(time.split(':')[0])
        minute = int(time.split(':')[1])
        if hour not in notifications_time:
            notifications_time.update({hour:[]})
            notifications_time[hour].append(minute)
        elif hour in notifications_time:
            notifications_time[hour].append(minute)
    return notifications_time


def add_notifications_to_db(user_id:int, time:str, fcast_type:str):
    notification_records = select_notifications_time(user_id, fcast_type)
    notifications_time = notification_records['notifications_time']
    updated_time = ""
    command = ""
    if not notification_records['user_id']:
        update_notifications_data(user_id=user_id, notifications_status="enabled", notifications_availability="found")
        updated_time = time
        command = f"INSERT INTO notifications_{fcast_type}_fcast VALUES ({user_id}, '{updated_time}')"
    else:
        updated_time = notifications_time.split(";")
        if time in updated_time:
            index = updated_time.index(time)
            del updated_time[index]
        else:
            updated_time.append(time)

        updated_time = ";".join(updated_time)
        if not updated_time:
            update_notifications_data(user_id=user_id, notifications_status="disabled", notifications_availability="not_found")
            command = f"DELETE FROM notifications_{fcast_type}_fcast WHERE user_id = {user_id}"
        else:
            update_notifications_data(user_id=user_id, notifications_status="enabled", notifications_availability="found")
            command = f"UPDATE notifications_{fcast_type}_fcast SET notifications_time = '{updated_time}' WHERE user_id = {user_id}"

    curs = conn.cursor()
    curs.execute(command)
    conn.commit()
    

def select_notifications_data_all():
    command = f"SELECT user_id, notifications_status, notifications_type FROM notifications_data"
    curs = conn.cursor()
    curs.execute(command)
    data = curs.fetchall()
    if not data:
        return
    
    notifications_data = []
    for i in range(0, len(data)):
        _data = {
            'user_id':data[i][0],
            'notifications_status':data[i][1],
            'notificatios_type':data[i][2]
        }
        notifications_data.append(_data)
    return notifications_data


def select_notifications_data(user_id:int):
    """
    Returned dict notification_data \n
    user_id, \n
    notifications_status, \n
    notifications_type
    """
    command = f"SELECT user_id, notifications_status, notifications_availability, notifications_type FROM notifications_data WHERE user_id={user_id}"
    curs = conn.cursor()
    curs.execute(command)
    data = curs.fetchone()
    if not data:
        print(f"Не найдено записей в таблице 'notifications_data' по пользователю id: {user_id}")
        return

    notifications_data = {
        'user_id':data[0], 
        'notifications_status':data[1],
        'notifications_availability':data[2],
        'notifications_type':data[3]
        }
    return notifications_data


def update_notifications_data(user_id, notifications_status=None, notifications_availability=None, notifications_type=None):
    notifications_data = select_notifications_data(user_id=user_id)
    if not notifications_data:
        notifications_status = "disabled"
        notifications_availability = "not_found"
        notifications_type = "text"
        command = f"INSERT INTO notifications_data VALUES ({user_id}, '{notifications_status}', '{notifications_type}', '{notifications_availability}')"
    else:
        if not notifications_status:
            notifications_status = notifications_data['notifications_status']
        if not notifications_type:
            notifications_type = notifications_data['notifications_type']
        if not notifications_availability:
            notifications_availability = notifications_data['notifications_availability']
        command = f"UPDATE notifications_data SET notifications_status = '{notifications_status}', notifications_availability = '{notifications_availability}', notifications_type = '{notifications_type}' WHERE user_id = {user_id}"

    curs = conn.cursor()
    curs.execute(command)
    conn.commit()
    print(f"Пользователь {user_id} обновил настройки уведомлений")


def drop_notifications(user_id):
    fcast_types = ['current', 'today', 'tomorrow', 'week']
    for fcast_type in fcast_types:
        command = f"DELETE FROM notifications_{fcast_type}_fcast WHERE user_id = {user_id}"
        curs = conn.cursor()
        curs.execute(command)
    conn.commit()
    update_notifications_data(user_id=user_id, notifications_status='disabled', notifications_availability='not_found')
    print(f"Все уведомления пользователя {user_id} удалены.")

### END NOTIFICATIONS ###
#########################


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
#drop_table('notifications')
#create_table("current_cities", ['id', 'user_id', 'username', 'city_address', 'city_coords'], ['INTEGER PRIMARY KEY', 'INTEGER', 'TEXT', 'TEXT', 'TEXT'])
#create_table("feedbacks", ['id', 'user_id', 'username', 'fb_text', 'action'], ['INTEGER PRIMARY KEY', 'INTEGER', 'TEXT', 'TEXT', 'TEXT'])
#create_table("notifications", ['id', 'user_id', 'username', 'city_address', 'city_coords', 'notification_time'], ['INTEGER PRIMARY KEY', 'INTEGER', 'TEXT', 'TEXT', 'TEXT', 'TEXT'])

# def select_cities_coords(user_id):
#     command = f"SELECT city_coords, notification_time, id FROM notifications WHERE user_id = {user_id}"
#     curs = conn.cursor()
#     curs.execute(command)
#     data = curs.fetchall()
#     if len(data) == 0:
#         return
#     follow_data = []
#     for i in range(0, len(data)):
#         city_coords = (data[i][0]).split(";")
#         follow_data.append([{"lat": city_coords[0], "lon": city_coords[1]}, data[i][1], data[i][2]])
#     return follow_data





# def select_follow_cities(user_id):
#     command = f"SELECT city_address FROM notifications WHERE user_id = {user_id}"
#     curs = conn.cursor()
#     curs.execute(command)
#     cities_list = curs.fetchall()
#     cities = []
#     if len(cities_list) > 0:
#         for city in cities_list:
#             cities.append(city[0])
#     return cities


# def select_city_coords(user_id, city_address=None):
#     command = f"SELECT city_coords FROM notifications WHERE (user_id = {user_id}) AND (city_address = '{city_address}')"
#     curs = conn.cursor()
#     curs.execute(command)
#     coords_list = (curs.fetchone()[0]).split(";")
#     coords = {"lat": coords_list[0], "lon": coords_list[1]}
#     return coords


# def select_notification_time(user_id, city_address = None, city_number = -1):
#     command = ""
#     if city_address and city_number == -1:
#         command = f"SELECT notification_time FROM notifications WHERE (city_address = '{city_address}') AND (user_id = {user_id})"
#     elif city_number != -1 and not city_address:
#         command = f"SELECT notification_time FROM notifications WHERE (id = '{city_number}') AND (user_id = {user_id})"
#     curs = conn.cursor()
#     curs.execute(command)
#     time = curs.fetchone()[0]
#     return time


# def select_city_number(user_id, city_address):
#     command = f"SELECT id FROM notifications WHERE (user_id = {user_id} AND city_address = '{city_address}')"
#     curs = conn.cursor()
#     curs.execute(command)
#     city_number = curs.fetchone()[0]
#     return city_number


# def select_city_address(user_id, city_number):
#     command = f"SELECT city_address FROM notifications WHERE (user_id = {user_id}) AND (id = {city_number})"
#     curs = conn.cursor()
#     curs.execute(command)
#     city_address = curs.fetchone()[0]
#     return city_address


# def select_count_following_cities(user_id):
#     command = f"SELECT COUNT (id) FROM notifications WHERE user_id = {user_id}"
#     curs = conn.cursor()
#     curs.execute(command)
#     city_count = curs.fetchone()[0]
#     return city_count


# def select_max_id_following_cities():
#     command = f"SELECT MAX (id) FROM notifications"
#     curs = conn.cursor()
#     curs.execute(command)
#     city_number = curs.fetchone()[0]
#     return city_number