from aiogram import types
from aiogram import Dispatcher
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher import FSMContext

#from app.database.database import insert_users_data
import app.database.database as db


def get_keyboard(buttons_text = None, resize_keyboard = True):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=resize_keyboard)
    if buttons_text:
        for text in buttons_text:
            keyboard.add(types.KeyboardButton(text))
    keyboard.add(types.KeyboardButton('\u274c Отмена'))
    return keyboard


def get_main_keyboard():
    buttons = [
        types.KeyboardButton(text='⛅ Текущая погода'),
        types.KeyboardButton(text='🌂 Прогноз на сегодня'),
        types.KeyboardButton(text='☂ Прогноз на завтра'),
        types.KeyboardButton(text='☔ Прогноз на 7 дней'),
        types.KeyboardButton(text='⚙ Настройки')
    ]
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(buttons[0], buttons[1])
    keyboard.add(buttons[2], buttons[3])
    keyboard.add(buttons[-1])
    return keyboard


async def cmd_cancel(message: types.Message, state: FSMContext):
    await state.finish()
    await message.answer("Действие отменено", reply_markup=get_main_keyboard())


async def cmd_start(message: types.Message, state: FSMContext):
    await state.finish()
    user = message.from_user
    db.insert_users_data(user=user)
    keyboard = get_main_keyboard()
    await message.answer("Выберите действие:", reply_markup=keyboard)


def register_handlers_common(dp: Dispatcher):
    dp.register_message_handler(cmd_cancel, commands='cancel', state='*')
    dp.register_message_handler(cmd_cancel, Text(endswith='отмена', ignore_case=True), state='*')
    dp.register_message_handler(cmd_start, commands='start', state="*")
