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
from app.database.database import delete_feedback, select_feedbacks
import app.handlers.feedback as feedback

from app.handlers.subscriptions import register_handlers_subs
from app.handlers.current_weather import register_handlers_city
from app.handlers.information import register_handlers_info
from app.scheduler.user_actions import scheduler_on_startup


logging.basicConfig(level=logging.INFO)


# Стартовая настрока бота
admin_id = getenv("ADMIN_ID")
bot_token = getenv("BOT_TOKEN")
if not bot_token:
    exit('Ошибка: токен не найден')
bot = Bot(token=bot_token, parse_mode=types.ParseMode.HTML)
dp = Dispatcher(bot, storage=MemoryStorage())


async def on_startup(dp):
    bot_commands = [
        types.BotCommand("city", "Проверить погоду"),
        types.BotCommand("subs", "Список отслеживаемых"),
        types.BotCommand("main", "Главное меню")
    ]
    await bot.set_my_commands(bot_commands)

@dp.message_handler(commands='cancel', state='*')
@dp.message_handler(Text(equals='отмена', ignore_case=True), state='*')
async def cmd_cancel(message: types.Message, state: FSMContext):
    await state.finish()
    await message.answer("Действие отменено", reply_markup=types.ReplyKeyboardRemove())


@dp.message_handler(commands='main', state='*')
async def cmd_main(message: types.Message, state: FSMContext):
    await state.finish()
    await message.answer(
        "<b>Главное меню.</b>\n\nВыберите действие:", 
        reply_markup=get_keyboard(["Проверить погоду", "Список отслеживаемых", "Информация"]))


class AnswerToFeedback(StatesGroup):
    waiting_action = State()
    waiting_answer = State()

fb = CallbackData("fb_answer", "action", "fb_id")
feedback_data = {}


@dp.message_handler(IDFilter(user_id=admin_id), commands="feedbacks", state='*')
async def check_feedbacks(message: types.Message, state: FSMContext):
    await state.finish()
    await AnswerToFeedback.waiting_action.set()
    feedbacks, fb_count = select_feedbacks()
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
            types.InlineKeyboardButton(text="Ответить", callback_data=fb.new(action='answer', fb_id=fb_id)),
            types.InlineKeyboardButton(text="Удалить", callback_data=fb.new(action='delete', fb_id=fb_id))
        ]
        keyboard = types.InlineKeyboardMarkup(row_width=2)
        keyboard.add(*buttons)
        message_text = f"[FeedBack] <b><u>#{fb_id}</u> От: {username} ({user_id})</b>\n\n{fb_text}"
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
    message_text = f"[Answer] От: Admin\n\n<i>Re: {fb_text}</i>\n\nОтвет: {message.text}"
    delete_feedback(fb_id)
    await bot.send_message(chat_id=user_id, text=message_text)
    await message.answer("[BOT] Ответ отправлен. Выйти из фидбека -> /cancel")
    #await state.finish()


@dp.callback_query_handler(fb.filter(action="delete"), state="*")
async def delete_fb(call: types.CallbackQuery, state: FSMContext, callback_data: dict):
    fb_id = callback_data['fb_id']
    delete_feedback(fb_id)
    #await state.finish()
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


if __name__ == '__main__':
    scheduler_on_startup(bot)
    register_handlers_city(dp)
    register_handlers_subs(dp)
    register_handlers_info(dp)
    feedback.register_handlers_feedback(dp)
    executor.start_polling(
        dispatcher=dp,
        skip_updates=True,
        on_startup=on_startup
    )