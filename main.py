import telebot
from telebot import types
from telebot.types import ReplyKeyboardRemove
import sqlite3
import requests
from selenium import webdriver
from bs4 import BeautifulSoup
import time


# Класс для работы с геокодером Яндекса
class YandexGeocoder:
    def __init__(self, yandex_token):
        self.YANDEX_API_KEY = yandex_token

    def get_geocode(self, addr):
        URL = f"https://geocode-maps.yandex.ru/1.x/?apikey={self.YANDEX_API_KEY}&geocode={addr}&format=json&results=1&lang=ru_RU"
        result = requests.get(URL).json()
        try:
            return result['response']['GeoObjectCollection']['featureMember'][0]['GeoObject']['Point']['pos']
        except:
            return -1

    def form_href_to_yamap(self, long, wide):
        return f"http://maps.yandex.ru/?ll={long},{wide}&spn=0.067205,0.018782&z=15&l=map,stv&text={wide}%20{long}"


def get_search_url(metro_station, place):
    return f"https://yandex.ru/maps/?text={metro_station} {place}, Москва"


def get_place_rating_and_timework(url):
    driver = webdriver.Chrome()
    driver.get(url)
    time.sleep(2)
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    driver.quit()

    try:
        rating = soup.find('span', {'class': 'business-rating-badge-view__rating-text'}).text
    except AttributeError:
        rating = "Рейтинг не найден"

    try:
        timework = soup.find('div', {'class': 'business-working-status-view'}).text
    except AttributeError:
        timework = "Описание не найдено"

    return rating, timework


# Создание объекта бота
bot = telebot.TeleBot('')

# Создание объекта геокодера
geocoder = YandexGeocoder('')


# Функция для получения списка мест на указанной станции метро и указанного типа
def get_places(metro_station, place_type):
    # Установка соединения с бд
    conn = sqlite3.connect('places.db')
    cursor = conn.cursor()
    cursor.execute("SELECT place, description, address FROM places WHERE metro = ? AND type = ?",
                   (metro_station, place_type))
    places = cursor.fetchall()

    # Список для хранения мест с описанием и ссылкой на Яндекс карты
    places_with_links = []

    for place, description, address in places:
        # Формируем поисковый URL на Яндекс Картах
        search_url = get_search_url(metro_station, place)

        # Получаем рейтинг и краткое описание места
        rating, timework = get_place_rating_and_timework(search_url)

        # Формируем ссылку на Яндекс карты
        coordinates = geocoder.get_geocode(f"{address}, Москва")
        if coordinates != -1:
            map_link = geocoder.form_href_to_yamap(*coordinates.split())
            places_with_links.append((place, description, address, map_link, rating, timework))
        else:
            places_with_links.append((place, description, address, "Координаты не найдены", rating, timework))

    # Закрываем соединение с базой данных
    conn.close()

    return places_with_links


# Функция для получения списка типов мест
def get_place_types():
    conn = sqlite3.connect('places.db')
    cursor = conn.cursor()
    cursor.execute("SELECT type FROM places")
    types = cursor.fetchall()
    conn.close()
    return list({type[0] for type in types})


# Обработчик команды /start
@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id,
                     "Привет! Я помогу тебе найти интересные места в центре Москвы! Введи название станции метро:")


# Обработчик выбора типа места
@bot.message_handler(func=lambda message: message.text in get_place_types())
def send_places(message):
    # Получаем выбранную станцию метро
    place_type = message.text.strip()
    places = get_places(metro_station, place_type)

    # Отправляем пользователю список мест
    if places:
        response = f"{place_type} на станции метро {metro_station}:\n\n"
        for place, description, address, map_link, rating, timework in places:
            response += f"📍 _{place}_\n{description}\n\n{address}\n\nРейтинг: {rating}\n\nЧасы работы: {timework}\n\nСсылка на Яндекс карты: {map_link}\n\n"
        bot.send_message(message.chat.id, response, parse_mode='Markdown', reply_markup=ReplyKeyboardRemove())
    else:
        bot.send_message(message.chat.id, "Извините, подходящих мест не найдено.")


# Обработчик отмены
@bot.message_handler(func=lambda message: message.text == 'Отмена')
def cancel(message):
    bot.send_message(message.chat.id, "Действие отменено.")
    bot.send_message(message.chat.id, "Введите название станции метро:")


# Обработчик текстового сообщения (станция метро)
@bot.message_handler(func=lambda message: True)
def get_place_type(message):
    global metro_station
    metro_station = message.text.strip().capitalize()
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(*[types.KeyboardButton(place_type) for place_type in get_place_types()])
    bot.send_message(message.chat.id, "Выбери тип места:", reply_markup=keyboard)


# Запуск бота
bot.polling()
