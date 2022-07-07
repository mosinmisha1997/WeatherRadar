# WeatherRadar
## Телеграм-бот погодник

Бот написан на языке **Python** с применением библиотек **asyncio**, **geopy** для определения населенных пунктов, HTTP-запросов для получения сведений о погоде с сервиса OpenWeather, а также БД **SQLite** для хранения пользовательских настроек.

Для получения сведений о погоде пользователь должен указать населенный пункт.

![image](https://user-images.githubusercontent.com/63463786/177544837-2f3a1a80-d11e-4884-8fdc-dcabc2315603.png)

У пользователя имеется возможность проверки текущей погоды, погоды на сегодняшний или завтрашний день или на неделю. Вывод сведений о погоде может быть реализован в текстовом формате или картинкой.

![image](https://user-images.githubusercontent.com/63463786/177544980-9faf11b5-2c88-4e90-aa1a-7c7ff464307b.png)

Управление ботом производится посредством reply-кнопок.

![image](https://user-images.githubusercontent.com/63463786/177545240-5b9ec032-b128-4d33-a8c3-d6e34c51d8bd.png)

В настройках можно изменить единицы измерения для сведений о погоде. Управление реализовано inline-кнопками.

![image](https://user-images.githubusercontent.com/63463786/177545448-024bece0-147a-41d8-bc78-55d0ae2799ad.png)
