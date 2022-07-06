import logging

from os import getenv
from sys import exit

from aiogram import Bot, Dispatcher, types, executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.builtin import IDFilter
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.types import user
from aiogram.utils.callback_data import CallbackData
import app.database.database as db
import app.handlers.check_weather as check_weather
import app.handlers.common as common
import app.handlers.feedback as feedback
import app.handlers.settings as settings
import app.scheduler.notifications as notifications


logging.basicConfig(level=logging.INFO)


# Стартовая настрока бота
#admin_id = getenv("ADMIN_ID")
#bot_token = getenv("BOT_TOKEN")
admin_id = '759409190'
bot_token = '2103585022:AAGEisLJRANxLiB0E_Q8Ml5ar_fZKD5M9Xo'
if not bot_token:
    exit('Ошибка: токен не найден')
bot = Bot(token=bot_token, parse_mode=types.ParseMode.HTML)
dp = Dispatcher(bot, storage=MemoryStorage())


async def on_startup(dp):
    bot_commands = [
        types.BotCommand("start", "Проверить погоду")
    ]
    await bot.set_my_commands(bot_commands)


@dp.message_handler(commands='main', state='*')
async def cmd_main(message: types.Message, state: FSMContext):
    await state.finish()
    await message.answer(
        "<b>Главное меню.</b>\n\nВыберите действие:", 
        reply_markup=common.get_keyboard(["\u26c5 Проверить погоду", "\u2b50 Список отслеживаемых", "\u2139 Информация"]))


class AnswerToFeedback(StatesGroup):
    waiting_action = State()
    waiting_answer = State()

fb = CallbackData("fb_answer", "action", "fb_id")
feedback_data = {}


@dp.message_handler(IDFilter(user_id=admin_id), commands="feedbacks", state='*')
async def check_feedbacks(message: types.Message, state: FSMContext):
    await state.finish()
    await AnswerToFeedback.waiting_action.set()
    feedbacks, fb_count = db.select_feedbacks()
    if len(feedbacks) == 0:
        await message.answer("Обращений не поступало.", reply_markup=types.ReplyKeyboardRemove())
        await state.finish()
        return
    await message.answer(f"Показано [{len(feedbacks)}/{fb_count}] обращений.")
    for fback in feedbacks:
        fb_id = fback[0]
        fb_text = fback[3]
        user_id = fback[1]
        username = fback[2]
        buttons = [
            types.InlineKeyboardButton(text="\u2705 Ответить", callback_data=fb.new(action='answer', fb_id=fb_id)),
            types.InlineKeyboardButton(text="\u274e Удалить", callback_data=fb.new(action='delete', fb_id=fb_id))
        ]
        keyboard = types.InlineKeyboardMarkup(row_width=2)
        keyboard.add(*buttons)
        message_text = f"<b>[FeedBack]</b> <b><u>#{fb_id}</u> От: {username} ({user_id})</b>\n\n{fb_text}"
        feedback_data.update({fb_id:{'fb_id':fb_id, 'message':message_text}})
        await state.update_data({fb_id:{'fb_id':fb_id, 'message':message_text, 'fb_text':fb_text, 'user_id':user_id, 'username':username}})
        await message.answer(text=message_text, reply_markup=keyboard)


@dp.callback_query_handler(fb.filter(action="answer"), state="*")
async def prepare_answer_to_user(call: types.CallbackQuery, callback_data: dict, state: FSMContext):
    await AnswerToFeedback.waiting_answer.set()
    data = await state.get_data()
    fb_id = int(callback_data['fb_id'])
    feedback_data.update(fb_id=fb_id)
    mes = data[fb_id]['message']
    await call.message.edit_text(mes)
    await call.message.answer("Наберите и отправьте ответ пользователю.")
    await call.answer()


@dp.message_handler(state=AnswerToFeedback.waiting_answer)
async def send_answer_to_user(message: types.Message, state: FSMContext):
    data = await state.get_data()
    fb_id = feedback_data['fb_id']
    user_id = data[fb_id]['user_id']
    fb_text = data[fb_id]['fb_text']
    message_text = f"<b>[Answer]</b> От: Admin\n\n<i>Re: {fb_text}</i>\n\nОтвет: {message.text}"
    db.delete_feedback(fb_id)
    await bot.send_message(chat_id=user_id, text=message_text)
    await message.answer("<b>[BOT]</b> Ответ отправлен. Выйти из фидбека -> /cancel")


@dp.callback_query_handler(fb.filter(action="delete"), state="*")
async def delete_fb(call: types.CallbackQuery, state: FSMContext, callback_data: dict):
    fb_id = callback_data['fb_id']
    db.delete_feedback(fb_id)
    await call.message.delete()
    await call.answer()


def get_bot():
    return bot


if __name__ == '__main__':
    notifications.scheduler_on_startup()
    common.register_handlers_common(dp)
    check_weather.register_handlers_weather(dp)
    settings.register_handlers_settings(dp)
    feedback.register_handlers_feedback(dp)
    executor.start_polling(
        dispatcher=dp,
        skip_updates=True,
        on_startup=on_startup
    )