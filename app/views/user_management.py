from flask import Blueprint, render_template

user_management_bp = Blueprint('user_management', __name__)

@user_management_bp.route('/')
def user_management():
    return render_template('user_management.html')
