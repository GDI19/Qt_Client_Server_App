"""
1. Задание на закрепление знаний по модулю CSV. 
Написать скрипт, осуществляющий выборку данных из файлов info_1.txt, info_2.txt, info_3.txt 
и формирующий новый «отчетный» файл в формате CSV. 
«Изготовитель системы», 
    «Название ОС», 
    «Код продукта», 
    «Тип системы». 

Для этого:
    Создать функцию get_data(), в которой в цикле осуществляется 
    перебор файлов с данными, их открытие и считывание данных. 
    В этой функции из считанных данных необходимо с помощью 
    регулярных выражений извлечь значения параметров 
    «Изготовитель системы», 
    «Название ОС», 
    «Код продукта», 
    «Тип системы». 
    Значения каждого параметра поместить в соответствующий список.
     Должно получиться четыре списка — например, os_prod_list, 
     os_name_list, os_code_list, os_type_list. В этой же функции 
     создать главный список для хранения данных отчета — 
     например, main_data — и поместить в него названия столбцов 
     отчета в виде списка: «Изготовитель системы», «Название ОС», 
     «Код продукта», «Тип системы». Значения для этих столбцов 
     также оформить в виде списка и поместить в файл main_data 
     (также для каждого файла);
    Создать функцию write_to_csv(), в которую передавать ссылку 
    на CSV-файл. В этой функции реализовать получение данных через 
    вызов функции get_data(), а также сохранение подготовленных 
    данных в соответствующий CSV-файл;
    Проверить работу программы через вызов функции write_to_csv(). 
"""
import csv
import re
import chardet

num_files = 3

os_prod_list = []
os_name_list = []
os_code_list = []
os_type_list = []

main_data = []
headers = ['Изготовитель системы', 'Название ОС', 'Код продукта', 'Тип системы']

filtered_data_file_name = 'filtered_data.csv'


def get_data(file):
    with open(file, 'rb') as f:
        data_bytes = f.read()
        code_format = chardet.detect(data_bytes)['encoding']
        print(f'{file} - ', code_format)

        data = data_bytes.decode(code_format)
        print(data, type(data))
    return data
    

def find_sep_data(data):     
    os_prod_reg = re.compile(r'Изготовитель системы:\s*\S*')
    os_prod_list.append(os_prod_reg.findall(data)[0].split()[2])

    os_name_reg = re.compile(r'Название ОС:\s*.*')
    os_name_list.append(' '.join(os_name_reg.findall(data)[0].split()[2:]))

    os_code_reg = re.compile(r'Код продукта:\s*\S*')
    os_code_list.append(os_code_reg.findall(data)[0].split()[2])

    os_type_reg = re.compile(r'Тип системы:\s*\S*')
    os_type_list.append(os_type_reg.findall(data)[0].split()[2])



def fill_new_data(num):
    for i in range(1, num):
        data = get_data(f'info_{i}.txt')
        find_sep_data(data)
    
    main_data.append(headers)

    j = 1
    for i in range(0, num_files):
        row_data = []
        row_data.append(j)
        row_data.append(os_prod_list[i])
        row_data.append(os_name_list[i])
        row_data.append(os_code_list[i])
        row_data.append(os_type_list[i])
        main_data.append(row_data)
        j += 1


def create_new_csvfile():
    fill_new_data(num_files + 1)

    with open(filtered_data_file_name, 'w', encoding='utf-8') as f:
        
        f_writer = csv.writer(f)
        for row in main_data:
            f_writer.writerow(row)



create_new_csvfile()

        
        
    