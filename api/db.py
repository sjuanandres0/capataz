'''
Create, Read, Update and Delete
For 2 databases:
- Local: dummy db for local testing
- Cloud: tbc
'''

import os
import json

data_folder_path = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), 'data')
print(f'data_folder_path: {data_folder_path}')


def read(collection):
    with open(f'{data_folder_path}/{collection}.json', 'r') as json_file:
        return json.load(json_file)


def create(collection, element):
    try:
        with open(f'{data_folder_path}/{collection}.json', 'r') as json_file:
            data = json.load(json_file)
        data.append(element)
        with open(f'{data_folder_path}/{collection}.json', 'w') as json_file:
            json.dump(data, json_file, indent=2)
        return 'success'
    except:
        return 'fail'


def update(collection, element):
    try:
        with open(f'{data_folder_path}/{collection}.json', 'r') as json_file:
            data = json.load(json_file)

        index_to_update = next((index for index, item in enumerate(
            data) if item.get('id') == element.get('id')), None)

        if index_to_update is not None:
            data[index_to_update].update({k: v for k, v in element.items() if k != 'id'})

            with open(f'{data_folder_path}/{collection}.json', 'w') as json_file:
                json.dump(data, json_file, indent=2)

            return 'success'
        else:
            return 'fail - ID not found'
    except Exception as e:
        return f'fail - {str(e)}'


# def addNewCpToLocal(new_element):
#     try:
#         with open(f'{data_folder_path}/cp.json', 'r') as json_file:
#             data = json.load(json_file)
#         data.append(new_element)
#         with open(f'{data_folder_path}/cp.json', 'w') as json_file:
#             json.dump(data, json_file, indent=2)
#         flash(['Nueva CP cargada exitosamente!', 'success'])
#         return print("New element appended successfully.")
#     except:
#         flash(['Error al guardar Nueva CP!', 'danger'])
#         print('Error to save new CP')
