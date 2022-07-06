import requests
import locale
import json
from enum import Enum
import datetime as dt
import pytz
from geopy.geocoders import Nominatim

from os import getenv
from sys import exit
import app.database.database as db
from app.painter.paint_forecast import get_image, get_image_404


locale.setlocale(locale.LC_ALL, "")

#weather_token = getenv("WEATHER_TOKEN")
weather_token = 'd21a4b969159321c09a5fe0ae7544b8b'
if not weather_token:
    exit("Погодный токен не найден")


geolocator = Nominatim(user_agent='WeatherRadar_bot')


def get_wind_direction(wind_deg):
    nord = [348.75, 11.25]
    nneast = [11.25, 33.75]
    neast = [33.75, 56.25]
    eneast = [56.25, 78.75]
    east = [78.75, 101.25]
    eseast = [101.25, 123.75]
    seast = [123.75, 146.25]
    sseast = [146.25, 168.75]
    south = [168.75, 191.25]
    sswest = [191.25, 213.75]
    swest = [213.75, 236.25]
    wswest = [236.25, 258.75]
    west = [258.75, 281.25]
    wnwest = [281.25, 303.75]
    nwest = [303.75, 326.25]
    nnwest = [326.25, 348.75]

    if nord[0] < wind_deg <= 360 or 0 <= wind_deg < nord[1]:
        direction = "С"
        icon = '\u2191'
    elif south[0] <= wind_deg <= south[1]:
        direction = "Ю"
        icon = '\u2193'
    elif west[0] <= wind_deg <= west[1]:
        direction = "З"
        icon = '\u2190'
    elif east[0] <= wind_deg <= east[1]:
        direction = "В"
        icon = '\u2192'
    elif nneast[0] <= wind_deg <= nneast[1]:
        direction = "ССВ"
        icon = '\u2B08'
    elif neast[0] <= wind_deg <= neast[1]:
        direction = "СВ"
        icon = '\u2B08'
    elif eneast[0] <= wind_deg <= eneast[1]:
        direction = "ВСВ"
        icon = '\u2B08'
    elif eseast[0] <= wind_deg <= eseast[1]:
        direction = "ВЮВ"
        icon = '\u2B0A'
    elif seast[0] <= wind_deg <= seast[1]:
        direction = "ЮВ"
        icon = '\u2B0A'
    elif sseast[0] <= wind_deg <= sseast[1]:
        direction = "ЮЮВ"
        icon = '\u2B0A'
    elif sswest[0] <= wind_deg <= sswest[1]:
        direction = "ЮЮЗ"
        icon = '\u2B0B'
    elif swest[0] <= wind_deg <= swest[1]:
        direction = "ЮЗ"
        icon = '\u2B0B'
    elif wswest[0] <= wind_deg <= wswest[1]:
        direction = "ЗЮЗ"
        icon = '\u2B0B'
    elif wnwest[0] <= wind_deg <= wnwest[1]:
        direction = "ЗСЗ"
        icon = '\u2B09'
    elif nwest[0] <= wind_deg <= nwest[1]:
        direction = "СЗ"
        icon = '\u2B09'
    elif nnwest[0] <= wind_deg <= nnwest[1]:
        direction = "ССЗ"
        icon = '\u2B09'
    return direction, icon


def get_weather_icon(icon_id):
    icons = {
        '01d':'🌞',
        '01n':'🌝',
        '02d':'🌤',
        '02n':'🌤',
        '03d':'☁',
        '03n':'☁',
        '04d':'⛅',
        '04n':'⛅',
        '09d':'🌧',
        '09n':'🌧',
        '10d':'🌦',
        '10n':'🌦',
        '11d':'🌩',
        '11n':'🌩',
        '13d':'❄',
        '13n':'❄',
        '50d':'🌫',
        '50n':'🌫',
        }
    icon_code = icons[icon_id]
    return icon_code


