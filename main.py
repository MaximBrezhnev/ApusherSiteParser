"""Модуль, через который осуществляется запуск парсера."""

import re
import csv
import os

from proxy import load_proxies
from utils import process_country


def main() -> None:
    """
    Основная функция парсера:
    * Получает через консоль от пользователя критерии поиска;
    * Создает на рабочем столе файл, в который будут записаны результаты;
    * Вызывает функцию поиска сайтов по полученным критериями для переданной страны.
    """

    start_position = 0
    num_iterations = 5

    # Получение критериев поиска
    country_input = input("Введите страну для поиска (с полным списком стран можно ознакомиться в txt файле): ")
    search_term = input("Введите запрос, который нужно найти: ")

    while True:
        try:
            num_selection = int(
                input("Укажите, сколько хотите сделать запросов (лучшие настройки по умолчанию), либо пропустите, "
                      "написав 0: ")
            )
            if num_selection != 0:
                num_iterations = num_selection
            break
        except ValueError:
            print("Введено некорректное значение для количества запросов. Попробуйте еще раз.")

    # Загрузка прокси для поиска
    proxy_file_path = input("Введите абсолютный путь к файлу, содержащему прокси, либо пропустите, написав 'нет': ")
    if proxy_file_path != "нет":
        load_proxies(proxy_file_path)

    # Создание на рабочем столе файла, в который будут записаны результаты
    safe_search_term = re.sub(r'[\\/*?:"<>|]', "_", search_term)
    home_dir = os.path.expanduser("~")
    desktop_dir = os.path.join(home_dir, "Desktop")
    file_path = os.path.join(desktop_dir, f"{safe_search_term}.csv")

    with open(file_path, mode="w", encoding="utf-8", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(
            [
                "Website",
                "Email",
                "Instagram",
                "Telegram",
                "Twitter",
                "Discord",
                "Facebook",
                "Reddit",
                "YouTube",
                "VK",
                "Country",
            ]
        )

    # Вызов функции поиска по запросу для необходимой страны
    process_country(country_input, search_term, start_position, num_iterations, file_path)


if __name__ == "__main__":
    main()
