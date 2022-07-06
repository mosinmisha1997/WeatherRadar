from os import fsdecode
from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters import state
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.types import user
from aiogram.types.message import ContentTypes
from aiogram.utils.exceptions import MessageNotModified

from contextlib import suppress
from enum import Enum
import app.database.database as db

from app.handlers.common import cmd_start, get_keyboard, get_main_keyboard
from app.handlers.weather import get_address, get_cities_data
import app.scheduler.notifications as notifications


class Settings(StatesGroup):
    waiting_action = State()


class ChangeCity(StatesGroup):
    waiting_city_name = State()
    waiting_full_address = State()


def get_settings_keyboard():
    buttons = [
        types.KeyboardButton(text="🌇 Изменить город"),
        types.KeyboardButton(text="🔔 Уведомления"),
        types.KeyboardButton(text="📐 Единицы измерения"),
        types.KeyboardButton(text="📋 Вид прогноза"),
        types.KeyboardButton(text="🔙 Назад")
    ]
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(buttons[0])
    keyboard.add(buttons[1], buttons[2], buttons[3])
    keyboard.add(buttons[-1])
    return keyboard


async def cmd_settings(message: types.Message, state: FSMContext):
    await state.finish()
    await Settings.waiting_action.set()
    await message.answer("Настройки", reply_markup=get_settings_keyboard())


async def return_back(message: types.Message, state: FSMContext):
    state_name = await state.get_state()
    #if state_name == 'Settings:waiting_action' or state_name == 'NotificationsSettings:waiting_action':
    await cmd_start(message=message, state=state)

##############################
### START "Изменить город" ###
def get_change_city_keyboard():
    buttons = [
        types.KeyboardButton(text="📍 Отправить местоположение", request_location=True),
        types.KeyboardButton(text="\u274c Отмена")
    ]
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(buttons[0])
    keyboard.add(buttons[1])
    return keyboard


async def change_city(message: types.Message, state: FSMContext):
    await ChangeCity.waiting_city_name.set()
    await message.answer(
        "Напишите название населенного пункта, в котором хотите посмотреть погоду, или отправьте своё местоположение.", 
        reply_markup=get_change_city_keyboard()
        )


async def waiting_city_name(message: types.Message, state: FSMContext):
    if message.location:
        user_id = message.from_user.id
        coords = {
            'lat':message.location['latitude'], 
            'lon':message.location['longitude']
            }
        # не вносится в базу адрес если затуп API
        address = get_address(coords=coords)
        db.update_user_settings(user_id=user_id, address=address, coords=coords)
        await state.finish()
        await cmd_start(message=message, state=state)
        return

    cities_data = get_cities_data(city_name=message.text)
    if not cities_data:
        await message.answer(
            f"Не удалось найти локацию {message.text}. Попробуйте дополнить адрес названием края/области и/или района.", 
            reply_markup=get_keyboard())
        return
    addresses = list(cities_data.keys())
    await ChangeCity.waiting_full_address.set()
    await state.update_data(addresses=addresses, cities_data=cities_data)
    await message.answer(
        "Вот те населенные пункты, отвечающие вашему запросу:", 
        reply_markup=get_keyboard(buttons_text=addresses))


async def waiting_full_address(message: types.Message, state: FSMContext):
    state_data = await state.get_data()
    cities_data = state_data['cities_data']
    addresses = state_data['addresses']
    address = message.text
    if address not in addresses:
        await message.answer("Пожалуйста, используйте клавиатуру.")
        return

    coords = cities_data[message.text]
    address = get_address(coords=coords)
    user_id = message.from_user.id
    db.update_user_settings(user_id=user_id, address=address, coords=coords)
    await cmd_start(message=message, state=state)
### END "Изменить город" ###
############################

###########################
### START "Уведомления" ###
class NotificationsSettings(StatesGroup):
    waiting_action = State()


class NotificationStatus(Enum):
    disabled = "disabled"
    enabled = "enabled"