def get_cities_data(city_name):
    geocodes = geolocator.geocode(city_name, exactly_one=False, country_codes='RU', addressdetails=True, namedetails=True)
    if not geocodes:
        geocodes = geolocator.geocode(city_name, exactly_one=False, addressdetails=True, namedetails=True)

    cities_data = {}

    if geocodes:
        i = 0
        for code in geocodes:
            if code.raw['class'] == 'place' and 'county' in code.raw['address'].keys():
                name = code.raw['namedetails']['name']
                state = code.raw['address']['state']
                country = code.raw['address']['country']
                county = code.raw['address']['county']
                
                address = ', '.join([name, county, state, country])
                coords = {'lat':code.raw['lat'], 'lon':code.raw['lon']}
                cities_data.update({address:coords})
                i += 1
    return cities_data
            

def get_coords(city_name: str):
    """
    Возвращает координаты в виде словаря
    Широта: lat
    Долгота: lon
    """
    geocodes = geolocator.geocode(city_name, exactly_one=False, country_codes='RU', addressdetails=True, namedetails=True)
    if not geocodes:
        geocodes = geolocator.geocode(city_name, exactly_one=False, addressdetails=True, namedetails=True)

    return {
        'lat': geolocator.geocode(city_name).raw['lat'],
        'lon': geolocator.geocode(city_name).raw['lon']
    }


def get_address(address: str = None, coords: dict = None):
    try:
        if not coords:
            coords = get_coords(address)
        location = geolocator.reverse(
            f"{coords['lat']}, {coords['lon']}").raw['address']
        
        address = []
        keys = location.keys()
        if 'village' in keys:  # село
            address.append(location['village'])
        elif 'city' in keys:  # город
            address.append(location['city'])
        elif 'hamlet' in keys:  # деревушка
            address.append(location['hamlet'])
        elif 'town' in keys:  # поселок
            address.append(location['town'])

        if 'state' in keys:
            address.append(location['state'])
        
        if 'county' in keys:
            address.append(location['county'])
        
        if 'country' in keys:
            address.append(location['country'])
        
        address = ', '.join(address)
    except:
        address = None
        print(f"Не удалось найти локацию {address}")
    finally:
        return address


def get_weather(user_id:int, coords: dict, fcast_type = 'current', notifications_type = 'text'):
    """
    Возвращает текущую погоду, 
    определенную по координатам, 
    в виде отформатированной строки
    """
    response = requests.get(
        f"http://api.openweathermap.org/data/2.5/onecall?lat={coords['lat']}&lon={coords['lon']}&appid={weather_token}&units=metric&lang=ru")
    if response.status_code != 200:
        return None

    weather_data = response.json()
    units_settings = db.select_units_settings(user_id=user_id)
    if notifications_type == 'text':
        if fcast_type == 'current':
            return get_current_weather(weather_data, units_settings=units_settings)
        elif fcast_type == 'today':
            return get_today_forecast(weather_data, units_settings=units_settings)
        elif fcast_type == 'week':
            return get_weekly_forecast(weather_data, units_settings=units_settings)
        elif fcast_type == 'tomorrow':
            return get_tomorrow_forecast(weather_data, units_settings=units_settings)
    elif notifications_type == 'image':
        if fcast_type == 'current':
            return get_current_weather_image(weather_data=weather_data, units_settings=units_settings)
        else:
            return get_image_404()


speed = {'м/с':1, 'миль/ч':1.598}
temp = {'°C':[1, 0], '°F':[1.8, 32]}
press = {'мм рт. ст.':1.333, 'дюйм рт. ст.':25.4*1.333}


