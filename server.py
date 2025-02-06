from flask import Flask, render_template, request, send_from_directory
from werkzeug.utils import secure_filename
import os
from marker.converters.pdf import PdfConverter
from marker.models import create_model_dict
from marker.output import text_from_rendered

app = Flask(__name__)

converter = PdfConverter(
    artifact_dict=create_model_dict(),
)

# Set the upload directory
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
# Ensure the directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Set the output directory (for markdown files)
OUTPUT_FOLDER = 'output'
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER
os.makedirs(OUTPUT_FOLDER, exist_ok=True)


ALLOWED_EXTENSIONS = {'pdf'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            return 'No file part'
        file = request.files['file']
        if file.filename == '':
            return 'No selected file'
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            fpath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(fpath)
            try:
                rendered = converter(fpath)
                content, _, _ = text_from_rendered(rendered)
                markdown_filename = filename[:-4] + ".md"  # Change .pdf to .md
                markdown_path = os.path.join(app.config['OUTPUT_FOLDER'], markdown_filename)

                with open(markdown_path, "w", encoding="utf-8") as md_file:  # Important: Specify encoding
                    md_file.write(content)

                return send_from_directory(app.config['OUTPUT_FOLDER'], markdown_filename, as_attachment=True)

            except Exception as e: # Catch potential errors during conversion
                return f"Error during conversion: {str(e)}"
            finally:  # Clean up uploaded PDF (good practice)
                os.remove(fpath) # Remove uploaded PDF


    return render_template('upload.html') # Create upload.html

if __name__ == '__main__':
    app.run(debug=False, host="0.0.0.0")  # Set debug=False for production