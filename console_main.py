import logging
from RanobeParser import *
import json

default_cookies = {
		"_ga": "GA1.1.453943953.1740239433",
		"_ga_C7J1M8PT9N": "GS1.1.1741115612.3.1.1741116516.0.0.0",
		"_ym_d": "1740239433",
		"_ym_isad": "2",
		"_ym_uid": "1740239433861123653",
		"wordpress_logged_in_35981584ee49ee4e18131611545f1192": "Voldex-o|1741449166|OdJG1dfCfOzljqoL5ZjwmcdzKVduEjoVYNW4bWtgY9y|377b88a64b5e11d0f693f03b9531f461f349dd3e79d175851ca05035289c728e",
		"wpdiscuz_nonce_35981584ee49ee4e18131611545f1192": "ce702f881e"
}

def main():
    logging.basicConfig(level=logging.DEBUG, filename="debug.log", filemode="w",
                        format="%(asctime)s - %(levelname)s - %(message)s", encoding='utf-8')
    
    logging.info("Start program")

    config = json.load(open("config.json", "r"))    
    max_chapers_on_desc = config.get("max_chapers_on_desc", 50)
    cookies = config.get("cookies", default_cookies)
    ranobe_url = config.get("ranobe_url", "")
    mode = config.get("mode", "fb2")
    file_name = config.get("file_name", "")

    proxies = config.get("proxies", None)
    sleep_time = config.get("sleep_time", 10)

    if ranobe_url != "":
        print(f"Ссылка на ранобе: {ranobe_url}")
    else:
        print("Введите ссылку на ранобе")
        ranobe_url = input()

    if file_name == "":
        print("Укажите название файла, куда будут загружены главы")
        file_name = input()
    print("Скачанные главы будут добавлены в конец файла")


    ranobeParser = RanobeParser(cookies=cookies, proxies=proxies, file_name=file_name, file_type=mode, sleep_time=sleep_time)
    
    ranobeParser.parse_ranobe(ranobe_url)
    print(f"Ранобе определено как: {ranobeParser.ranobe_name}")
    print_found_chapters(ranobeParser.chapters_url, max_chapers_on_desc)
    
    print("Выберите какие главы ранобе хотите спарсить")
    print("Для парсинга всех глав введите 0")
    print("Для парсинга последних глав введите -1")
    print("Номера глав вводите через пробел, для указания промежутка вопсользуйтесь '-'")
    print("Например '1-10 19' для парсинга последних 10 и 19-ой глав")
    selector = input()

    ranobeParser.select_chapters(selector)
    print("Парсинг глав завершен")
    
if __name__ == "__main__":
    main()
    print("Парсинг завершён успешно")
    # try:
    #     main()
    #     print("Парсинг завершён успешно")
    # except Exception as e:
    #     print("Произошла ошибка: ", e)
    #     logging.error(f"Произошла ошибка: {e}")