def get_current_weather_image(weather_data, units_settings):
    coords = {'lat':weather_data['lat'], 'lon':weather_data['lon']}
    address = get_address(coords=coords)
    if address:
        address = address.split(",")[0]
    tz = weather_data['timezone']
    time = dt.datetime.now(pytz.timezone(tz)).strftime('%H:%M (%#d %b %Y)')
    weather_description = weather_data['current']['weather'][0]['description']
    icon_id = weather_data['current']['weather'][0]['icon']

    _temp = round(weather_data['current']['temp']*temp[units_settings['temperature']][0]+temp[units_settings['temperature']][1])
    temp_feels_like = round(weather_data['current']['feels_like']*temp[units_settings['temperature']][0]+temp[units_settings['temperature']][1])
    pressure = round(weather_data['current']['pressure']/press[units_settings['pressure']])
    humidity = weather_data['current']['humidity']
    clouds = weather_data['current']['clouds']
    wind_speed = round(weather_data['current']['wind_speed']*speed[units_settings['speed']])
    wind_deg = weather_data['current']['wind_deg']
    wind_gust = 0
    if 'wind_gust' in weather_data['current'].keys():
        wind_gust = weather_data['current']['wind_gust']*speed[units_settings['speed']]    # возможно у какого-то города не будет одного из параметров
    wind_dir, wind_icon = get_wind_direction(wind_deg)
    
    data = {
        'city_name':address,
        'fcast_type':'сейчас',
        'temp':_temp,
        'temp_feels_like':temp_feels_like,
        'pressure':pressure,
        'humidity':humidity,
        'clouds':clouds,
        'wind_speed':wind_speed,
        'wind_dir':wind_dir,
        'time':time,
        'weather_description':weather_description,
        'icon_id':icon_id
    }

    image_path = get_image(data, units_settings)
    return image_path


def get_current_weather(weather_data, units_settings):
    coords = {'lat':weather_data['lat'], 'lon':weather_data['lon']}
    address = get_address(coords=coords)
    tz = weather_data['timezone']
    time = dt.datetime.now(pytz.timezone(tz)).strftime('%H:%M (%#d %b %Y)')
    weather_description = weather_data['current']['weather'][0]['description']
    icon_id = weather_data['current']['weather'][0]['icon']
    icon = get_weather_icon(icon_id)
    
    _temp = weather_data['current']['temp']*temp[units_settings['temperature']][0]+temp[units_settings['temperature']][1]
    temp_feels_like = weather_data['current']['feels_like']*temp[units_settings['temperature']][0]+temp[units_settings['temperature']][1]
    pressure = weather_data['current']['pressure']/press[units_settings['pressure']]
    humidity = weather_data['current']['humidity']
    clouds = weather_data['current']['clouds']
    wind_speed = weather_data['current']['wind_speed']*speed[units_settings['speed']]
    wind_deg = weather_data['current']['wind_deg']
    wind_gust = 0
    if 'wind_gust' in weather_data['current'].keys():
        wind_gust = weather_data['current']['wind_gust']*speed[units_settings['speed']]    # возможно у какого-то города не будет одного из параметров
    wind_dir, wind_icon = get_wind_direction(wind_deg)
    
    weather = f"Сейчас в {address}\n" \
        f"{icon} {weather_description}\n" \
        f"🌡 Температура {round(_temp, 1)}{units_settings['temperature']}, ощущается как {round(temp_feels_like, 1)}{units_settings['temperature']}\n" \
        f"🚑 Атм. давление {round(pressure)} {units_settings['pressure']}\n" \
        f"💧 Влажность {humidity}%\n" \
        f"☁ Облачность {clouds}%\n" \
        f"🚩 Ветер {wind_dir} ({wind_deg}\u00B0 {wind_icon}) {round(wind_speed, 1)} {units_settings['speed']} с порывами до {round(wind_gust, 1)} {units_settings['speed']}\n" \
        f"🕰 Местное время: {time}"
    return weather


