from flask import Blueprint, render_template, request, jsonify
import requests
import pandas as pd
from datetime import datetime

climate_analysis_bp = Blueprint('climate_analysis', __name__)

@climate_analysis_bp.route('/', methods=['GET', 'POST'])
def climate_analysis():
    if request.method == 'POST':
        # Handle CSV upload
        if 'file' in request.files:
            file = request.files['file']
            if file.filename.endswith('.csv'):
                data = pd.read_csv(file)
                # Process the CSV data as needed
                return jsonify({'message': 'CSV data processed successfully'}), 200
        
        # Handle API request
        location = request.form.get('location')
        if location:
            api_key = 'YOUR_API_KEY'  # Replace with your actual API key
            response = requests.get(f'https://api.openweathermap.org/data/2.5/weather?q={location}&appid={api_key}')
            if response.status_code == 200:
                weather_data = response.json()
                # Process weather data as needed
                return jsonify(weather_data), 200
            else:
                return jsonify({'error': 'Failed to fetch weather data'}), 400

    return render_template('climate_analysis.html')
