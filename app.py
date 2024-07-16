from flask import Flask, request, jsonify, render_template
import pandas as pd
import requests
from io import StringIO

app = Flask(__name__)

# Direct download URL from OneDrive
file_url ='https://tmpfiles.org/dl/9206840/menupricingrawdatafirst.csv'
def load_data(file_url):
    try:
        # Download the Excel file from the URL
        response = requests.get(file_url)
        response.raise_for_status()  # Check if the request was successful
        
        # Read the CSV file into a pandas DataFrame
        data = pd.read_csv(StringIO(response.text))
        
        # Fill NaN values in operation columns with zeros
        labour_columns = [col for col in data.columns if 'L Time' in col]
        paint_columns = [col for col in data.columns if 'P Time' in col]
        
        data[labour_columns] = data[labour_columns].fillna(0)
        data[paint_columns] = data[paint_columns].fillna(0)
        data = data[(data[labour_columns].sum(axis=1) != 0) | (data[paint_columns].sum(axis=1) != 0)]
        
        return data, labour_columns, paint_columns, None
    except Exception as e:
        return None, None, None, str(e)

def calculate_times(data, labour_columns, paint_columns, car_type, price, damaged_part, damage_type, damage_severity, area_code,price_range=0):
    # Define the price range
    min_price = price - price_range
    max_price = price + price_range

    # Filter data based on input parameters
    filtered_data = data[
        (data['price'] >= min_price) &
        (data['price'] <= max_price) &
        (data['car_type'].str.lower() == car_type) &
        (data['damage_severity'].str.lower() == damage_severity) &
        (data['damage_type'].str.lower() == damage_type) &
        (data['area_code'] == area_code) &
        (data['damaged_part'].str.lower() == damaged_part)
    ]
    
    # If filtered_data is not empty, calculate total labour and paint time for exact match
    if not filtered_data.empty:
        total_labour_time = filtered_data[labour_columns].sum(axis=1).values[0]
        total_paint_time = filtered_data[paint_columns].sum(axis=1).values[0]
        return total_labour_time, total_paint_time, "Exact match found."

    # Estimation based on similar data if no exact match is found
    similar_data_1 = data[
        (data['price'] >= min_price) &
        (data['price'] <= max_price) &
        (data['car_type'].str.lower() == car_type) &
        (data['damage_severity'].str.lower() == damage_severity) &
        (data['damage_type'].str.lower() == damage_type) &
        (data['area_code'] == area_code)
    ]

    if not similar_data_1.empty:
        total_labour_time = similar_data_1[labour_columns].sum(axis=1).mean()
        total_paint_time = similar_data_1[paint_columns].sum(axis=1).mean()
        return total_labour_time, total_paint_time, "Estimation based on similar data 1."

    similar_data_2 = data[
        (data['price'] >= min_price) &
        (data['price'] <= max_price) &
        (data['car_type'].str.lower() == car_type) &
        (data['damage_severity'].str.lower() == damage_severity) &
        (data['damage_type'].str.lower() == damage_type)
    ]

    if not similar_data_2.empty:
        total_labour_time = similar_data_2[labour_columns].sum(axis=1).mean()
        total_paint_time = similar_data_2[paint_columns].sum(axis=1).mean()
        return total_labour_time, total_paint_time, "Estimation based on similar data 2."

    similar_data_3 = data[
        (data['price'] >= min_price) &
        (data['price'] <= max_price) &
        (data['car_type'].str.lower() == car_type) &
        (data['damage_severity'].str.lower() == damage_severity)
    ]

    if not similar_data_3.empty:
        total_labour_time = similar_data_3[labour_columns].sum(axis=1).mean()
        total_paint_time = similar_data_3[paint_columns].sum(axis=1).mean()
        return total_labour_time, total_paint_time, "Estimation based on similar data 3."
    
    similar_data_4 = data[
        (data['price'] >= min_price) &
        (data['price'] <= max_price) &
        (data['car_type'].str.lower() == car_type)
    ]

    if not similar_data_4.empty:
        total_labour_time = similar_data_4[labour_columns].sum(axis=1).mean()
        total_paint_time = similar_data_4[paint_columns].sum(axis=1).mean()
        return total_labour_time, total_paint_time, "Estimation based on similar data 4."

    # If no similar data is found
    return 0, 0, "No similar data available for the given inputs."

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/calculate', methods=['POST'])
def calculate():
    car_data = request.get_json()
    price = float(car_data['price'])
    damaged_part = car_data['damaged_part'].lower()
    damage_type = car_data['damage_type'].lower()
    damage_severity = car_data['damage_severity'].lower()
    car_type = car_data['car_type'].lower()
    area_code = float(car_data['area_code'])
    
    # Load data dynamically
    data, labour_columns, paint_columns, error = load_data(file_url)
    if error:
        return jsonify(error=error), 500
    
    total_labour_time, total_paint_time, status = calculate_times(data, labour_columns, paint_columns, car_type, price, damaged_part, damage_type, damage_severity, area_code)
    return jsonify(total_labour_time=int(total_labour_time), total_paint_time=int(total_paint_time), status=status)

if __name__ == '__main__':
    app.run(debug=True)