def get_notifications_menu(notifications_status=None, notifications_availability=None):
    """
    Возвращает меню настройки уведомлений в зависимости от состояния уведомлений\n
    notification_state - текущее состояние уведомлений (disabled - отключены, enabled - включены, Если ничего не передавать, значит они отсутствуют)
    """
    buttons = [
        types.InlineKeyboardButton(text="Текущая погода", callback_data="fcast_current"),
        types.InlineKeyboardButton(text="Прогноз на день", callback_data="fcast_today"),
        types.InlineKeyboardButton(text="Прогноз на завтра", callback_data="fcast_tomorrow"),
        types.InlineKeyboardButton(text="Прогноз на неделю", callback_data="fcast_week"),
        types.InlineKeyboardButton(text="Отключить уведомления", callback_data="notif_off"),
        types.InlineKeyboardButton(text="Включить уведомления", callback_data="notif_on"),
        types.InlineKeyboardButton(text="___", callback_data="nothing_"),
        types.InlineKeyboardButton(text="Удалить все уведомления", callback_data="notif_del")
    ]
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    keyboard.add(buttons[0], buttons[1])
    keyboard.add(buttons[2], buttons[3])
    if notifications_availability == 'found':
        if notifications_status == 'disabled':
            keyboard.add(buttons[5])
            keyboard.add(buttons[6])
            keyboard.add(buttons[7])
        elif notifications_status == 'enabled':
            keyboard.add(buttons[4])
    return keyboard


def get_minutes_keyboard(hour, minutes:list=[]):
    """
    Передавать час, для которого необходимо вывести минуты и минуты, на которые уже установлены уведомления

    Возвращает клавиатуру
    """
    keyboard = types.InlineKeyboardMarkup(row_width=3)
    minute = 0
    for i in range(0, 4):
        btns = []
        for j in range(0, 3):
            emoji = "⚪"
            if minute in minutes:
                emoji = "🔘"
            tminute = str(minute).zfill(2)
            thour = str(hour).zfill(2)
            btns.append(types.InlineKeyboardButton(text=f"{emoji} {thour}:{tminute}", callback_data=f"min_{minute}"))
            minute += 5
        keyboard.add(*btns)
    keyboard.add(types.InlineKeyboardButton(text="🔙Назад", callback_data="back_hours"))
    return keyboard


def get_hours_keyboard(hours:list=[]):
    """
    Передавать час, для которого необходимо вывести минуты и минуты, на которые уже установлены уведомления

    Возвращает клавиатуру
    """
    keyboard = types.InlineKeyboardMarkup(row_width=4)
    hour = 0
    for i in range(0, 6):
        btns = []
        for j in range(0, 4):
            emoji = "⚪"
            if hour in hours:
                emoji = "🔘"
            thour = str(hour).zfill(2)
            btns.append(types.InlineKeyboardButton(text=f"{emoji} {thour}:00", callback_data=f"hour_{hour}"))
            hour += 1
        keyboard.add(*btns)
    keyboard.add(types.InlineKeyboardButton(text="🔙Назад", callback_data="back_begin"))
    return keyboard


async def notifications_settings(message: types.Message, state: FSMContext):
    await NotificationsSettings.waiting_action.set()

    user_id = message.from_user.id
    notification_data = db.select_notifications_data(user_id)
    notifications_status = notification_data['notifications_status']
    notifications_availability = notification_data['notifications_availability']
    message_text = f"Настройка ежедневных уведомлений."
    await message.answer(message_text, reply_markup=get_notifications_menu(notifications_status, notifications_availability))        
    await state.update_data(notification_data=notification_data)


async def waiting_type_forecast(call: types.CallbackQuery, state: FSMContext):
    action = call.data.split('_')[1]
    user_id = call.from_user.id
    notifications_time = db.get_notifications_time(user_id=user_id, fcast_type=action)
    hours = []
    if notifications_time:
        hours = notifications_time.keys()
    await call.message.edit_text(
        text="Выберите время уведомления", 
        reply_markup=get_hours_keyboard(hours=hours)
        )

    await state.update_data(fcast_type=action, notifications_time=notifications_time)
    await call.answer()