def get_today_forecast(weather_data, units_settings):
    coords = {'lat':weather_data['lat'], 'lon':weather_data['lon']}
    address = get_address(coords=coords)

    date = dt.datetime.fromtimestamp(weather_data['daily'][0]['dt']).strftime('%#d %b')
    description = weather_data['daily'][0]['weather'][0]['description']
    icon_id = weather_data['daily'][0]['weather'][0]['icon']
    icon = get_weather_icon(icon_id)
    temp_min = weather_data['daily'][0]['temp']['min']*temp[units_settings['temperature']][0]+temp[units_settings['temperature']][1]
    temp_max = weather_data['daily'][0]['temp']['max']*temp[units_settings['temperature']][0]+temp[units_settings['temperature']][1]
    temp_morn = weather_data['daily'][0]['temp']['morn']*temp[units_settings['temperature']][0]+temp[units_settings['temperature']][1]
    temp_day = weather_data['daily'][0]['temp']['day']*temp[units_settings['temperature']][0]+temp[units_settings['temperature']][1]
    temp_eve = weather_data['daily'][0]['temp']['eve']*temp[units_settings['temperature']][0]+temp[units_settings['temperature']][1]
    temp_night = weather_data['daily'][0]['temp']['night']*temp[units_settings['temperature']][0]+temp[units_settings['temperature']][1]
    temp_feels_like_morn = weather_data['daily'][0]['feels_like']['morn']*temp[units_settings['temperature']][0]+temp[units_settings['temperature']][1]
    temp_feels_like_day = weather_data['daily'][0]['feels_like']['day']*temp[units_settings['temperature']][0]+temp[units_settings['temperature']][1]
    temp_feels_like_eve = weather_data['daily'][0]['feels_like']['eve']*temp[units_settings['temperature']][0]+temp[units_settings['temperature']][1]
    temp_feels_like_night = weather_data['daily'][0]['feels_like']['night']*temp[units_settings['temperature']][0]+temp[units_settings['temperature']][1]
    pressure = weather_data['daily'][0]['pressure']/press[units_settings['pressure']]
    humidity = weather_data['daily'][0]['humidity']
    clouds = weather_data['daily'][0]['clouds']
    wind_speed = weather_data['daily'][0]['wind_speed']*speed[units_settings['speed']]
    wind_deg = weather_data['daily'][0]['wind_deg']
    wind_gust = 0
    if 'wind_gust' in weather_data['daily'][0].keys():
        wind_gust = weather_data['daily'][0]['wind_gust']*speed[units_settings['speed']]
    wind_dir, wind_icon = get_wind_direction(wind_deg)

    forecast = f"Сегодня {date} в {address}\n" \
        f"{icon} {description}\n" \
        f"🌡 Температура от {round(temp_min, 1)}{units_settings['temperature']} до {round(temp_max, 1)}{units_settings['temperature']}\n" \
        f"🌡 Утром {round(temp_morn, 1)}{units_settings['temperature']}, ощущается как {round(temp_feels_like_morn, 1)}{units_settings['temperature']}\n" \
        f"🌡 Днем {round(temp_day, 1)}{units_settings['temperature']}, ощущается как {round(temp_feels_like_day, 1)}{units_settings['temperature']}\n" \
        f"🌡 Вечером {round(temp_eve, 1)}{units_settings['temperature']}, ощущается как {round(temp_feels_like_eve, 1)}{units_settings['temperature']}\n" \
        f"🌡 Ночью {round(temp_night, 1)}{units_settings['temperature']}, ощущается как {round(temp_feels_like_night, 1)}{units_settings['temperature']}\n" \
        f"🚑 Атм. давление {round(pressure)} {units_settings['pressure']}\n" \
        f"💧 Влажность {humidity}%\n" \
        f"☁ Облачность {clouds}%\n" \
        f"🚩 Ветер {wind_dir} ({wind_deg}\u00B0 {wind_icon}) {round(wind_speed, 1)} {units_settings['speed']} с порывами до {round(wind_gust, 1)} {units_settings['speed']}"

    return forecast
    

