import logging
import requests
import bs4
import os
import time
import winsound

default_cookies = {
		"_ga": "GA1.1.453943953.1740239433",
		"_ga_C7J1M8PT9N": "GS1.1.1741115612.3.1.1741116516.0.0.0",
		"_ym_d": "1740239433",
		"_ym_isad": "2",
		"_ym_uid": "1740239433861123653",
		"wordpress_logged_in_35981584ee49ee4e18131611545f1192": "Voldex-o|1741449166|OdJG1dfCfOzljqoL5ZjwmcdzKVduEjoVYNW4bWtgY9y|377b88a64b5e11d0f693f03b9531f461f349dd3e79d175851ca05035289c728e",
		"wpdiscuz_nonce_35981584ee49ee4e18131611545f1192": "ce702f881e"
}

class ConsoleChaptersOut():
    @classmethod
    def print_parse_chapter_error(self, chapter_url):
            print("В процессе получения текста главы произошла ошибка")
            print(f"Перейдите по ссылке {chapter_url},\nпосле чего нажмите 'ввод' чтобы попробовать получить текст главы ещё раз")
            input()
            print("Повторная попытка получить текст главы")

    @classmethod
    def print_parse_chapter_info(self, chapter_url, chapter_name):
            print(f"Парсинг главы {chapter_name}")
            print(f"Ссылка на главу: {chapter_url}")


