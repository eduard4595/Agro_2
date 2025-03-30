from flask import Blueprint, render_template, flash, session, redirect, url_for, request
from datetime import datetime
import os
import csv

dashboard_citricos_bp = Blueprint('dashboard_citricos', __name__)

@dashboard_citricos_bp.route('/')
def dashboard_citricos():
        user_id = session.get('user_id')
        if not user_id:
            flash('Por favor, inicia sesión para acceder al dashboard.', 'danger')
            return redirect(url_for('login'))

        # Leer datos generales desde el archivo CSV
        user_folder = os.path.join('data', user_id)
        file_path = os.path.join(user_folder, 'datos_generales.csv')
        general_data = {}
        if os.path.isfile(file_path):
            with open(file_path, mode='r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                general_data = next(reader, {})

        return render_template('dashboard_citricos.html', data=general_data)

# Ruta para guardar datos de cítricos
@dashboard_citricos_bp.route('/submit_citrus_form', methods=['POST'])
def submit_citrus_form():
    user_id = session.get('user_id')
    if not user_id:
        flash('Por favor, inicia sesión.', 'danger')
        return redirect(url_for('login'))

    # Datos específicos del formulario de cítricos
    data = {
        'total_ingresos': request.form['q1'],
        'toneladas_cosechadas': request.form['q1_2'],
        'tipos_citricos': request.form['q1_3'],
        'hectareas': request.form['q1_4'],
        'gastos_insumos': request.form['q2'],
        'pago_jornales': request.form['q3'],
        'gastos_servicios': request.form['q4'],
        'valor_maquinaria': request.form['q5'],
        'dinero_disponible': request.form['q6'],
        'gastos_imprevistos': request.form['q7'],
        'total_deudas': request.form['q8'],
        'fecha_captura': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    }

    # Guardar datos en un archivo CSV
    file_path = f'{user_id}_citricos.csv'
    file_exists = os.path.isfile(file_path)
    with open(file_path, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=data.keys())
        if not file_exists:
            writer.writeheader()
        writer.writerow(data)

    flash('Datos de cítricos guardados exitosamente.', 'success')
    return redirect(url_for('dashboard_citricos.dashboard_citricos'))

# Ruta para acceder a los datos financieros de cítricos
# @app.route('/database_access_citricos')
@dashboard_citricos_bp.route('/database_access_citricos')
def database_access_citricos():
    user_id = session.get('user_id')
    if not user_id:
        flash('Por favor, inicia sesión para acceder a la base de datos.', 'danger')
        return redirect(url_for('login'))

    # Leer datos financieros desde el archivo CSV
    file_path = f'{user_id}_citricos.csv'
    financial_data = []
    if os.path.isfile(file_path):
        with open(file_path, mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            financial_data = list(reader)

    return render_template('database_access_citricos.html', data=financial_data)

# Ruta para generar estados financieros de cítricos
# @app.route('/financial_statements_citricos')
@dashboard_citricos_bp.route('/financial_statements_citricos')
def financial_statements_citricos():
    user_id = session.get('user_id')
    if not user_id:
        flash('Por favor, inicia sesión para acceder a los estados financieros.', 'danger')
        return redirect(url_for('login'))

    # Leer datos financieros desde el archivo CSV
    file_path = f'{user_id}_citricos.csv'
    financial_data = []
    if os.path.isfile(file_path):
        with open(file_path, mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            financial_data = list(reader)

    return render_template('financial_statements_citricos.html', data=financial_data)

@dashboard_citricos_bp.route('/citricos_form', methods=['GET'])
def citricos_form():
    user_id = session.get('user_id')
    if not user_id:
        flash('Por favor, inicia sesión para acceder al formulario.', 'danger')
        return redirect(url_for('login'))

    return render_template('citricos_form.html')

@dashboard_citricos_bp.route('/my_analysis_citricos', methods=['GET' ,'POST'])
def my_analysis_citricos():
    user_id = session.get('user_id')
    if not user_id:
        flash('Por favor, inicia sesión para acceder al análisis.', 'danger')
        return redirect(url_for('login'))

    # Leer datos financieros desde el archivo CSV
    file_path = f'data/{user_id}/datos_financieros_citricos.csv'
    financial_data = []
    if os.path.isfile(file_path):
        with open(file_path, mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            financial_data = list(reader)

    return render_template('my_analysis_citricos.html', data=financial_data)
