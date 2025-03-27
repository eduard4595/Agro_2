from flask import Blueprint, render_template, session, flash, redirect, url_for
from app.models import read_general_data

financial_info_bp = Blueprint('financial_info', __name__)

@financial_info_bp.route('/financial-info')
def financial_info():
    user_id = session.get('user_id')
    if not user_id:
        flash('Por favor, inicia sesión para acceder a esta página.', 'danger')
        return redirect(url_for('login'))

    # Leer datos generales desde el archivo CSV
    general_data = read_general_data(user_id, 'cafe')  # Cambiamos la consulta SQL por la lectura del archivo CSV
    if not general_data:
        flash('No se encontraron datos generales para este usuario.', 'danger')
        return redirect(url_for('datos_generales'))

    return render_template('financial_info.html', general_data=general_data)