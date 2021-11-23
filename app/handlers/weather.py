import requests
import json
from geopy.geocoders import Nominatim

from os import getenv
from sys import exit


weather_token = getenv("WEATHER_TOKEN")
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
        direction = "северный"
        icon = '\u2191'
    elif south[0] <= wind_deg <= south[1]:
        direction = "южный"
        icon = '\u2193'
    elif west[0] <= wind_deg <= west[1]:
        direction = "западный"
        icon = '\u2190'
    elif east[0] <= wind_deg <= east[1]:
        direction = "восточный"
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


def definition_city(city):
    response = requests.get(
        f'http://api.openweathermap.org/data/2.5/weather?q={city}&appid={weather_token}&units=metric&lang=ru')
    if response.status_code != 200:
        return False

    coord = response.json()['coord']  # return
    location = geolocator.reverse(
        f"{coord['lat']}, {coord['lon']}"
    ).raw['address']

    keys = location.keys()
    locality = ""
    if 'village' in keys:  # село
        locality = location['village']
    elif 'city' in keys:  # город
        locality = location['city']
    elif 'hamlet' in keys:  # деревушка
        locality = location['hamlet']
    elif 'town' in keys:  # поселок
        locality = location['town']
    elif 'town' in keys:  # поселок
        locality = location['town']

    address = ', '.join(
        location['country'], location['state'], location['county'], locality)  # return
    return {'address': address, 'coord': coord}
    # print(location.address)
    #print(json.dumps(location.raw, sort_keys=True, indent=4, ensure_ascii=False))


def get_coords(city_name: str):
    """
    Возвращает координаты в виде словаря
    Широта: lat
    Долгота: lon
    """
    return {
        'lat': geolocator.geocode(city_name).raw['lat'],
        'lon': geolocator.geocode(city_name).raw['lon']
    }


def get_address(city_name: str):
    try:
        coord = get_coords(city_name)
        location = geolocator.reverse(
            f"{coord['lat']}, {coord['lon']}").raw['address']
        
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
        print(f"Ошибка, не удалось найти локацию {city_name}")
    finally:
        return address


def get_weather(coords: dict):
    """
    Возвращает текущую погоду, 
    определенную по координатам, 
    в виде отформатированной строки
    """
    response = requests.get(
        f"http://api.openweathermap.org/data/2.5/weather?lat={coords['lat']}&lon={coords['lon']}&appid={weather_token}&units=metric&lang=ru")
    if response.status_code != 200:
        return None

    weather_data = response.json()
    city_name = weather_data['name']
    weather_description = weather_data['weather'][0]['description']
    temp = weather_data['main']['temp']
    pressure = weather_data['main']['pressure']
    humidity = weather_data['main']['humidity']
    wind_speed = weather_data['wind']['speed']
    wind_deg = weather_data['wind']['deg']
    wind_dir, wind_icon = get_wind_direction(wind_deg)
    weather = f"Сейчас в {city_name} {weather_description}\n" \
        f"Температура {round(temp, 1)} \u2103 \n" \
        f"Атм. давление {round(pressure/1.333)} мм рт. ст.\n" \
        f"Влажность {humidity}%\n" \
        f"Ветер {wind_dir} ({wind_deg}\u00B0 {wind_icon}) {wind_speed} м/с"
    return weather


def current_weather_by_coordinates(coord: dict):
    response = requests.get(
        f"api.openweathermap.org/data/2.5/weather?lat={coord['lat']}&lon={coord['lon']}&appid={weather_token}&units=metric&lang=ru")
    if response.status_code != 200:
        return None
    return get_weather(response.json())


def current_weather_by_city_name(city='Москва'):
    response = requests.get(
        f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={weather_token}&units=metric&lang=ru")
    if response.status_code == 200:
        #json_text = json.dumps(response.json(), sort_keys=True, indent=4, ensure_ascii=False)
        json_text = response.json()
        city_name = json_text['name']
        weather_description = json_text['weather'][0]['description']
        temp = json_text['main']['temp']
        pressure = json_text['main']['pressure']
        humidity = json_text['main']['humidity']
        wind_speed = json_text['wind']['speed']
        wind_deg = json_text['wind']['deg']
        wind_dir = get_wind_direction(wind_deg)
        answer_text = f"Сейчас в {city_name} {weather_description}\n" \
            f"Температура {round(temp, 1)} \u2103 \n" \
            f"Атм. давление {round(pressure/1.333)} мм рт. ст.\n" \
            f"Влажность {humidity}%\n" \
            f"Ветер {wind_dir} {wind_speed} м/с"
    elif response.status_code != 200:
        answer_text = "Возникла непредвиденная ошибка. Попробуйте выполнить операцию позже."
        city_name = None

    return {'city': city_name, 'weather': answer_text}


# city_name = 'Соколово'

# response = requests.get(f'http://api.openweathermap.org/data/2.5/weather?q={city_name}&appid={weather_token}&units=metric&lang=ru')

# print(response.status_code)

# def jprint(obj):
#     text = json.dumps(obj, sort_keys=True, indent=4, ensure_ascii=False)
#     print(text)

# jprint(response.json())

# json_text = response.json()

# print(json_text['name'], json_text['weather'][0]['description'], json_text['main']['temp'], json_text['wind']['speed'])
