"""Модуль, содержащий основные утилиты парсера."""

import csv
import re
import time

import requests
from bs4 import BeautifulSoup
from seleniumwire import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

from constants import HEADERS, COUNTRY_CODES
from proxy import get_current_proxy, rotate_proxy


def get_html_with_selenium(url: str) -> str:
    """Возвращает html-код страницы, полученной по переданному url."""

    while True:
        options = webdriver.ChromeOptions()
        options.add_argument(f"user-agent={HEADERS['User-Agent']}")
        options.add_argument("--headless")

        current_proxy = get_current_proxy()
        print(f"Текущий прокси: {current_proxy}")

        seleniumwire_options = {}
        if current_proxy:
            seleniumwire_options = {
                "proxy": {
                    "http": current_proxy,
                    "https": current_proxy
                },
            }
            options.add_argument(f"--proxy-server={current_proxy}")

        driver_path = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(
            service=driver_path,
            seleniumwire_options=seleniumwire_options,
            options=options
        )
        driver.get(url)

        if "sorry/index" in driver.current_url:
            print("Не удалось получить доступ к ресурсу. Меняем прокси...")

            driver.quit()

            if current_proxy:
                rotate_proxy()

            time.sleep(5)
            continue

        time.sleep(8)
        page_source = driver.page_source
        driver.quit()
        return page_source


def get_site_data(url: str) -> tuple:
    """
    Возвращает адреса электронных почт, ссылки на соц. сети,
    информацию о наличии комментариев для переданного url.
    """

    emails = set()
    instagrams = set()
    telegrams = set()
    twitters = set()
    discords = set()
    facebooks = set()
    youtubes = set()
    reddits = set()
    vks = set()

    found_email = False
    found_instagram = False
    found_telegram = False
    found_discord = False
    found_facebook = False
    found_twitter = False
    found_reddit = False
    found_youtube = False
    found_vk = False
    found_comments = False

    current_proxy = get_current_proxy()
    if current_proxy:
        proxies = {"http": current_proxy, "https": current_proxy}
    else:
        proxies = {}

    try:
        result = requests.get(url, headers=HEADERS, proxies=proxies, timeout=60)
        result.raise_for_status()
        soup = BeautifulSoup(result.text, "lxml")

        # Поиск адреса электронной почты
        texts = soup.stripped_strings
        for mail in soup.find_all("a", href=True):
            href = mail.get("href")

            if href.startswith("/cdn-cgi/l/email-protection#"):
                decoded_email = href.replace("/cdn-cgi/l/email-protection#", "")
                key = int(decoded_email[:2], 16)
                hex_str = decoded_email[2:]
                email = ''
                for i in range(0, len(hex_str), 2):
                    email += chr(int(hex_str[i:i+2], 16) ^ key)
                email = re.sub(r"\?subject.*", "", email)
                email = re.sub(r"\?Subject.*", "", email)
                emails.add(email)
                found_email = True

            elif href.startswith("mailto:") and not href.startswith("malito:?"):
                default_email = href.replace("mailto:", '')
                emails.add(default_email)
                found_email = True

        email_pattern = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
        for text in texts:
            matches = email_pattern.findall(text)
            if matches:
                emails.update(matches)
                found_email = True

        # Поиск ссылок на социальные сети
        social_media_domains = {
            "instagram.com": (instagrams, "Инст не найден", found_instagram),
            "t.me": (telegrams, "Тг не найден", found_telegram),
            "twitter.com": (twitters, "Твиттер не найден", found_twitter),
            "discord.gg": (discords, "Дс не найден", found_discord),
            "facebook.com": (facebooks, "Фейсбук не найден", found_facebook),
            "reddit.com": (reddits, "Реддит не найден", found_reddit),
            "youtube.com": (youtubes, "Ютуб не найден", found_youtube),
            "vk.com": (vks, "Вк не найден", found_vk),
        }

        for link in soup.find_all("a", href=True):
            href = link.get("href")
            for domain, (collection, not_found_message, found_flag) in social_media_domains.items():
                if domain in href:
                    collection.add(href)
                    social_media_domains[domain] = (collection, not_found_message, True)
                    break

            # Отдельная проверка для Твиттера, т.к. соц. сеть поддерживает два домена
            if "/x.com" in href:
                twitters.add(href)
                social_media_domains["twitter.com"] = (twitters, "Твиттер не найден", True)
                break

        for domain, (collection, not_found_message, found_flag) in social_media_domains.items():
            if not found_flag:
                collection.add(not_found_message)
        if not found_email:
            emails.add("Почты на сайте не найдены")

        # Поиск секции комментариев на сайте
        comments_keywords = ["comment", "comments", "reply", "disqus", "review"]
        for keyword in comments_keywords:
            if soup.find_all(class_=re.compile(keyword, re.I)) or soup.find_all(id=re.compile(keyword, re.I)):
                found_comments = True
                break

    except requests.exceptions.RequestException as e:
        print(f"Error accessing {url}: {e}")
        return set(), set(), set(), set(), set(), set(), set(), set(), set(), False

    return emails, instagrams, telegrams, twitters, discords, facebooks, reddits, youtubes, vks, found_comments


