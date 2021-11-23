from aiogram import types, Dispatcher
from aiogram.dispatcher.filters import Text


async def cmd_information(message: types.Message):
    message_text = "О сервисе\n\n" \
        "WeatherRadar – это телеграм-бот, с помощью которого вы можете:\n" \
        "- проверить погоду в любом городе;\n" \
        "- создать список городов для отслеживания погоды в определенное время.\n\n" \
        "Команды бота:\n" \
        "<b>/main</b> - выйти в главное меню;\n" \
        "<b>/city</b> - проверить погоду в населенном пункте;\n" \
        "<b>/subs</b> - открыть список отслеживаемых.\n\n" \
        "Для того, чтобы проверить погоду, введите команду <b>/city</b>, или выйдете в главное меню и нажмите <b>«Проверить погоду»</b>. " \
        "После этого введите название или адрес населенного пункта, например: <b>Москва</b> или <b>Москва, штат Огайо</b>.\n\n" \
        "На этапе проверки погоды вам будет предложено «подписаться» на ежедневные уведомления о погоде." \
        "В списке отслеживаемых <b>/subs</b> вы можете удалять города из списка, или редактировать время уведомлений для каждого города.\n" \
        "Максимальное количество подписок – 3.\n\n" \
        "Вы можете отменить действие, нажав на клавиатуре <b>«Отмена»</b>, или введя команду <b>/cancel</b>\n\n" \
        "Если у вас возникли сложности, или вы заметили неточности работы с сервисом, напишите нам об этом, используя команду <b>/fb [текст]</b>.\n" \
        "Например: <i>/fb Добавьте больше информации о погоде.</i>\n\n" \
        "Разработчик: <a href='https://t.me/Polkastolka'>Polkastolka</a>"
    await message.answer(message_text, reply_markup=types.ReplyKeyboardRemove())


def register_handlers_info(dp: Dispatcher):
    dp.register_message_handler(cmd_information, commands=['start', 'info'], state="*")
    dp.register_message_handler(cmd_information, Text(equals="Информация", ignore_case=True), state="*")
