from enum import Enum
from aiogram import types, Bot
from aiogram.types import user
from apscheduler.schedulers.asyncio import AsyncIOScheduler
#from app.database.database import select_notifications_data, select_notifications_data_all, select_notifications_time, select_user_settings
import app.database.database as db

from app.handlers.weather import get_weather
import bot

scheduler = AsyncIOScheduler(timezone="Europe/Moscow")
scheduler.start()


async def send_forecast(user_id, fcast_type, bot:Bot=None):
    user_settings = db.select_user_settings(user_id)
    city_coords = user_settings['coords']

    notifications_data = db.select_notifications_data(user_id=user_id)
    notifications_type = notifications_data['notifications_type']
    if notifications_type == 'text':
        forecast_text = get_weather(user_id=user_id, coords=city_coords, fcast_type=fcast_type)
        await bot.send_message(chat_id=user_id, text=forecast_text)
    elif notifications_type == 'image':
        forecast_image = types.InputFile(get_weather(user_id=user_id, coords=city_coords, fcast_type=fcast_type, notifications_type=notifications_type))
        await bot.send_photo(chat_id=user_id, photo=forecast_image)

def update_notifications_scheduler(user_id, fcast_type, hour, minute):
    job_id = f"{user_id}/{hour}{minute}/{fcast_type}"
    jobs = scheduler.get_jobs()
    
    jobs_ids = []
    for i in range(0, len(jobs)):
        jobs_ids.append(jobs[i].id)
    if len(jobs_ids) > 0:
        if job_id in jobs_ids:
            scheduler.remove_job(job_id=job_id)
        else:
            create_job(user_id, fcast_type, hour, minute, bot=bot.get_bot())
    else:
        create_job(user_id, fcast_type, hour, minute, bot=bot.get_bot())


def update_scheduler_status(user_id):
    notifications_data = db.select_notifications_data(user_id=user_id)
    if not notifications_data:
        print("Планировщику нечего запускать")
        return
    
    fcast_types = ['current', 'today', 'tomorrow', 'week']
    notifications_status = notifications_data['notifications_status']
    if notifications_status == 'disabled':
        jobs = scheduler.get_jobs()
        jobs_ids = []
        for i in range(0, len(jobs)):
            job_id = jobs[i].id.split("/")[0]
            if int(job_id) == user_id:
                scheduler.remove_job(job_id=jobs[i].id)
                
    else:
        for fcast_type in fcast_types:
            notifications_time = db.select_notifications_time(user_id=user_id, fcast_type=fcast_type)
            if not notifications_time['user_id']:
                continue
            time_list = notifications_time['notifications_time'].split(';')
            for time in time_list:
                hour = int(time.split(':')[0])
                minute = int(time.split(':')[1])
                create_job(user_id=user_id, fcast_type=fcast_type, hour=hour, minute=minute, bot=bot.get_bot())


def scheduler_on_startup():
    notifications_data = db.select_notifications_data_all()
    if not notifications_data:
        print("Планировщику нечего запускать")
        return
    
    fcast_types = ['current', 'today', 'tomorrow', 'week']
    for i in range(0, len(notifications_data)):
        user_id = notifications_data[i]['user_id']
        notifications_status = notifications_data[i]['notifications_status']
        if notifications_status == 'disabled':
            continue

        for fcast_type in fcast_types:
            notifications_time = db.select_notifications_time(user_id=user_id, fcast_type=fcast_type)
            if not notifications_time['user_id']:
                continue
            time_list = notifications_time['notifications_time'].split(';')
            for time in time_list:
                hour = int(time.split(':')[0])
                minute = int(time.split(':')[1])
                create_job(user_id=user_id, fcast_type=fcast_type, hour=hour, minute=minute, bot=bot.get_bot())


def create_job(user_id, fcast_type, hour, minute, bot):
    job_id = f"{user_id}/{hour}{minute}/{fcast_type}"
    scheduler.add_job(send_forecast, 'cron', [user_id, fcast_type, bot], hour=hour, minute=minute, id=job_id)


# def new_scheduler_notification(user_id, fcast_type, notification_time, bot=None, message=None):
#     shed_id = f"{user_id};{fcast_type};{notification_time}"
#     jobs = scheduler.get_jobs()
#     jobs_ids = []
#     for i in range(0, len(jobs)):
#         jobs_ids.append(jobs[i].id)
#     if len(jobs_ids) > 0:
#         if shed_id in jobs_ids:
#             scheduler.remove_job(job_id=shed_id)

#     notifications_data = select_notifications_data(user_id=user_id)
#     city_coords = notifications_data['city_coords']
#     hours = notification_time['hours']
#     minutes = notification_time['minutes']
#     scheduler.add_job(notifications, 'cron', [user_id, city_coords, bot, message], hour=hours, minute=minutes, id=shed_id)


# def scheduler_notifications_stop(user_id, fcast_type, notification_time):
#     shed_id = f"{user_id};{fcast_type};{notification_time}"
#     jobs = scheduler.get_jobs()
#     jobs_ids = []
#     for i in range(0, len(jobs)):
#         jobs_ids.append(jobs[i].id)
#     if shed_id not in jobs_ids:
#         return
#     scheduler.remove_job(job_id=shed_id)


#def scheduler_on_startup(bot: Bot):
    # notifications_data = select_notifications_data(user_id)
    # notifications_status = notifications_data['notifications_status']
    # #
    # if notifications_status == "disabled":
    #     return
    
    # fcast_types = [
    #     "current", 
    #     "today", 
    #     "tomorrow", 
    #     "week"
    #     ]
    
    # for fcast_type in fcast_types:
    #     notification_time = select_notifications_time(user_id=user_id, fcast_type=fcast_type)
    #     if notification_time:
    #         for ntime in notification_time:
    #             shed_id = f"{user_id};{fcast_type};{ntime}"  
    
    #pass
    # users_id = select_users_id()
    # for id in users_id:
    #     follow_data = select_cities_coords(id)
    #     for i in range(0, len(follow_data)):
    #         scheduler_notifications_start(
    #             bot=bot, user_id=id, city_coords=follow_data[i][0], notifications_time=follow_data[i][1], city_number=follow_data[i][2])
    # print("Планировщик запущен")