async def edit_notifications(call: types.CallbackQuery, state: FSMContext):
    user_id = call.from_user.id
    action = call.data.split('_')[0]
    value = call.data.split('_')[1]
    state_data = await state.get_data()

    if action == 'hour':
        fcast_type = state_data['fcast_type']
        notifications_time = db.get_notifications_time(user_id=user_id, fcast_type=fcast_type)
        minutes = []
        if notifications_time:
            keys = notifications_time.keys()
            if int(value) in keys:
                minutes = notifications_time[int(value)]
        await state.update_data(hour=value)
        await call.message.edit_text(
            text="Выберите время уведомления", 
            reply_markup=get_minutes_keyboard(hour=value, minutes=minutes)
            )
    elif action == 'min':
        hour = state_data['hour'].zfill(2)
        minute = value.zfill(2)
        time = f"{hour}:{minute}"
        fcast_type = state_data['fcast_type']

        db.add_notifications_to_db(
            user_id=user_id, 
            time=time, 
            fcast_type=fcast_type)

        notifications_time = db.get_notifications_time(
            user_id=user_id, 
            fcast_type=fcast_type
            )

        notifications.update_notifications_scheduler(user_id=user_id, fcast_type=fcast_type, hour=int(hour), minute=int(minute))

        minutes = []
        if notifications_time and int(hour) in notifications_time:
            minutes = notifications_time[int(hour)]
        with suppress(MessageNotModified):
            await call.message.edit_text(
                text="Выберите время уведомления",
                reply_markup=get_minutes_keyboard(hour=hour, minutes=minutes)
                )
    elif action == 'notif':
        if value == 'on':
            db.update_notifications_data(user_id=user_id, notifications_status='enabled')
        elif value == 'off':
            db.update_notifications_data(user_id=user_id, notifications_status='disabled')
        elif value == 'del':
            db.drop_notifications(user_id=user_id)
        notifications.update_scheduler_status(user_id=user_id)
        notification_data = db.select_notifications_data(user_id)
        notifications_status = notification_data['notifications_status']
        notifications_availability = notification_data['notifications_availability']
        await call.message.edit_text(
            "Настройка ежедневных уведомлений",
            reply_markup=get_notifications_menu(notifications_status, notifications_availability)
            )
    elif action == 'back':
        if value == 'begin':
            notification_data = db.select_notifications_data(user_id)
            notifications_status = notification_data['notifications_status']
            notifications_availability = notification_data['notifications_availability']
            await call.message.edit_text(
                "Настройка ежедневных уведомлений", 
                reply_markup=get_notifications_menu(notifications_status, notifications_availability)
                )
        elif value == 'hours':
            fcast_type = state_data['fcast_type']
            notifications_time = db.get_notifications_time(user_id=user_id, fcast_type=fcast_type)
            hours = []
            if notifications_time:
                hours = notifications_time.keys()
            await call.message.edit_text(
                "Выберите время уведомления",
                reply_markup=get_hours_keyboard(hours)
            )
    await call.answer()

### END "Уведомления" ###
#########################


#################################
### START "Единицы измерения" ###

class UnitsSettings(StatesGroup):
    waiting_action = State()


def get_units_main_keyboard(name=None):
    buttons = [
        types.InlineKeyboardButton(text="⚪ Метрические", callback_data='units_metric'),
        types.InlineKeyboardButton(text="🔘 Метрические", callback_data='units_metric'),
        types.InlineKeyboardButton(text="⚪ Имперские", callback_data='units_imperial'),
        types.InlineKeyboardButton(text="🔘 Имперские", callback_data='units_imperial'),
        types.InlineKeyboardButton(text="⚪ Пользовательские", callback_data='units_custom'),
        types.InlineKeyboardButton(text="🔘 Пользовательские", callback_data='units_custom')
    ]
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    if name == 'metric':
        keyboard.add(buttons[1], buttons[2])
        keyboard.add(buttons[4])
    elif name == 'imperial':
        keyboard.add(buttons[0], buttons[3])
        keyboard.add(buttons[4])
    elif name == 'custom':
        keyboard.add(buttons[0], buttons[2])
        keyboard.add(buttons[5])
    return keyboard


