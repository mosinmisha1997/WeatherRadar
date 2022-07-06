import os
from PIL import Image, ImageDraw, ImageFont

from enum import Enum

# img = Image.new('RGBA', (600, 600), 'white')
# idraw = ImageDraw.Draw(img)


class Coords(Enum):
    CITY_NAME = [300, 25]
    FCAST_TYPE = [300, 65]
    WEATHER_ICON = [300, 180]
    TEMPERATURE = [300, 280]
    TEMPERATURE_FEELS_LIKE = [300, 340]
    WEATHER_DESCRIPTION = [300, 375]
    WIND_ICON = [75, 455]
    HUMIDITY_ICON = [225, 455]
    PRESSURE_ICON = [375, 455]
    CLOUDY_ICON = [525, 455]
    WIND = [75, 515]
    HUMIDITY = [225, 515]
    PRESSURE = [375, 515]
    CLOUDY = [525, 515]
    WIND_UNITS = [75, 540]
    HUMIDITY_UNITS = [225, 540]
    PRESSURE_UNITS = [375, 540]
    CLOUDY_UNITS = [525, 540]
    DATE = [300, 580]


class FcastIcons(Enum):
    CLOUDY = './static/pictures/forecast/cloudy.png'
    HUMIDITY = './static/pictures/forecast/humidity.png'
    PRESSURE = './static/pictures/forecast/pressure.png'
    WIND = './static/pictures/forecast/wind.png'


class Fonts(Enum):
    REGULAR = './static/fonts/RobotoSlab-Regular.ttf'
    BOLD = './static/fonts/RobotoSlab-Bold.ttf'


class FontColor(Enum):
    MAIN = '#000000'
    SUB = '#888888'


weather_icons = {
    '01d':'./static/pictures/weather/01d.png',
    '01n':'./static/pictures/weather/01n.png',
    '02d':'./static/pictures/weather/02d.png',
    '02n':'./static/pictures/weather/02n.png',
    '03d':'./static/pictures/weather/03d.png',
    '03n':'./static/pictures/weather/03n.png',
    '04d':'./static/pictures/weather/04d.png',
    '04n':'./static/pictures/weather/04n.png',
    '09d':'./static/pictures/weather/09d.png',
    '09n':'./static/pictures/weather/09n.png',
    '10d':'./static/pictures/weather/10d.png',
    '10n':'./static/pictures/weather/10n.png',
    '11d':'./static/pictures/weather/11d.png',
    '11n':'./static/pictures/weather/11n.png',
    '13d':'./static/pictures/weather/13d.png',
    '13n':'./static/pictures/weather/13n.png',
    '50d':'./static/pictures/weather/50d.png',
    '50n':'./static/pictures/weather/50n.png',
    }


speed = {'м/с':1, 'миль/ч':1.598}
temp = {'℃':[1, 0], '℉':[1.8, 32]}
press = {'мм рт. ст.':1.333, 'дюйм рт. ст.':25.4*1.333}


def paste_img(bg, img_path, xy):
    img = Image.open(img_path).convert("RGBA")
    size = img.size
    width = int(size[0]/2)
    height = int(size[1]/2)
    bg.paste(img, (xy[0]-width, xy[1]-height), mask=img)


def paste_text(bg, text, xy, font, size, color):
    font_info = ImageFont.truetype(font=font, size=size)
    draw_text = ImageDraw.Draw(bg)
    draw_text.text(
        xy=(xy[0], xy[1]),
        text=text,
        font=font_info,
        fill=color,
        anchor='mt'
    )


