from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.types.message import ContentTypes

#from app.database.database import select_user_settings
import app.database.database as db
from app.handlers.settings import change_city
from app.handlers.weather import get_weather


class CurrentCity(StatesGroup):
    waiting_city_name = State()
    waiting_full_address = State()


async def today_weather(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    user_settings = db.select_user_settings(user_id)
    weather_type = 'today'
    if not user_settings:
        await change_city(message=message, state=state)
    else:
        city_coords = user_settings['coords']
        notifications_data = db.select_notifications_data(user_id)
        notifications_type = notifications_data['notifications_type']
        if notifications_type == 'text':
            await message.answer(get_weather(user_id=user_id, coords=city_coords, fcast_type=weather_type, notifications_type=notifications_type))
        elif notifications_type == 'image':
            await message.answer_photo(photo=types.InputFile(get_weather(user_id=user_id, coords=city_coords, fcast_type=weather_type, notifications_type=notifications_type)))


async def tomorrow_weather(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    user_settings = db.select_user_settings(user_id)
    weather_type = 'tomorrow'
    if not user_settings:
        await change_city(message=message, state=state)
    else:
        city_coords = user_settings['coords']
        notifications_data = db.select_notifications_data(user_id)
        notifications_type = notifications_data['notifications_type']
        if notifications_type == 'text':
            await message.answer(get_weather(user_id=user_id, coords=city_coords, fcast_type=weather_type, notifications_type=notifications_type))
        elif notifications_type == 'image':
            await message.answer_photo(photo=types.InputFile(get_weather(user_id=user_id, coords=city_coords, fcast_type=weather_type, notifications_type=notifications_type)))


async def weekly_weather(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    user_settings = db.select_user_settings(user_id)
    weather_type = 'week'
    if not user_settings:
        await change_city(message=message, state=state)
    else:
        city_coords = user_settings['coords']
        notifications_data = db.select_notifications_data(user_id)
        notifications_type = notifications_data['notifications_type']
        if notifications_type == 'text':
            await message.answer(get_weather(user_id=user_id, coords=city_coords, fcast_type=weather_type, notifications_type=notifications_type))
        elif notifications_type == 'image':
            await message.answer_photo(photo=types.InputFile(get_weather(user_id=user_id, coords=city_coords, fcast_type=weather_type, notifications_type=notifications_type)))


async def current_weather(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    user_settings = db.select_user_settings(user_id)
    weather_type = 'current'
    if not user_settings:
        await change_city(message=message, state=state)
    else:
        city_coords = user_settings['coords']
        notifications_data = db.select_notifications_data(user_id)
        notifications_type = notifications_data['notifications_type']
        if notifications_type == 'text':
            await message.answer(get_weather(user_id=user_id, coords=city_coords, fcast_type=weather_type, notifications_type=notifications_type))
        elif notifications_type == 'image':
            await message.answer_photo(photo=types.InputFile(get_weather(user_id=user_id, coords=city_coords, fcast_type=weather_type, notifications_type=notifications_type)))


def register_handlers_weather(dp: Dispatcher):
    dp.register_message_handler(current_weather, Text(endswith="Текущая погода"), state='*')
    dp.register_message_handler(today_weather, Text(endswith="Прогноз на сегодня"), state='*')
    dp.register_message_handler(tomorrow_weather, Text(endswith="Прогноз на завтра"), state='*')
    dp.register_message_handler(weekly_weather, Text(endswith="Прогноз на 7 дней"), state='*')