def get_units_custom_keyboard(units_settings):
    buttons = [
        types.InlineKeyboardButton(text="Скорость ветра", callback_data='nothing_'),
        types.InlineKeyboardButton(text="⚪ м/с", callback_data='speed_metre'),
        types.InlineKeyboardButton(text="🔘 м/с", callback_data='speed_metre'),
        types.InlineKeyboardButton(text="⚪ миль/ч", callback_data='speed_mile'),
        types.InlineKeyboardButton(text="🔘 миль/ч", callback_data='speed_mile'),
        types.InlineKeyboardButton(text="Температура", callback_data='nothing_'),
        types.InlineKeyboardButton(text="⚪ °C", callback_data='temp_celsius'),
        types.InlineKeyboardButton(text="🔘 °C", callback_data='temp_celsius'), 
        types.InlineKeyboardButton(text="⚪ °F", callback_data='temp_fahrenheit'),
        types.InlineKeyboardButton(text="🔘 °F", callback_data='temp_fahrenheit'),
        types.InlineKeyboardButton(text="Давление", callback_data='nothing_'),
        types.InlineKeyboardButton(text="⚪ мм рт. ст.", callback_data='press_mm'),
        types.InlineKeyboardButton(text="🔘 мм рт. ст.", callback_data='press_mm'),
        types.InlineKeyboardButton(text="⚪ дюйм рт. ст.", callback_data='press_in'),
        types.InlineKeyboardButton(text="🔘 дюйм рт. ст.", callback_data='press_in'),
        types.InlineKeyboardButton(text="🔙Назад", callback_data="back_units")
    ]
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    keyboard.add(buttons[0])
    if units_settings['speed'] == 'м/с':
        keyboard.add(buttons[2], buttons[3])
    elif units_settings['speed'] == 'миль/ч':
        keyboard.add(buttons[1], buttons[4])
    keyboard.add(buttons[5])
    if units_settings['temperature'] == '°C':
        keyboard.add(buttons[7], buttons[8])
    elif units_settings['temperature'] == '°F':
        keyboard.add(buttons[6], buttons[9])
    keyboard.add(buttons[10])
    if units_settings['pressure'] == 'мм рт. ст.':
        keyboard.add(buttons[12], buttons[13])
    elif units_settings['pressure'] == 'дюйм рт. ст.':
        keyboard.add(buttons[11], buttons[14])
    keyboard.add(buttons[15])
    return keyboard


async def units_settings(message: types.Message, state: FSMContext):
    await UnitsSettings.waiting_action.set()
    user_id = message.from_user.id
    units_settings = db.select_units_settings(user_id=user_id)
    name = units_settings['name']
    await message.answer(text="Настройки единиц измерения", reply_markup=get_units_main_keyboard(name))


async def edit_units_settings(call: types.CallbackQuery, state: FSMContext):
    user_id = call.from_user.id
    action = call.data.split('_')[0]
    value = call.data.split('_')[1]

    units_settings = db.select_units_settings(user_id=user_id)

    if action == 'units':
        name = units_settings['name']
        if value == 'metric' and not name == 'metric':
            db.update_units_settings(user_id=user_id, name='metric')
            units_settings = db.select_units_settings(user_id=user_id)
            name = units_settings['name']
            await call.message.edit_text(text="Настройки единиц измерения", reply_markup=get_units_main_keyboard(name=name))
        elif value == 'imperial' and not name == 'imperial':
            db.update_units_settings(user_id=user_id, name='imperial')
            units_settings = db.select_units_settings(user_id=user_id)
            name = units_settings['name']
            await call.message.edit_text(text="Настройки единиц измерения", reply_markup=get_units_main_keyboard(name=name))
        elif value == 'custom':
            units_settings = db.select_units_settings(user_id=user_id)
            await call.message.edit_text(text="Настройки единиц измерения", reply_markup=get_units_custom_keyboard(units_settings=units_settings))
    elif action == 'speed':
        speed = units_settings['speed']
        if value == 'metre' and not speed == 'м/с':
            db.update_units_settings(user_id=user_id, speed='м/с')
            units_settings = db.select_units_settings(user_id=user_id)
            await call.message.edit_text(text="Настройки единиц измерения", reply_markup=get_units_custom_keyboard(units_settings=units_settings))
        elif value == 'mile' and not speed == 'миль/ч':
            db.update_units_settings(user_id=user_id, speed='миль/ч')
            units_settings = db.select_units_settings(user_id=user_id)
            await call.message.edit_text(text="Настройки единиц измерения", reply_markup=get_units_custom_keyboard(units_settings=units_settings))
    elif action == 'temp':
        temp = units_settings['temperature']
        if value == 'celsius' and not temp == '°C':
            db.update_units_settings(user_id=user_id, temperature='°C')
            units_settings = db.select_units_settings(user_id=user_id)
            await call.message.edit_text(text="Настройки единиц измерения", reply_markup=get_units_custom_keyboard(units_settings=units_settings))
        elif value == 'fahrenheit' and not temp == '°F':
            db.update_units_settings(user_id=user_id, temperature='°F')
            units_settings = db.select_units_settings(user_id=user_id)
            await call.message.edit_text(text="Настройки единиц измерения", reply_markup=get_units_custom_keyboard(units_settings=units_settings))
    elif action == 'press':
        press = units_settings['pressure']
        if value == 'mm' and not press == 'мм рт. ст.':
            db.update_units_settings(user_id=user_id, pressure='мм рт. ст.')
            units_settings = db.select_units_settings(user_id=user_id)
            await call.message.edit_text(text="Настройки единиц измерения", reply_markup=get_units_custom_keyboard(units_settings=units_settings))
        elif value == 'in' and not press == 'дюйм рт. ст.':
            db.update_units_settings(user_id=user_id, pressure='дюйм рт. ст.')
            units_settings = db.select_units_settings(user_id=user_id)
            await call.message.edit_text(text="Настройки единиц измерения", reply_markup=get_units_custom_keyboard(units_settings=units_settings))
    elif action == 'back':
        units_settings = db.select_units_settings(user_id=user_id)
        name = units_settings['name']
        await call.message.edit_text(text="Настройки единиц измерения", reply_markup=get_units_main_keyboard(name=name))
    await call.answer()

