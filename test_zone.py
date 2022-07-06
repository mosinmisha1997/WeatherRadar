import sqlite3

conn = sqlite3.connect("./weather_radar.db")

curs = conn.cursor()
#command = "CREATE TABLE users_data(user_id INTEGER PRIMARY KEY, username TEXT, first_name TEXT, last_name TEXT, lang_code TEXT, date_of_register TEXT)"
# command = "CREATE TABLE notifications_current_fcast(user_id INTEGER, notifications_time TEXT)"
# curs.execute(command)
# command = "CREATE TABLE notifications_week_fcast(user_id INTEGER, notifications_time TEXT)"
# curs.execute(command)
# command = "CREATE TABLE notifications_today_fcast(user_id INTEGER, notifications_time TEXT)"
# curs.execute(command)
# command = "CREATE TABLE notifications_tomorrow_fcast(user_id INTEGER, notifications_time TEXT)"
# curs.execute(command)
# command = "CREATE TABLE notifications_data(user_id INTEGER, notifications_status TEXT, lang_code TEXT, city_coords TEXT, notifications_type TEXT)"
# curs.execute(command)
#command = "DROP TABLE notifications_data"
# curs.execute(command)
# conn.commit()