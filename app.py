from flask import Flask, render_template, request, send_file, redirect, url_for, flash
import os
import pandas as pd
from server_monitor import process_servers


app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY')  
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['DOWNLOAD_FOLDER'] = 'downloads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB upload limit

# Ensure upload and download directories exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['DOWNLOAD_FOLDER'], exist_ok=True)





@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # If user does not select file, browser may submit an empty part
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = 'uploaded_input.xlsx'
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

            # Read the uploaded Excel file
            try:
                servers_df = pd.read_excel(filepath)
            except Exception as e:
                flash(f'Error reading Excel file: {e}')
                return redirect(request.url)

            # Process the servers
            results = process_servers(servers_df)

            if results:
                # Create a DataFrame from results
                final_results_df = pd.DataFrame(results)

                # Save to a CSV file on disk
                output_filepath = os.path.join(app.config['DOWNLOAD_FOLDER'], 'output.csv')
                final_results_df.to_csv(output_filepath, index=False)

                return send_file(output_filepath, download_name='output.csv', as_attachment=True)

            else:
                flash('No valid data collected.')
                return redirect(request.url)
        else:
            flash('Allowed file types are .xlsx, .xls')
            return redirect(request.url)
    return render_template('index.html')

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'xlsx', 'xls'}

if __name__ == '__main__':
    app.run(debug=True)