def get_tomorrow_forecast(weather_data, units_settings):
    coords = {'lat':weather_data['lat'], 'lon':weather_data['lon']}
    address = get_address(coords=coords)

    date = dt.datetime.fromtimestamp(weather_data['daily'][1]['dt']).strftime('%#d %b')
    description = weather_data['daily'][1]['weather'][0]['description']
    icon_id = weather_data['daily'][1]['weather'][0]['icon']
    icon = get_weather_icon(icon_id)
    temp_min = weather_data['daily'][1]['temp']['min']*temp[units_settings['temperature']][0]+temp[units_settings['temperature']][1]
    temp_max = weather_data['daily'][1]['temp']['max']*temp[units_settings['temperature']][0]+temp[units_settings['temperature']][1]
    temp_morn = weather_data['daily'][1]['temp']['morn']*temp[units_settings['temperature']][0]+temp[units_settings['temperature']][1]
    temp_day = weather_data['daily'][1]['temp']['day']*temp[units_settings['temperature']][0]+temp[units_settings['temperature']][1]
    temp_eve = weather_data['daily'][1]['temp']['eve']*temp[units_settings['temperature']][0]+temp[units_settings['temperature']][1]
    temp_night = weather_data['daily'][1]['temp']['night']*temp[units_settings['temperature']][0]+temp[units_settings['temperature']][1]
    temp_feels_like_morn = weather_data['daily'][1]['feels_like']['morn']*temp[units_settings['temperature']][0]+temp[units_settings['temperature']][1]
    temp_feels_like_day = weather_data['daily'][1]['feels_like']['day']*temp[units_settings['temperature']][0]+temp[units_settings['temperature']][1]
    temp_feels_like_eve = weather_data['daily'][1]['feels_like']['eve']*temp[units_settings['temperature']][0]+temp[units_settings['temperature']][1]
    temp_feels_like_night = weather_data['daily'][1]['feels_like']['night']*temp[units_settings['temperature']][0]+temp[units_settings['temperature']][1]
    pressure = weather_data['daily'][1]['pressure']/press[units_settings['pressure']]
    humidity = weather_data['daily'][1]['humidity']
    clouds = weather_data['daily'][1]['clouds']
    wind_speed = weather_data['daily'][1]['wind_speed']*speed[units_settings['speed']]
    wind_deg = weather_data['daily'][1]['wind_deg']
    wind_gust = 0
    if 'wind_gust' in weather_data['daily'][1].keys():
        wind_gust = weather_data['daily'][1]['wind_gust']*speed[units_settings['speed']]
    wind_dir, wind_icon = get_wind_direction(wind_deg)

    forecast = f"Завтра {date} в {address}\n" \
        f"{icon} {description}\n" \
        f"🌡 Температура от {round(temp_min, 1)}{units_settings['temperature']} до {round(temp_max, 1)}{units_settings['temperature']}\n" \
        f"🌡 Утром {round(temp_morn, 1)}{units_settings['temperature']}, ощущается как {round(temp_feels_like_morn, 1)}{units_settings['temperature']}\n" \
        f"🌡 Днем {round(temp_day, 1)}{units_settings['temperature']}, ощущается как {round(temp_feels_like_day, 1)}{units_settings['temperature']}\n" \
        f"🌡 Вечером {round(temp_eve, 1)}{units_settings['temperature']}, ощущается как {round(temp_feels_like_eve, 1)}{units_settings['temperature']}\n" \
        f"🌡 Ночью {round(temp_night, 1)}{units_settings['temperature']}, ощущается как {round(temp_feels_like_night, 1)}{units_settings['temperature']}\n" \
       f"🚑 Атм. давление {round(pressure)} {units_settings['pressure']}\n" \
        f"💧 Влажность {humidity}%\n" \
        f"☁ Облачность {clouds}%\n" \
        f"🚩 Ветер {wind_dir} ({wind_deg}\u00B0 {wind_icon}) {round(wind_speed, 1)} {units_settings['speed']} с порывами до {round(wind_gust, 1)} {units_settings['speed']}"

    return forecast


