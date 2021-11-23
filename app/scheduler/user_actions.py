from aiogram import types, Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.database.database import select_cities_coords, select_users_id

from app.handlers.weather import get_weather

scheduler = AsyncIOScheduler(timezone="Europe/Moscow")
scheduler.start()


async def notifications(user_id, city_coords, bot=None, message=None):
    weather = get_weather(city_coords)
    if bot:
        await bot.send_message(chat_id=user_id, text=weather)
    elif message:
        await message.answer(text=weather)


def scheduler_notifications_start(user_id, city_coords, notifications_time, city_number, bot=None, message=None):
    shed_id = f"{user_id},{city_number}"
    jobs = scheduler.get_jobs()
    if len(jobs) > 0:
        jobs = scheduler.get_jobs()[0]
        if shed_id in jobs.id:
            scheduler.remove_job(job_id=shed_id)
    scheduler.add_job(notifications, 'cron', [user_id, city_coords, bot, message], hour=notifications_time, minute=0, id=shed_id)


def scheduler_notifications_stop(user_id, city_number):
    shed_id = f"{user_id},{city_number}"
    if shed_id not in scheduler.get_jobs():
        return
    scheduler.remove_job(job_id=shed_id)


def scheduler_on_startup(bot: Bot):
    users_id = select_users_id()
    for id in users_id:
        follow_data = select_cities_coords(id)
        for i in range(0, len(follow_data)):
            scheduler_notifications_start(
                bot=bot, user_id=id, city_coords=follow_data[i][0], notifications_time=follow_data[i][1], city_number=follow_data[i][2])
    print("Планировщик запущен")