def get_google_url(google: str) -> set[str]:
    """Возвращает все ссылки на сайты, полученные по переданному запросу."""

    links = set()
    try:
        html = get_html_with_selenium(google)
        soup = BeautifulSoup(html, "html.parser")
        request_links = soup.find_all("div", class_="GyAeWb")

        for div in request_links:
            for a_tag in div.find_all("a", href=True):
                href = a_tag.get("href")
                if not href.startswith("/search") and "google" not in href and not href.startswith("/preferences?") \
                        and not href.startswith("#"):
                    links.add(href)
    except requests.exceptions.RequestException as e:
        print(f"Error accessing Google: {e}")
        return set()

    return links


def change_country(google: str, country: str) -> str:
    """Возвращает строку запроса с добавленным в нее кодом страны, если таковая поддерживается."""

    country = country.strip()
    if country in COUNTRY_CODES:
        country_code = COUNTRY_CODES[country]
        google = google + f"&cr={country_code}"
        return google
    else:
        return "Страна не поддерживается"


def process_country(
    country: str, search_term: str, start_position: int, num_iterations: int, file_path: str
) -> None:
    """
    Производит сбор информации с сайтов для переданной страны:
    * Проверяет, поддерживается ли переданная страна;
    * Собирает ссылки на все сайты, выданные по запросу (`num_iterations` раз);
    * Для каждой ссылки вызывает функцию сбора информации с сайта;
    * Записывает результаты работы в csv-файл.
    """

    for _ in range(num_iterations):
        count = 0
        a = 100

        google = "https://www.google.com/search?q=intext:&as_qdr=all&filter=&num=&start=&complete=1"
        google = change_country(google, country)
        if google == "Страна не поддерживается":
            print(google)
            continue

        google = google.replace("intext:", f"{search_term}")
        google = google.replace("num=", f"num={a}")
        google = google.replace("start=", f"start={start_position}")

        websites = get_google_url(google)
        if websites is None:
            continue
        if not websites:
            print("Страницы, выдаваемые по данному запросу, закончились.")
            break
        print(google)

        for site in websites:

            try:
                result = get_site_data(site)
                if result is None:
                    continue

                result_emails, instagram_links, telegram_links, twitter_links, discord_links, facebook_links, reddits_links, youtube_links, vk_links, found_comments = result
                for email, instagram, telegram, twitter, discord, facebook, reddit, youtube, vk in zip(result_emails, instagram_links, telegram_links, twitter_links, discord_links, facebook_links, reddits_links, youtube_links, vk_links):
                    print(site)
                    count += 1

                    with open(file_path, mode="a", encoding="utf-8", newline="") as csvfile:
                        writer = csv.writer(csvfile)

                        if found_comments:
                            comments_message = "Комментарии открыты"
                        else:
                            comments_message = "Комментарии закрыты"
                        writer.writerow([site, email, instagram, telegram, twitter, discord, facebook, reddit, youtube, vk, country, comments_message])

            except ValueError as e:
                print(f"Ошибка при обработке сайта {site}: {e}")
                count += 1

        start_position += count
