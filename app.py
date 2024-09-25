from flask import Flask, render_template, request, jsonify, session
import pandas as pd
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max-limit
app.secret_key = 'your_secret_key_here' 

# Make sure we have a place to put uploaded files
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def load_data(filename=None):
    """
    Load data from a CSV file.
    If no file is uploaded, use the default sample data.
    """
    try:
        # Check if we have an uploaded file, otherwise use the sample data
        if filename and os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], filename)):
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            print(f"Loading uploaded file: {file_path}")
        else:
            file_path = 'data/sample_data.csv'
            print(f"Loading default sample file: {file_path}")
        
        df = pd.read_csv(file_path)
        print(f"Loaded data shape: {df.shape}")
        print(f"Columns: {df.columns}")
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])  # Convert date strings to datetime objects
        return df
    except Exception as e:
        print(f"Error loading data: {str(e)}")
        return pd.DataFrame()  # Return empty DataFrame if something goes wrong

def process_data(df):
    try:
        # Calculate basic stats
        total = df['value'].sum()
        average = df['value'].mean()
        categories = df.groupby('category')['value'].sum().to_dict()
        
        # Handle date data
        time_series = {}
        if 'date' in df.columns:
            df['date'] = df['date'].dt.strftime('%Y-%m-%d')  # Format dates as strings
            grouped = df.groupby(['date', 'category'])['value'].sum().unstack()
            time_series = {
                category: [
                    {'date': date, 'value': value} 
                    for date, value in grouped[category].items()
                ]
                for category in grouped.columns
            }
        
        # place into dictionary
        result = {
            'total': float(total),
            'average': float(average),
            'categories': {k: float(v) for k, v in categories.items()},
            'time_series': time_series
        }
        print("Processed data:", result)
        return result
    except Exception as e:
        print(f"Error processing data: {str(e)}")
        return {}  # Return empty dict 

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Handle file upload
        if 'file' not in request.files:
            return 'No file part'
        file = request.files['file']
        if file.filename == '':
            return 'No selected file'
        if file and file.filename.endswith('.csv'):
            filename = secure_filename(file.filename)  # ensure filename is safe
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            session['uploaded_file'] = filename  
            print(f"File uploaded: {filename}")
        else:
            return 'Invalid file type. Please upload a CSV file.'
    
    # Load and process data
    uploaded_file = session.get('uploaded_file')
    print(f"Using file: {uploaded_file if uploaded_file else 'default sample data'}")
    df = load_data(uploaded_file)
    data = process_data(df)
    return render_template('index.html', data=data)

@app.route('/api/data')
def get_data():
    # API endpoint to get the processed data
    uploaded_file = session.get('uploaded_file')
    print(f"API call using file: {uploaded_file if uploaded_file else 'default sample data'}")
    df = load_data(uploaded_file)
    data = process_data(df)
    return jsonify(data)

if __name__ == '__main__':
    app.run(debug=True)  # Remember to set debug=False in production!