def get_weekly_forecast(weather_data, units_settings):
    coords = {'lat':weather_data['lat'], 'lon':weather_data['lon']}
    address = get_address(coords=coords)
    daily_forecast = []
    for i in range(0, 6):
        date = dt.datetime.fromtimestamp(weather_data['daily'][i]['dt']).strftime('%#d %b')
        description = weather_data['daily'][i]['weather'][0]['description']
        icon_id = weather_data['daily'][i]['weather'][0]['icon']
        icon = get_weather_icon(icon_id)
        temp_min = weather_data['daily'][i]['temp']['min']*temp[units_settings['temperature']][0]+temp[units_settings['temperature']][1]
        temp_max = weather_data['daily'][i]['temp']['max']*temp[units_settings['temperature']][0]+temp[units_settings['temperature']][1]
        temp_morn = weather_data['daily'][i]['temp']['morn']*temp[units_settings['temperature']][0]+temp[units_settings['temperature']][1]
        temp_day = weather_data['daily'][i]['temp']['day']*temp[units_settings['temperature']][0]+temp[units_settings['temperature']][1]
        temp_eve = weather_data['daily'][i]['temp']['eve']*temp[units_settings['temperature']][0]+temp[units_settings['temperature']][1]
        temp_night = weather_data['daily'][i]['temp']['night']*temp[units_settings['temperature']][0]+temp[units_settings['temperature']][1]
        temp_feels_like_morn = weather_data['daily'][i]['feels_like']['morn']*temp[units_settings['temperature']][0]+temp[units_settings['temperature']][1]
        temp_feels_like_day = weather_data['daily'][i]['feels_like']['day']*temp[units_settings['temperature']][0]+temp[units_settings['temperature']][1]
        temp_feels_like_eve = weather_data['daily'][i]['feels_like']['eve']*temp[units_settings['temperature']][0]+temp[units_settings['temperature']][1]
        temp_feels_like_night = weather_data['daily'][i]['feels_like']['night']*temp[units_settings['temperature']][0]+temp[units_settings['temperature']][1]
        pressure = weather_data['daily'][i]['pressure']/press[units_settings['pressure']]
        humidity = weather_data['daily'][i]['humidity']
        clouds = weather_data['daily'][i]['clouds']
        wind_speed = weather_data['daily'][i]['wind_speed']*speed[units_settings['speed']]
        wind_deg = weather_data['daily'][i]['wind_deg']
        wind_gust = 0
        if 'wind_gust' in weather_data['daily'][i].keys():
            wind_gust = weather_data['daily'][i]['wind_gust']*speed[units_settings['speed']]
        wind_dir, wind_icon = get_wind_direction(wind_deg)

        forecast = f"{date} в {address}\n" \
            f"{icon} {description}\n" \
            f"🌡 Температура от {round(temp_min, 1)}{units_settings['temperature']} до {round(temp_max, 1)}{units_settings['temperature']}\n" \
            f"🌡 Утром {round(temp_morn, 1)}{units_settings['temperature']}, ощущается как {round(temp_feels_like_morn, 1)}{units_settings['temperature']}\n" \
            f"🌡 Днем {round(temp_day, 1)}{units_settings['temperature']}, ощущается как {round(temp_feels_like_day, 1)}{units_settings['temperature']}\n" \
            f"🌡 Вечером {round(temp_eve, 1)}{units_settings['temperature']}, ощущается как {round(temp_feels_like_eve, 1)}{units_settings['temperature']}\n" \
            f"🌡 Ночью {round(temp_night, 1)}{units_settings['temperature']}, ощущается как {round(temp_feels_like_night, 1)}{units_settings['temperature']}\n" \
            f"🚑 Атм. давление {round(pressure)} {units_settings['pressure']}\n" \
            f"💧 Влажность {humidity}%\n" \
            f"☁ Облачность {clouds}%\n" \
            f"🚩 Ветер {wind_dir} ({wind_deg}\u00B0 {wind_icon}) {round(wind_speed, 1)} {units_settings['speed']} с порывами до {round(wind_gust, 1)} {units_settings['speed']}"
        daily_forecast.append(forecast)
    return '\n\n'.join(daily_forecast)


# city_name = 'Соколово'

# response = requests.get(f'http://api.openweathermap.org/data/2.5/weather?q={city_name}&appid={weather_token}&units=metric&lang=ru')

# print(response.status_code)

# def jprint(obj):
#     text = json.dumps(obj, sort_keys=True, indent=4, ensure_ascii=False)
#     print(text)

# jprint(response.json())

# json_text = response.json()

# print(json_text['name'], json_text['weather'][0]['description'], json_text['main']['temp'], json_text['wind']['speed'])
