import requests

class Geocoder:
    def __init__(self, yandex_token):
        self.YANDEX_API_KEY = ''

    def get_geocode(self, addr):
        """Метод для получения широты и долготы по введенному адресу с помощью API Яндекс-карт"""
        URL = f"https://geocode-maps.yandex.ru/1.x/?apikey={self.YANDEX_API_KEY}&geocode={addr}&format=json&results=1&lang=ru_RU"
        result = requests.get(URL).json()
        try:
            return result['response']['GeoObjectCollection']['featureMember'][0]['GeoObject']['Point']['pos']
        except:
            return -1

    def form_href_to_yamap(self, long, wide):
        """Формируем ссылку на карты для перехода"""
        return f"http://maps.yandex.ru/?ll={long},{wide}&spn=0.067205,0.018782&z=15&l=map,stv&text={wide}%20{long}"
