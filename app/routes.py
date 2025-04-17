import os
import csv
from flask import render_template, request, redirect, url_for, flash, session, make_response
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from .views.financial_info import financial_info_bp
from .views.climate_analysis import climate_analysis_bp
from .views.chat_ai import chat_ai_bp
from .views.user_management import user_management_bp
from .views.dashboard_citricos import dashboard_citricos_bp
# import pdfkit  # Asegúrate de instalar pdfkit y wkhtmltopdf
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

def register_routes(app):
    """
    Registra todos los blueprints de los módulos en la aplicación Flask.
    """
    app.register_blueprint(financial_info_bp, url_prefix='/financial-info')
    app.register_blueprint(climate_analysis_bp, url_prefix='/climate-analysis')
    app.register_blueprint(chat_ai_bp, url_prefix='/chat-ai')
    app.register_blueprint(user_management_bp, url_prefix='/user-management')
    app.register_blueprint(dashboard_citricos_bp, url_prefix='/dashboard_citricos')

    # Ruta para registrar usuarios
    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if request.method == 'POST':
            # Obtener los datos del formulario
            username = request.form['username']
            telefono = request.form['telefono']
            email = request.form['email']
            password = generate_password_hash(request.form['password'], method='pbkdf2:sha256')
            dia = request.form['dia']
            mes = request.form['mes']
            año = request.form['año']
            genero = request.form['genero']
            terminos = request.form.get('terminos')

            # Ruta del archivo y creación de la carpeta si no existe
            file_path = 'users.csv'
            file_exists = os.path.isfile(file_path)

            # Guardar los datos en un archivo CSV
            with open(file_path, mode='a', newline='', encoding='utf-8') as file:
                writer = csv.DictWriter(file, fieldnames=['username', 'telefono', 'email', 'password', 'fecha_nacimiento', 'genero', 'terminos'])
                if not file_exists:
                    writer.writeheader()
                writer.writerow({
                    'username': username,
                    'telefono': telefono,
                    'email': email,
                    'password': password,
                    'fecha_nacimiento': f"{dia}/{mes}/{año}",
                    'genero': genero,
                    'terminos': 'Aceptado' if terminos else 'No aceptado'
                })

            # Crear carpeta asociada al correo electrónico del usuario
            user_folder = os.path.join('data', email)
            if not os.path.exists(user_folder):
                os.makedirs(user_folder)

            # Iniciar sesión automáticamente después del registro
            session['user_id'] = email

            flash('Registro exitoso. Por favor, completa tus datos generales.', 'success')
            return redirect(url_for('datos_generales'))  # Redirigir al formulario de datos generales
        return render_template('register.html')

    # Ruta para iniciar sesión
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            email = request.form['email']
            password = request.form['password']

            # Verificar usuario en el archivo CSV
            file_path = 'users.csv'
            if not os.path.isfile(file_path):
                flash('El archivo de usuarios no existe. Contacte al administrador.', 'danger')
                return render_template('login.html')  # Mostrar error en la misma página

            with open(file_path, mode='r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    if row['email'] == email and check_password_hash(row['password'], password):
                        session['user_id'] = email  # Usar el correo como identificador único

                        # Leer la actividad principal desde datos_generales.csv
                        user_folder = os.path.join('data', email)
                        general_file = os.path.join(user_folder, 'datos_generales.csv')
                        if os.path.isfile(general_file):
                            with open(general_file, mode='r', encoding='utf-8') as general_data_file:
                                general_reader = csv.DictReader(general_data_file)
                                general_data = next(general_reader, {})
                                actividad_principal = general_data.get('actividad_principal', '').strip().lower()

                                # Redirigir al dashboard correspondiente
                                if actividad_principal == 'citricos':
                                    return redirect(url_for('dashboard_citricos.dashboard_citricos'))
                                elif actividad_principal == 'cafe':
                                    return redirect(url_for('dashboard_cafe'))
                                elif actividad_principal == 'maiz':
                                    return redirect(url_for('dashboard_maiz'))
                                elif actividad_principal == 'ganado_bovino':
                                    return redirect(url_for('dashboard_ganado'))
                                elif actividad_principal == 'cerdos':
                                    return redirect(url_for('dashboard_cerdos'))
                                elif actividad_principal == 'huevo':
                                    return redirect(url_for('dashboard_huevos'))
                                elif actividad_principal == 'litchi':  # Nueva opción para Litchi
                                    return redirect(url_for('dashboard_litchi'))
                                else:
                                    flash('Actividad principal no válida. Contacte al administrador.', 'warning')
                                    return render_template('login.html')

                        flash('No se encontró información de actividad principal. Complete sus datos generales.', 'warning')
                        return render_template('login.html')

            flash('Credenciales inválidas. Por favor, intente nuevamente.', 'danger')
        return render_template('login.html')

    # Ruta para cerrar sesión
    @app.route('/logout')
    def logout():
        session.pop('user_id', None)
        flash('Has cerrado sesión.', 'success')
        return redirect(url_for('login'))
    @app.route('/base')
    def base():
        return render_template('base.html')

    # Ruta para procesar el formulario de datos generales
    @app.route('/datos_generales', methods=['GET', 'POST'])
    def datos_generales():
        user_id = session.get('user_id')  # Obtener el correo electrónico del usuario desde la sesión
        if not user_id:
            flash('Por favor, inicia sesión.', 'danger')
            return redirect(url_for('login'))

        if request.method == 'POST':
            # Datos enviados desde el formulario
            data = {
                'idioma': request.form['idioma'],
                'actividad_principal': request.form['actividad_principal'],
                'otras_actividades': ', '.join(request.form.getlist('otras_actividades')),  # Manejar múltiples selecciones
                'tamano_produccion': request.form['tamano_produccion'],
                'anos_actividad': request.form['anos_actividad'],
                'ubicacion': request.form['ubicacion'],
                'coordenadas': request.form['coordenadas'],
                'clima_preocupacion': request.form['clima_preocupacion'],
                'perdidas_clima': request.form['perdidas_clima'],
                'tipo_ayuda': request.form['tipo_ayuda'],
                'frecuencia_chat': request.form['frecuencia_chat'],
                'comodidad_tecnologia': request.form['comodidad_tecnologia'],
                'aceptar_mejoras': request.form['aceptar_mejoras'],
                'aceptar_terminos': request.form['aceptar_terminos'],
                'fecha_captura': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
            }

            # Crear carpeta del usuario si no existe
            user_folder = os.path.join('data', user_id)
            if not os.path.exists(user_folder):
                os.makedirs(user_folder)

            # Guardar los datos en un archivo CSV dentro de la carpeta del usuario
            file_path = os.path.join(user_folder, 'datos_generales.csv')
            file_exists = os.path.isfile(file_path)
            with open(file_path, mode='a', newline='', encoding='utf-8') as file:
                writer = csv.DictWriter(file, fieldnames=data.keys())
                if not file_exists:
                    writer.writeheader()
                writer.writerow(data)

            flash('Datos generales guardados exitosamente.', 'success')
            # Leer la actividad principal desde el archivo guardado
            if os.path.isfile(file_path):
                with open(file_path, mode='r', encoding='utf-8') as general_data_file:
                    general_reader = csv.DictReader(general_data_file)
                    general_data = next(general_reader, {})
                    actividad_principal = general_data.get('actividad_principal', '').strip().lower()

                    # Redirigir al dashboard correspondiente
                    if actividad_principal == 'citricos':
                        return redirect(url_for('dashboard_citricos'))
                    elif actividad_principal == 'cafe':
                        return redirect(url_for('dashboard_cafe'))
                    elif actividad_principal == 'maiz':
                        return redirect(url_for('dashboard_maiz'))
                    elif actividad_principal == 'ganado_bovino':
                        return redirect(url_for('dashboard_ganado'))
                    elif actividad_principal == 'cerdos':
                        return redirect(url_for('dashboard_cerdos'))
                    elif actividad_principal == 'huevo':
                        return redirect(url_for('dashboard_huevos'))
                    elif actividad_principal == 'litchi':  # Nueva opción para Litchi
                        return redirect(url_for('dashboard_litchi'))
                    else:
                        flash('Actividad principal no válida. Contacte al administrador.', 'warning')
                        return render_template('datos_generales.html')
        return render_template('datos_generales.html')

    @app.route('/coffee_form', methods=['GET'])
    def coffee_form():
        user_id = session.get('user_id')
        if not user_id:
            flash('Por favor, inicia sesión para acceder al formulario.', 'danger')
            return redirect(url_for('login'))

        return render_template('coffee_form.html')


    # Ruta para guardar datos de café
    @app.route('/submit_coffee_form', methods=['POST'])
    def submit_coffee_form():
        user_id = session.get('user_id')
        if not user_id:
            flash('Por favor, inicia sesión.', 'danger')
            return redirect(url_for('login'))

        try:
            # Función para limpiar y convertir valores numéricos
            def parse_float(value):
                return float(value.replace(',', '').strip()) if value else 0

            # Datos específicos del formulario de café
            lugar_comercializacion = request.form.get('q13', '')
            if lugar_comercializacion == 'Other':
                lugar_comercializacion = f"Otro: {request.form.get('q13_other', '').strip()}"

            # Datos específicos del formulario de café
            data = {
                # Datos financieros
                'total_ingresos': parse_float(request.form.get('q1', '0')),
                'produccion_total': parse_float(request.form.get('q1_2', '0')),
                'hectareas': parse_float(request.form.get('q1_3', '0')),
                'gastos_insumos': parse_float(request.form.get('q2', '0')),
                'pago_jornales': parse_float(request.form.get('q3', '0')),
                'gastos_servicios': parse_float(request.form.get('q4', '0')),
                'valor_maquinaria': parse_float(request.form.get('q5', '0')),
                'dinero_disponible': parse_float(request.form.get('q6', '0')),
                'gastos_imprevistos': parse_float(request.form.get('q7', '0')),
                'total_deudas': parse_float(request.form.get('q8', '0')),
                # Datos operativos
                'dias_trabajo': parse_float(request.form.get('q9', '0')),
                'trabajadores': parse_float(request.form.get('q10', '0')),
                'horas_venta': parse_float(request.form.get('q11', '0')),
                'horas_supervision': parse_float(request.form.get('q12', '0')),
                'lugar_comercializacion': lugar_comercializacion,
                'comentarios': request.form.get('comments', ''),
                # Fecha de captura enviada desde el formulario
                'fecha_captura': request.form.get('fecha_captura', '')
            }

            # Agregar 'unidad_produccion' al final del diccionario
            data['unidad_produccion'] = request.form.get('unidad_produccion', '')

            # Validar datos obligatorios
            if not data['total_ingresos'] or not data['produccion_total'] or not data['hectareas']:
                flash('Por favor, completa todos los campos obligatorios.', 'danger')
                return redirect(url_for('coffee_form'))

            # Cálculos financieros
            costos_directos = data['gastos_insumos'] + data['pago_jornales'] + data['gastos_servicios'] + data['gastos_imprevistos']
            data['utilidad_bruta'] = data['total_ingresos'] - costos_directos
            data['utilidad_neta'] = data['utilidad_bruta'] - data['total_deudas']
            activos_totales = data['dinero_disponible'] + data['valor_maquinaria']
            data['activos_totales'] = activos_totales
            data['patrimonio_neto'] = activos_totales - data['total_deudas']
            data['costo_por_unidad'] = costos_directos / data['produccion_total'] if data['produccion_total'] else 0
            data['margen_ganancia'] = (data['utilidad_bruta'] / data['total_ingresos']) * 100 if data['total_ingresos'] else 0
            data['razon_endeudamiento'] = data['total_deudas'] / activos_totales if activos_totales else 0
            data['productividad_por_hectarea'] = data['produccion_total'] / data['hectareas'] if data['hectareas'] else 0
            data['gastos_totales'] = costos_directos

            # Crear carpeta del usuario si no existe
            user_folder = os.path.join('data', user_id)
            if not os.path.exists(user_folder):
                os.makedirs(user_folder)

            # Ruta del archivo CSV
            file_path = os.path.join(user_folder, 'datos_financieros_cafe.csv')

            # Verificar si el archivo existe
            file_exists = os.path.isfile(file_path)

            # Reorganizar las claves para que 'unidad_produccion' esté al final
            ordered_data = {key: data[key] for key in data.keys()}

            # Guardar los datos en el archivo CSV
            with open(file_path, mode='a', newline='', encoding='utf-8') as file:
                writer = csv.DictWriter(file, fieldnames=ordered_data.keys())
                if not file_exists:
                    writer.writeheader()  # Escribir encabezado si el archivo no existe
                writer.writerow(ordered_data)  # Agregar los datos al archivo

            flash('Datos de café guardados exitosamente.', 'success')
            return redirect(url_for('dashboard_cafe'))

        except ValueError as e:
            flash(f'Error en los datos ingresados: {e}', 'danger')
            return redirect(url_for('coffee_form'))
        except Exception as e:
            flash(f'Ocurrió un error inesperado: {e}', 'danger')
            return redirect(url_for('coffee_form'))


    @app.route('/pig_form', methods=['GET'])
    def pig_form():
        user_id = session.get('user_id')
        if not user_id:
            flash('Por favor, inicia sesión para acceder al formulario.', 'danger')
            return redirect(url_for('login'))

        return render_template('pig_form.html')
    # Ruta para guardar datos de cerdos
    @app.route('/submit_pig_form', methods=['POST'])
    def submit_pig_form():
        user_id = session.get('user_id')
        if not user_id:
            flash('Por favor, inicia sesión.', 'danger')
            return redirect(url_for('login'))

        try:
            # Función para limpiar y convertir valores numéricos
            def parse_float(value):
                return float(value.replace(',', '').strip()) if value else 0

            # Datos específicos del formulario de cerdos
            lugar_comercializacion = request.form.get('q14', '')
            if lugar_comercializacion == 'Other':
                lugar_comercializacion = f"Otro: {request.form.get('q14_other', '').strip()}"

            data = {
                # Sección 1: Ingresos y Gastos
                'total_ingresos': parse_float(request.form.get('q1', '0')),
                'cantidad_animales': parse_float(request.form.get('q1_1', '0')),
                'peso_promedio': parse_float(request.form.get('q1_2', '0')),
                'ciclos_anuales': parse_float(request.form.get('q1_3', '0')),
                'duracion_ciclo': parse_float(request.form.get('q1_4', '0')),
                'animales_actuales': parse_float(request.form.get('q1_5', '0')),
                'peso_promedio_actual': parse_float(request.form.get('q1_6', '0')),
                'valor_maquinaria': parse_float(request.form.get('q1_7', '0')),
                'gastos_alimento': parse_float(request.form.get('q2', '0')),
                'pago_mano_obra': parse_float(request.form.get('q3', '0')),
                'gastos_servicios': parse_float(request.form.get('q4', '0')),
                'gastos_veterinario': parse_float(request.form.get('q4_1', '0')),
                'meses_engorda': parse_float(request.form.get('q5', '0')),
                'perdidas_animales': parse_float(request.form.get('q6', '0')),
                'dinero_disponible': parse_float(request.form.get('q7', '0')),
                'gastos_imprevistos': parse_float(request.form.get('q8', '0')),
                'total_deudas': parse_float(request.form.get('q9', '0')),

                # Sección 2: Procesos Productivos
                'horas_supervision': parse_float(request.form.get('q10', '0')),
                'dias_tratamientos': parse_float(request.form.get('q11', '0')),
                'horas_preparacion_venta': parse_float(request.form.get('q12', '0')),
                'trabajadores_necesarios': parse_float(request.form.get('q13', '0')),
                'lugar_comercializacion': lugar_comercializacion,

                # Fecha de captura enviada desde el formulario
                'fecha_captura': request.form.get('fecha_captura', ''),
                'comentarios': request.form.get('comments', '')
            }

            # Validar datos obligatorios
            if not data['total_ingresos'] or not data['cantidad_animales'] or not data['gastos_alimento']:
                flash('Por favor, completa todos los campos obligatorios.', 'danger')
                return redirect(url_for('pig_form'))

            # Cálculos financieros
            costos_directos = (
                data['gastos_alimento'] +
                data['pago_mano_obra'] +
                data['gastos_servicios'] +
                data['gastos_veterinario'] +
                data['gastos_imprevistos']
            )
            data['utilidad_bruta'] = data['total_ingresos'] - costos_directos
            data['utilidad_neta'] = data['utilidad_bruta'] - data['total_deudas']
            activos_totales = data['dinero_disponible'] + data['valor_maquinaria']
            data['activos_totales'] = activos_totales
            data['patrimonio_neto'] = activos_totales - data['total_deudas']
            data['costo_por_animal'] = costos_directos / data['cantidad_animales'] if data['cantidad_animales'] else 0
            data['margen_ganancia'] = (data['utilidad_bruta'] / data['total_ingresos']) * 100 if data['total_ingresos'] else 0
            data['razon_endeudamiento'] = data['total_deudas'] / activos_totales if activos_totales else 0
            data['productividad_por_trabajador'] = data['animales_actuales'] / data['trabajadores_necesarios'] if data['trabajadores_necesarios'] else 0
            data['gastos_totales'] = costos_directos


            # Crear carpeta del usuario si no existe
            user_folder = os.path.join('data', user_id)
            if not os.path.exists(user_folder):
                os.makedirs(user_folder)

            # Ruta del archivo CSV
            file_path = os.path.join(user_folder, 'datos_financieros_cerdos.csv')

            # Verificar si el archivo existe
            file_exists = os.path.isfile(file_path)

            # Guardar los datos en el archivo CSV
            with open(file_path, mode='a', newline='', encoding='utf-8') as file:
                writer = csv.DictWriter(file, fieldnames=data.keys())
                if not file_exists:
                    writer.writeheader()  # Escribir encabezado si el archivo no existe
                writer.writerow(data)  # Agregar los datos al archivo

            flash('Datos de cerdos guardados exitosamente.', 'success')
            return redirect(url_for('dashboard_cerdos'))

        except ValueError as e:
            flash(f'Error en los datos ingresados: {e}', 'danger')
            return redirect(url_for('pig_form'))
        except Exception as e:
            flash(f'Ocurrió un error inesperado: {e}', 'danger')
            return redirect(url_for('pig_form'))

    @app.route('/bovino_form', methods=['GET'])
    def bovino_form():
        user_id = session.get('user_id')
        if not user_id:
            flash('Por favor, inicia sesión para acceder al formulario.', 'danger')
            return redirect(url_for('login'))

        return render_template('bovino_form.html')

    # Ruta para guardar datos de ganado bovino
    @app.route('/submit_bovine_form', methods=['POST'])
    def submit_bovine_form():
        user_id = session.get('user_id')
        if not user_id:
            flash('Por favor, inicia sesión.', 'danger')
            return redirect(url_for('login'))

        try:
            # Función para limpiar y convertir valores numéricos
            def parse_float(value):
                return float(value.replace(',', '').strip()) if value else 0

            # Datos específicos del formulario de ganado bovino
            terreno_instalaciones = request.form.get('q17', '')
            if terreno_instalaciones == 'Other':
                terreno_instalaciones = f"Otro: {request.form.get('q17_other', '').strip()}"

            tipo_cubierta = request.form.get('q18', '')
            if tipo_cubierta == 'Other':
                tipo_cubierta = f"Otro: {request.form.get('q18_other', '').strip()}"

            lugar_venta = request.form.get('q19', '')
            if lugar_venta == 'Other':
                lugar_venta = f"Otro: {request.form.get('q19_other', '').strip()}"

            # Datos específicos del formulario de ganado bovino
            data = {
                # Sección 1: Ingresos y Gastos
                'total_ingresos': parse_float(request.form.get('q1', '0')),
                'cantidad_becerros': parse_float(request.form.get('q1_1', '0')),
                'animales_actuales': parse_float(request.form.get('q1_2', '0')),
                'peso_vivo_actual': parse_float(request.form.get('q1_3', '0')),
                'meses_engorda': parse_float(request.form.get('q2', '0')),
                'ciclos_anuales': parse_float(request.form.get('q3', '0')),
                'meses_intervalo': parse_float(request.form.get('q4', '0')),
                'gastos_alimento': parse_float(request.form.get('q5', '0')),
                'pago_mano_obra': parse_float(request.form.get('q6', '0')),
                'gastos_servicios': parse_float(request.form.get('q7', '0')),
                'valor_maquinaria': parse_float(request.form.get('q7_1', '0')),
                'perdidas_animales': parse_float(request.form.get('q8', '0')),
                'dinero_disponible': parse_float(request.form.get('q9', '0')),
                'gastos_imprevistos': parse_float(request.form.get('q10', '0')),
                'total_deudas': parse_float(request.form.get('q11', '0')),

                # Sección 2: Procesos Productivos
                'horas_preparacion_alimento': parse_float(request.form.get('q12', '0')),
                'dias_aplicacion_tratamientos': parse_float(request.form.get('q13', '0')),
                'horas_preparacion_venta': parse_float(request.form.get('q14', '0')),
                'trabajadores_necesarios': parse_float(request.form.get('q15', '0')),
                'horas_supervision_diarias': parse_float(request.form.get('q16', '0')),
                'terreno_instalaciones': terreno_instalaciones,
                'tipo_cubierta': tipo_cubierta,
                'lugar_venta': lugar_venta,
                'fecha_captura': request.form.get('fecha_captura', ''),
                'comentarios': request.form.get('comments', '')
            }

            # Validar datos obligatorios
            if not data['total_ingresos'] or not data['cantidad_becerros'] or not data['peso_vivo_actual']:
                flash('Por favor, completa todos los campos obligatorios.', 'danger')
                return redirect(url_for('bovino_form'))

            # Cálculos financieros
            costos_directos = (
                data['gastos_alimento'] +
                data['pago_mano_obra'] +
                data['gastos_servicios'] +
                data['gastos_imprevistos']
            )
            data['utilidad_bruta'] = data['total_ingresos'] - costos_directos
            data['utilidad_neta'] = data['utilidad_bruta'] - data['total_deudas']
            activos_totales = data['dinero_disponible'] + data['valor_maquinaria']
            data['activos_totales'] = activos_totales
            data['patrimonio_neto'] = activos_totales - data['total_deudas']
            data['costo_por_animal'] = costos_directos / data['cantidad_becerros'] if data['cantidad_becerros'] else 0
            data['margen_ganancia'] = (data['utilidad_bruta'] / data['total_ingresos']) * 100 if data['total_ingresos'] else 0
            data['razon_endeudamiento'] = data['total_deudas'] / activos_totales if activos_totales else 0
            data['productividad_por_trabajador'] = data['cantidad_becerros'] / data['trabajadores_necesarios'] if data['trabajadores_necesarios'] else 0
            data['gastos_totales'] = costos_directos

            # Crear carpeta del usuario si no existe
            user_folder = os.path.join('data', user_id)
            if not os.path.exists(user_folder):
                os.makedirs(user_folder)

            # Ruta del archivo CSV
            file_path = os.path.join(user_folder, 'datos_financieros_ganado.csv')

            # Verificar si el archivo existe
            file_exists = os.path.isfile(file_path)

            # Guardar los datos en el archivo CSV
            with open(file_path, mode='a', newline='', encoding='utf-8') as file:
                writer = csv.DictWriter(file, fieldnames=data.keys())
                if not file_exists:
                    writer.writeheader()  # Escribir encabezado si el archivo no existe
                writer.writerow(data)  # Agregar los datos al archivo

            flash('Datos de ganado bovino guardados exitosamente.', 'success')
            return redirect(url_for('dashboard_ganado'))

        except ValueError as e:
            flash(f'Error en los datos ingresados: {e}', 'danger')
            return redirect(url_for('bovino_form'))
        except Exception as e:
            flash(f'Ocurrió un error inesperado: {e}', 'danger')
            return redirect(url_for('bovino_form'))

    @app.route('/huevo_form', methods=['GET'])
    def huevo_form():
        user_id = session.get('user_id')
        if not user_id:
            flash('Por favor, inicia sesión para acceder al formulario.', 'danger')
            return redirect(url_for('login'))

        return render_template('huevo_form.html')


    # Ruta para guardar datos de huevos
    @app.route('/submit_eggs_form', methods=['POST'])
    def submit_eggs_form():
        user_id = session.get('user_id')
        if not user_id:
            flash('Por favor, inicia sesión.', 'danger')
            return redirect(url_for('login'))

        try:
            # Función para limpiar y convertir valores numéricos
            def parse_float(value):
                return float(value.replace(',', '').strip()) if value else 0

            # Datos específicos del formulario de huevos
            lugar_comercializacion = request.form.getlist('q14')
            if 'otro' in lugar_comercializacion:
                lugar_comercializacion.append(f"Otro: {request.form.get('q14_other', '').strip()}")

            data = {
                # Sección 1: Ingresos y Gastos
                'total_ingresos': parse_float(request.form.get('q1', '0')),
                'cantidad_aves': parse_float(request.form.get('q1_1', '0')),
                'porcentaje_produccion': parse_float(request.form.get('q1_2', '0')),
                'huevos_diarios': parse_float(request.form.get('q1_3', '0')),
                'precio_promedio_gallinas': parse_float(request.form.get('q1_4', '0')),  # Nuevo campo
                'gastos_alimento': parse_float(request.form.get('q2', '0')),
                'pago_mano_obra': parse_float(request.form.get('q3', '0')),
                'gastos_servicios': parse_float(request.form.get('q4', '0')),
                'dinero_disponible': parse_float(request.form.get('q5', '0')),
                'gastos_imprevistos': parse_float(request.form.get('q6', '0')),
                'total_deudas': parse_float(request.form.get('q7', '0')),
                'valor_maquinaria': parse_float(request.form.get('q7_1', '0')),  # Nuevo campo

                # Sección 2: Procesos Productivos
                'horas_preparacion_alimento': parse_float(request.form.get('q8', '0')),
                'horas_supervision': parse_float(request.form.get('q9', '0')),
                'dias_tratamientos': parse_float(request.form.get('q10', '0')),
                'tiempo_recoleccion': parse_float(request.form.get('q11', '0')),
                'trabajadores': parse_float(request.form.get('q12', '0')),
                'dias_inicio_produccion': parse_float(request.form.get('q13', '0')),
                'lugar_comercializacion': ', '.join(lugar_comercializacion),

                # Fecha de captura y comentarios
                'fecha_captura': request.form.get('fecha_captura', ''),
                'comentarios': request.form.get('comments', '')
            }

            # Validar datos obligatorios
            if not data['total_ingresos'] or not data['cantidad_aves'] or not data['huevos_diarios']:
                flash('Por favor, completa todos los campos obligatorios.', 'danger')
                return redirect(url_for('huevo_form'))

            # Cálculos financieros
            costos_directos = (
                data['gastos_alimento'] +
                data['pago_mano_obra'] +
                data['gastos_servicios'] +
                data['gastos_imprevistos']
            )
            valor_aves = data['cantidad_aves'] * data['precio_promedio_gallinas']  # Valor estimado de las aves
            activos_totales = data['dinero_disponible'] + data['valor_maquinaria'] + valor_aves  # Activos totales

            data['utilidad_bruta'] = data['total_ingresos'] - costos_directos
            data['utilidad_neta'] = data['utilidad_bruta'] - data['total_deudas']
            data['activos_totales'] = activos_totales
            data['patrimonio_neto'] = activos_totales - data['total_deudas']
            data['costo_por_huevo'] = costos_directos / (data['huevos_diarios'] * 30) if data['huevos_diarios'] else 0
            data['margen_ganancia'] = (data['utilidad_bruta'] / data['total_ingresos']) * 100 if data['total_ingresos'] else 0
            data['razon_endeudamiento'] = data['total_deudas'] / activos_totales if activos_totales else 0
            data['productividad_por_ave'] = (data['huevos_diarios'] / data['cantidad_aves']) if data['cantidad_aves'] else 0
            data['gastos_totales'] = costos_directos
            data['valor_aves'] = valor_aves  # Agregar el valor estimado de las aves

            # Crear carpeta del usuario si no existe
            user_folder = os.path.join('data', user_id)
            if not os.path.exists(user_folder):
                os.makedirs(user_folder)

            # Ruta del archivo CSV
            file_path = os.path.join(user_folder, 'datos_financieros_huevos.csv')

            # Verificar si el archivo existe
            file_exists = os.path.isfile(file_path)

            # Guardar los datos en el archivo CSV
            with open(file_path, mode='a', newline='', encoding='utf-8') as file:
                writer = csv.DictWriter(file, fieldnames=data.keys())
                if not file_exists:
                    writer.writeheader()  # Escribir encabezado si el archivo no existe
                writer.writerow(data)  # Agregar los datos al archivo

            flash('Datos de huevos guardados exitosamente.', 'success')
            return redirect(url_for('dashboard_huevos'))

        except ValueError as e:
            flash(f'Error en los datos ingresados: {e}', 'danger')
            return redirect(url_for('huevo_form'))
        except Exception as e:
            flash(f'Ocurrió un error inesperado: {e}', 'danger')
            return redirect(url_for('huevo_form'))


    @app.route('/maiz_form', methods=['GET'])
    def maiz_form():
        user_id = session.get('user_id')
        if not user_id:
            flash('Por favor, inicia sesión para acceder al formulario.', 'danger')
            return redirect(url_for('login'))

        return render_template('maiz_form.html')

    # Ruta para el dashboard de maíz
    @app.route('/dashboard_maiz')
    def dashboard_maiz():
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

        return render_template('dashboard_maiz.html', data=general_data)


    # Ruta para guardar datos de maíz
    @app.route('/submit_corn_form', methods=['POST'])
    def submit_corn_form():
        user_id = session.get('user_id')
        if not user_id:
            flash('Por favor, inicia sesión.', 'danger')
            return redirect(url_for('login'))

        try:
            # Función para limpiar y convertir valores numéricos
            def parse_float(value):
                return float(value.replace(',', '').strip()) if value else 0

            # Datos específicos del formulario de maíz
            lugar_comercializacion = request.form.get('q15', '')
            if lugar_comercializacion.lower() == 'otro':  # Verifica si se seleccionó "Otro"
                lugar_comercializacion = request.form.get('q15_other', '').strip()  # Toma el valor del campo de texto

            # Datos específicos del formulario de maíz
            data = {
                # Sección 1: Ingresos y Gastos
                'total_ingresos': parse_float(request.form.get('q1', '0')),
                'meses_cosecha': parse_float(request.form.get('q1_1', '0')),
                'variedad_maiz': request.form.get('q1_2', ''),
                'hectareas': parse_float(request.form.get('q1_3', '0')),
                'gastos_insumos': parse_float(request.form.get('q2', '0')),
                'pago_jornales': parse_float(request.form.get('q3', '0')),
                'gastos_servicios': parse_float(request.form.get('q4', '0')),
                'valor_maquinaria': parse_float(request.form.get('q5', '0')),
                'dinero_disponible': parse_float(request.form.get('q6', '0')),
                'gastos_imprevistos': parse_float(request.form.get('q7', '0')),
                'total_deudas': parse_float(request.form.get('q8', '0')),

                # Sección 2: Procesos Productivos
                'dias_preparacion_terreno': parse_float(request.form.get('q9', '0')),
                'dias_aplicacion_fertilizantes': parse_float(request.form.get('q10', '0')),
                'horas_cosecha_hectarea': parse_float(request.form.get('q11', '0')),
                'trabajadores_cosecha': parse_float(request.form.get('q12', '0')),
                'dias_secado_procesamiento': parse_float(request.form.get('q13', '0')),
                'dias_venta_semanal': parse_float(request.form.get('q14', '0')),
                'lugar_comercializacion': lugar_comercializacion,  # Incluye el valor procesado
                'porcentaje_autoconsumo': parse_float(request.form.get('q16', '0')),
                'horas_supervision_diaria': parse_float(request.form.get('q17', '0')),

                # Fecha de captura enviada desde el formulario
                'fecha_captura': request.form.get('fecha_captura', '')
            }

            # Validar datos obligatorios
            if not data['total_ingresos'] or not data['hectareas'] or not data['gastos_insumos']:
                flash('Por favor, completa todos los campos obligatorios.', 'danger')
                return redirect(url_for('maiz_form'))

            # Cálculos financieros
            costos_directos = (
                data['gastos_insumos'] +
                data['pago_jornales'] +
                data['gastos_servicios'] +
                data['gastos_imprevistos']
            )
            data['utilidad_bruta'] = data['total_ingresos'] - costos_directos
            data['utilidad_neta'] = data['utilidad_bruta'] - data['total_deudas']
            activos_totales = data['dinero_disponible'] + data['valor_maquinaria']
            data['activos_totales'] = activos_totales
            data['patrimonio_neto'] = activos_totales - data['total_deudas']
            data['costo_por_hectarea'] = costos_directos / data['hectareas'] if data['hectareas'] else 0
            data['margen_ganancia'] = (data['utilidad_bruta'] / data['total_ingresos']) * 100 if data['total_ingresos'] else 0
            data['razon_endeudamiento'] = data['total_deudas'] / activos_totales if activos_totales else 0
            data['productividad_por_hectarea'] = data['total_ingresos'] / data['hectareas'] if data['hectareas'] else 0
            data['gastos_totales'] = costos_directos

            # Crear carpeta del usuario si no existe
            user_folder = os.path.join('data', user_id)
            if not os.path.exists(user_folder):
                os.makedirs(user_folder)

            # Ruta del archivo CSV
            file_path = os.path.join(user_folder, 'datos_financieros_maiz.csv')

            # Verificar si el archivo existe
            file_exists = os.path.isfile(file_path)

            # Guardar los datos en el archivo CSV
            with open(file_path, mode='a', newline='', encoding='utf-8') as file:
                writer = csv.DictWriter(file, fieldnames=data.keys())
                if not file_exists:
                    writer.writeheader()  # Escribir encabezado si el archivo no existe
                writer.writerow(data)  # Agregar los datos al archivo

            flash('Datos de maíz guardados exitosamente.', 'success')
            return redirect(url_for('dashboard_maiz'))

        except ValueError as e:
            flash(f'Error en los datos ingresados: {e}', 'danger')
            return redirect(url_for('maiz_form'))
        except Exception as e:
            flash(f'Ocurrió un error inesperado: {e}', 'danger')
            return redirect(url_for('maiz_form'))


     # Ruta para el dashboard de café
    @app.route('/dashboard_cafe')
    def dashboard_cafe():
        user_id = session.get('user_id')
        if not user_id:
            flash('Por favor, inicia sesión para acceder al dashboard.', 'danger')
            return redirect(url_for('login'))

        # Leer datos generales desde el archivo CSV
        file_path = f'{user_id}_general_cafe.csv'
        general_data = {}
        if os.path.isfile(file_path):
            with open(file_path, mode='r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                general_data = next(reader, {})

        return render_template('dashboard_cafe.html', data=general_data)

    # Ruta para el dashboard de cerdos
    @app.route('/dashboard_cerdos')
    def dashboard_cerdos():
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

        return render_template('dashboard_cerdos.html', data=general_data)
    # Ruta para el dashboard de ganado
    @app.route('/dashboard_ganado')
    def dashboard_ganado():
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

        return render_template('dashboard_ganado.html', data=general_data)

    # Ruta para el dashboard de huevos
    @app.route('/dashboard_huevos')
    def dashboard_huevos():
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

        return render_template('dashboard_huevos.html', data=general_data)



    # Ruta para acceder a los datos financieros de café
    @app.route('/database_access_cafe', methods=['GET'])
    def database_access_cafe():
        user_id = session.get('user_id')
        if not user_id:
            flash('Por favor, inicia sesión para acceder a la base de datos.', 'danger')
            return redirect(url_for('login'))

        # Ruta del archivo CSV
        user_folder = os.path.join('data', user_id)
        file_path = os.path.join(user_folder, 'datos_financieros_cafe.csv')

        data = []
        rubros = [
            {'key': 'total_ingresos', 'label': 'Total de Ingresos'},
            {'key': 'produccion_total', 'label': 'Producción Total'},
            {'key': 'hectareas', 'label': 'Hectáreas'},
            {'key': 'gastos_insumos', 'label': 'Gastos en Insumos'},
            {'key': 'pago_jornales', 'label': 'Pago de Jornales'},
            {'key': 'gastos_servicios', 'label': 'Gastos en Servicios'},
            {'key': 'valor_maquinaria', 'label': 'Valor de Maquinaria'},
            {'key': 'dinero_disponible', 'label': 'Dinero Disponible'},
            {'key': 'gastos_imprevistos', 'label': 'Gastos Imprevistos'},
            {'key': 'total_deudas', 'label': 'Total de Deudas'},
            {'key': 'dias_trabajo', 'label': 'Días de Trabajo'},
            {'key': 'trabajadores', 'label': 'Trabajadores'},
            {'key': 'horas_venta', 'label': 'Horas de Venta'},
            {'key': 'horas_supervision', 'label': 'Horas de Supervisión'},
            {'key': 'lugar_comercializacion', 'label': 'Lugar de Comercialización'},
            {'key': 'comentarios', 'label': 'Comentarios'}
        ]

        if os.path.isfile(file_path):
            with open(file_path, mode='r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                data = list(reader)

        # Ordenar las fechas de captura en orden descendente
        fechas = sorted({row['fecha_captura'] for row in data}, reverse=True)

        return render_template('database_access_cafe.html', data=data, rubros=rubros, fechas=fechas)

    # Ruta para acceder a los datos financieros de cerdos
    @app.route('/database_access_cerdos', methods=['GET'])
    def database_access_cerdos():
        user_id = session.get('user_id')
        if not user_id:
            flash('Por favor, inicia sesión para acceder a la base de datos.', 'danger')
            return redirect(url_for('login'))

        # Ruta del archivo CSV
        file_path = f"data/{user_id}/datos_financieros_cerdos.csv"
        financial_data = []
        rubros = [
            {'key': 'total_ingresos', 'label': 'Total de Ingresos'},
            {'key': 'cantidad_animales', 'label': 'Cantidad de Animales'},
            {'key': 'peso_promedio', 'label': 'Peso Promedio (kg)'},
            {'key': 'ciclos_anuales', 'label': 'Ciclos Anuales'},
            {'key': 'duracion_ciclo', 'label': 'Duración del Ciclo (meses)'},
            {'key': 'animales_actuales', 'label': 'Animales Actuales en Engorda'},
            {'key': 'peso_promedio_actual', 'label': 'Peso Promedio Actual (kg)'},
            {'key': 'gastos_alimento', 'label': 'Gastos en Alimento'},
            {'key': 'pago_mano_obra', 'label': 'Pago de Mano de Obra'},
            {'key': 'gastos_servicios', 'label': 'Gastos en Servicios'},
            {'key': 'gastos_veterinario', 'label': 'Gastos en Veterinario y Medicamentos'},
            {'key': 'meses_engorda', 'label': 'Meses de Engorda'},
            {'key': 'perdidas_animales', 'label': 'Pérdidas de Animales'},
            {'key': 'dinero_disponible', 'label': 'Dinero Disponible'},
            {'key': 'gastos_imprevistos', 'label': 'Gastos Imprevistos'},
            {'key': 'total_deudas', 'label': 'Total de Deudas'},
            {'key': 'horas_supervision', 'label': 'Horas de Supervisión Diaria'},
            {'key': 'dias_tratamientos', 'label': 'Días entre Tratamientos'},
            {'key': 'horas_preparacion_venta', 'label': 'Horas de Preparación para la Venta'},
            {'key': 'trabajadores_necesarios', 'label': 'Trabajadores Necesarios'},
            {'key': 'lugar_comercializacion', 'label': 'Lugar de Comercialización'},
            {'key': 'fecha_captura', 'label': 'Fecha de Captura'},
            {'key': 'comentarios', 'label': 'Comentarios'},
            {'key': 'utilidad_bruta', 'label': 'Utilidad Bruta'},
            {'key': 'utilidad_neta', 'label': 'Utilidad Neta'},
            {'key': 'activos_totales', 'label': 'Activos Totales'},
            {'key': 'patrimonio_neto', 'label': 'Patrimonio Neto'},
            {'key': 'costo_por_animal', 'label': 'Costo por Animal'},
            {'key': 'margen_ganancia', 'label': 'Margen de Ganancia (%)'},
            {'key': 'razon_endeudamiento', 'label': 'Razón de Endeudamiento'},
            {'key': 'productividad_por_trabajador', 'label': 'Productividad por Trabajador'},
            {'key': 'gastos_totales', 'label': 'Gastos Totales'}
        ]

        if os.path.isfile(file_path):
            with open(file_path, mode='r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                financial_data = list(reader)

        # Ordenar las fechas de captura en orden descendente
        fechas = sorted({row['fecha_captura'] for row in financial_data}, reverse=True)

        return render_template('database_access_cerdos.html', data=financial_data, rubros=rubros, fechas=fechas)

    # Ruta para acceder a los datos financieros de ganado
    @app.route('/database_access_ganado')
    def database_access_ganado():
        user_id = session.get('user_id')
        if not user_id:
            flash('Por favor, inicia sesión para acceder a la base de datos.', 'danger')
            return redirect(url_for('login'))

        # Leer datos financieros desde el archivo CSV
        file_path = f'data/{user_id}/datos_financieros_ganado.csv'
        financial_data = []
        rubros = [
            {'key': 'total_ingresos', 'label': 'Total de Ingresos'},
            {'key': 'cantidad_becerros', 'label': 'Cantidad de Becerros'},
            {'key': 'animales_actuales', 'label': 'Animales Actuales en Engorda'},
            {'key': 'peso_vivo_actual', 'label': 'Peso Vivo Promedio (kg)'},
            {'key': 'meses_engorda', 'label': 'Meses de Engorda'},
            {'key': 'ciclos_anuales', 'label': 'Ciclos Anuales'},
            {'key': 'meses_intervalo', 'label': 'Meses de Intervalo'},
            {'key': 'gastos_alimento', 'label': 'Gastos en Alimento'},
            {'key': 'pago_mano_obra', 'label': 'Pago de Mano de Obra'},
            {'key': 'gastos_servicios', 'label': 'Gastos en Servicios'},
            {'key': 'valor_maquinaria', 'label': 'Valor de Maquinaria y Equipo'},  # Nuevo rubro
            {'key': 'perdidas_animales', 'label': 'Pérdidas de Animales'},
            {'key': 'dinero_disponible', 'label': 'Dinero Disponible'},
            {'key': 'gastos_imprevistos', 'label': 'Gastos Imprevistos'},
            {'key': 'total_deudas', 'label': 'Total de Deudas'},
            {'key': 'fecha_captura', 'label': 'Fecha de Captura'}
        ]

        if os.path.isfile(file_path):
            with open(file_path, mode='r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                financial_data = list(reader)

        return render_template('database_access_ganado.html', data=financial_data, rubros=rubros)

     # Ruta para acceder a los datos financieros de maíz
    @app.route('/database_access_maiz', methods=['GET'])
    def database_access_maiz():
        user_id = session.get('user_id')
        if not user_id:
            flash('Por favor, inicia sesión para acceder a la base de datos.', 'danger')
            return redirect(url_for('login'))

        # Ruta del archivo CSV
        file_path = f"data/{user_id}/datos_financieros_maiz.csv"
        financial_data = []
        rubros = [
            {'key': 'total_ingresos', 'label': 'Total de Ingresos'},
            {'key': 'meses_cosecha', 'label': 'Meses de Cosecha'},
            {'key': 'variedad_maiz', 'label': 'Variedad de Maíz'},
            {'key': 'hectareas', 'label': 'Hectáreas Sembradas'},
            {'key': 'gastos_insumos', 'label': 'Gastos en Insumos'},
            {'key': 'pago_jornales', 'label': 'Pago de Jornales'},
            {'key': 'gastos_servicios', 'label': 'Gastos en Servicios'},
            {'key': 'valor_maquinaria', 'label': 'Valor de Maquinaria'},
            {'key': 'dinero_disponible', 'label': 'Dinero Disponible'},
            {'key': 'gastos_imprevistos', 'label': 'Gastos Imprevistos'},
            {'key': 'total_deudas', 'label': 'Total de Deudas'},
            {'key': 'dias_preparacion_terreno', 'label': 'Días de Preparación del Terreno'},
            {'key': 'dias_aplicacion_fertilizantes', 'label': 'Días de Aplicación de Fertilizantes'},
            {'key': 'horas_cosecha_hectarea', 'label': 'Horas de Cosecha por Hectárea'},
            {'key': 'trabajadores_cosecha', 'label': 'Trabajadores en la Cosecha'},
            {'key': 'dias_secado_procesamiento', 'label': 'Días de Secado o Procesamiento'},
            {'key': 'dias_venta_semanal', 'label': 'Días de Venta Semanal'},
            {'key': 'lugar_comercializacion', 'label': 'Lugar de Comercialización'},
            {'key': 'porcentaje_autoconsumo', 'label': 'Porcentaje de Autoconsumo'},
            {'key': 'horas_supervision_diaria', 'label': 'Horas de Supervisión Diaria'},
            {'key': 'fecha_captura', 'label': 'Fecha de Captura'},
            {'key': 'utilidad_bruta', 'label': 'Utilidad Bruta'},
            {'key': 'utilidad_neta', 'label': 'Utilidad Neta'},
            {'key': 'activos_totales', 'label': 'Activos Totales'},
            {'key': 'patrimonio_neto', 'label': 'Patrimonio Neto'},
            {'key': 'costo_por_hectarea', 'label': 'Costo por Hectárea'},
            {'key': 'margen_ganancia', 'label': 'Margen de Ganancia (%)'},
            {'key': 'razon_endeudamiento', 'label': 'Razón de Endeudamiento'},
            {'key': 'productividad_por_hectarea', 'label': 'Productividad por Hectárea'},
            {'key': 'gastos_totales', 'label': 'Gastos Totales'}
        ]

        if os.path.isfile(file_path):
            with open(file_path, mode='r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                financial_data = list(reader)

        # Ordenar las fechas de captura en orden descendente
        fechas = sorted({row['fecha_captura'] for row in financial_data}, reverse=True)

        return render_template('database_access_maiz.html', data=financial_data, rubros=rubros, fechas=fechas)




    # Ruta para acceder a los datos financieros de huevos
    @app.route('/database_access_huevos', methods=['GET'])
    def database_access_huevos():
        user_id = session.get('user_id')
        if not user_id:
            flash('Por favor, inicia sesión para acceder a la base de datos.', 'danger')
            return redirect(url_for('login'))

        # Ruta del archivo CSV
        user_folder = os.path.join('data', user_id)
        file_path = os.path.join(user_folder, 'datos_financieros_huevos.csv')

        data = []
        fechas = []
        rubros = [
            {'key': 'total_ingresos', 'label': 'Total Ingresos'},
            {'key': 'cantidad_aves', 'label': 'Cantidad de Aves'},
            {'key': 'porcentaje_produccion', 'label': 'Porcentaje de Producción'},
            {'key': 'huevos_diarios', 'label': 'Huevos Diarios'},
            {'key': 'precio_promedio_gallinas', 'label': 'Precio Promedio Gallinas'},
            {'key': 'gastos_alimento', 'label': 'Gastos en Alimento'},
            {'key': 'pago_mano_obra', 'label': 'Pago de Mano de Obra'},
            {'key': 'gastos_servicios', 'label': 'Gastos en Servicios'},
            {'key': 'dinero_disponible', 'label': 'Dinero Disponible'},
            {'key': 'gastos_imprevistos', 'label': 'Gastos Imprevistos'},
            {'key': 'total_deudas', 'label': 'Total Deudas'},
            {'key': 'valor_maquinaria', 'label': 'Valor de Maquinaria'},
            {'key': 'horas_preparacion_alimento', 'label': 'Horas de Preparación de Alimento'},
            {'key': 'horas_supervision', 'label': 'Horas de Supervisión'},
            {'key': 'dias_tratamientos', 'label': 'Días de Tratamientos'},
            {'key': 'tiempo_recoleccion', 'label': 'Tiempo de Recolección'},
            {'key': 'trabajadores', 'label': 'Trabajadores'},
            {'key': 'dias_inicio_produccion', 'label': 'Días para Inicio de Producción'},
            {'key': 'lugar_comercializacion', 'label': 'Lugar de Comercialización'},
            {'key': 'fecha_captura', 'label': 'Fecha de Captura'},
            {'key': 'comentarios', 'label': 'Comentarios'},
            {'key': 'utilidad_bruta', 'label': 'Utilidad Bruta'},
            {'key': 'utilidad_neta', 'label': 'Utilidad Neta'},
            {'key': 'activos_totales', 'label': 'Activos Totales'},
            {'key': 'patrimonio_neto', 'label': 'Patrimonio Neto'},
            {'key': 'costo_por_huevo', 'label': 'Costo por Huevo'},
            {'key': 'margen_ganancia', 'label': 'Margen de Ganancia'},
            {'key': 'razon_endeudamiento', 'label': 'Razón de Endeudamiento'},
            {'key': 'productividad_por_ave', 'label': 'Productividad por Ave'},
            {'key': 'gastos_totales', 'label': 'Gastos Totales'},
            {'key': 'valor_aves', 'label': 'Valor de las Aves'}
        ]

        if os.path.isfile(file_path):
            with open(file_path, mode='r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                data = list(reader)
                fechas = sorted({row['fecha_captura'] for row in data}, reverse=True)

        return render_template('database_access_huevos.html', data=data, fechas=fechas, rubros=rubros)

        # Ruta para generar estados financieros de café
    @app.route('/financial_statements_cafe', methods=['GET', 'POST'])
    def financial_statements_cafe():
        user_id = session.get('user_id')
        if not user_id:
            flash('Por favor, inicia sesión para acceder a los estados financieros.', 'danger')
            return redirect(url_for('login'))

        # Ruta del archivo CSV
        user_folder = os.path.join('data', user_id)
        file_path = os.path.join(user_folder, 'datos_financieros_cafe.csv')

        financial_data = []
        selected_date = None

        if os.path.isfile(file_path):
            with open(file_path, mode='r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                financial_data = list(reader)

        # Ordenar las fechas de captura en orden descendente
        fechas_disponibles = sorted([row['fecha_captura'] for row in financial_data], reverse=True)

        # Si no se envía una fecha desde el formulario, usar la fecha más reciente
        if request.method == 'POST':
            selected_date = request.form.get('fecha_captura')
        elif fechas_disponibles:
            selected_date = fechas_disponibles[0]  # Fecha más reciente

        # Filtrar los datos por la fecha seleccionada
        filtered_data = [row for row in financial_data if row['fecha_captura'] == selected_date]

        # Calcular estados financieros y razones financieras
        if filtered_data:
            data = filtered_data[0]  # Tomar el primer registro filtrado

            # Calcular costos directos
            costos_directos = float(data['gastos_insumos']) + float(data['pago_jornales']) + float(data['gastos_servicios']) + float(data['gastos_imprevistos'])
            utilidad_bruta = float(data['total_ingresos']) - costos_directos
            utilidad_neta = utilidad_bruta
            activos_totales = float(data['dinero_disponible']) + float(data['valor_maquinaria'])
            patrimonio_neto = activos_totales - float(data['total_deudas'])
            total_gastos = costos_directos
            margen_ganancia = (utilidad_bruta / float(data['total_ingresos'])) * 100 if float(data['total_ingresos']) else 0
            razon_endeudamiento = float(data['total_deudas']) / activos_totales if activos_totales else 0

            # Calcular productividad por hectárea
            productividad_por_hectarea = float(data['produccion_total']) / float(data['hectareas']) if float(data['hectareas']) > 0 else 0

            # Calcular costo por unidad
            costo_por_unidad = costos_directos / float(data['produccion_total']) if float(data['produccion_total']) > 0 else 0

            # Calcular Capital más Pasivo
            capital_mas_pasivo = patrimonio_neto + float(data['total_deudas'])

            # Valores de referencia para razones financieras
            referencias = {
                'margen_ganancia': 'Mayor al 20% es favorable',
                'razon_endeudamiento': 'Menor al 50% es favorable'
            }

            # Agregar datos de referencia
            datos_referencia = {
                'produccion_total': float(data['produccion_total']),
                'unidad_produccion': data['unidad_produccion'],
                'hectareas': float(data['hectareas']),
                'trabajadores': float(data['trabajadores']),
                'lugar_comercializacion': data['lugar_comercializacion']
            }

            # Generar interpretación AI
            interpretacion_ai = []

            if float(data['total_ingresos']) > total_gastos:
                interpretacion_ai.append("Los ingresos son mayores que los gastos, lo cual es positivo.")
            else:
                interpretacion_ai.append("Los gastos superan los ingresos, lo que indica posibles pérdidas.")

            if margen_ganancia >= 20:
                interpretacion_ai.append(f"El margen de ganancia es del {margen_ganancia:.2f}%, lo cual es favorable.")
            else:
                interpretacion_ai.append(f"El margen de ganancia es del {margen_ganancia:.2f}%, podría mejorar.")

            if razon_endeudamiento < 0.5:
                interpretacion_ai.append(f"La razón de endeudamiento es del {razon_endeudamiento:.2%}, lo cual es manejable.")
            else:
                interpretacion_ai.append(f"La razón de endeudamiento es del {razon_endeudamiento:.2%}, se recomienda reducir deudas.")

            interpretacion_ai.append(f"La productividad por hectárea es de {productividad_por_hectarea:.2f} unidades.")
            interpretacion_ai.append(f"El costo por unidad producida es de ${costo_por_unidad:.2f}.")

            # Convertir lista a string
            interpretacion_ai = " ".join(interpretacion_ai)

            # Preparar datos para el HTML
            financial_summary = {
                'activos': {
                    'maquinaria_equipo': float(data['valor_maquinaria']),
                    'dinero_disponible': float(data['dinero_disponible']),
                    'total_activos': activos_totales
                },
                'pasivos': {
                    'deudas': float(data['total_deudas']),
                    'total_pasivos': float(data['total_deudas'])
                },
                'patrimonio': patrimonio_neto,
                'capital_mas_pasivo': capital_mas_pasivo,  # Agregar Capital más Pasivo
                'ingresos': {
                    'venta_cafe': float(data['total_ingresos'])
                },
                'gastos': {
                    'insumos': float(data['gastos_insumos']),
                    'jornales': float(data['pago_jornales']),
                    'servicios': float(data['gastos_servicios']),
                    'imprevistos': float(data['gastos_imprevistos']),
                    'total_gastos': total_gastos
                },
                'utilidad_neta': utilidad_neta,
                'razones_financieras': {
                    'margen_ganancia': margen_ganancia,
                    'razon_endeudamiento': razon_endeudamiento,
                    'productividad_por_hectarea': productividad_por_hectarea,
                    'costo_por_unidad': costo_por_unidad
                },
                'referencias': referencias,
                'datos_referencia': datos_referencia,
                'fecha_captura': selected_date,
                'interpretacion_ai': interpretacion_ai
            }
        else:
            financial_summary = None

        return render_template('financial_statements_cafe.html', data=financial_summary, fechas=fechas_disponibles)

    @app.route('/financial_statements_cerdos', methods=['GET', 'POST'])
    def financial_statements_cerdos():
        user_id = session.get('user_id')
        if not user_id:
            flash('Por favor, inicia sesión para acceder a los estados financieros.', 'danger')
            return redirect(url_for('login'))

        # Ruta del archivo CSV
        user_folder = os.path.join('data', user_id)
        file_path = os.path.join(user_folder, 'datos_financieros_cerdos.csv')

        financial_data = []
        selected_date = None

        if os.path.isfile(file_path):
            with open(file_path, mode='r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                financial_data = list(reader)

        # Ordenar las fechas de captura en orden descendente
        fechas_disponibles = sorted([row['fecha_captura'] for row in financial_data], reverse=True)

        # Si no se envía una fecha desde el formulario, usar la fecha más reciente
        if request.method == 'POST':
            selected_date = request.form.get('fecha_captura')
        elif fechas_disponibles:
            selected_date = fechas_disponibles[0]  # Fecha más reciente

        # Filtrar los datos por la fecha seleccionada
        filtered_data = [row for row in financial_data if row['fecha_captura'] == selected_date]

        # Calcular estados financieros y razones financieras
        if filtered_data:
            data = filtered_data[0]  # Tomar el primer registro filtrado

            # Calcular costos directos
            costos_directos = (
                float(data['gastos_alimento']) +
                float(data['pago_mano_obra']) +
                float(data['gastos_servicios']) +
                float(data['gastos_veterinario']) +
                float(data['gastos_imprevistos'])
            )
            utilidad_bruta = float(data['total_ingresos']) - costos_directos
            utilidad_neta = utilidad_bruta
            activos_totales = float(data['dinero_disponible']) + float(data['valor_maquinaria'])
            patrimonio_neto = activos_totales - float(data['total_deudas'])
            total_gastos = costos_directos
            margen_ganancia = (utilidad_bruta / float(data['total_ingresos'])) * 100 if float(data['total_ingresos']) else 0
            razon_endeudamiento = float(data['total_deudas']) / activos_totales if activos_totales else 0

            # Calcular productividad por trabajador
            productividad_por_trabajador = float(data['animales_actuales']) / float(data['trabajadores_necesarios']) if float(data['trabajadores_necesarios']) > 0 else 0

            # Calcular costo por animal
            costo_por_animal = costos_directos / float(data['cantidad_animales']) if float(data['cantidad_animales']) > 0 else 0

            # Estimación del valor por kilo de carne
            valor_por_kilo = float(data['total_ingresos']) / (float(data['cantidad_animales']) * float(data['peso_promedio'])) if float(data['cantidad_animales']) > 0 else 0

            # Estimación del valor de los animales actuales en engorda
            valor_animales_actuales = float(data['animales_actuales']) * float(data['peso_promedio_actual']) * valor_por_kilo

            # Agregar el valor estimado de los animales actuales como activo
            activos_totales += valor_animales_actuales
            patrimonio_neto += valor_animales_actuales

            # Calcular Capital más Pasivo
            capital_mas_pasivo = patrimonio_neto + float(data['total_deudas'])

            # Valores de referencia para razones financieras
            referencias = {
                'margen_ganancia': 'Mayor al 20% es favorable',
                'razon_endeudamiento': 'Menor al 50% es favorable'
            }

            # Agregar datos de referencia
            datos_referencia = {
                'cantidad_animales': float(data['cantidad_animales']),
                'peso_promedio': float(data['peso_promedio']),
                'animales_actuales': float(data['animales_actuales']),
                'peso_promedio_actual': float(data['peso_promedio_actual']),
                'lugar_comercializacion': data['lugar_comercializacion'],
                'valor_maquinaria': float(data['valor_maquinaria'])
            }

            # Generar interpretación AI
            interpretacion_ai = []

            if float(data['total_ingresos']) > total_gastos:
                interpretacion_ai.append("Los ingresos son mayores que los gastos, lo cual es positivo.")
            else:
                interpretacion_ai.append("Los gastos superan los ingresos, lo que indica posibles pérdidas.")

            if margen_ganancia >= 20:
                interpretacion_ai.append(f"El margen de ganancia es del {margen_ganancia:.2f}%, lo cual es favorable.")
            else:
                interpretacion_ai.append(f"El margen de ganancia es del {margen_ganancia:.2f}%, podría mejorar.")

            if razon_endeudamiento < 0.5:
                interpretacion_ai.append(f"La razón de endeudamiento es del {razon_endeudamiento:.2%}, lo cual es manejable.")
            else:
                interpretacion_ai.append(f"La razón de endeudamiento es del {razon_endeudamiento:.2%}, se recomienda reducir deudas.")

            interpretacion_ai.append(f"El valor estimado por kilo de carne es de ${valor_por_kilo:.2f}.")
            interpretacion_ai.append(f"El valor aproximado de los animales actuales en engorda es de ${valor_animales_actuales:,.2f}.")

            # Convertir lista a string
            interpretacion_ai = " ".join(interpretacion_ai)

            # Preparar datos para el HTML
            financial_summary = {
                'activos': {
                    'maquinaria_equipo': float(data['valor_maquinaria']),
                    'dinero_disponible': float(data['dinero_disponible']),
                    'valor_animales_actuales': valor_animales_actuales,
                    'total_activos': activos_totales
                },
                'pasivos': {
                    'deudas': float(data['total_deudas']),
                    'total_pasivos': float(data['total_deudas'])
                },
                'patrimonio': patrimonio_neto,
                'capital_mas_pasivo': capital_mas_pasivo,
                'ingresos': {
                    'venta_cerdos': float(data['total_ingresos'])
                },
                'gastos': {
                    'alimento': float(data['gastos_alimento']),
                    'mano_obra': float(data['pago_mano_obra']),
                    'servicios': float(data['gastos_servicios']),
                    'veterinario': float(data['gastos_veterinario']),
                    'imprevistos': float(data['gastos_imprevistos']),
                    'total_gastos': total_gastos
                },
                'utilidad_neta': utilidad_neta,
                'razones_financieras': {
                    'margen_ganancia': margen_ganancia,
                    'razon_endeudamiento': razon_endeudamiento,
                    'productividad_por_trabajador': productividad_por_trabajador,
                    'costo_por_animal': costo_por_animal
                },
                'referencias': referencias,
                'datos_referencia': datos_referencia,
                'fecha_captura': selected_date,
                'interpretacion_ai': interpretacion_ai
            }
        else:
            financial_summary = None

        return render_template('financial_statements_cerdos.html', data=financial_summary, fechas=fechas_disponibles)


    # Ruta para generar estados financieros de ganado
    @app.route('/financial_statements_ganado', methods=['GET', 'POST'])
    def financial_statements_ganado():
        user_id = session.get('user_id')
        if not user_id:
            flash('Por favor, inicia sesión para acceder a los estados financieros.', 'danger')
            return redirect(url_for('login'))

        # Ruta del archivo CSV
        user_folder = os.path.join('data', user_id)
        file_path = os.path.join(user_folder, 'datos_financieros_ganado.csv')

        financial_data = []
        selected_date = None

        if os.path.isfile(file_path):
            with open(file_path, mode='r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                financial_data = list(reader)

        # Ordenar las fechas de captura en orden descendente
        fechas_disponibles = sorted([row['fecha_captura'] for row in financial_data], reverse=True)

        # Si no se envía una fecha desde el formulario, usar la fecha más reciente
        if request.method == 'POST':
            selected_date = request.form.get('fecha_captura')
        elif fechas_disponibles:
            selected_date = fechas_disponibles[0]  # Fecha más reciente

        # Filtrar los datos por la fecha seleccionada
        filtered_data = [row for row in financial_data if row['fecha_captura'] == selected_date]

        # Calcular estados financieros y razones financieras
        if filtered_data:
            data = filtered_data[0]  # Tomar el primer registro filtrado

            # Calcular costos directos
            costos_directos = (
                float(data['gastos_alimento']) +
                float(data['pago_mano_obra']) +
                float(data['gastos_servicios']) +
                float(data['gastos_imprevistos'])
            )
            utilidad_bruta = float(data['total_ingresos']) - costos_directos
            utilidad_neta = utilidad_bruta
            activos_totales = float(data['dinero_disponible']) + float(data['valor_maquinaria'])
            patrimonio_neto = activos_totales - float(data['total_deudas'])
            total_gastos = costos_directos
            margen_ganancia = (utilidad_bruta / float(data['total_ingresos'])) * 100 if float(data['total_ingresos']) else 0
            razon_endeudamiento = float(data['total_deudas']) / activos_totales if activos_totales else 0

            # Calcular productividad por trabajador
            productividad_por_trabajador = float(data['cantidad_becerros']) / float(data['trabajadores_necesarios']) if float(data['trabajadores_necesarios']) > 0 else 0

            # Calcular costo por animal
            costo_por_animal = costos_directos / float(data['cantidad_becerros']) if float(data['cantidad_becerros']) > 0 else 0

            # Estimación del valor por kilo de carne
            valor_por_kilo = float(data['total_ingresos']) / (float(data['cantidad_becerros']) * float(data['peso_vivo_actual'])) if float(data['cantidad_becerros']) > 0 else 0

            # Estimación del valor de los animales actuales en engorda
            valor_animales_actuales = float(data['animales_actuales']) * float(data['peso_vivo_actual']) * valor_por_kilo

            # Agregar el valor estimado de los animales actuales como activo
            activos_totales += valor_animales_actuales
            patrimonio_neto += valor_animales_actuales

            # Calcular Capital más Pasivo
            capital_mas_pasivo = patrimonio_neto + float(data['total_deudas'])

            # Valores de referencia para razones financieras
            referencias = {
                'margen_ganancia': 'Mayor al 20% es favorable',
                'razon_endeudamiento': 'Menor al 50% es favorable'
            }

            # Agregar datos de referencia
            datos_referencia = {
                'cantidad_becerros': float(data['cantidad_becerros']),
                'peso_vivo_actual': float(data['peso_vivo_actual']),
                'animales_actuales': float(data['animales_actuales']),
                'valor_maquinaria': float(data['valor_maquinaria']),  # Nuevo análisis de maquinaria
                'lugar_venta': data['lugar_venta']
            }

            # Generar interpretación AI
            interpretacion_ai = []

            if float(data['total_ingresos']) > total_gastos:
                interpretacion_ai.append("Los ingresos son mayores que los gastos, lo cual es positivo.")
            else:
                interpretacion_ai.append("Los gastos superan los ingresos, lo que indica posibles pérdidas.")

            if margen_ganancia >= 20:
                interpretacion_ai.append(f"El margen de ganancia es del {margen_ganancia:.2f}%, lo cual es favorable.")
            else:
                interpretacion_ai.append(f"El margen de ganancia es del {margen_ganancia:.2f}%, podría mejorar.")

            if razon_endeudamiento < 0.5:
                interpretacion_ai.append(f"La razón de endeudamiento es del {razon_endeudamiento:.2%}, lo cual es manejable.")
            else:
                interpretacion_ai.append(f"La razón de endeudamiento es del {razon_endeudamiento:.2%}, se recomienda reducir deudas.")

            interpretacion_ai.append(f"El valor estimado por kilo de carne es de ${valor_por_kilo:.2f}.")
            interpretacion_ai.append(f"El valor aproximado de los animales actuales en engorda es de ${valor_animales_actuales:,.2f}.")
            interpretacion_ai.append(f"El valor de la maquinaria y equipo es de ${float(data['valor_maquinaria']):,.2f}.")  # Nuevo análisis

            # Convertir lista a string
            interpretacion_ai = " ".join(interpretacion_ai)

            # Preparar datos para el HTML
            financial_summary = {
                'activos': {
                    'dinero_disponible': float(data['dinero_disponible']),
                    'valor_maquinaria': float(data['valor_maquinaria']),  # Agregar maquinaria a los activos
                    'valor_animales_actuales': valor_animales_actuales,
                    'total_activos': activos_totales
                },
                'pasivos': {
                    'deudas': float(data['total_deudas']),
                    'total_pasivos': float(data['total_deudas'])
                },
                'patrimonio': patrimonio_neto,
                'capital_mas_pasivo': capital_mas_pasivo,
                'ingresos': {
                    'venta_ganado': float(data['total_ingresos'])
                },
                'gastos': {
                    'alimento': float(data['gastos_alimento']),
                    'mano_obra': float(data['pago_mano_obra']),
                    'servicios': float(data['gastos_servicios']),
                    'imprevistos': float(data['gastos_imprevistos']),
                    'total_gastos': total_gastos
                },
                'utilidad_neta': utilidad_neta,
                'razones_financieras': {
                    'margen_ganancia': margen_ganancia,
                    'razon_endeudamiento': razon_endeudamiento,
                    'productividad_por_trabajador': productividad_por_trabajador,
                    'costo_por_animal': costo_por_animal
                },
                'referencias': referencias,
                'datos_referencia': datos_referencia,
                'fecha_captura': selected_date,
                'interpretacion_ai': interpretacion_ai
            }
        else:
            financial_summary = None

        return render_template('financial_statements_ganado.html', data=financial_summary, fechas=fechas_disponibles)

    # Ruta para generar estados financieros de huevos
    @app.route('/financial_statements_huevos', methods=['GET', 'POST'])
    def financial_statements_huevos():
        user_id = session.get('user_id')
        if not user_id:
            flash('Por favor, inicia sesión para acceder a los estados financieros.', 'danger')
            return redirect(url_for('login'))

        # Ruta del archivo CSV
        user_folder = os.path.join('data', user_id)
        file_path = os.path.join(user_folder, 'datos_financieros_huevos.csv')

        financial_data = []
        selected_date = None

        if os.path.isfile(file_path):
            with open(file_path, mode='r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                financial_data = list(reader)

        # Ordenar las fechas de captura en orden descendente
        fechas_disponibles = sorted([row['fecha_captura'] for row in financial_data], reverse=True)

        # Si no se envía una fecha desde el formulario, usar la fecha más reciente
        if request.method == 'POST':
            selected_date = request.form.get('fecha_captura')
        elif fechas_disponibles:
            selected_date = fechas_disponibles[0]  # Fecha más reciente

        # Filtrar los datos por la fecha seleccionada
        filtered_data = [row for row in financial_data if row['fecha_captura'] == selected_date]

        # Calcular estados financieros y razones financieras
        if filtered_data:
            data = filtered_data[0]  # Tomar el primer registro filtrado

            # Calcular costos directos
            costos_directos = (
                float(data['gastos_alimento']) +
                float(data['pago_mano_obra']) +
                float(data['gastos_servicios']) +
                float(data['gastos_imprevistos'])
            )
            utilidad_bruta = float(data['total_ingresos']) - costos_directos
            utilidad_neta = utilidad_bruta - float(data['total_deudas'])

            # Calcular activos
            valor_maquinaria = float(data.get('valor_maquinaria', 0))  # Valor de maquinaria y equipo
            valor_aves = float(data.get('cantidad_aves', 0)) * float(data.get('precio_promedio_gallinas', 0))  # Cantidad de aves * precio promedio por ave
            activos_totales = float(data['dinero_disponible']) + valor_maquinaria + valor_aves
            patrimonio_neto = activos_totales - float(data['total_deudas'])

            # Calcular razones financieras
            margen_ganancia = (utilidad_bruta / float(data['total_ingresos'])) * 100 if float(data['total_ingresos']) else 0
            razon_endeudamiento = float(data['total_deudas']) / activos_totales if activos_totales else 0
            productividad_por_ave = float(data['huevos_diarios']) / float(data['cantidad_aves']) if float(data['cantidad_aves']) > 0 else 0
            costo_por_huevo = costos_directos / (float(data['huevos_diarios']) * 30) if float(data['huevos_diarios']) > 0 else 0
            # Calcular Capital más Pasivo
            capital_mas_pasivo = patrimonio_neto + float(data['total_deudas'])
            # Valores de referencia para razones financieras
            referencias = {
                'margen_ganancia': 'Mayor al 20% es favorable',
                'razon_endeudamiento': 'Menor al 50% es favorable'
            }

            # Agregar datos de referencia
            datos_referencia = {
                'cantidad_aves': float(data['cantidad_aves']),
                'huevos_diarios': float(data['huevos_diarios']),
                'valor_promedio_ave': float(data.get('precio_promedio_gallinas', 0)),
                'valor_maquinaria': valor_maquinaria,
                'lugar_comercializacion': data['lugar_comercializacion']
            }

            # Generar interpretación AI
            interpretacion_ai = []

            if float(data['total_ingresos']) > costos_directos:
                interpretacion_ai.append("Los ingresos son mayores que los gastos, lo cual es positivo.")
            else:
                interpretacion_ai.append("Los gastos superan los ingresos, lo que indica posibles pérdidas.")

            if margen_ganancia >= 20:
                interpretacion_ai.append(f"El margen de ganancia es del {margen_ganancia:.2f}%, lo cual es favorable.")
            else:
                interpretacion_ai.append(f"El margen de ganancia es del {margen_ganancia:.2f}%, podría mejorar.")

            if razon_endeudamiento < 0.5:
                interpretacion_ai.append(f"La razón de endeudamiento es del {razon_endeudamiento:.2%}, lo cual es manejable.")
            else:
                interpretacion_ai.append(f"La razón de endeudamiento es del {razon_endeudamiento:.2%}, se recomienda reducir deudas.")

            interpretacion_ai.append(f"La productividad por ave es de {productividad_por_ave:.2f} huevos diarios.")
            interpretacion_ai.append(f"El costo por huevo producido es de ${costo_por_huevo:.2f}.")
            interpretacion_ai.append(f"El valor promedio estimado por ave es de ${float(data.get('precio_promedio_gallinas', 0)):.2f}.")
            interpretacion_ai.append(f"El valor de la maquinaria y equipo es de ${valor_maquinaria:.2f}.")

            # Convertir lista a string
            interpretacion_ai = " ".join(interpretacion_ai)

            # Preparar datos para el HTML
            financial_summary = {
                'activos': {
                    'dinero_disponible': float(data['dinero_disponible']),
                    'valor_maquinaria': valor_maquinaria,
                    'valor_aves': valor_aves,
                    'total_activos': activos_totales
                },
                'pasivos': {
                    'deudas': float(data['total_deudas']),
                    'total_pasivos': float(data['total_deudas'])
                },
                'patrimonio': patrimonio_neto,
                'capital_mas_pasivo': capital_mas_pasivo,
                'ingresos': {
                    'venta_huevos': float(data['total_ingresos'])
                },
                'gastos': {
                    'alimento': float(data['gastos_alimento']),
                    'mano_obra': float(data['pago_mano_obra']),
                    'servicios': float(data['gastos_servicios']),
                    'imprevistos': float(data['gastos_imprevistos']),
                    'total_gastos': costos_directos
                },
                'utilidad_neta': utilidad_neta,
                'razones_financieras': {
                    'margen_ganancia': margen_ganancia,
                    'razon_endeudamiento': razon_endeudamiento,
                    'productividad_por_ave': productividad_por_ave,
                    'costo_por_huevo': costo_por_huevo
                },
                'referencias': referencias,
                'datos_referencia': datos_referencia,
                'fecha_captura': selected_date,
                'interpretacion_ai': interpretacion_ai
            }
        else:
            financial_summary = None

        return render_template('financial_statements_huevos.html', data=financial_summary, fechas=fechas_disponibles)

    # Ruta para generar estados financieros de maíz
    @app.route('/financial_statements_maiz', methods=['GET', 'POST'])
    def financial_statements_maiz():
        user_id = session.get('user_id')
        if not user_id:
            flash('Por favor, inicia sesión para acceder a los estados financieros.', 'danger')
            return redirect(url_for('login'))

        # Ruta del archivo CSV
        user_folder = os.path.join('data', user_id)
        file_path = os.path.join(user_folder, 'datos_financieros_maiz.csv')

        financial_data = []
        selected_date = None

        if os.path.isfile(file_path):
            with open(file_path, mode='r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                financial_data = list(reader)

        # Verificar si hay datos disponibles
        if not financial_data:
            flash('No se encontraron datos financieros para maíz.', 'danger')
            return render_template('financial_statements_maiz.html', data=None, fechas=[])

        # Ordenar las fechas de captura en orden descendente
        fechas_disponibles = sorted([row['fecha_captura'] for row in financial_data], reverse=True)

        # Si no se envía una fecha desde el formulario, usar la fecha más reciente
        if request.method == 'POST':
            selected_date = request.form.get('fecha_captura')
        elif fechas_disponibles:
            selected_date = fechas_disponibles[0]  # Fecha más reciente

        # Filtrar los datos por la fecha seleccionada
        filtered_data = [row for row in financial_data if row['fecha_captura'] == selected_date]

        # Calcular estados financieros y razones financieras
        if filtered_data:
            data = filtered_data[0]  # Tomar el primer registro filtrado

            try:
                # Calcular costos directos
                costos_directos = (
                    float(data.get('gastos_insumos', 0)) +
                    float(data.get('pago_jornales', 0)) +
                    float(data.get('gastos_servicios', 0)) +
                    float(data.get('gastos_imprevistos', 0))
                )
                utilidad_bruta = float(data.get('total_ingresos', 0)) - costos_directos
                utilidad_neta = utilidad_bruta
                activos_totales = float(data.get('dinero_disponible', 0)) + float(data.get('valor_maquinaria', 0))
                patrimonio_neto = activos_totales - float(data.get('total_deudas', 0))
                total_gastos = costos_directos
                margen_ganancia = (utilidad_bruta / float(data.get('total_ingresos', 1))) * 100 if float(data.get('total_ingresos', 0)) else 0
                razon_endeudamiento = float(data.get('total_deudas', 0)) / activos_totales if activos_totales else 0

                # Calcular productividad por hectárea
                productividad_por_hectarea = float(data.get('total_ingresos', 0)) / float(data.get('hectareas', 1)) if float(data.get('hectareas', 0)) > 0 else 0

                # Calcular costo por hectárea
                costo_por_hectarea = costos_directos / float(data.get('hectareas', 1)) if float(data.get('hectareas', 0)) > 0 else 0

                # Calcular Capital más Pasivo
                capital_mas_pasivo = patrimonio_neto + float(data.get('total_deudas', 0))

                # Valores de referencia para razones financieras
                referencias = {
                    'margen_ganancia': 'Mayor al 20% es favorable',
                    'razon_endeudamiento': 'Menor al 50% es favorable'
                }

                # Agregar datos de referencia
                datos_referencia = {
                    'variedad_maiz': data.get('variedad_maiz', 'N/A'),
                    'hectareas': float(data.get('hectareas', 0)),
                    'dias_preparacion_terreno': float(data.get('dias_preparacion_terreno', 0)),
                    'dias_aplicacion_fertilizantes': float(data.get('dias_aplicacion_fertilizantes', 0)),
                    'dias_secado_procesamiento': float(data.get('dias_secado_procesamiento', 0)),
                    'lugar_comercializacion': data.get('lugar_comercializacion', 'N/A')
                }

                # Generar interpretación AI
                interpretacion_ai = []

                if float(data.get('total_ingresos', 0)) > total_gastos:
                    interpretacion_ai.append("Los ingresos son mayores que los gastos, lo cual es positivo.")
                else:
                    interpretacion_ai.append("Los gastos superan los ingresos, lo que indica posibles pérdidas.")

                if margen_ganancia >= 20:
                    interpretacion_ai.append(f"El margen de ganancia es del {margen_ganancia:.2f}%, lo cual es favorable.")
                else:
                    interpretacion_ai.append(f"El margen de ganancia es del {margen_ganancia:.2f}%, podría mejorar.")

                if razon_endeudamiento < 0.5:
                    interpretacion_ai.append(f"La razón de endeudamiento es del {razon_endeudamiento:.2%}, lo cual es manejable.")
                else:
                    interpretacion_ai.append(f"La razón de endeudamiento es del {razon_endeudamiento:.2%}, se recomienda reducir deudas.")

                interpretacion_ai.append(f"La productividad por hectárea es de ${productividad_por_hectarea:.2f}.")
                interpretacion_ai.append(f"El costo por hectárea es de ${costo_por_hectarea:.2f}.")

                # Convertir lista a string
                interpretacion_ai = " ".join(interpretacion_ai)

                # Preparar datos para el HTML
                financial_summary = {
                    'activos': {
                        'maquinaria_equipo': float(data.get('valor_maquinaria', 0)),
                        'dinero_disponible': float(data.get('dinero_disponible', 0)),
                        'total_activos': activos_totales
                    },
                    'pasivos': {
                        'deudas': float(data.get('total_deudas', 0)),
                        'total_pasivos': float(data.get('total_deudas', 0))
                    },
                    'patrimonio': patrimonio_neto,
                    'capital_mas_pasivo': capital_mas_pasivo,
                    'ingresos': {
                        'venta_maiz': float(data.get('total_ingresos', 0))
                    },
                    'gastos': {
                        'insumos': float(data.get('gastos_insumos', 0)),
                        'jornales': float(data.get('pago_jornales', 0)),
                        'servicios': float(data.get('gastos_servicios', 0)),
                        'imprevistos': float(data.get('gastos_imprevistos', 0)),
                        'total_gastos': total_gastos
                    },
                    'utilidad_neta': utilidad_neta,
                    'razones_financieras': {
                        'margen_ganancia': margen_ganancia,
                        'razon_endeudamiento': razon_endeudamiento,
                        'productividad_por_hectarea': productividad_por_hectarea,
                        'costo_por_hectarea': costo_por_hectarea
                    },
                    'referencias': referencias,
                    'datos_referencia': datos_referencia,
                    'fecha_captura': selected_date,
                    'interpretacion_ai': interpretacion_ai
                }
            except (ValueError, KeyError) as e:
                flash(f'Error al procesar los datos: {e}', 'danger')
                financial_summary = None
        else:
            financial_summary = None

        return render_template('financial_statements_maiz.html', data=financial_summary, fechas=fechas_disponibles)

    @app.route('/submit_registro_cliente', methods=['POST'])
    def submit_registro_cliente():
        nombre = request.form['nombre']
        telefono = request.form['telefono']
        verificacion = request.form['verificacion']
        email = request.form.get('email', '')  # Opcional
        password = generate_password_hash(request.form['password'], method='pbkdf2:sha256')
        dia = request.form['dia']
        mes = request.form['mes']
        año = request.form['año']
        genero = request.form['genero']
        terminos = request.form.get('terminos')

        # Ruta del archivo y creación de la carpeta si no existe
        base_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
        if not os.path.exists(base_dir):
            os.makedirs(base_dir)
        file_path = os.path.join(base_dir, 'users.csv')

        # Guardar los datos en un archivo CSV
        file_exists = os.path.isfile(file_path)
        with open(file_path, mode='a', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=['nombre', 'telefono', 'verificacion', 'email', 'password', 'fecha_nacimiento', 'genero'])
            if not file_exists:
                writer.writeheader()
            writer.writerow({
                'nombre': nombre,
                'telefono': telefono,
                'verificacion': verificacion,
                'email': email,
                'password': password,
                'fecha_nacimiento': f"{dia}/{mes}/{año}",
                'genero': genero
            })

        flash('Registro exitoso.', 'success')
        return redirect(url_for('login'))

    @app.route('/request_modification', methods=['POST'])
    def request_modification():
        try:
            # Obtener datos del formulario
            user_email = request.form.get('email')
            user_name = request.form.get('name')
            modification_details = request.form.get('details')

            # Validar que los campos no estén vacíos
            if not user_email or not user_name or not modification_details:
                return {'status': 'error', 'message': 'Todos los campos son obligatorios.'}, 400

            # Configuración del correo
            sender_email = "cidatmex@gmail.com"
            sender_password = "TU_CONTRASEÑA"  # Reemplaza con la contraseña del correo
            recipient_email = "cidatmex@gmail.com"

            # Correo para el administrador
            admin_subject = f"Cambio de base de datos de {user_email}"
            admin_body = f"""
            Se ha solicitado un cambio en la base de datos:
            - Nombre: {user_name}
            - Correo: {user_email}
            - Detalles: {modification_details}
            """
            send_email(sender_email, sender_password, recipient_email, admin_subject, admin_body)

            # Correo de confirmación para el usuario
            user_subject = "Tu solicitud está siendo procesada"
            user_body = f"""
            Estimado/a {user_name},

            Hemos recibido tu solicitud para modificar la base de datos. Nuestro equipo de servicio al cliente se pondrá en contacto contigo pronto.

            Agradecemos tu preferencia.

            Atentamente,
            Ciencia de Datos México
            """
            send_email(sender_email, sender_password, user_email, user_subject, user_body)

            return {'status': 'success', 'message': 'Solicitud enviada correctamente.'}, 200

        except Exception as e:
            return {'status': 'error', 'message': str(e)}, 500


    def send_email(sender_email, sender_password, recipient_email, subject, body):
        """Función para enviar correos electrónicos."""
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = recipient_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)

    # Ruta para el análisis de datos de café
    @app.route('/my_analysis_cafe', methods=['GET', 'POST'])
    def my_analysis_cafe():
        user_id = session.get('user_id')
        if not user_id:
            flash('Por favor, inicia sesión para acceder al análisis.', 'danger')
            return redirect(url_for('login'))

        # Ruta del archivo CSV
        file_path = f"data/{user_id}/datos_financieros_cafe.csv"
        try:
            data = pd.read_csv(file_path)

            # Ordenar las fechas y obtener la más reciente
            data['fecha_captura'] = pd.to_datetime(data['fecha_captura'])
            data = data.sort_values(by='fecha_captura', ascending=False)
            fechas_disponibles = data['fecha_captura'].dt.strftime('%Y-%m-%d').unique()
            fecha_seleccionada = request.form.get('fecha_captura', fechas_disponibles[0])

            # Filtrar los datos por la fecha seleccionada
            data_filtrada = data[data['fecha_captura'] == pd.to_datetime(fecha_seleccionada)]

            # Cálculos obligatorios
            if 'gastos_insumos' in data.columns and 'pago_jornales' in data.columns and \
               'gastos_servicios' in data.columns and 'gastos_imprevistos' in data.columns:
                data['gastos_totales'] = data['gastos_insumos'] + data['pago_jornales'] + data['gastos_servicios'] + data['gastos_imprevistos']
            else:
                flash('Faltan columnas necesarias para calcular gastos totales.', 'danger')
                return render_template('my_analysis_cafe.html')

            # Verifica que la columna 'gastos_totales' exista
            if 'gastos_totales' not in data.columns:
                flash('Error al calcular gastos totales. Verifica los datos.', 'danger')
                return render_template('my_analysis_cafe.html')

            # Gráficos para Rentabilidad
            fig_sunburst = px.sunburst(
                data_filtrada,
                path=['gastos_insumos', 'pago_jornales', 'gastos_servicios', 'gastos_imprevistos'],
                values='gastos_totales',
                title="Jerarquía de Gastos"
            )
            fig_line = px.line(
                data,
                x='fecha_captura',
                y=['total_ingresos', 'utilidad_neta'],
                title="Ingresos vs. Utilidad Neta"
            )
            fig_bar = px.bar(
                data,
                x='fecha_captura',
                y=['total_ingresos', 'gastos_totales'],
                title="Ingresos vs. Gastos Totales"
            )

            # Convertir gráficos a HTML
            sunburst_html = fig_sunburst.to_html(full_html=False)
            line_html = fig_line.to_html(full_html=False)
            bar_html = fig_bar.to_html(full_html=False)

            # Gráficos para Producción
            # Producción total por hectárea
            data['produccion_por_hectarea'] = data['produccion_total'] / data['hectareas']
            fig_bar_produccion = px.bar(
                data,
                x='fecha_captura',
                y='produccion_por_hectarea',
                title="Producción Total por Hectárea"
            )

            # Costos de insumos vs producción
            fig_line_costos_vs_produccion = px.line(
                data,
                x='fecha_captura',
                y=['produccion_total', 'gastos_insumos'],
                title="Costos de Insumos vs Producción Total"
            )

            # Costo por unidad producida
            fig_line_costo_por_unidad = px.line(
                data,
                x='fecha_captura',
                y='costo_por_unidad',
                title="Costo por Unidad Producida"
            )

            # Correlación insumos-producción
            fig_scatter_insumos_vs_produccion = px.scatter(
                data,
                x='gastos_insumos',
                y='produccion_total',
                title="Correlación Insumos vs Producción Total",
                labels={'x': 'Gastos Insumos', 'y': 'Producción Total'}
            )

            # Convertir gráficos a HTML
            bar_produccion_html = fig_bar_produccion.to_html(full_html=False)
            line_costos_vs_produccion_html = fig_line_costos_vs_produccion.to_html(full_html=False)
            line_costo_por_unidad_html = fig_line_costo_por_unidad.to_html(full_html=False)
            scatter_insumos_vs_produccion_html = fig_scatter_insumos_vs_produccion.to_html(full_html=False)

            # Gráficos para Mano de Obra
            # Distribución de costos laborales
            fig_pie_costos_laborales = px.pie(
                data_filtrada,
                names=['pago_jornales', 'gastos_totales'],
                values=[data_filtrada['pago_jornales'].sum(), data_filtrada['gastos_totales'].sum()],
                title="Distribución de Costos Laborales"
            )

            # Días trabajados vs trabajadores
            fig_bar_dias_vs_trabajadores = px.bar(
                data,
                x='dias_trabajo',
                y='trabajadores',
                title="Días Trabajados vs Trabajadores"
            )

            # Horas de supervisión vs ventas
            fig_line_supervision_vs_ventas = px.line(
                data,
                x='fecha_captura',
                y=['horas_supervision', 'horas_venta'],
                title="Horas de Supervisión vs Ventas"
            )

            # Productividad por trabajador
            data['productividad_por_trabajador'] = data['produccion_total'] / data['trabajadores']
            fig_bar_productividad_trabajador = px.bar(
                data,
                x='fecha_captura',
                y='productividad_por_trabajador',
                title="Productividad por Trabajador"
            )

            # Convertir gráficos a HTML
            pie_costos_laborales_html = fig_pie_costos_laborales.to_html(full_html=False)
            bar_dias_vs_trabajadores_html = fig_bar_dias_vs_trabajadores.to_html(full_html=False)
            line_supervision_vs_ventas_html = fig_line_supervision_vs_ventas.to_html(full_html=False)
            bar_productividad_trabajador_html = fig_bar_productividad_trabajador.to_html(full_html=False)

            # Gráficos para Patrimonio
            # Composición del patrimonio neto
            fig_pie_patrimonio = px.pie(
                data_filtrada,
                names=['patrimonio_neto', 'activos_totales', 'valor_maquinaria'],
                values=[data_filtrada['patrimonio_neto'].sum(), data_filtrada['activos_totales'].sum(), data_filtrada['valor_maquinaria'].sum()],
                title="Composición del Patrimonio Neto"
            )

            # Razón de endeudamiento
            fig_line_razon_endeudamiento = px.line(
                data,
                x='fecha_captura',
                y='razon_endeudamiento',
                title="Razón de Endeudamiento vs Tiempo"
            )

            # Activos vs deudas
            fig_bar_activos_vs_deudas = px.bar(
                data,
                x='fecha_captura',
                y=['activos_totales', 'total_deudas'],
                barmode='group',
                title="Activos Totales vs Total de Deudas"
            )

            # Valor maquinaria vs patrimonio
            fig_scatter_maquinaria_vs_patrimonio = px.scatter(
                data,
                x='valor_maquinaria',
                y='patrimonio_neto',
                title="Valor Maquinaria vs Patrimonio Neto",
                labels={'x': 'Valor Maquinaria', 'y': 'Patrimonio Neto'}
            )

            # Convertir gráficos a HTML
            pie_patrimonio_html = fig_pie_patrimonio.to_html(full_html=False)
            line_razon_endeudamiento_html = fig_line_razon_endeudamiento.to_html(full_html=False)
            bar_activos_vs_deudas_html = fig_bar_activos_vs_deudas.to_html(full_html=False)
            scatter_maquinaria_vs_patrimonio_html = fig_scatter_maquinaria_vs_patrimonio.to_html(full_html=False)

            return render_template(
                'my_analysis_cafe.html',
                sunburst_html=sunburst_html,
                line_html=line_html,
                bar_html=bar_html,
                bar_produccion_html=bar_produccion_html,
                line_costos_vs_produccion_html=line_costos_vs_produccion_html,
                line_costo_por_unidad_html=line_costo_por_unidad_html,
                scatter_insumos_vs_produccion_html=scatter_insumos_vs_produccion_html,
                pie_costos_laborales_html=pie_costos_laborales_html,
                bar_dias_vs_trabajadores_html=bar_dias_vs_trabajadores_html,
                line_supervision_vs_ventas_html=line_supervision_vs_ventas_html,
                bar_productividad_trabajador_html=bar_productividad_trabajador_html,
                pie_patrimonio_html=pie_patrimonio_html,
                line_razon_endeudamiento_html=line_razon_endeudamiento_html,
                bar_activos_vs_deudas_html=bar_activos_vs_deudas_html,
                scatter_maquinaria_vs_patrimonio_html=scatter_maquinaria_vs_patrimonio_html,
                ultimos_valores=data_filtrada.iloc[0].to_dict(),
                fechas_disponibles=fechas_disponibles,
                fecha_seleccionada=fecha_seleccionada
            )
        except FileNotFoundError:
            flash('No se encontraron datos para generar el análisis.', 'danger')
            return render_template('my_analysis_cafe.html')


    @app.route('/my_analysis_bovino', methods=['GET', 'POST'])
    def my_analysis_bovino():
        user_id = session.get('user_id')
        if not user_id:
            flash('Por favor, inicia sesión para acceder al análisis.', 'danger')
            return redirect(url_for('login'))

        # Ruta del archivo CSV
        file_path = f"data/{user_id}/datos_financieros_ganado.csv"
        try:
            data = pd.read_csv(file_path)

            # Ordenar las fechas y obtener la más reciente
            data['fecha_captura'] = pd.to_datetime(data['fecha_captura'], format='%d/%m/%Y %H:%M', errors='coerce')

            # Verificar si hay fechas inválidas
            if data['fecha_captura'].isna().any():
                flash('Algunas fechas no tienen un formato válido. Verifica los datos.', 'danger')
                return render_template('my_analysis_bovino.html')

            data = data.sort_values(by='fecha_captura', ascending=False)
            fechas_disponibles = data['fecha_captura'].dt.strftime('%Y-%m-%d').unique()
            fecha_seleccionada = request.form.get('fecha_captura', fechas_disponibles[0])

            # Filtrar los datos por la fecha seleccionada
            data_filtrada = data[data['fecha_captura'] == pd.to_datetime(fecha_seleccionada)]

            # Verifica que las columnas necesarias existan
            required_columns = [
                'gastos_alimento', 'pago_mano_obra', 'gastos_servicios', 'gastos_imprevistos',
                'cantidad_becerros', 'peso_vivo_actual', 'trabajadores_necesarios', 'total_ingresos'
            ]
            for col in required_columns:
                if col not in data.columns:
                    flash(f'Falta la columna necesaria: {col}', 'danger')
                    return render_template('my_analysis_bovino.html')

            # Cálculos obligatorios
            data['gastos_totales'] = data['gastos_alimento'] + data['pago_mano_obra'] + data['gastos_servicios'] + data['gastos_imprevistos']
            data['productividad_por_trabajador'] = data['cantidad_becerros'] / data['trabajadores_necesarios']
            data['costo_por_animal'] = data['gastos_totales'] / data['cantidad_becerros']

            # Gráficos para Rentabilidad
            fig_sunburst = px.sunburst(
                data_filtrada,
                path=['gastos_alimento', 'pago_mano_obra', 'gastos_servicios', 'gastos_imprevistos'],
                values='gastos_totales',
                title="Jerarquía de Gastos"
            )
            fig_line = px.line(
                data,
                x='fecha_captura',
                y=['total_ingresos', 'utilidad_neta'],
                title="Ingresos vs. Utilidad Neta"
            )
            fig_bar = px.bar(
                data,
                x='fecha_captura',
                y=['total_ingresos', 'gastos_totales'],
                title="Ingresos vs. Gastos Totales"
            )

            # Convertir gráficos a HTML
            sunburst_html = fig_sunburst.to_html(full_html=False)
            line_html = fig_line.to_html(full_html=False)
            bar_html = fig_bar.to_html(full_html=False)

            # Gráficos para Producción
            # Producción total por becerro
            fig_bar_produccion = px.bar(
                data,
                x='fecha_captura',
                y='cantidad_becerros',
                title="Cantidad de Becerros por Fecha"
            )

            # Costos de alimento vs producción
            fig_line_costos_vs_produccion = px.line(
                data,
                x='fecha_captura',
                y=['cantidad_becerros', 'gastos_alimento'],
                title="Costos de Alimento vs Cantidad de Becerros"
            )

            # Costo por animal
            fig_line_costo_por_animal = px.line(
                data,
                x='fecha_captura',
                y='costo_por_animal',
                title="Costo por Animal"
            )

            # Correlación entre peso vivo y cantidad de becerros
            fig_scatter_peso_vs_becerros = px.scatter(
                data,
                x='peso_vivo_actual',
                y='cantidad_becerros',
                title="Peso Vivo Promedio vs Cantidad de Becerros",
                labels={'x': 'Peso Vivo Promedio (kg)', 'y': 'Cantidad de Becerros'}
            )

            # Convertir gráficos a HTML
            bar_produccion_html = fig_bar_produccion.to_html(full_html=False)
            line_costos_vs_produccion_html = fig_line_costos_vs_produccion.to_html(full_html=False)
            line_costo_por_animal_html = fig_line_costo_por_animal.to_html(full_html=False)
            scatter_peso_vs_becerros_html = fig_scatter_peso_vs_becerros.to_html(full_html=False)

            # Gráficos para Mano de Obra
            # Distribución de costos laborales
            fig_pie_costos_laborales = px.pie(
                data_filtrada,
                names=['pago_mano_obra', 'gastos_totales'],
                values=[data_filtrada['pago_mano_obra'].sum(), data_filtrada['gastos_totales'].sum()],
                title="Distribución de Costos Laborales"
            )

            # Días de aplicación de tratamientos vs trabajadores necesarios
            fig_bar_dias_vs_trabajadores = px.bar(
                data,
                x='dias_aplicacion_tratamientos',
                y='trabajadores_necesarios',
                title="Días de Aplicación de Tratamientos vs Trabajadores Necesarios"
            )

            # Horas de supervisión vs preparación de alimento
            fig_line_supervision_vs_preparacion = px.line(
                data,
                x='fecha_captura',
                y=['horas_supervision_diarias', 'horas_preparacion_alimento'],
                title="Horas de Supervisión vs Preparación de Alimento"
            )

            # Productividad por trabajador
            fig_bar_productividad_trabajador = px.bar(
                data,
                x='fecha_captura',
                y='productividad_por_trabajador',
                title="Productividad por Trabajador"
            )

            # Convertir gráficos a HTML
            pie_costos_laborales_html = fig_pie_costos_laborales.to_html(full_html=False)
            bar_dias_vs_trabajadores_html = fig_bar_dias_vs_trabajadores.to_html(full_html=False)
            line_supervision_vs_preparacion_html = fig_line_supervision_vs_preparacion.to_html(full_html=False)
            bar_productividad_trabajador_html = fig_bar_productividad_trabajador.to_html(full_html=False)

            # Gráficos para Patrimonio
            # Composición del patrimonio neto
            fig_pie_patrimonio = px.pie(
                data_filtrada,
                names=['patrimonio_neto', 'activos_totales', 'valor_maquinaria'],
                values=[data_filtrada['patrimonio_neto'].sum(), data_filtrada['activos_totales'].sum(), data_filtrada['valor_maquinaria'].sum()],
                title="Composición del Patrimonio Neto"
            )

            # Razón de endeudamiento
            fig_line_razon_endeudamiento = px.line(
                data,
                x='fecha_captura',
                y='razon_endeudamiento',
                title="Razón de Endeudamiento vs Tiempo"
            )

            # Activos vs deudas
            fig_bar_activos_vs_deudas = px.bar(
                data,
                x='fecha_captura',
                y=['activos_totales', 'total_deudas'],
                barmode='group',
                title="Activos Totales vs Total de Deudas"
            )

            # Valor maquinaria vs patrimonio
            fig_scatter_maquinaria_vs_patrimonio = px.scatter(
                data,
                x='valor_maquinaria',
                y='patrimonio_neto',
                title="Valor Maquinaria vs Patrimonio Neto",
                labels={'x': 'Valor Maquinaria', 'y': 'Patrimonio Neto'}
            )

            # Convertir gráficos a HTML
            pie_patrimonio_html = fig_pie_patrimonio.to_html(full_html=False)
            line_razon_endeudamiento_html = fig_line_razon_endeudamiento.to_html(full_html=False)
            bar_activos_vs_deudas_html = fig_bar_activos_vs_deudas.to_html(full_html=False)
            scatter_maquinaria_vs_patrimonio_html = fig_scatter_maquinaria_vs_patrimonio.to_html(full_html=False)

            return render_template(
                'my_analysis_bovino.html',
                sunburst_html=sunburst_html,
                line_html=line_html,
                bar_html=bar_html,
                bar_produccion_html=bar_produccion_html,
                line_costos_vs_produccion_html=line_costos_vs_produccion_html,
                line_costo_por_animal_html=line_costo_por_animal_html,
                scatter_peso_vs_becerros_html=scatter_peso_vs_becerros_html,
                pie_costos_laborales_html=pie_costos_laborales_html,
                bar_dias_vs_trabajadores_html=bar_dias_vs_trabajadores_html,
                line_supervision_vs_preparacion_html=line_supervision_vs_preparacion_html,
                bar_productividad_trabajador_html=bar_productividad_trabajador_html,
                pie_patrimonio_html=pie_patrimonio_html,
                line_razon_endeudamiento_html=line_razon_endeudamiento_html,
                bar_activos_vs_deudas_html=bar_activos_vs_deudas_html,
                scatter_maquinaria_vs_patrimonio_html=scatter_maquinaria_vs_patrimonio_html,
                ultimos_valores=data_filtrada.iloc[0].to_dict(),
                fechas_disponibles=fechas_disponibles,
                fecha_seleccionada=fecha_seleccionada
            )
        except FileNotFoundError:
            flash('No se encontraron datos para generar el análisis.', 'danger')
            return render_template('my_analysis_bovino.html')


    @app.route('/my_analysis_maiz', methods=['GET', 'POST'])
    def my_analysis_maiz():
        user_id = session.get('user_id')
        if not user_id:
            flash('Por favor, inicia sesión para acceder al análisis.', 'danger')
            return redirect(url_for('login'))

        # Ruta del archivo CSV
        file_path = f"data/{user_id}/datos_financieros_maiz.csv"
        try:
            data = pd.read_csv(file_path)

            # Ordenar las fechas y obtener la más reciente
            data['fecha_captura'] = pd.to_datetime(data['fecha_captura'])
            data = data.sort_values(by='fecha_captura', ascending=False)
            fechas_disponibles = data['fecha_captura'].dt.strftime('%Y-%m-%d').unique()
            fecha_seleccionada = request.form.get('fecha_captura', fechas_disponibles[0])

            # Filtrar los datos por la fecha seleccionada
            data_filtrada = data[data['fecha_captura'] == pd.to_datetime(fecha_seleccionada)]

            # Cálculos obligatorios
            if 'gastos_insumos' in data.columns and 'pago_jornales' in data.columns and \
            'gastos_servicios' in data.columns and 'gastos_imprevistos' in data.columns:
                data['gastos_totales'] = data['gastos_insumos'] + data['pago_jornales'] + data['gastos_servicios'] + data['gastos_imprevistos']
            else:
                flash('Faltan columnas necesarias para calcular gastos totales.', 'danger')
                return render_template('my_analysis_maiz.html')

            # Verifica que la columna 'gastos_totales' exista
            if 'gastos_totales' not in data.columns:
                flash('Error al calcular gastos totales. Verifica los datos.', 'danger')
                return render_template('my_analysis_maiz.html')

            # Gráficos para Rentabilidad
            fig_sunburst = px.sunburst(
                data_filtrada,
                path=['gastos_insumos', 'pago_jornales', 'gastos_servicios', 'gastos_imprevistos'],
                values='gastos_totales',
                title="Jerarquía de Gastos"
            )
            fig_line = px.line(
                data,
                x='fecha_captura',
                y=['total_ingresos', 'utilidad_neta'],
                title="Ingresos vs. Utilidad Neta"
            )
            fig_bar = px.bar(
                data,
                x='fecha_captura',
                y=['total_ingresos', 'gastos_totales'],
                title="Ingresos vs. Gastos Totales"
            )

            # Convertir gráficos a HTML
            sunburst_html = fig_sunburst.to_html(full_html=False)
            line_html = fig_line.to_html(full_html=False)
            bar_html = fig_bar.to_html(full_html=False)

            # Gráficos para Producción
            # Producción total por hectárea
            data['productividad_por_hectarea'] = data['total_ingresos'] / data['hectareas']
            fig_bar_produccion = px.bar(
                data,
                x='fecha_captura',
                y='productividad_por_hectarea',
                title="Productividad por Hectárea"
            )

            # Costos de insumos vs ingresos
            fig_line_costos_vs_ingresos = px.line(
                data,
                x='fecha_captura',
                y=['total_ingresos', 'gastos_insumos'],
                title="Costos de Insumos vs Ingresos Totales"
            )

            # Costo por hectárea
            data['costo_por_hectarea'] = data['gastos_totales'] / data['hectareas']
            fig_line_costo_por_hectarea = px.line(
                data,
                x='fecha_captura',
                y='costo_por_hectarea',
                title="Costo por Hectárea"
            )

            # Correlación entre insumos y productividad
            fig_scatter_insumos_vs_productividad = px.scatter(
                data,
                x='gastos_insumos',
                y='productividad_por_hectarea',
                title="Correlación Insumos vs Productividad por Hectárea",
                labels={'x': 'Gastos Insumos', 'y': 'Productividad por Hectárea'}
            )

            # Convertir gráficos a HTML
            bar_produccion_html = fig_bar_produccion.to_html(full_html=False)
            line_costos_vs_ingresos_html = fig_line_costos_vs_ingresos.to_html(full_html=False)
            line_costo_por_hectarea_html = fig_line_costo_por_hectarea.to_html(full_html=False)
            scatter_insumos_vs_productividad_html = fig_scatter_insumos_vs_productividad.to_html(full_html=False)

            # Gráficos para Mano de Obra
            # Distribución de costos laborales
            fig_pie_costos_laborales = px.pie(
                data_filtrada,
                names=['pago_jornales', 'gastos_totales'],
                values=[data_filtrada['pago_jornales'].sum(), data_filtrada['gastos_totales'].sum()],
                title="Distribución de Costos Laborales"
            )

            # Días de preparación del terreno vs trabajadores
            fig_bar_dias_vs_trabajadores = px.bar(
                data,
                x='dias_preparacion_terreno',
                y='trabajadores_cosecha',
                title="Días de Preparación del Terreno vs Trabajadores"
            )

            # Horas de supervisión vs ingresos
            fig_line_supervision_vs_ingresos = px.line(
                data,
                x='fecha_captura',
                y=['horas_supervision_diaria', 'total_ingresos'],
                title="Horas de Supervisión vs Ingresos Totales"
            )

            # Convertir gráficos a HTML
            pie_costos_laborales_html = fig_pie_costos_laborales.to_html(full_html=False)
            bar_dias_vs_trabajadores_html = fig_bar_dias_vs_trabajadores.to_html(full_html=False)
            line_supervision_vs_ingresos_html = fig_line_supervision_vs_ingresos.to_html(full_html=False)

            # Gráficos para Patrimonio
            # Composición del patrimonio neto
            fig_pie_patrimonio = px.pie(
                data_filtrada,
                names=['patrimonio_neto', 'activos_totales', 'valor_maquinaria'],
                values=[data_filtrada['patrimonio_neto'].sum(), data_filtrada['activos_totales'].sum(), data_filtrada['valor_maquinaria'].sum()],
                title="Composición del Patrimonio Neto"
            )

            # Razón de endeudamiento
            fig_line_razon_endeudamiento = px.line(
                data,
                x='fecha_captura',
                y='razon_endeudamiento',
                title="Razón de Endeudamiento vs Tiempo"
            )

            # Activos vs deudas
            fig_bar_activos_vs_deudas = px.bar(
                data,
                x='fecha_captura',
                y=['activos_totales', 'total_deudas'],
                barmode='group',
                title="Activos Totales vs Total de Deudas"
            )

            # Convertir gráficos a HTML
            pie_patrimonio_html = fig_pie_patrimonio.to_html(full_html=False)
            line_razon_endeudamiento_html = fig_line_razon_endeudamiento.to_html(full_html=False)
            bar_activos_vs_deudas_html = fig_bar_activos_vs_deudas.to_html(full_html=False)

            return render_template(
                'my_analysis_maiz.html',
                sunburst_html=sunburst_html,
                line_html=line_html,
                bar_html=bar_html,
                bar_produccion_html=bar_produccion_html,
                line_costos_vs_ingresos_html=line_costos_vs_ingresos_html,
                line_costo_por_hectarea_html=line_costo_por_hectarea_html,
                scatter_insumos_vs_productividad_html=scatter_insumos_vs_productividad_html,
                pie_costos_laborales_html=pie_costos_laborales_html,
                bar_dias_vs_trabajadores_html=bar_dias_vs_trabajadores_html,
                line_supervision_vs_ingresos_html=line_supervision_vs_ingresos_html,
                pie_patrimonio_html=pie_patrimonio_html,
                line_razon_endeudamiento_html=line_razon_endeudamiento_html,
                bar_activos_vs_deudas_html=bar_activos_vs_deudas_html,
                ultimos_valores=data_filtrada.iloc[0].to_dict(),
                fechas_disponibles=fechas_disponibles,
                fecha_seleccionada=fecha_seleccionada
            )
        except FileNotFoundError:
            flash('No se encontraron datos para generar el análisis.', 'danger')
            return render_template('my_analysis_maiz.html')

    @app.route('/my_analysis_cerdos', methods=['GET', 'POST'])
    def my_analysis_cerdos():
        user_id = session.get('user_id')
        if not user_id:
            flash('Por favor, inicia sesión para acceder al análisis.', 'danger')
            return redirect(url_for('login'))

        # Ruta del archivo CSV
        file_path = f"data/{user_id}/datos_financieros_cerdos.csv"
        try:
            data = pd.read_csv(file_path)

            # Ordenar las fechas y obtener la más reciente
            data['fecha_captura'] = pd.to_datetime(data['fecha_captura'])
            data = data.sort_values(by='fecha_captura', ascending=False)
            fechas_disponibles = data['fecha_captura'].dt.strftime('%Y-%m-%d').unique()
            fecha_seleccionada = request.form.get('fecha_captura', fechas_disponibles[0])

            # Filtrar los datos por la fecha seleccionada
            data_filtrada = data[data['fecha_captura'] == pd.to_datetime(fecha_seleccionada)]

            # Cálculos obligatorios
            if 'gastos_alimento' in data.columns and 'pago_mano_obra' in data.columns and \
            'gastos_servicios' in data.columns and 'gastos_veterinario' in data.columns and \
            'gastos_imprevistos' in data.columns:
                data['gastos_totales'] = (
                    data['gastos_alimento'] + data['pago_mano_obra'] + data['gastos_servicios'] +
                    data['gastos_veterinario'] + data['gastos_imprevistos']
                )
            else:
                flash('Faltan columnas necesarias para calcular gastos totales.', 'danger')
                return render_template('my_analysis_cerdos.html')

            # Verifica que la columna 'gastos_totales' exista
            if 'gastos_totales' not in data.columns:
                flash('Error al calcular gastos totales. Verifica los datos.', 'danger')
                return render_template('my_analysis_cerdos.html')

            # Gráficos para Rentabilidad
            fig_sunburst = px.sunburst(
                data_filtrada,
                path=['gastos_alimento', 'pago_mano_obra', 'gastos_servicios', 'gastos_veterinario', 'gastos_imprevistos'],
                values='gastos_totales',
                title="Jerarquía de Gastos"
            )
            fig_line = px.line(
                data,
                x='fecha_captura',
                y=['total_ingresos', 'utilidad_neta'],
                title="Ingresos vs. Utilidad Neta"
            )
            fig_bar = px.bar(
                data,
                x='fecha_captura',
                y=['total_ingresos', 'gastos_totales'],
                title="Ingresos vs. Gastos Totales"
            )

            # Convertir gráficos a HTML
            sunburst_html = fig_sunburst.to_html(full_html=False)
            line_html = fig_line.to_html(full_html=False)
            bar_html = fig_bar.to_html(full_html=False)

            # Gráficos para Producción
            # Producción total por animal
            data['productividad_por_animal'] = data['total_ingresos'] / data['cantidad_animales']
            fig_bar_produccion = px.bar(
                data,
                x='fecha_captura',
                y='productividad_por_animal',
                title="Productividad por Animal"
            )

            # Costos de alimento vs ingresos
            fig_line_costos_vs_ingresos = px.line(
                data,
                x='fecha_captura',
                y=['total_ingresos', 'gastos_alimento'],
                title="Costos de Alimento vs Ingresos Totales"
            )

            # Costo por animal
            data['costo_por_animal'] = data['gastos_totales'] / data['cantidad_animales']
            fig_line_costo_por_animal = px.line(
                data,
                x='fecha_captura',
                y='costo_por_animal',
                title="Costo por Animal"
            )

            # Correlación entre peso promedio y productividad
            fig_scatter_peso_vs_productividad = px.scatter(
                data,
                x='peso_promedio',
                y='productividad_por_animal',
                title="Correlación Peso Promedio vs Productividad por Animal",
                labels={'x': 'Peso Promedio (kg)', 'y': 'Productividad por Animal'}
            )

            # Convertir gráficos a HTML
            bar_produccion_html = fig_bar_produccion.to_html(full_html=False)
            line_costos_vs_ingresos_html = fig_line_costos_vs_ingresos.to_html(full_html=False)
            line_costo_por_animal_html = fig_line_costo_por_animal.to_html(full_html=False)
            scatter_peso_vs_productividad_html = fig_scatter_peso_vs_productividad.to_html(full_html=False)

            # Gráficos para Mano de Obra
            # Distribución de costos laborales
            fig_pie_costos_laborales = px.pie(
                data_filtrada,
                names=['pago_mano_obra', 'gastos_totales'],
                values=[data_filtrada['pago_mano_obra'].sum(), data_filtrada['gastos_totales'].sum()],
                title="Distribución de Costos Laborales"
            )

            # Horas de supervisión vs preparación de venta
            fig_line_supervision_vs_preparacion = px.line(
                data,
                x='fecha_captura',
                y=['horas_supervision', 'horas_preparacion_venta'],
                title="Horas de Supervisión vs Preparación de Venta"
            )

            # Convertir gráficos a HTML
            pie_costos_laborales_html = fig_pie_costos_laborales.to_html(full_html=False)
            line_supervision_vs_preparacion_html = fig_line_supervision_vs_preparacion.to_html(full_html=False)

            # Gráficos para Patrimonio
            # Composición del patrimonio neto
            fig_pie_patrimonio = px.pie(
                data_filtrada,
                names=['patrimonio_neto', 'activos_totales', 'valor_maquinaria'],
                values=[data_filtrada['patrimonio_neto'].sum(), data_filtrada['activos_totales'].sum(), data_filtrada['valor_maquinaria'].sum()],
                title="Composición del Patrimonio Neto"
            )

            # Razón de endeudamiento
            fig_line_razon_endeudamiento = px.line(
                data,
                x='fecha_captura',
                y='razon_endeudamiento',
                title="Razón de Endeudamiento vs Tiempo"
            )

            # Activos vs deudas
            fig_bar_activos_vs_deudas = px.bar(
                data,
                x='fecha_captura',
                y=['activos_totales', 'total_deudas'],
                barmode='group',
                title="Activos Totales vs Total de Deudas"
            )

            # Convertir gráficos a HTML
            pie_patrimonio_html = fig_pie_patrimonio.to_html(full_html=False)
            line_razon_endeudamiento_html = fig_line_razon_endeudamiento.to_html(full_html=False)
            bar_activos_vs_deudas_html = fig_bar_activos_vs_deudas.to_html(full_html=False)

            return render_template(
                'my_analysis_cerdos.html',
                sunburst_html=sunburst_html,
                line_html=line_html,
                bar_html=bar_html,
                bar_produccion_html=bar_produccion_html,
                line_costos_vs_ingresos_html=line_costos_vs_ingresos_html,
                line_costo_por_animal_html=line_costo_por_animal_html,
                scatter_peso_vs_productividad_html=scatter_peso_vs_productividad_html,
                pie_costos_laborales_html=pie_costos_laborales_html,
                line_supervision_vs_preparacion_html=line_supervision_vs_preparacion_html,
                pie_patrimonio_html=pie_patrimonio_html,
                line_razon_endeudamiento_html=line_razon_endeudamiento_html,
                bar_activos_vs_deudas_html=bar_activos_vs_deudas_html,
                ultimos_valores=data_filtrada.iloc[0].to_dict(),
                fechas_disponibles=fechas_disponibles,
                fecha_seleccionada=fecha_seleccionada
            )
        except FileNotFoundError:
            flash('No se encontraron datos para generar el análisis.', 'danger')
            return render_template('my_analysis_cerdos.html')


    @app.route('/my_analysis_huevos', methods=['GET', 'POST'])
    def my_analysis_huevos():
        user_id = session.get('user_id')
        if not user_id:
            flash('Por favor, inicia sesión para acceder al análisis.', 'danger')
            return redirect(url_for('login'))

        # Ruta del archivo CSV
        file_path = f"data/{user_id}/datos_financieros_huevos.csv"
        try:
            data = pd.read_csv(file_path)

            # Ordenar las fechas y obtener la más reciente
            data['fecha_captura'] = pd.to_datetime(data['fecha_captura'], format='%d/%m/%Y', errors='coerce')
            data = data.sort_values(by='fecha_captura', ascending=False)
            fechas_disponibles = data['fecha_captura'].dt.strftime('%Y-%m-%d').unique()
            fecha_seleccionada = request.form.get('fecha_captura', fechas_disponibles[0])

            # Filtrar los datos por la fecha seleccionada
            data_filtrada = data[data['fecha_captura'] == pd.to_datetime(fecha_seleccionada)]

            # Cálculos obligatorios
            if 'gastos_alimento' in data.columns and 'pago_mano_obra' in data.columns and \
            'gastos_servicios' in data.columns and 'gastos_imprevistos' in data.columns:
                data['gastos_totales'] = (
                    data['gastos_alimento'] + data['pago_mano_obra'] + data['gastos_servicios'] +
                    data['gastos_imprevistos']
                )
            else:
                flash('Faltan columnas necesarias para calcular gastos totales.', 'danger')
                return render_template('my_analysis_huevos.html')

            # Verifica que la columna 'gastos_totales' exista
            if 'gastos_totales' not in data.columns:
                flash('Error al calcular gastos totales. Verifica los datos.', 'danger')
                return render_template('my_analysis_huevos.html')

            # Gráficos para Rentabilidad
            fig_sunburst = px.sunburst(
                data_filtrada,
                path=['gastos_alimento', 'pago_mano_obra', 'gastos_servicios', 'gastos_imprevistos'],
                values='gastos_totales',
                title="Jerarquía de Gastos"
            )
            fig_line = px.line(
                data,
                x='fecha_captura',
                y=['total_ingresos', 'utilidad_neta'],
                title="Ingresos vs. Utilidad Neta"
            )
            fig_bar = px.bar(
                data,
                x='fecha_captura',
                y=['total_ingresos', 'gastos_totales'],
                title="Ingresos vs. Gastos Totales"
            )

            # Convertir gráficos a HTML
            sunburst_html = fig_sunburst.to_html(full_html=False)
            line_html = fig_line.to_html(full_html=False)
            bar_html = fig_bar.to_html(full_html=False)

            # Gráficos para Producción
            # Productividad por ave
            data['productividad_por_ave'] = data['huevos_diarios'] / data['cantidad_aves']
            fig_bar_produccion = px.bar(
                data,
                x='fecha_captura',
                y='productividad_por_ave',
                title="Productividad por Ave"
            )

            # Costos de alimento vs ingresos
            fig_line_costos_vs_ingresos = px.line(
                data,
                x='fecha_captura',
                y=['total_ingresos', 'gastos_alimento'],
                title="Costos de Alimento vs Ingresos Totales"
            )

            # Costo por huevo
            data['costo_por_huevo'] = data['gastos_totales'] / (data['huevos_diarios'] * 30)
            fig_line_costo_por_huevo = px.line(
                data,
                x='fecha_captura',
                y='costo_por_huevo',
                title="Costo por Huevo"
            )

            # Convertir gráficos a HTML
            bar_produccion_html = fig_bar_produccion.to_html(full_html=False)
            line_costos_vs_ingresos_html = fig_line_costos_vs_ingresos.to_html(full_html=False)
            line_costo_por_huevo_html = fig_line_costo_por_huevo.to_html(full_html=False)

            # Gráficos para Mano de Obra
            # Distribución de costos laborales
            fig_pie_costos_laborales = px.pie(
                data_filtrada,
                names=['pago_mano_obra', 'gastos_totales'],
                values=[data_filtrada['pago_mano_obra'].sum(), data_filtrada['gastos_totales'].sum()],
                title="Distribución de Costos Laborales"
            )

            # Horas de supervisión vs tiempo de recolección
            fig_line_supervision_vs_recoleccion = px.line(
                data,
                x='fecha_captura',
                y=['horas_supervision', 'tiempo_recoleccion'],
                title="Horas de Supervisión vs Tiempo de Recolección"
            )

            # Convertir gráficos a HTML
            pie_costos_laborales_html = fig_pie_costos_laborales.to_html(full_html=False)
            line_supervision_vs_recoleccion_html = fig_line_supervision_vs_recoleccion.to_html(full_html=False)

            # Gráficos para Patrimonio
            # Composición del patrimonio neto
            fig_pie_patrimonio = px.pie(
                data_filtrada,
                names=['patrimonio_neto', 'activos_totales', 'valor_maquinaria'],
                values=[data_filtrada['patrimonio_neto'].sum(), data_filtrada['activos_totales'].sum(), data_filtrada['valor_maquinaria'].sum()],
                title="Composición del Patrimonio Neto"
            )

            # Razón de endeudamiento
            fig_line_razon_endeudamiento = px.line(
                data,
                x='fecha_captura',
                y='razon_endeudamiento',
                title="Razón de Endeudamiento vs Tiempo"
            )

            # Activos vs deudas
            fig_bar_activos_vs_deudas = px.bar(
                data,
                x='fecha_captura',
                y=['activos_totales', 'total_deudas'],
                barmode='group',
                title="Activos Totales vs Total de Deudas"
            )

            # Convertir gráficos a HTML
            pie_patrimonio_html = fig_pie_patrimonio.to_html(full_html=False)
            line_razon_endeudamiento_html = fig_line_razon_endeudamiento.to_html(full_html=False)
            bar_activos_vs_deudas_html = fig_bar_activos_vs_deudas.to_html(full_html=False)

            return render_template(
                'my_analysis_huevos.html',
                sunburst_html=sunburst_html,
                line_html=line_html,
                bar_html=bar_html,
                bar_produccion_html=bar_produccion_html,
                line_costos_vs_ingresos_html=line_costos_vs_ingresos_html,
                line_costo_por_huevo_html=line_costo_por_huevo_html,
                pie_costos_laborales_html=pie_costos_laborales_html,
                line_supervision_vs_recoleccion_html=line_supervision_vs_recoleccion_html,
                pie_patrimonio_html=pie_patrimonio_html,
                line_razon_endeudamiento_html=line_razon_endeudamiento_html,
                bar_activos_vs_deudas_html=bar_activos_vs_deudas_html,
                ultimos_valores=data_filtrada.iloc[0].to_dict(),
                fechas_disponibles=fechas_disponibles,
                fecha_seleccionada=fecha_seleccionada
            )
        except FileNotFoundError:
            flash('No se encontraron datos para generar el análisis.', 'danger')
            return render_template('my_analysis_huevos.html')


    @app.route('/litchi_form', methods=['GET'])
    def litchi_form():
        user_id = session.get('user_id')
        if not user_id:
            flash('Por favor, inicia sesión para acceder al formulario.', 'danger')
            return redirect(url_for('login'))

        return render_template('litchi_form.html')


    # Ruta para guardar datos de litchi
    @app.route('/submit_litchi_form', methods=['POST'])
    def submit_litchi_form():
        user_id = session.get('user_id')
        if not user_id:
            flash('Por favor, inicia sesión.', 'danger')
            return redirect(url_for('login'))

        try:
            # Función para limpiar y convertir valores numéricos
            def parse_float(value):
                return float(value.replace(',', '').strip()) if value else 0

            # Datos específicos del formulario de litchi
            lugar_comercializacion = request.form.get('q10', '')
            if lugar_comercializacion == 'Other':
                lugar_comercializacion = f"Otro: {request.form.get('q10_other', '').strip()}"

            # Datos específicos del formulario de litchi
            data = {
                # Sección 1: Ingresos y Gastos
                'total_ingresos': parse_float(request.form.get('q1', '0')),
                'toneladas_cosechadas': parse_float(request.form.get('q1_1', '0')),
                'hectareas_sembradas': parse_float(request.form.get('q1_2', '0')),
                'gastos_insumos': parse_float(request.form.get('q2', '0')),
                'pago_jornales': parse_float(request.form.get('q3', '0')),
                'gastos_servicios': parse_float(request.form.get('q4', '0')),
                'valor_maquinaria': parse_float(request.form.get('q5', '0')),
                'dinero_disponible': parse_float(request.form.get('q6', '0')),
                'gastos_imprevistos': parse_float(request.form.get('q7', '0')),
                'total_deudas': parse_float(request.form.get('q8', '0')),

                # Sección 2: Procesos Productivos
                'trabajadores_necesarios': parse_float(request.form.get('q9', '0')),
                'lugar_comercializacion': lugar_comercializacion,

                # Fecha de captura enviada desde el formulario
                'fecha_captura': request.form.get('fecha_captura', '')
            }

            # Validar datos obligatorios
            if not data['total_ingresos'] or not data['toneladas_cosechadas'] or not data['hectareas_sembradas']:
                flash('Por favor, completa todos los campos obligatorios.', 'danger')
                return redirect(url_for('litchi_form'))

            # Cálculos financieros
            costos_directos = (
                data['gastos_insumos'] +
                data['pago_jornales'] +
                data['gastos_servicios'] +
                data['gastos_imprevistos']
            )
            data['utilidad_bruta'] = data['total_ingresos'] - costos_directos
            data['utilidad_neta'] = data['utilidad_bruta'] - data['total_deudas']
            activos_totales = data['dinero_disponible'] + data['valor_maquinaria']
            data['activos_totales'] = activos_totales
            data['patrimonio_neto'] = activos_totales - data['total_deudas']
            data['costo_por_hectarea'] = costos_directos / data['hectareas_sembradas'] if data['hectareas_sembradas'] else 0
            data['margen_ganancia'] = (data['utilidad_bruta'] / data['total_ingresos']) * 100 if data['total_ingresos'] else 0
            data['razon_endeudamiento'] = data['total_deudas'] / activos_totales if activos_totales else 0
            data['productividad_por_hectarea'] = data['toneladas_cosechadas'] / data['hectareas_sembradas'] if data['hectareas_sembradas'] else 0
            data['gastos_totales'] = costos_directos

            # Crear carpeta del usuario si no existe
            user_folder = os.path.join('data', user_id)
            if not os.path.exists(user_folder):
                os.makedirs(user_folder)

            # Ruta del archivo CSV
            file_path = os.path.join(user_folder, 'datos_financieros_litchi.csv')

            # Verificar si el archivo existe
            file_exists = os.path.isfile(file_path)

            # Guardar los datos en el archivo CSV
            with open(file_path, mode='a', newline='', encoding='utf-8') as file:
                writer = csv.DictWriter(file, fieldnames=data.keys())
                if not file_exists:
                    writer.writeheader()  # Escribir encabezado si el archivo no existe
                writer.writerow(data)  # Agregar los datos al archivo

            flash('Datos de litchi guardados exitosamente.', 'success')
            return redirect(url_for('dashboard_litchi'))

        except ValueError as e:
            flash(f'Error en los datos ingresados: {e}', 'danger')
            return redirect(url_for('litchi_form'))
        except Exception as e:
            flash(f'Ocurrió un error inesperado: {e}', 'danger')
            return redirect(url_for('litchi_form'))

        # Ruta para el dashboard de litchi
    @app.route('/dashboard_litchi')
    def dashboard_litchi():
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

        return render_template('dashboard_litchi.html', data=general_data)



    # Ruta para generar estados financieros de litchi
    @app.route('/financial_statements_litchi', methods=['GET', 'POST'])
    def financial_statements_litchi():
        user_id = session.get('user_id')
        if not user_id:
            flash('Por favor, inicia sesión para acceder a los estados financieros.', 'danger')
            return redirect(url_for('login'))

        # Ruta del archivo CSV
        user_folder = os.path.join('data', user_id)
        file_path = os.path.join(user_folder, 'datos_financieros_litchi.csv')

        financial_data = []
        selected_date = None

        if os.path.isfile(file_path):
            with open(file_path, mode='r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                financial_data = list(reader)

        # Ordenar las fechas de captura en orden descendente
        fechas_disponibles = sorted([row['fecha_captura'] for row in financial_data], reverse=True)

        # Si no se envía una fecha desde el formulario, usar la fecha más reciente
        if request.method == 'POST':
            selected_date = request.form.get('fecha_captura')
        elif fechas_disponibles:
            selected_date = fechas_disponibles[0]  # Fecha más reciente

        # Filtrar los datos por la fecha seleccionada
        filtered_data = [row for row in financial_data if row['fecha_captura'] == selected_date]

        # Calcular estados financieros y razones financieras
        if filtered_data:
            data = filtered_data[0]  # Tomar el primer registro filtrado

            # Calcular costos directos
            costos_directos = (
                float(data['gastos_insumos']) +
                float(data['pago_jornales']) +
                float(data['gastos_servicios']) +
                float(data['gastos_imprevistos'])
            )
            utilidad_bruta = float(data['total_ingresos']) - costos_directos
            utilidad_neta = utilidad_bruta
            activos_totales = float(data['dinero_disponible']) + float(data['valor_maquinaria'])
            patrimonio_neto = activos_totales - float(data['total_deudas'])
            total_gastos = costos_directos
            margen_ganancia = (utilidad_bruta / float(data['total_ingresos'])) * 100 if float(data['total_ingresos']) else 0
            razon_endeudamiento = float(data['total_deudas']) / activos_totales if activos_totales else 0

            # Calcular productividad por hectárea
            productividad_por_hectarea = float(data['toneladas_cosechadas']) / float(data['hectareas_sembradas']) if float(data['hectareas_sembradas']) > 0 else 0

            # Calcular costo por hectárea
            costo_por_hectarea = costos_directos / float(data['hectareas_sembradas']) if float(data['hectareas_sembradas']) > 0 else 0

            # Calcular Capital más Pasivo
            capital_mas_pasivo = patrimonio_neto + float(data['total_deudas'])

            # Valores de referencia para razones financieras
            referencias = {
                'margen_ganancia': 'Mayor al 20% es favorable',
                'razon_endeudamiento': 'Menor al 50% es favorable'
            }

            # Agregar datos de referencia
            datos_referencia = {
                'toneladas_cosechadas': float(data['toneladas_cosechadas']),
                'hectareas_sembradas': float(data['hectareas_sembradas']),
                'trabajadores_necesarios': float(data['trabajadores_necesarios']),
                'lugar_comercializacion': data['lugar_comercializacion']
            }

            # Generar interpretación AI
            interpretacion_ai = []

            if float(data['total_ingresos']) > total_gastos:
                interpretacion_ai.append("Los ingresos son mayores que los gastos, lo cual es positivo.")
            else:
                interpretacion_ai.append("Los gastos superan los ingresos, lo que indica posibles pérdidas.")

            if margen_ganancia >= 20:
                interpretacion_ai.append(f"El margen de ganancia es del {margen_ganancia:.2f}%, lo cual es favorable.")
            else:
                interpretacion_ai.append(f"El margen de ganancia es del {margen_ganancia:.2f}%, podría mejorar.")

            if razon_endeudamiento < 0.5:
                interpretacion_ai.append(f"La razón de endeudamiento es del {razon_endeudamiento:.2%}, lo cual es manejable.")
            else:
                interpretacion_ai.append(f"La razón de endeudamiento es del {razon_endeudamiento:.2%}, se recomienda reducir deudas.")

            interpretacion_ai.append(f"La productividad por hectárea es de {productividad_por_hectarea:.2f} toneladas.")
            interpretacion_ai.append(f"El costo por hectárea es de ${costo_por_hectarea:.2f}.")

            # Convertir lista a string
            interpretacion_ai = " ".join(interpretacion_ai)

            # Preparar datos para el HTML
            financial_summary = {
                'activos': {
                    'maquinaria_equipo': float(data['valor_maquinaria']),
                    'dinero_disponible': float(data['dinero_disponible']),
                    'total_activos': activos_totales
                },
                'pasivos': {
                    'deudas': float(data['total_deudas']),
                    'total_pasivos': float(data['total_deudas'])
                },
                'patrimonio': patrimonio_neto,
                'capital_mas_pasivo': capital_mas_pasivo,
                'ingresos': {
                    'venta_litchi': float(data['total_ingresos'])
                },
                'gastos': {
                    'insumos': float(data['gastos_insumos']),
                    'jornales': float(data['pago_jornales']),
                    'servicios': float(data['gastos_servicios']),
                    'imprevistos': float(data['gastos_imprevistos']),
                    'total_gastos': total_gastos
                },
                'utilidad_neta': utilidad_neta,
                'razones_financieras': {
                    'margen_ganancia': margen_ganancia,
                    'razon_endeudamiento': razon_endeudamiento,
                    'productividad_por_hectarea': productividad_por_hectarea,
                    'costo_por_hectarea': costo_por_hectarea
                },
                'referencias': referencias,
                'datos_referencia': datos_referencia,
                'fecha_captura': selected_date,
                'interpretacion_ai': interpretacion_ai
            }
        else:
            financial_summary = None

        return render_template('financial_statements_litchi.html', data=financial_summary, fechas=fechas_disponibles)

    @app.route('/database_access_litchi', methods=['GET'])
    def database_access_litchi():
        user_id = session.get('user_id')
        if not user_id:
            flash('Por favor, inicia sesión para acceder a la base de datos.', 'danger')
            return redirect(url_for('login'))

        # Ruta del archivo CSV
        user_folder = os.path.join('data', user_id)
        file_path = os.path.join(user_folder, 'datos_financieros_litchi.csv')

        data = []
        fechas = []
        rubros = [
            {'key': 'total_ingresos', 'label': 'Total de Ingresos'},
            {'key': 'toneladas_cosechadas', 'label': 'Toneladas Cosechadas'},
            {'key': 'hectareas_sembradas', 'label': 'Hectáreas Sembradas'},
            {'key': 'gastos_insumos', 'label': 'Gastos en Insumos'},
            {'key': 'pago_jornales', 'label': 'Pago de Jornales'},
            {'key': 'gastos_servicios', 'label': 'Gastos en Servicios'},
            {'key': 'valor_maquinaria', 'label': 'Valor de Maquinaria'},
            {'key': 'dinero_disponible', 'label': 'Dinero Disponible'},
            {'key': 'gastos_imprevistos', 'label': 'Gastos Imprevistos'},
            {'key': 'total_deudas', 'label': 'Total de Deudas'},
            {'key': 'trabajadores_necesarios', 'label': 'Trabajadores Necesarios'},
            {'key': 'lugar_comercializacion', 'label': 'Lugar de Comercialización'},
            {'key': 'fecha_captura', 'label': 'Fecha de Captura'},
            {'key': 'utilidad_bruta', 'label': 'Utilidad Bruta'},
            {'key': 'utilidad_neta', 'label': 'Utilidad Neta'},
            {'key': 'activos_totales', 'label': 'Activos Totales'},
            {'key': 'patrimonio_neto', 'label': 'Patrimonio Neto'},
            {'key': 'costo_por_hectarea', 'label': 'Costo por Hectárea'},
            {'key': 'margen_ganancia', 'label': 'Margen de Ganancia (%)'},
            {'key': 'razon_endeudamiento', 'label': 'Razón de Endeudamiento'},
            {'key': 'productividad_por_hectarea', 'label': 'Productividad por Hectárea'},
            {'key': 'gastos_totales', 'label': 'Gastos Totales'}
        ]

        if os.path.isfile(file_path):
            with open(file_path, mode='r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                data = list(reader)
                fechas = sorted({row['fecha_captura'] for row in data}, reverse=True)

        return render_template('database_access_litchi.html', data=data, rubros=rubros, fechas=fechas)



    @app.route('/my_analysis_litchi', methods=['GET', 'POST'])
    def my_analysis_litchi():
        user_id = session.get('user_id')
        if not user_id:
            flash('Por favor, inicia sesión para acceder al análisis.', 'danger')
            return redirect(url_for('login'))

        # Ruta del archivo CSV
        file_path = f"data/{user_id}/datos_financieros_litchi.csv"
        try:
            data = pd.read_csv(file_path)

            # Ordenar las fechas y obtener la más reciente
            data['fecha_captura'] = pd.to_datetime(data['fecha_captura'], format='%d/%m/%Y', errors='coerce')
            data = data.sort_values(by='fecha_captura', ascending=False)
            fechas_disponibles = data['fecha_captura'].dt.strftime('%Y-%m-%d').unique()
            fecha_seleccionada = request.form.get('fecha_captura', fechas_disponibles[0])

            # Filtrar los datos por la fecha seleccionada
            data_filtrada = data[data['fecha_captura'] == pd.to_datetime(fecha_seleccionada)]

            # Cálculos obligatorios
            if 'gastos_insumos' in data.columns and 'pago_jornales' in data.columns and \
            'gastos_servicios' in data.columns and 'gastos_imprevistos' in data.columns:
                data['gastos_totales'] = (
                    data['gastos_insumos'] + data['pago_jornales'] + data['gastos_servicios'] +
                    data['gastos_imprevistos']
                )
            else:
                flash('Faltan columnas necesarias para calcular gastos totales.', 'danger')
                return render_template('my_analysis_litchi.html')

            # Verifica que la columna 'gastos_totales' exista
            if 'gastos_totales' not in data.columns:
                flash('Error al calcular gastos totales. Verifica los datos.', 'danger')
                return render_template('my_analysis_litchi.html')

            # Gráficos para Rentabilidad
            fig_sunburst = px.sunburst(
                data_filtrada,
                path=['gastos_insumos', 'pago_jornales', 'gastos_servicios', 'gastos_imprevistos'],
                values='gastos_totales',
                title="Jerarquía de Gastos"
            )
            fig_line = px.line(
                data,
                x='fecha_captura',
                y=['total_ingresos', 'utilidad_neta'],
                title="Ingresos vs. Utilidad Neta"
            )
            fig_bar = px.bar(
                data,
                x='fecha_captura',
                y=['total_ingresos', 'gastos_totales'],
                title="Ingresos vs. Gastos Totales"
            )

            # Convertir gráficos a HTML
            sunburst_html = fig_sunburst.to_html(full_html=False)
            line_html = fig_line.to_html(full_html=False)
            bar_html = fig_bar.to_html(full_html=False)

            # Gráficos para Producción
            # Productividad por hectárea
            data['productividad_por_hectarea'] = data['toneladas_cosechadas'] / data['hectareas_sembradas']
            fig_bar_produccion = px.bar(
                data,
                x='fecha_captura',
                y='productividad_por_hectarea',
                title="Productividad por Hectárea"
            )

            # Costos de insumos vs ingresos
            fig_line_costos_vs_ingresos = px.line(
                data,
                x='fecha_captura',
                y=['total_ingresos', 'gastos_insumos'],
                title="Costos de Insumos vs Ingresos Totales"
            )

            # Costo por hectárea
            data['costo_por_hectarea'] = data['gastos_totales'] / data['hectareas_sembradas']
            fig_line_costo_por_hectarea = px.line(
                data,
                x='fecha_captura',
                y='costo_por_hectarea',
                title="Costo por Hectárea"
            )

            # Convertir gráficos a HTML
            bar_produccion_html = fig_bar_produccion.to_html(full_html=False)
            line_costos_vs_ingresos_html = fig_line_costos_vs_ingresos.to_html(full_html=False)
            line_costo_por_hectarea_html = fig_line_costo_por_hectarea.to_html(full_html=False)

            # Gráficos para Patrimonio
            # Composición del patrimonio neto
            fig_pie_patrimonio = px.pie(
                data_filtrada,
                names=['patrimonio_neto', 'activos_totales', 'valor_maquinaria'],
                values=[data_filtrada['patrimonio_neto'].sum(), data_filtrada['activos_totales'].sum(), data_filtrada['valor_maquinaria'].sum()],
                title="Composición del Patrimonio Neto"
            )

            # Razón de endeudamiento
            fig_line_razon_endeudamiento = px.line(
                data,
                x='fecha_captura',
                y='razon_endeudamiento',
                title="Razón de Endeudamiento vs Tiempo"
            )

            # Activos vs deudas
            fig_bar_activos_vs_deudas = px.bar(
                data,
                x='fecha_captura',
                y=['activos_totales', 'total_deudas'],
                barmode='group',
                title="Activos Totales vs Total de Deudas"
            )

            # Convertir gráficos a HTML
            pie_patrimonio_html = fig_pie_patrimonio.to_html(full_html=False)
            line_razon_endeudamiento_html = fig_line_razon_endeudamiento.to_html(full_html=False)
            bar_activos_vs_deudas_html = fig_bar_activos_vs_deudas.to_html(full_html=False)

            return render_template(
                'my_analysis_litchi.html',
                sunburst_html=sunburst_html,
                line_html=line_html,
                bar_html=bar_html,
                bar_produccion_html=bar_produccion_html,
                line_costos_vs_ingresos_html=line_costos_vs_ingresos_html,
                line_costo_por_hectarea_html=line_costo_por_hectarea_html,
                pie_patrimonio_html=pie_patrimonio_html,
                line_razon_endeudamiento_html=line_razon_endeudamiento_html,
                bar_activos_vs_deudas_html=bar_activos_vs_deudas_html,
                ultimos_valores=data_filtrada.iloc[0].to_dict(),
                fechas_disponibles=fechas_disponibles,
                fecha_seleccionada=fecha_seleccionada
            )
        except FileNotFoundError:
            flash('No se encontraron datos para generar el análisis.', 'danger')
            return render_template('my_analysis_litchi.html')



    @app.route('/dashboard_citricos')
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
    @app.route('/submit_citrus_form', methods=['POST'])
    def submit_citrus_form():
        user_id = session.get('user_id')
        if not user_id:
            flash('Por favor, inicia sesión.', 'danger')
            return redirect(url_for('login'))

        try:
            # Función para limpiar y convertir valores numéricos
            def parse_float(value):
                return float(value.replace(',', '').strip()) if value else 0

            # Procesar el campo "Otro" para tipos de cítricos (q1_3)
            tipos_citricos = request.form.getlist('q1_3')
            if 'other' in tipos_citricos:
                otros_citricos = request.form.get('otherInput1', '').strip()
                if otros_citricos:
                    tipos_citricos.append(f"Otro: {otros_citricos}")
                tipos_citricos.remove('other')  # Eliminar la opción "other" de la lista

            # Procesar el campo "Otro" para lugares de comercialización (q11)
            lugares_comercializacion = request.form.getlist('q11')
            if 'other' in lugares_comercializacion:
                otro_lugar = request.form.get('otherInput2', '').strip()
                if otro_lugar:
                    lugares_comercializacion.append(f"Otro: {otro_lugar}")
                lugares_comercializacion.remove('other')  # Eliminar la opción "other" de la lista

            # Datos específicos del formulario de cítricos
            data = {
                'total_ingresos': parse_float(request.form.get('q1', '0')),
                'toneladas_cosechadas': parse_float(request.form.get('q1_2', '0')),
                'tipos_citricos': ', '.join(tipos_citricos),  # Convertir lista a cadena
                'hectareas': parse_float(request.form.get('q1_4', '0')),
                'gastos_insumos': parse_float(request.form.get('q2', '0')),
                'pago_jornales': parse_float(request.form.get('q3', '0')),
                'gastos_servicios': parse_float(request.form.get('q4', '0')),
                'valor_maquinaria': parse_float(request.form.get('q5', '0')),
                'dinero_disponible': parse_float(request.form.get('q6', '0')),
                'gastos_imprevistos': parse_float(request.form.get('q7', '0')),
                'total_deudas': parse_float(request.form.get('q8', '0')),
                'trabajadores_necesarios': parse_float(request.form.get('q9', '0')),
                'dias_supervision': parse_float(request.form.get('q10', '0')),
                'lugares_comercializacion': ', '.join(lugares_comercializacion),  # Convertir lista a cadena
                'fecha_captura': request.form.get('fecha_captura', ''),
                'comentarios': request.form.get('comments', '').strip()
            }

            # Validar datos obligatorios
            if not data['total_ingresos'] or not data['toneladas_cosechadas'] or not data['hectareas']:
                flash('Por favor, completa todos los campos obligatorios.', 'danger')
                return redirect(url_for('citricos_form'))

            # Cálculos financieros
            costos_directos = (
                data['gastos_insumos'] +
                data['pago_jornales'] +
                data['gastos_servicios'] +
                data['gastos_imprevistos']
            )
            data['utilidad_bruta'] = data['total_ingresos'] - costos_directos
            data['utilidad_neta'] = data['utilidad_bruta'] - data['total_deudas']
            activos_totales = data['dinero_disponible'] + data['valor_maquinaria']
            data['activos_totales'] = activos_totales
            data['patrimonio_neto'] = activos_totales - data['total_deudas']
            data['costo_por_hectarea'] = costos_directos / data['hectareas'] if data['hectareas'] else 0
            data['margen_ganancia'] = (data['utilidad_bruta'] / data['total_ingresos']) * 100 if data['total_ingresos'] else 0
            data['razon_endeudamiento'] = data['total_deudas'] / activos_totales if activos_totales else 0
            data['productividad_por_hectarea'] = data['toneladas_cosechadas'] / data['hectareas'] if data['hectareas'] else 0
            data['gastos_totales'] = costos_directos

            # Crear carpeta del usuario si no existe
            user_folder = os.path.join('data', user_id)
            if not os.path.exists(user_folder):
                os.makedirs(user_folder)

            # Ruta del archivo CSV
            file_path = os.path.join(user_folder, 'datos_financieros_citricos.csv')

            # Verificar si el archivo existe
            file_exists = os.path.isfile(file_path)

            # Guardar los datos en el archivo CSV
            with open(file_path, mode='a', newline='', encoding='utf-8') as file:
                writer = csv.DictWriter(file, fieldnames=data.keys())
                if not file_exists:
                    writer.writeheader()  # Escribir encabezado si el archivo no existe
                writer.writerow(data)  # Agregar los datos al archivo

            flash('Datos de cítricos guardados exitosamente.', 'success')
            return redirect(url_for('dashboard_citricos'))

        except ValueError as e:
            flash(f'Error en los datos ingresados: {e}', 'danger')
            return redirect(url_for('citricos_form'))
        except Exception as e:
            flash(f'Ocurrió un error inesperado: {e}', 'danger')
            return redirect(url_for('citricos_form'))

    # Ruta para acceder a los datos financieros de cítricos
    # @app.route('/database_access_citricos')
    @app.route('/database_access_citricos', methods=['GET'])
    def database_access_citricos():
        user_id = session.get('user_id')
        if not user_id:
            flash('Por favor, inicia sesión para acceder a la base de datos.', 'danger')
            return redirect(url_for('login'))

        # Ruta del archivo CSV
        user_folder = os.path.join('data', user_id)
        file_path = os.path.join(user_folder, 'datos_financieros_citricos.csv')

        data = []
        fechas = []
        rubros = [
            {'key': 'total_ingresos', 'label': 'Total de Ingresos'},
            {'key': 'toneladas_cosechadas', 'label': 'Toneladas Cosechadas'},
            {'key': 'tipos_citricos', 'label': 'Tipos de Cítricos'},
            {'key': 'hectareas', 'label': 'Hectáreas'},
            {'key': 'gastos_insumos', 'label': 'Gastos en Insumos'},
            {'key': 'pago_jornales', 'label': 'Pago de Jornales'},
            {'key': 'gastos_servicios', 'label': 'Gastos en Servicios'},
            {'key': 'valor_maquinaria', 'label': 'Valor de Maquinaria'},
            {'key': 'dinero_disponible', 'label': 'Dinero Disponible'},
            {'key': 'gastos_imprevistos', 'label': 'Gastos Imprevistos'},
            {'key': 'total_deudas', 'label': 'Total de Deudas'},
            {'key': 'trabajadores_necesarios', 'label': 'Trabajadores Necesarios'},
            {'key': 'dias_supervision', 'label': 'Días de Supervisión'},
            {'key': 'lugares_comercializacion', 'label': 'Lugares de Comercialización'},
            {'key': 'fecha_captura', 'label': 'Fecha de Captura'},
            {'key': 'comentarios', 'label': 'Comentarios'},
            {'key': 'utilidad_bruta', 'label': 'Utilidad Bruta'},
            {'key': 'utilidad_neta', 'label': 'Utilidad Neta'},
            {'key': 'activos_totales', 'label': 'Activos Totales'},
            {'key': 'patrimonio_neto', 'label': 'Patrimonio Neto'},
            {'key': 'costo_por_hectarea', 'label': 'Costo por Hectárea'},
            {'key': 'margen_ganancia', 'label': 'Margen de Ganancia (%)'},
            {'key': 'razon_endeudamiento', 'label': 'Razón de Endeudamiento'},
            {'key': 'productividad_por_hectarea', 'label': 'Productividad por Hectárea'},
            {'key': 'gastos_totales', 'label': 'Gastos Totales'}
        ]

        if os.path.isfile(file_path):
            with open(file_path, mode='r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                data = list(reader)
                fechas = sorted({row['fecha_captura'] for row in data}, reverse=True)

        return render_template('database_access_citricos.html', data=data, rubros=rubros, fechas=fechas)


    # Ruta para generar estados financieros de cítricos
    # @app.route('/financial_statements_citricos')
    @app.route('/financial_statements_citricos', methods=['GET', 'POST'])
    def financial_statements_citricos():
        user_id = session.get('user_id')
        if not user_id:
            flash('Por favor, inicia sesión para acceder a los estados financieros.', 'danger')
            return redirect(url_for('login'))

        # Ruta del archivo CSV
        user_folder = os.path.join('data', user_id)
        file_path = os.path.join(user_folder, 'datos_financieros_citricos.csv')

        financial_data = []
        selected_date = None

        if os.path.isfile(file_path):
            with open(file_path, mode='r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                financial_data = list(reader)

        # Ordenar las fechas de captura en orden descendente
        fechas_disponibles = sorted([row['fecha_captura'] for row in financial_data], reverse=True)

        # Si no se envía una fecha desde el formulario, usar la fecha más reciente
        if request.method == 'POST':
            selected_date = request.form.get('fecha_captura')
        elif fechas_disponibles:
            selected_date = fechas_disponibles[0]  # Fecha más reciente

        # Filtrar los datos por la fecha seleccionada
        filtered_data = [row for row in financial_data if row['fecha_captura'] == selected_date]

        # Calcular estados financieros y razones financieras
        if filtered_data:
            data = filtered_data[0]  # Tomar el primer registro filtrado

            # Calcular costos directos
            costos_directos = (
                float(data['gastos_insumos']) +
                float(data['pago_jornales']) +
                float(data['gastos_servicios']) +
                float(data['gastos_imprevistos'])
            )
            utilidad_bruta = float(data['total_ingresos']) - costos_directos
            utilidad_neta = utilidad_bruta
            activos_totales = float(data['dinero_disponible']) + float(data['valor_maquinaria'])
            patrimonio_neto = activos_totales - float(data['total_deudas'])
            total_gastos = costos_directos
            margen_ganancia = (utilidad_bruta / float(data['total_ingresos'])) * 100 if float(data['total_ingresos']) else 0
            razon_endeudamiento = float(data['total_deudas']) / activos_totales if activos_totales else 0

            # Calcular productividad por hectárea
            productividad_por_hectarea = float(data['toneladas_cosechadas']) / float(data['hectareas']) if float(data['hectareas']) > 0 else 0

            # Calcular costo por hectárea
            costo_por_hectarea = costos_directos / float(data['hectareas']) if float(data['hectareas']) > 0 else 0

            # Calcular Capital más Pasivo
            capital_mas_pasivo = patrimonio_neto + float(data['total_deudas'])

            # Valores de referencia para razones financieras
            referencias = {
                'margen_ganancia': 'Mayor al 20% es favorable',
                'razon_endeudamiento': 'Menor al 50% es favorable'
            }

            # Agregar datos de referencia
            datos_referencia = {
                'toneladas_cosechadas': float(data['toneladas_cosechadas']),
                'hectareas': float(data['hectareas']),
                'trabajadores_necesarios': float(data['trabajadores_necesarios']),
                'lugares_comercializacion': data['lugares_comercializacion']
            }

            # Generar interpretación AI
            interpretacion_ai = []

            if float(data['total_ingresos']) > total_gastos:
                interpretacion_ai.append("Los ingresos son mayores que los gastos, lo cual es positivo.")
            else:
                interpretacion_ai.append("Los gastos superan los ingresos, lo que indica posibles pérdidas.")

            if margen_ganancia >= 20:
                interpretacion_ai.append(f"El margen de ganancia es del {margen_ganancia:.2f}%, lo cual es favorable.")
            else:
                interpretacion_ai.append(f"El margen de ganancia es del {margen_ganancia:.2f}%, podría mejorar.")

            if razon_endeudamiento < 0.5:
                interpretacion_ai.append(f"La razón de endeudamiento es del {razon_endeudamiento:.2%}, lo cual es manejable.")
            else:
                interpretacion_ai.append(f"La razón de endeudamiento es del {razon_endeudamiento:.2%}, se recomienda reducir deudas.")

            interpretacion_ai.append(f"La productividad por hectárea es de {productividad_por_hectarea:.2f} toneladas.")
            interpretacion_ai.append(f"El costo por hectárea es de ${costo_por_hectarea:.2f}.")

            # Convertir lista a string
            interpretacion_ai = " ".join(interpretacion_ai)

            # Preparar datos para el HTML
            financial_summary = {
                'activos': {
                    'maquinaria_equipo': float(data['valor_maquinaria']),
                    'dinero_disponible': float(data['dinero_disponible']),
                    'total_activos': activos_totales
                },
                'pasivos': {
                    'deudas': float(data['total_deudas']),
                    'total_pasivos': float(data['total_deudas'])
                },
                'patrimonio': patrimonio_neto,
                'capital_mas_pasivo': capital_mas_pasivo,
                'ingresos': {
                    'venta_citricos': float(data['total_ingresos'])
                },
                'gastos': {
                    'insumos': float(data['gastos_insumos']),
                    'jornales': float(data['pago_jornales']),
                    'servicios': float(data['gastos_servicios']),
                    'imprevistos': float(data['gastos_imprevistos']),
                    'total_gastos': total_gastos
                },
                'utilidad_neta': utilidad_neta,
                'razones_financieras': {
                    'margen_ganancia': margen_ganancia,
                    'razon_endeudamiento': razon_endeudamiento,
                    'productividad_por_hectarea': productividad_por_hectarea,
                    'costo_por_hectarea': costo_por_hectarea
                },
                'referencias': referencias,
                'datos_referencia': datos_referencia,
                'fecha_captura': selected_date,
                'interpretacion_ai': interpretacion_ai
            }
        else:
            financial_summary = None

        return render_template('financial_statements_citricos.html', data=financial_summary, fechas=fechas_disponibles)

    @app.route('/citricos_form', methods=['GET'])
    def citricos_form():
        user_id = session.get('user_id')
        if not user_id:
            flash('Por favor, inicia sesión para acceder al formulario.', 'danger')
            return redirect(url_for('login'))

        return render_template('citricos_form.html')

    @app.route('/my_analysis_citricos', methods=['GET', 'POST'])
    def my_analysis_citricos():
        user_id = session.get('user_id')
        if not user_id:
            flash('Por favor, inicia sesión para acceder al análisis.', 'danger')
            return redirect(url_for('login'))

        # Ruta del archivo CSV
        file_path = f"data/{user_id}/datos_financieros_citricos.csv"
        try:
            data = pd.read_csv(file_path)

            # Ordenar las fechas y obtener la más reciente
            data['fecha_captura'] = pd.to_datetime(data['fecha_captura'], format='%d/%m/%Y', errors='coerce')
            data = data.sort_values(by='fecha_captura', ascending=False)
            fechas_disponibles = data['fecha_captura'].dt.strftime('%Y-%m-%d').unique()
            fecha_seleccionada = request.form.get('fecha_captura', fechas_disponibles[0])

            # Filtrar los datos por la fecha seleccionada
            data_filtrada = data[data['fecha_captura'] == pd.to_datetime(fecha_seleccionada)]

            # Cálculos obligatorios
            if 'gastos_insumos' in data.columns and 'pago_jornales' in data.columns and \
            'gastos_servicios' in data.columns and 'gastos_imprevistos' in data.columns:
                data['gastos_totales'] = (
                    data['gastos_insumos'] + data['pago_jornales'] + data['gastos_servicios'] +
                    data['gastos_imprevistos']
                )
            else:
                flash('Faltan columnas necesarias para calcular gastos totales.', 'danger')
                return render_template('my_analysis_citricos.html')

            # Verifica que la columna 'gastos_totales' exista
            if 'gastos_totales' not in data.columns:
                flash('Error al calcular gastos totales. Verifica los datos.', 'danger')
                return render_template('my_analysis_citricos.html')

            # Gráficos para Rentabilidad
            fig_sunburst = px.sunburst(
                data_filtrada,
                path=['gastos_insumos', 'pago_jornales', 'gastos_servicios', 'gastos_imprevistos'],
                values='gastos_totales',
                title="Jerarquía de Gastos"
            )
            fig_line = px.line(
                data,
                x='fecha_captura',
                y=['total_ingresos', 'utilidad_neta'],
                title="Ingresos vs. Utilidad Neta"
            )
            fig_bar = px.bar(
                data,
                x='fecha_captura',
                y=['total_ingresos', 'gastos_totales'],
                title="Ingresos vs. Gastos Totales"
            )

            # Convertir gráficos a HTML
            sunburst_html = fig_sunburst.to_html(full_html=False)
            line_html = fig_line.to_html(full_html=False)
            bar_html = fig_bar.to_html(full_html=False)

            # Gráficos para Producción
            # Productividad por hectárea
            data['productividad_por_hectarea'] = data['toneladas_cosechadas'] / data['hectareas']
            fig_bar_produccion = px.bar(
                data,
                x='fecha_captura',
                y='productividad_por_hectarea',
                title="Productividad por Hectárea"
            )

            # Costos de insumos vs ingresos
            fig_line_costos_vs_ingresos = px.line(
                data,
                x='fecha_captura',
                y=['total_ingresos', 'gastos_insumos'],
                title="Costos de Insumos vs Ingresos Totales"
            )

            # Costo por hectárea
            data['costo_por_hectarea'] = data['gastos_totales'] / data['hectareas']
            fig_line_costo_por_hectarea = px.line(
                data,
                x='fecha_captura',
                y='costo_por_hectarea',
                title="Costo por Hectárea"
            )

            # Convertir gráficos a HTML
            bar_produccion_html = fig_bar_produccion.to_html(full_html=False)
            line_costos_vs_ingresos_html = fig_line_costos_vs_ingresos.to_html(full_html=False)
            line_costo_por_hectarea_html = fig_line_costo_por_hectarea.to_html(full_html=False)

            # Gráficos para Patrimonio
            # Composición del patrimonio neto
            fig_pie_patrimonio = px.pie(
                data_filtrada,
                names=['patrimonio_neto', 'activos_totales', 'valor_maquinaria'],
                values=[data_filtrada['patrimonio_neto'].sum(), data_filtrada['activos_totales'].sum(), data_filtrada['valor_maquinaria'].sum()],
                title="Composición del Patrimonio Neto"
            )

            # Razón de endeudamiento
            fig_line_razon_endeudamiento = px.line(
                data,
                x='fecha_captura',
                y='razon_endeudamiento',
                title="Razón de Endeudamiento vs Tiempo"
            )

            # Activos vs deudas
            fig_bar_activos_vs_deudas = px.bar(
                data,
                x='fecha_captura',
                y=['activos_totales', 'total_deudas'],
                barmode='group',
                title="Activos Totales vs Total de Deudas"
            )

            # Convertir gráficos a HTML
            pie_patrimonio_html = fig_pie_patrimonio.to_html(full_html=False)
            line_razon_endeudamiento_html = fig_line_razon_endeudamiento.to_html(full_html=False)
            bar_activos_vs_deudas_html = fig_bar_activos_vs_deudas.to_html(full_html=False)

            return render_template(
                'my_analysis_citricos.html',
                sunburst_html=sunburst_html,
                line_html=line_html,
                bar_html=bar_html,
                bar_produccion_html=bar_produccion_html,
                line_costos_vs_ingresos_html=line_costos_vs_ingresos_html,
                line_costo_por_hectarea_html=line_costo_por_hectarea_html,
                pie_patrimonio_html=pie_patrimonio_html,
                line_razon_endeudamiento_html=line_razon_endeudamiento_html,
                bar_activos_vs_deudas_html=bar_activos_vs_deudas_html,
                ultimos_valores=data_filtrada.iloc[0].to_dict(),
                fechas_disponibles=fechas_disponibles,
                fecha_seleccionada=fecha_seleccionada
            )
        except FileNotFoundError:
            flash('No se encontraron datos para generar el análisis.', 'danger')
            return render_template('my_analysis_citricos.html')

        
    @app.route('/dashboard_coffee')
    def dashboard_coffee():
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

            return render_template('dashboard_coffee.html', data=general_data)


    @app.route('/climatico', methods=['GET'])
    def climatico():
        
        return render_template('climatico.html')

    
    # Carga de modelo de embeddings
    embedder = SentenceTransformer('all-MiniLM-L6-v2')

    # Cargar base de datos de preguntas y respuestas desde JSON
    with open("faq_ganado.json", "r", encoding="utf-8") as f:
        faq_data = json.load(f)

    # Precalcular embeddings de las preguntas
    faq_embeddings = embedder.encode([item["pregunta"] for item in faq_data])

    # Lista de respuestas afirmativas
    AFFIRMATIVE_RESPONSES = {"sí", "si", "así es", "correcto", "exacto", "sí, eso es", "afirmativo", "claro", "claro que sí"}

    # Lista de saludos
    GREETINGS = {"hola", "buenos días", "buenas tardes", "buenas noches", "qué tal", "hey"}

    def buscar_respuesta(pregunta_usuario, session_data=None):
        embedding_usuario = embedder.encode([pregunta_usuario])
        similitudes = cosine_similarity(embedding_usuario, faq_embeddings)[0]

        idx_max = np.argmax(similitudes)
        similitud_max = similitudes[idx_max]
        pregunta_cercana = faq_data[idx_max]["pregunta"]

        if similitud_max >= 0.95:  # Umbral para respuesta directa
            return {
                "respuesta": faq_data[idx_max]["respuesta"],
                "session_data": None
            }
        elif similitud_max >= 0.5:  # Umbral para sugerir pregunta cercana
            return {
                "respuesta": f"¿Te refieres a '{pregunta_cercana}'?",
                "session_data": {
                    "pending_question": pregunta_usuario,
                    "suggested_question": pregunta_cercana,
                    "suggested_index": int(idx_max),
                    "similitud": float(similitud_max)
                }
            }
        else:
            return {
                "respuesta": "Disculpa, esa información no está en mi base de datos. ¿Algo más en lo que pueda ayudarte?",
                "session_data": None
            }

    # Función para manejar interacciones generales como saludos
    def manejar_interaccion_general(pregunta_usuario):
        if pregunta_usuario.lower() in GREETINGS:
            return "¡Hola! ¿Cómo estás? Entusiasta de la ganadería, ¿en qué puedo ayudarte hoy?"
        return None

    @app.route('/preguntar', methods=['POST'])
    def preguntar():
        data = request.get_json()
        pregunta = data.get("pregunta")
        session_data = data.get("session_data")

        if not pregunta:
            return jsonify({"respuesta": "Por favor, escribe una pregunta válida."}), 400

        # Manejar interacciones generales
        respuesta_general = manejar_interaccion_general(pregunta)
        if respuesta_general:
            return jsonify({"respuesta": respuesta_general, "session_data": None})

        if session_data:
            print("Session data recibida:", session_data)  # Depuración
            print("Respuesta usuario:", pregunta)  # Depuración

            respuesta_usuario = pregunta.lower().strip()
            respuesta_usuario = respuesta_usuario.replace("¿", "").replace("?", "")  # Limpieza extra

            # ✅ CASO 2.1: El usuario acepta la sugerencia
            if respuesta_usuario in AFFIRMATIVE_RESPONSES:
                idx = session_data.get("suggested_index")
                if idx is not None and 0 <= idx < len(faq_data):
                    return jsonify({
                        "respuesta": faq_data[idx]["respuesta"],
                        "session_data": None
                    })
                else:
                    return jsonify({
                        "respuesta": "Error: No se encontró la respuesta sugerida. ¿Algo más en lo que pueda ayudarte?",
                        "session_data": None
                    })
            else:
                # ❌ CASO 2.2: El usuario rechaza o no confirma
                return jsonify({
                    "respuesta": "Entiendo. ¿Podés reformular tu pregunta?",
                    "session_data": None
                })

        # 🟢 CASO 1, 2 o 3: Primera vez que hace la pregunta
        resultado = buscar_respuesta(pregunta)
        print("Resultado enviado:", resultado)  # Depuración
        return jsonify({
            "respuesta": resultado["respuesta"],
            "session_data": resultado["session_data"]
        })

