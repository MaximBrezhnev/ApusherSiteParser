"""Модуль для работы с прокси."""


proxies_list = []
current_proxy_index = 0


def load_proxies(file_path: str) -> None:
    """Записывает прокси из переданного файла в переменную `proxies_list`."""

    global proxies_list

    processed_file_path = file_path.strip('"')

    try:
        with open(processed_file_path, "r") as f:
            proxies_list = [line.strip() for line in f if line.strip()]
    except Exception as exc:
        print(f"Не удалось получить прокси из файла: {exc}")


def get_current_proxy() -> str | None:
    """Возвращает текущий прокси. Если прокси добавлено не было, возвращает `None`."""

    if proxies_list:
        proxy: str = proxies_list[current_proxy_index]
        return f"http://{proxy}"


def rotate_proxy() -> None:
    """
    Производит переключение на следующий прокси.
    Если список прокси кончился, возвращается к началу списка.
    """

    global current_proxy_index

    current_proxy_index = (current_proxy_index + 1) % len(proxies_list)
