"""
2. Задание на закрепление знаний по модулю json. Есть файл orders 
в формате JSON с информацией о заказах. Написать скрипт, 
автоматизирующий его заполнение данными. 
5 параметров — 

товар (item), 
количество (quantity), 
цена (price), 
покупатель (buyer), 
дата (date).

Для этого:
Создать функцию write_order_to_json(), в которую передается 
5 параметров — товар (item), количество (quantity), цена (price), 
покупатель (buyer), дата (date). 
Функция должна предусматривать запись данных в виде словаря в файл 
orders.json. При записи данных указать величину отступа в 4 
пробельных символа;
Проверить работу программы через вызов функции 
write_order_to_json() с передачей в нее значений каждого параметра. 
{
    "orders": [
        {
            "item": "printer",
            "quantity": "10",
            "price": "6700",
            "buyer": "Ivanov I.I.",
            "date": "24.09.2017"
        },
        {
            "item": "scaner",
            "quantity": "20",
            "price": "10000",
            "buyer": "Petrov P.P.",
            "date": "11.01.2018"
        }
    ]
}
"""

import json


def write_order_to_json(item, quantity, price, buyer, date):
    previous_data = {}

    with open('orders.json', 'r', encoding='utf-8') as f_to_read:
        previous_data = json.load(f_to_read)
        

    with open('orders.json', 'w', encoding='utf-8') as f_to_write:
        orders = previous_data['orders']
        new_order = {
            "item": item,
            "quantity": quantity,
            "price": price,
            "buyer": buyer,
            "date": date
        } 
        
        orders.append(new_order)
        json.dump(previous_data, f_to_write, indent=4, ensure_ascii=False)


write_order_to_json('printer', '10', '6700', 'Ivanov I.I.', '24.09.2017')
write_order_to_json('scaner', '20', '10000', 'Petrov P.P.', '11.01.2018')
write_order_to_json('лоптоп', '5', '40000', 'Sidorov S.S.', '2.05.2019')