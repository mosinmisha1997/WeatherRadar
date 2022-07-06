from aiogram.dispatcher.filters import Text
from aiogram import types, Dispatcher
#from app.database.database import insert_feedback
import app.database.database as db


def get_inline_keyboard():
    buttons = [
        types.InlineKeyboardButton(text="\u2709 Отправить", callback_data="fb_send"),
        types.InlineKeyboardButton(text="\u274c Не отправлять", callback_data="fb_cancel")
    ]
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    keyboard.add(*buttons)
    return keyboard


feedback_text = {}


async def receiving_feedback(message: types.Message):
    fb_text = message.text.split("/fb ")[1]
    message_length = {'min':15, 'max':300}
    if len(fb_text) < message_length['min']:
        await message.answer(f"Сообщение не может быть меньше {message_length['min']} символов.")
        return
    elif len(fb_text) > message_length['max']:
        await message.answer(f"Сообщение не может быть больше {message_length['max']} символов.")
        return
    feedback_text.update(mes=f"Сообщение разработчикам: {fb_text}", fb_text=fb_text)
    await message.answer(feedback_text['mes'], reply_markup=get_inline_keyboard())


async def send_feedback(call: types.CallbackQuery):
    action = call.data.split('_')[1]
    mes = feedback_text['mes']
    fb_text = feedback_text['fb_text']
    save_feedback(call.from_user.id, call.from_user.username, fb_text, action)
    await call.message.edit_text(mes)
    await call.answer()
    if action == "cancel":
        return
    elif action == "send":
        await call.message.answer("Сообщение передано разработчикам.")
        

def save_feedback(user_id, username, fb_text, action):
    db.insert_feedback(user_id, username, fb_text, action)


def register_handlers_feedback(dp: Dispatcher):
    dp.register_message_handler(receiving_feedback, Text(startswith="/fb "), state="*")
    dp.register_callback_query_handler(send_feedback, Text(startswith="fb_"), state="*")