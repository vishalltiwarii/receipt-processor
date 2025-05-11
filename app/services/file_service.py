import os
import uuid
from werkzeug.utils import secure_filename
from pypdf import PdfReader
from flask import current_app


def allowed_file(filename):
    """Checks if the file extension is allowed based on app configuration."""
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']


def save_file(file):
    """Saves an uploaded file to the uploads directory and returns its path."""
    if not file:
        raise ValueError("No file provided")
        
    filename = secure_filename(file.filename)
    if not filename:
        raise ValueError("Invalid filename")
        
    # Create uploads directory if it doesn't exist
    upload_dir = os.path.join(current_app.root_path, '..', 'uploads')
    os.makedirs(upload_dir, exist_ok=True)
    
    # Save file
    file_path = os.path.join(upload_dir, filename)
    file.save(file_path)
    
    return file_path


def validate_pdf(file_path):
    """Validates if a file is a valid PDF by trying to read it."""
    if not os.path.exists(file_path):
        return False, "File not found"
    
    try:
        # Try to open and read the PDF
        with open(file_path, 'rb') as file:
            pdf = PdfReader(file)
            # Check if the PDF has at least one page
            if len(pdf.pages) == 0:
                return False, "PDF has no pages"
        return True, None
    except Exception as e:
        return False, f"Invalid PDF: {str(e)}"


def move_to_processed_folder(file_path):
    """Moves a file from unprocessed to processed folder."""
    filename = os.path.basename(file_path)
    new_path = os.path.join(current_app.config['PROCESSED_FOLDER'], filename)
    os.rename(file_path, new_path)
    return new_path
    

def get_file_path(filename):
    """Gets the full path for a file in the uploads directory."""
    return os.path.join(current_app.root_path, '..', 'uploads', secure_filename(filename))