def get_image(data, units):
    bg = Image.new('RGBA', (600, 600), 'white')

    city_name = data['city_name']
    fcast_type = data['fcast_type']
    temp = data['temp']
    temp_feels_like = data['temp_feels_like']
    pressure = data['pressure']
    humidity = data['humidity']
    clouds = data['clouds']
    wind_speed = data['wind_speed']
    wind_dir = data['wind_dir']
    time = data['time']
    weather_description = data['weather_description']
    icon_id = data['icon_id']

    paste_text(bg=bg, text=city_name, xy=Coords.CITY_NAME.value, font=Fonts.BOLD.value, size=30, color=FontColor.MAIN.value)
    paste_text(bg=bg, text=fcast_type, xy=Coords.FCAST_TYPE.value, font=Fonts.REGULAR.value, size=18, color=FontColor.MAIN.value)

    paste_img(bg=bg, img_path=weather_icons[icon_id], xy=Coords.WEATHER_ICON.value)
    paste_text(bg=bg, text=f"{temp} {units['temperature']}", xy=Coords.TEMPERATURE.value, font=Fonts.BOLD.value, size=62, color=FontColor.MAIN.value)
    paste_text(bg=bg, text=f"ощущается как: {temp_feels_like} {units['temperature']}", xy=Coords.TEMPERATURE_FEELS_LIKE.value, font=Fonts.REGULAR.value, size=22, color=FontColor.SUB.value)
    paste_text(bg=bg, text=weather_description, xy=Coords.WEATHER_DESCRIPTION.value, font=Fonts.BOLD.value, size=30, color=FontColor.MAIN.value)

    paste_img(bg=bg, img_path=FcastIcons.WIND.value, xy=Coords.WIND_ICON.value)
    paste_text(bg=bg, text=f"{wind_dir} {wind_speed}", xy=Coords.WIND.value, font=Fonts.BOLD.value, size=22, color=FontColor.MAIN.value)
    paste_text(bg=bg, text=units['speed'], xy=Coords.WIND_UNITS.value, font=Fonts.REGULAR.value, size=22, color=FontColor.MAIN.value)

    paste_img(bg=bg, img_path=FcastIcons.HUMIDITY.value, xy=Coords.HUMIDITY_ICON.value)
    paste_text(bg=bg, text=f"{humidity}", xy=Coords.HUMIDITY.value, font=Fonts.BOLD.value, size=22, color=FontColor.MAIN.value)
    paste_text(bg=bg, text=units['humidity'], xy=Coords.HUMIDITY_UNITS.value, font=Fonts.REGULAR.value, size=22, color=FontColor.MAIN.value)

    paste_img(bg=bg, img_path=FcastIcons.PRESSURE.value, xy=Coords.PRESSURE_ICON.value)
    paste_text(bg=bg, text=f"{pressure}", xy=Coords.PRESSURE.value, font=Fonts.BOLD.value, size=22, color=FontColor.MAIN.value)
    paste_text(bg=bg, text=units['pressure'], xy=Coords.PRESSURE_UNITS.value, font=Fonts.REGULAR.value, size=22, color=FontColor.MAIN.value)

    paste_img(bg=bg, img_path=FcastIcons.CLOUDY.value, xy=Coords.CLOUDY_ICON.value)
    paste_text(bg=bg, text=f"{clouds}", xy=Coords.CLOUDY.value, font=Fonts.BOLD.value, size=22, color=FontColor.MAIN.value)
    paste_text(bg=bg, text=units['cloudy'], xy=Coords.CLOUDY_UNITS.value, font=Fonts.REGULAR.value, size=22, color=FontColor.MAIN.value)

    paste_text(bg=bg, text=f"{time}", xy=Coords.DATE.value, font=Fonts.REGULAR.value, size=14, color=FontColor.SUB.value)

    image_path = './static/forecast.png'
    bg.save(image_path)
    return image_path


def get_image_404():
    bg = Image.new('RGBA', (600, 600), 'white')
    paste_text(bg=bg, text="Ой :(", xy=[300, 250], font=Fonts.BOLD.value, size=60, color=FontColor.MAIN.value)
    paste_text(bg=bg, text="что-то пошло не так...", xy=[300, 350], font=Fonts.BOLD.value, size=22, color=FontColor.MAIN.value)
    
    image_path = './static/forecast.png'
    bg.save(image_path)
    return image_path