### END "Единицы измерения" ###
###############################


############################
### START "Вид прогноза" ###

class FcastType(StatesGroup):
    waiting_action = State()


def get_notifications_type_keyboard(fcast_type):
    buttons = [
        types.InlineKeyboardButton(text="⚪ Текст", callback_data="fcast_text"),
        types.InlineKeyboardButton(text="🔘 Текст", callback_data="fcast_text"),
        types.InlineKeyboardButton(text="⚪ Картинка", callback_data="fcast_image"),
        types.InlineKeyboardButton(text="🔘 Картинка", callback_data="fcast_image")
    ]
    keyboard = types.InlineKeyboardMarkup(row_width=2)

    if fcast_type == 'text':
        keyboard.add(buttons[1], buttons[2])
    elif fcast_type == 'image':
        keyboard.add(buttons[0], buttons[3])
    return keyboard


async def notifications_type(message: types.Message, state: FSMContext):
    await FcastType.waiting_action.set()
    
    user_id = message.from_user.id
    notifications_data = db.select_notifications_data(user_id=user_id)
    notifications_type = notifications_data['notifications_type']
    await message.answer("Изменить вид прогноза", reply_markup=get_notifications_type_keyboard(notifications_type))


async def edit_notifications_type(call: types.CallbackQuery, state: FSMContext):
    user_id = call.from_user.id
    action = call.data.split('_')[0]
    value = call.data.split('_')[1]

    if action == 'fcast':
        if value == 'text':
            db.update_notifications_data(user_id=user_id, notifications_type='text')
        elif value == 'image':
            db.update_notifications_data(user_id=user_id, notifications_type='image')
        notifications_data = db.select_notifications_data(user_id=user_id)
        notifications_type = notifications_data['notifications_type']
        await call.message.edit_text("Изменить вид прогноза", reply_markup=get_notifications_type_keyboard(notifications_type))
    await call.answer()


def register_handlers_settings(dp: Dispatcher):
    dp.register_message_handler(cmd_settings, Text(endswith="Настройки"), state='*')
    dp.register_message_handler(return_back, Text(endswith="Назад"), state=[Settings.waiting_action, NotificationsSettings.waiting_action, UnitsSettings.waiting_action, FcastType.waiting_action])
    dp.register_message_handler(change_city, Text(endswith="Изменить город"), state='*')
    dp.register_message_handler(waiting_city_name, content_types=ContentTypes.LOCATION, state=ChangeCity.waiting_city_name)
    dp.register_message_handler(waiting_city_name, state=ChangeCity.waiting_city_name)
    dp.register_message_handler(waiting_full_address, state=ChangeCity.waiting_full_address)
    dp.register_message_handler(notifications_settings, Text(endswith="Уведомления"), state='*')
    dp.register_callback_query_handler(waiting_type_forecast, Text(startswith="fcast_"), state=NotificationsSettings.waiting_action)
    dp.register_callback_query_handler(edit_notifications, Text(startswith=["hour_", "min_", "back_", "notif_", "nothing_"]), state=NotificationsSettings.waiting_action)
    dp.register_message_handler(units_settings, Text(endswith="Единицы измерения"), state='*')
    dp.register_callback_query_handler(edit_units_settings, Text(startswith=["units_", "speed_", "temp_", "press_", "back_", "nothing_"]), state=UnitsSettings.waiting_action)
    dp.register_message_handler(notifications_type, Text(endswith="Вид прогноза"), state='*')
    dp.register_callback_query_handler(edit_notifications_type, Text(startswith=["fcast_"]), state=FcastType.waiting_action)
