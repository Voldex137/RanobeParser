import flet as ft
import logging
from RanobeParser import *
import json
import threading
import time

ranobeParser = None

class FletChaptersOut():
    def __init__(self, text_box: ft.AlertDialog):
        self.text_box = text_box
        self.waiter = False
    def print_parse_chapter_error(self, chapter_url):
        self.text_box.content.controls=[
            ft.Text(f"В процессе получения текста главы произошла ошибка", color=ft.colors.RED),
            ft.TextButton(text=f"Перейдите по ссылке {chapter_url}", url=chapter_url),
            ft.Text(f"после чего нажмите 'Повторить' чтобы попробовать получить текст главы ещё раз"),
        ]
        self.text_box.actions[1].visible = True
        self.text_box.actions[1].update()
        self.text_box.update()

        self.waiter = True
        while self.waiter:
            time.sleep(1)
        print("Повторная попытка получить текст главы")
    def print_parse_chapter_info(self, chapter_url, chapter_name):
        self.text_box.content.controls=[
            ft.Text(f"Парсинг главы {chapter_name}"),
            ft.TextButton(text=f"Ссылка на главу: {chapter_url}", url=chapter_url),
        ]
        self.text_box.actions[1].visible = False
        self.text_box.update()

def main(page: ft.Page):
    logging.basicConfig(level=logging.DEBUG, filename="debug.log", filemode="w",
                        format="%(asctime)s - %(levelname)s - %(message)s", encoding='utf-8')
    
    logging.info("Start program")

    page.title = "RanobeParser"
    page.adaptive = True

    page.appbar = ft.AppBar(
        title=ft.Text("RanobeParser"),
        actions=[
        ft.IconButton(ft.CupertinoIcons.ADD, style=ft.ButtonStyle(padding=0))
        ],
        bgcolor=ft.Colors.with_opacity(0.04, ft.CupertinoColors.SYSTEM_BACKGROUND),
    )



    config = json.load(open("config.json", "r"))    
    max_chapters_on_desc = config.get("max_chapters_on_desc", 10)
    cookies = config.get("cookies", default_cookies)
    ranobe_url = config.get("ranobe_url", "")
    file_type = config.get("file_type", "txt")
    file_name = config.get("file_name", "")

    proxies = config.get("proxies", None)
    sleep_time = config.get("sleep_time", 10)


    ranobe_url_field = ft.TextField(label="Ссылка на ранобе", autofocus=True)
    file_name_field = ft.TextField(label="Имя файла для записи (с расширением)")
    file_type_field = ft.Dropdown(
        width=100,
        options=[
            ft.dropdown.Option("fb2"),
            ft.dropdown.Option("txt"),
        ],
    )
    proxies_field = ft.TextField(label="Прокси (необязательно)")
    selector_field = ft.TextField(label="Выбор глав (по умолчанию все новые главы)", autofocus=True, value="-1")

    ranobe_url_field.value = ranobe_url
    file_name_field.value = file_name
    file_type_field.value = file_type
    proxies_field.value = proxies.get("http", "")

    chapters_info_field = ft.Column()
    chapters_field = ft.Container(
        ft.Column(
            spacing=10,
            height=200,
            scroll=ft.ScrollMode.ALWAYS,
        ),
        alignment=ft.alignment.top_left,
        expand=True,
        padding=10,
        margin=10,
        border_radius=10,
        border=ft.border.all(1)
    )
    thread = None
    
    def close_parsing_window(e):
        page.close(parsing_window)
        page.update()

    parsing_window = None

    fletChaptersOut = FletChaptersOut(text_box=parsing_window)

    def update_fletCpatersOut(e):
        fletChaptersOut.waiter = False
        page.update()

    parsing_window = ft.AlertDialog(
        modal=True,
        title=ft.Text("Парсинг глав"),
        actions=[
            ft.ElevatedButton("Прервать", on_click=lambda e: close_parsing_window(e)),
            ft.ElevatedButton("Повторить", on_click=lambda e: update_fletCpatersOut(e), visible=False),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
        content=ft.Column(
            controls=[
            ],
            width=page.width/2,
            height=page.height/2,
        )
    )
    fletChaptersOut.text_box = parsing_window
    

    containers = []
    def btn_parse_chapters(e):
        global thread
        page.open(parsing_window)
        ranobeParser.update_last_saved_chapter()
        thread = threading.Thread(target=ranobeParser.select_chapters, args=(selector_field.value,))
        thread.start()
        print("Парсинг глав завершен")


    def btn_find_chapters(e):
        global ranobeParser
        ranobe_url = ranobe_url_field.value
        file_name = file_name_field.value
        file_type = file_type_field.value
        if proxies_field.value != "":
            proxies = {"http": proxies_field.value, "https": proxies_field.value}

        ranobeParser = RanobeParser(cookies=cookies, proxies=proxies, file_name=file_name, file_type=file_type, sleep_time=sleep_time, chaptersOut=fletChaptersOut)
        logging.info("Начало поиска глав")
        ranobeParser.parse_ranobe(ranobe_url)
        chapters_info_field.controls.clear()
        chapters_info_field.controls.append(ft.Text(f"Ранобе определено как: {ranobeParser.ranobe_name}"))
        chapters_info_field.controls.append(ft.Text(f"Найдено глав: {len(ranobeParser.chapters_url)}"))
        chapters_info_field.controls.append(ft.Text(f"Обнаружены следующие главы:"))

        paged_chapter_urls = ranobeParser.chapters_url.copy()
        paged_chapter_urls = [paged_chapter_urls[i:i + max_chapters_on_desc] for i in range(0, len(paged_chapter_urls), max_chapters_on_desc)]
        container = ft.Container(
                ft.Column(),
                alignment=ft.alignment.top_left,
            )
        for i in range(len(ranobeParser.chapters_url)):
            print(f"{i+1}. {ranobeParser.chapters_url[i].text}")
            container.content.controls.append(ft.Text(f"{i+1}. {ranobeParser.chapters_url[i].text}"))
        containers.append(container)
        chapters_field.content.controls.append(containers[0])
        chapters_info_field.controls.append(chapters_field)
        main_window.content.controls.append(selector_field)
        main_window.content.controls.append(ft.ElevatedButton("Начать парсинг", on_click=btn_parse_chapters))
        page.update()

    def btn_save_settings(e):
        config["ranobe_url"] = ranobe_url_field.value
        config["file_name"] = file_name_field.value
        config["file_type"] = file_type_field.value
        config["proxies"] = {"http": proxies_field.value, "https": proxies_field.value}
        json.dump(config, open("config.json", "w"), indent=4)
        page.close(settings_window)
        btn_find_chapters(e)

    main_window=ft.Container(
    ft.Column(
        controls=[
            ft.ElevatedButton("Обновить страницу", on_click=btn_find_chapters),
            ft.Container(chapters_info_field),

        ],
        expand=True,
    ),
    alignment=ft.alignment.top_center,
    expand=True,
    padding=10,
    margin=10,
    border_radius=10,
    border=ft.border.all(1)
    )
    settings_window = ft.AlertDialog(
        modal=True,
        title=ft.Text("Настройки"),
        actions=[
            ft.ElevatedButton("Закрыть", on_click=lambda e: page.close(settings_window)),
            ft.ElevatedButton("Сохранить", on_click=btn_save_settings),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
        content=ft.Column(
            controls=[
                ft.Text("Настройки парсинга"),
                ranobe_url_field,
                file_name_field,
                file_type_field,
                proxies_field,
            ],
            width=page.width/2,
            height=page.height/2,
        )
    )
    page.appbar.leading = ft.IconButton(ft.CupertinoIcons.SETTINGS, on_click=lambda e: page.open(settings_window))

    main_area = ft.SafeArea(
        expand=True,
        content=main_window
    )

    page.add(main_area)

if __name__ == "__main__":
    ft.app(target=main, assets_dir="assets")
    #ft.app(target=main, assets_dir="assets", view=ft.AppView.WEB_BROWSER)
