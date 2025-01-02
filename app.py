from flask import Flask, request, render_template, send_file, flash, url_for, send_from_directory
import pandas as pd
import io
from generator import generate_variations
import os
from werkzeug.utils import secure_filename

app = Flask(__name__, template_folder='.')
app.secret_key = 'your-secret-key-here'  # Add this line
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')

@app.route('/style.css')
def serve_css():
    return send_from_directory('.', 'style.css', mimetype='text/css')

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        try:
            if 'source_file' not in request.files:
                return "No file uploaded", 400
                
            source_file = request.files['source_file']
            if source_file.filename == '':
                return "No file selected", 400
                
            if not source_file.filename.endswith(('.xlsx', '.xls')):
                return "Invalid file format. Please upload an Excel file.", 400

            variations = int(request.form.get('variations', 5))
            digits_to_vary = int(request.form.get('digits_to_vary', 3))
            
            # Read source file
            df_source = pd.read_excel(source_file)
            
            # Generate variations
            df_result = generate_variations(df_source, variations, digits_to_vary)
            
            # Create Excel file in memory
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df_result.to_excel(writer, index=False)
            output.seek(0)
            
            return send_file(
                output,
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                as_attachment=True,
                download_name='generated_numbers.xlsx'
            )
            
        except Exception as e:
            return f"Error: {str(e)}", 400
            
    return render_template('index.html')

@app.errorhandler(404)
def page_not_found(e):
    return f"Error 404: Page not found. <a href='{url_for('index')}'>Return to home</a>", 404

if __name__ == '__main__': 
    # Create required directories
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'css'), exist_ok=True)
    app.run(debug=True)