from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.utils.callback_data import CallbackData

from app.handlers.weather import get_address, get_coords, get_weather
from app.database.database import insert_follow_city, select_count_following_cities, select_follow_cities
from app.scheduler.user_actions import scheduler_notifications_start


class RequestCurrentWeather(StatesGroup):
    waiting_city = State()
    waiting_confirm = State()


cb_weather = CallbackData("weather", "action")
cb_follow = CallbackData("follow", "action")


async def cmd_city(message: types.Message, state: FSMContext):
    await state.finish()
    await RequestCurrentWeather.waiting_city.set()
    await message.answer("Введите адрес населенного пункта, или его название.", reply_markup=get_keyboard())


weather_data = {}


async def waiting_city(message: types.Message, state: FSMContext):   
    addr = message.text
    address = get_address(addr)
    if not address:
        await message.answer(f"Не удалось найти {addr}. Попробуйте дополнить адрес названием края/области и района.")
        return

    available_addresses = select_follow_cities(message.from_user.id)
    if address in available_addresses:
        await state.finish()
        await message.answer(get_weather(get_coords(address)), reply_markup=types.ReplyKeyboardRemove())
        return

    buttons = [
            types.InlineKeyboardButton(text="Да", callback_data=cb_weather.new(action='yes')),
            types.InlineKeyboardButton(text="Нет", callback_data=cb_weather.new(action='no'))
        ]
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    keyboard.add(*buttons)

    weather_data.update(address=address)
    await message.answer(text="Возможно, вы имели ввиду:\n" + address, reply_markup=keyboard)


async def show_current_weather(call: types.CallbackQuery, state: FSMContext):    
    await state.finish()
    
    address = weather_data['address']
    coords = get_coords(address)
    weather = get_weather(coords)
    weather_data.update(weather=weather, coords=coords)

    available_addresses = select_follow_cities(call.from_user.id)
    message_text = f"{weather}"
    await call.message.delete()
    await call.message.answer(message_text, reply_markup=types.ReplyKeyboardRemove())

    keyboard = None
    if address not in available_addresses:
        message_text = f"Добавить в отслеживаемое?"
        buttons = [
            types.InlineKeyboardButton(text="Да", callback_data=cb_follow.new(action='yes')),
            types.InlineKeyboardButton(text="Нет", callback_data=cb_follow.new(action='no'))
        ]
        keyboard = types.InlineKeyboardMarkup(row_width=2)
        keyboard.add(*buttons)
        await call.message.answer(message_text, reply_markup=keyboard)
    await call.answer()


async def cancel_weather(call: types.CallbackQuery, state: FSMContext):
    address = weather_data['address']
    await call.message.answer("Попробуйте дополнить адрес названием края/области и/или района.")
    await call.message.edit_text(address)
    await call.answer()


async def add_city_follow(call: types.CallbackQuery):
    await call.message.delete()
    await call.answer()

    city_count = select_count_following_cities(call.from_user.id)
    if city_count >= 3:
        await call.message.answer("Действие отменено. Превышен лимит подписок (3)")
        return
    
    address = weather_data['address']
    coords = ';'.join(weather_data['coords'].values())
    city_number = insert_follow_city(call.from_user.id, call.from_user.username, address, coords)
    scheduler_notifications_start(
        message=call.message, user_id=call.from_user.id, city_coords=weather_data['coords'], notifications_time=12, city_number=city_number)
    await call.message.answer(f"{address} добавлен в отслеживаемое.\nВремя уведомления <b>12:00 (МСК)</b>.\n\nИзменить - <b>/subs</b> -> <b>«Редактировать»</b>.")
    


async def cancel_follow(call: types.CallbackQuery):
    await call.message.delete()
    await call.answer()


def get_keyboard(buttons_text = None):
    buttons = []
    if buttons_text:
        for text in buttons_text:
            buttons.append(types.KeyboardButton(text))
    buttons.append(types.KeyboardButton('Отмена'))
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    keyboard.add(*buttons)
    return keyboard


def register_handlers_city(dp: Dispatcher):
    dp.register_message_handler(cmd_city, Text(equals="Проверить погоду", ignore_case=True), state='*')
    dp.register_message_handler(cmd_city, commands='city', state='*')
    dp.register_message_handler(waiting_city, state=RequestCurrentWeather.waiting_city)
    dp.register_callback_query_handler(show_current_weather, cb_weather.filter(action='yes'), state='*')
    dp.register_callback_query_handler(cancel_weather, cb_weather.filter(action='no'), state='*')
    dp.register_callback_query_handler(add_city_follow, cb_follow.filter(action='yes'), state='*')
    dp.register_callback_query_handler(cancel_follow, cb_follow.filter(action='no'), state='*')
