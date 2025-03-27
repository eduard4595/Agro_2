import os
import csv
from datetime import datetime


# Ruta base para los archivos CSV
BASE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')

# Asegúrate de que la carpeta exista
if not os.path.exists(BASE_DIR):
    os.makedirs(BASE_DIR)

# Función para guardar usuarios
def save_user(username, password, role='user'):
    file_path = os.path.join(BASE_DIR, 'users.csv')
    file_exists = os.path.isfile(file_path)
    with open(file_path, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=['id', 'username', 'password', 'role'])
        if not file_exists:
            writer.writeheader()
        user_id = sum(1 for _ in open(file_path))  # Generar un ID simple basado en el número de líneas
        writer.writerow({'id': user_id, 'username': username, 'password': password, 'role': role})

# Función para guardar datos financieros
def save_financial_data(user_id, product_type, data):
    file_path = os.path.join(BASE_DIR, f'{user_id}_{product_type}.csv')
    file_exists = os.path.isfile(file_path)
    with open(file_path, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=data.keys())
        if not file_exists:
            writer.writeheader()
        writer.writerow(data)

# Función para leer datos financieros
def read_financial_data(user_id, product_type):
    file_path = os.path.join(BASE_DIR, f'{user_id}_{product_type}.csv')
    if not os.path.isfile(file_path):
        return []
    with open(file_path, mode='r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        return list(reader)

# Función para guardar datos generales
def save_general_data(user_id, product_type, data):
    file_path = os.path.join(BASE_DIR, f'{user_id}_general_{product_type}.csv')
    with open(file_path, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=data.keys())
        writer.writeheader()
        writer.writerow(data)

# Función para leer datos generales
def read_general_data(user_id, product_type):
    file_path = os.path.join(BASE_DIR, f'{user_id}_general_{product_type}.csv')
    if not os.path.isfile(file_path):
        return {}
    with open(file_path, mode='r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        return next(reader, {})

# Estructuras de datos para cada producto
def get_financial_data_structure(product_type):
    structures = {
        'cafe': ['total_ingresos', 'gastos_insumos', 'pago_jornales', 'gastos_servicios', 'valor_maquinaria', 'dinero_disponible', 'gastos_imprevistos', 'total_deudas', 'fecha_captura'],
        'cerdos': ['total_ingresos', 'cantidad_animales', 'gastos_alimento', 'pago_mano_obra', 'gastos_servicios', 'meses_engorda', 'perdidas_animales', 'dinero_disponible', 'gastos_imprevistos', 'total_deudas', 'fecha_captura'],
        'ganado': ['total_ingresos', 'cantidad_animales', 'meses_engorda', 'gastos_alimento', 'pago_mano_obra', 'gastos_servicios', 'perdidas_animales', 'dinero_disponible', 'gastos_imprevistos', 'total_deudas', 'fecha_captura'],
        'huevos': ['total_ingresos', 'cantidad_aves', 'porcentaje_produccion', 'huevos_diarios', 'gastos_alimento', 'pago_mano_obra', 'gastos_servicios', 'dinero_disponible', 'gastos_imprevistos', 'total_deudas', 'fecha_captura'],
        'maiz': ['total_ingresos', 'meses_cosecha', 'variedad_maiz', 'hectareas', 'gastos_insumos', 'pago_jornales', 'gastos_servicios', 'valor_maquinaria', 'dinero_disponible', 'gastos_imprevistos', 'total_deudas', 'fecha_captura'],
        'citricos': ['total_ingresos', 'toneladas_cosechadas', 'tipos_citricos', 'hectareas', 'gastos_insumos', 'pago_jornales', 'gastos_servicios', 'valor_maquinaria', 'dinero_disponible', 'gastos_imprevistos', 'total_deudas', 'fecha_captura']
    }
    return structures.get(product_type, [])

# Ejemplo de guardar datos financieros para un producto
def save_product_data(user_id, product_type, data):
    structure = get_financial_data_structure(product_type)
    formatted_data = {key: data.get(key, '') for key in structure}
    save_financial_data(user_id, product_type, formatted_data)

# Ejemplo de leer datos financieros para un producto
def read_product_data(user_id, product_type):
    return read_financial_data(user_id, product_type)

