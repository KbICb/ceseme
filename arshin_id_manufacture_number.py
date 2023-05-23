"""с аршина скачиваем файл с результатами поверки
после чего получаем заводские номера по результатам поверки
соотносим результаты и номера и сортируем по возрастанию номера"

import time
from json.decoder import JSONDecodeError
from requests.exceptions import Timeout
import requests
import xml.etree.ElementTree as ET
import os
import os.path


def get_number(global_id):
    response = request_fgis(global_id)
    try:
        response_json = response.json()
        response_manufacture_number = response_json["result"]["miInfo"]["singleMI"]["manufactureNum"]
    except JSONDecodeError:
        print("ошибка парсинга json")
        response_manufacture_number = ""
    return response_manufacture_number


def request_fgis(global_id: str):
    url = f"https://fgis.gost.ru/fundmetrology/cm/iaux/vri/{global_id}"
    payload = {}
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36',
    }
    response = ""
    for _ in range(5):
        time.sleep(0.3)
        try:
            response = requests.request("GET", url, headers=headers, data=payload, timeout=1, verify=False)
            if response.status_code == 200:
                print("OK")
                break
        except Timeout:
            print("BAD", end=" ")
            continue
    return response


def get_file() -> str:
    cur_dir = (os.path.dirname(os.path.abspath(__file__)))
    path_file = ""
    for root, dirs, files in os.walk(cur_dir):
        for file in files:
            if file.startswith("protocol") and file.endswith(".xml"):
                path_file = os.path.join(root, file)
                print("Найден файл с данными ", path_file)
    if path_file == "":
        print("---------Файл с данными НЕ НАЙДЕН!----------")
    return path_file


def get_records(record_data: dict, file_path: str) -> dict:
    if file_path != "":
        for elem in ET.iterparse(file_path):
            if "globalID" in elem[1].tag:
                record_data[elem[1].text] = ""
    return record_data


file_path = get_file()
dir_file = os.path.dirname(file_path)
name_file = os.path.basename(file_path)
record_data = get_records({}, file_path)
if record_data == {}:
    print("---------Номера записей не найдены!---------")
    exit()
else:
    print(f"Найдено {len(record_data)} записей ")
err_data = {}
for key in record_data:
    print(f"Получение данных записи {key}..............", end="")
    number = get_number(key)
    if number == "":
        err_data[key] = ""
    record_data[key] = number
if len(err_data) > 0:
    print("------Необходимо проверить данные------")
    print(err_data)
else:
    print("Данные получены")

sorted_record_data = dict(sorted(record_data.items(), key=lambda item: item[1]))

os.rename(file_path, dir_file + "/compited_" + name_file)
print("Исходный файл переименован")

with open(dir_file + "/result_arshin.txt", "w+") as file:
    if len(err_data) > 0:
        file.write(f'\nНе получены заводские номера для записей:\n\n')
        for key, value in err_data.items():
            file.write(f'{key}, {value}\n')
        file.write(f'\n\nПолучены заводские номера для записей:\n')
    for key, value in sorted_record_data.items():
        file.write(f'{key}\n')
    file.write(f'\n\n\n{name_file} - обработанные данные\n\n')
    for key, value in sorted_record_data.items():
        file.write(f'{key}, {value}\n')




print(f"Обработанные данные записаны в файл {dir_file + '/result_arshin.txt'}")