class RanobeParser:
    def __init__(self, *, file_type="txt", file_name=None, proxies=None, sleep_time=10, cookies=default_cookies, chaptersOut = ConsoleChaptersOut):
        self.file_type = file_type
        self.file_name = file_name
        self.proxies = proxies
        self.sleep_time = sleep_time
        self.cookies = cookies

        if not os.path.exists("out"):
            os.makedirs("out")

        self.last_saved_chapter_name = self.get_last_saved_chapter()
        self.chaptersOut = chaptersOut

        self.ranobe_name = None
        self.chapters_url = []




    def get_last_saved_chapter_fb2(self):
        logging.debug("Получение последней сохраненной главы fb2")
        with open("out/" + self.file_name, "r", encoding="utf-8") as file:
            last_chapter_name = None
            for row in file:
                if "</body>" in row:
                    logging.info(f"Последняя сохраненная глава: {last_chapter_name}")
                    return last_chapter_name.capitalize()
                if "<title>" in row:
                    last_chapter_name = row[10:-13]
        logging.error("Не удалось найти последнюю сохраненную главу")
        return None


    def get_last_saved_chapter_txt(self):
        logging.debug("Получение последней сохраненной главы txt")
        with open("out/" + self.file_name, "r", encoding="utf-8") as file:
            last_chapter_name = None
            for row in file:
                if "$$$" in row:
                    last_chapter_name = row[4:]
            logging.info(f"Последняя сохраненная глава: {last_chapter_name}")
            return last_chapter_name.capitalize()
        

    def get_last_saved_chapter(self):
        try:
            logging.debug("Получение последней сохраненной главы")
            if self.file_type == "fb2":
                return self.get_last_saved_chapter_fb2()
            elif self.file_type == "txt":
                return self.get_last_saved_chapter_txt()
            else:
                logging.error("Unknown file type")
        except:
            return None
        

    def update_last_saved_chapter(self):
        logging.debug("Обновление последней сохраненной главы")
        self.last_saved_chapter_name = self.get_last_saved_chapter()       

    
    def get_ranobe_name(self, soup):
        ranobe_name = soup.find("h1", itemprop="name").text
        logging.info(f"Название манги: {ranobe_name}")
        return ranobe_name


    def get_chapter_name(self, soup):
        ranobe_name = soup.find("h1", class_="entry-title").text
        logging.info(f"Название главы: {ranobe_name}")
        return ranobe_name.capitalize()
    
    def row_is_not_chapter_text(self, row):
        row_text = row.text.replace("/", "").lower()
        if ("novel" in row_text ) or ("com" in row_text ) or ("удалить рекламу" in row_text ):
            return True
        return False
    
    def create_new_fb2(self, file_name, text):
        logging.debug("Сохранение главы в новый fb2 файл")
        text = f"""<?xml version="1.0" encoding="utf-8"?>
        <FictionBook xmlns="http://www.gribuser.ru/xml/fictionbook/2.0" xmlns:l="http://www.w3.org/1999/xlink">
            <description>
                <title-info>
                    <book-title>{file_name}</book-title>
                    <author>
                        <first-name>Автор</first-name>
                    </author>
                </title-info>
            </description>
            <body>
                {text}
            </body>
        </FictionBook>
        """
        with open("out/" + file_name, "w", encoding="utf-8") as file:
            file.write(text)


    def edit_existing_fb2(self, file_name, text):
        logging.debug("Добавление главы в сущестующий fb2 ф")
        os.rename("out/" + file_name, "out/" + file_name + ".bak")
        with open("out/" + file_name + ".bak", "r", encoding="utf-8") as rfile:
            with open("out/" + file_name, "w", encoding="utf-8") as wfile:
                temp = None
                for row in rfile:
                    if "</body>" in row:
                        break
                    wfile.write(row)
                wfile.write(text)
                wfile.write(row)

                for row in rfile:
                    wfile.write(row)      
        os.remove("out/" + file_name + ".bak")

    
    def save_to_fb2(self, file_name, text):
        logging.debug("Сохранение главы в файл fb2")
        if not os.path.exists("out/" + file_name):
            self.create_new_fb2(file_name, text)
        else:
            self.edit_existing_fb2(file_name, text)
    

    def save_to_txt(file_name, text):
        logging.debug("Сохранение главы в файл txt")
        with open("out/" + file_name, "a", encoding="utf-8") as file:
            file.write(text)

    
    def save(self, file_name, text):
        logging.info("Сохранение главы в файл")
        if self.file_type == "fb2":
            self.save_to_fb2(file_name, text)
        elif self.file_type == "txt":
            self.save_to_txt(file_name, text)
        else:
            logging.error("Unknown file type")

    def find_chapters(self, soup):
        chapters_url = soup.find_all("div", class_="title")
        if chapters_url:
            logging.info(f"Обнаружено {len(chapters_url)} глав")
            logging.debug(f"Обнаружены следующие главы:\n")
            for i in range(len(chapters_url)):
                logging.debug(f"{i+1}. {chapters_url[i].text}")
        return chapters_url
    
    def parse_chapters(self, start, end):
        global mode
        result = ""
        if end == 0:
            end = len(self.chapters_url)
        for i in range(end-1, start-1, -1):
            chapter_href = self.chapters_url[i].find("a").get("href")
            self.chaptersOut.print_parse_chapter_info(chapter_href, f"{i+1}. {self.chapters_url[i].text}")
            logging.info(f"Парсинг главы {i+1}")
            logging.info(f"Ссылка на главу: {chapter_href}")
            result = self.parse_chapter(self.chapters_url[i].find("a").get("href"))
            self.save(self.file_name, result)
            time.sleep(self.sleep_time)

    def parse_chapter(self, chapter_url):
        result = ""
        if self.proxies is not None:
            response = requests.get(chapter_url, cookies=self.cookies, proxies=self.proxies)
        else:
            response = requests.get(chapter_url, cookies=self.ookies)
        logging.debug(f"Получен ответ от сайта: \n Код доступа: {response.status_code}, \n\n\n\n\n {response.text}")
        soup = bs4.BeautifulSoup(response.text, "lxml")
        chapter_name = self.get_chapter_name(soup=soup)
        logging.info(f"Название главы: {chapter_name}")
        print(f"Название главы: {chapter_name}")
        container =  soup.find("div", class_="entry themeform")
        rows = container.find_all("p")
        if len(rows) < 5:
            winsound.Beep(500, 1000)
            logging.error(f"В процессе получения текста главы '{chapter_url}' произошла ошибка")
            self.chaptersOut.print_parse_chapter_error(chapter_url)
            logging.debug("Повторная попытка получить текст главы")
            return self.parse_chapter(chapter_url)
        
        if self.file_type == "fb2":
            result += "<section>\n"
            result += f"<title><p>{chapter_name}</p></title>\n"
            for row in rows:
                if self.row_is_not_chapter_text(row=row):
                    continue
                result += f"<p>{row.text}</p>\n"
            result += "</section>\n"
        elif self.file_type == "txt":
            result += "$$$ " + chapter_name + "\n\n"
            for row in rows:
                if self.row_is_not_chapter_text(row=row):
                    continue
                result += row.text + "\n" 
        else:
            logging.error("Unknown file type")
        logging.debug(f"Текст главы:\n{result}")
        return result
    
    def parse_ranobe(self, ranobe_url):
        if self.proxies is not None:
            response = requests.get(ranobe_url, cookies=self.cookies, proxies=self.proxies)
        else:
            response = requests.get(ranobe_url, cookies=self.cookies)
        logging.debug(f"Получен ответ от сайта: \n Код доступа: {response.status_code}, \n\n\n\n\n {response.text}")
        if response.status_code != 200:
            logging.error(f"Произошла ошибка доступа к сайту! {response.status_code}")
            return
        soup = bs4.BeautifulSoup(response.text, "lxml")
        self.ranobe_name = self.get_ranobe_name(soup=soup)
        self.chapters_url = self.find_chapters(soup=soup)

    def select_chapters(self, selector):
        if selector == "-1":
            print(f"Последняя сохраненная глава: {self.last_saved_chapter_name}")
            if self.last_saved_chapter_name == None:
                selector = "0"
            else:
                for i in range(len(self.chapters_url)):
                    if self.last_saved_chapter_name in self.chapters_url[i].text.strip().capitalize():
                        selector = f"1-{i}"
                        break

        print(f"Парсинг глав {selector}...")

        if selector == "0":
            self.parse_chapters( 0, 0)
        else:  
            selector = selector.split(" ")
            for i in selector:
                if "-" in i:
                    start, end = i.split("-")
                    start = int(start)-1
                    end = int(end)
                    self.parse_chapters( start, end)
                else:
                    i = int(i)-1
                    self.parse_chapters( i, i+1)

def print_found_chapters(chapters_url, max_chapters_on_desc):
    print(f"Обнаружено {len(chapters_url)} глав")
    print(f"Для удобства показаны только последние {max_chapters_on_desc} глав")
    print(f"Обнаружены следующие главы:\n")
    for i in range(max_chapters_on_desc):
        if i >= len(chapters_url):
            break
        print(f"{i+1}. {chapters_url[i].text}")
        