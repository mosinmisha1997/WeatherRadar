from contextlib import suppress

from aiogram import types
from aiogram.dispatcher.dispatcher import Dispatcher
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.dispatcher.storage import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.types import user
from aiogram.utils.callback_data import CallbackData
from aiogram.utils.exceptions import MessageNotModified

from app.database.database import delete_subscription_city, select_city_address, select_city_number, select_follow_cities, select_city_coords, select_notification_time, update_notification_time
from app.handlers.weather import get_weather
from app.scheduler.user_actions import scheduler_notifications_start, scheduler_notifications_stop


def get_keyboard(buttons_text = None):
    buttons = []
    if buttons_text:
        for text in buttons_text:
            buttons.append(types.KeyboardButton(text))
    buttons.append(types.KeyboardButton('Отмена'))
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    keyboard.add(*buttons)
    return keyboard


class ListOfSubscriptions(StatesGroup):
    waiting_action = State()
    waiting_city = State()


async def cmd_subs(message: types.Message, state: FSMContext):
    
    await state.finish()
    await ListOfSubscriptions.waiting_action.set()
    
    await message.answer("Список отслеживаемых населенных пунктов.", reply_markup=get_keyboard(['Открыть список', 'Редактировать']))


async def open_list_of_subs(message: types.Message, state: FSMContext):
    await ListOfSubscriptions.waiting_city.set()
    cities = select_follow_cities(message.from_user.id)
    if len(cities) == 0:
        await message.answer("Список отслеживаемых пуст.\n<i>Добавьте город в список командой <b>/city</b></i>", reply_markup=types.ReplyKeyboardRemove())
        return
    await message.answer("Где хотите проверить погоду?", reply_markup=get_keyboard(cities))


async def show_weather(message: types.Message, state: FSMContext):
    city_address = message.text
    user_id = message.from_user.id
    coords = select_city_coords(user_id, city_address)
    weather = get_weather(coords)
    notification_time = select_notification_time(user_id, city_address)
    await state.finish()
    await message.answer(weather, reply_markup=types.ReplyKeyboardRemove())
    if not notification_time:
        await message.answer("<i>Настройте уведомления для проверки погоды по расписанию\n<b>/subs -> Редактировать.</b></i>")


user_data = {}
cb = CallbackData("edit_list", "city_number", "action")


async def edit_list_of_subs(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    follow_cities = select_follow_cities(user_id)
    
    for i in range(0, len(follow_cities)):
        city_number = select_city_number(user_id, follow_cities[i])
        notification_time = select_notification_time(user_id=user_id, city_number=city_number)
        buttons = [
            types.InlineKeyboardButton(text="Редактировать", callback_data=cb.new(city_number=city_number, action="edit")),
            types.InlineKeyboardButton(text="Удалить", callback_data=cb.new(city_number=city_number, action="delete"))
            ]
        keyboard = types.InlineKeyboardMarkup(row_width=1)
        keyboard.add(*buttons)
        await message.answer(text=f"{i+1}. {follow_cities[i]}\nВремя уведомления: {notification_time}:00 (МСК).", reply_markup=keyboard)


def get_inline_keyboard():
    buttons = [
        types.InlineKeyboardButton(text="+1", callback_data="time_incr"),
        types.InlineKeyboardButton(text="-1", callback_data="time_decr"),
        types.InlineKeyboardButton(text="Подтвердить", callback_data="time_accept")
    ]
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    keyboard.add(*buttons)
    return keyboard


async def edit_subscriptions(call: types.CallbackQuery, callback_data: dict):
    user_id = call.from_user.id
    city_number = callback_data['city_number']
    city_address = select_city_address(user_id, city_number)
    notification_time = select_notification_time(user_id=user_id, city_number=city_number)
    user_data.update(notification_time=notification_time, city_address=city_address, user_id=user_id, city_number=city_number)
    
    message_text = f"{city_address}\nВремя уведомления: {notification_time}:00 (МСК)."
    await call.message.delete()
    await call.message.answer(message_text, reply_markup=get_inline_keyboard())
    await call.answer()


async def edit_notification_time_message(message: types.Message, new_value: int):
    city_address = user_data['city_address']
    with suppress(MessageNotModified):
        await message.edit_text(f"{city_address}\nВремя уведомления: {new_value}:00 (МСК).", reply_markup=get_inline_keyboard())


async def notifications_time_change(call: types.CallbackQuery):
    user_id = user_data['user_id']
    city_number = user_data['city_number']
    city_address = user_data['city_address']
    notification_time = user_data['notification_time']
    action = call.data.split('_')[1]
    if action == "incr":
        if notification_time == 23:
            notification_time = -1
        user_data.update(notification_time=notification_time + 1)
        await edit_notification_time_message(call.message, notification_time + 1)
    elif action == "decr":
        if notification_time == 0:
            notification_time = 24
        user_data.update(notification_time=notification_time - 1)
        await edit_notification_time_message(call.message, notification_time - 1)
    elif action == "accept":
        update_notification_time(user_id, city_number, notification_time)
        city_coords = select_city_coords(user_id, city_address)
        scheduler_notifications_start(message=call.message, user_id=call.from_user.id, city_coords=city_coords, notifications_time=notification_time, city_number=city_number)
        await call.message.delete()
        await call.message.answer(f"Для {city_address} установлено новое время уведомления:\n{notification_time}:00 (МСК).")
    await call.answer()


async def delete_subscriptions(call: types.CallbackQuery, callback_data: dict, state: FSMContext):
    city_number = callback_data['city_number']
    user_id = call.from_user.id
    city_address = select_city_address(user_id, city_number)
    delete_subscription_city(user_id, city_number)
    scheduler_notifications_stop(user_id, city_number)
    await call.message.delete()
    await call.message.answer(f"{city_address} удален из отслеживаемых.")
    await call.answer()


def register_handlers_subs(dp: Dispatcher):
    dp.register_message_handler(cmd_subs, commands="subs", state="*")
    dp.register_message_handler(cmd_subs, Text(equals="Список отслеживаемых", ignore_case=True), state="*")
    dp.register_message_handler(edit_list_of_subs, Text(equals="Редактировать"), state=ListOfSubscriptions.waiting_action)
    dp.register_callback_query_handler(edit_subscriptions, cb.filter(action="edit"), state="*")
    dp.register_callback_query_handler(notifications_time_change, Text(startswith="time_"), state='*')
    dp.register_callback_query_handler(delete_subscriptions, cb.filter(action="delete"), state="*")
    dp.register_message_handler(open_list_of_subs, Text(equals="Открыть список"), state=ListOfSubscriptions.waiting_action)
    dp.register_message_handler(show_weather, state=ListOfSubscriptions.waiting_city)