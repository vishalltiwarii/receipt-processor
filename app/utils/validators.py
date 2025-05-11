from flask import request, jsonify
from functools import wraps
from marshmallow import Schema, fields, ValidationError
from werkzeug.utils import secure_filename
import os

ALLOWED_EXTENSIONS = {'pdf'}

def allowed_file(filename):
    """Check if the file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def validate_receipt_file_upload(file):
    """Validate an uploaded receipt file"""
    if not file:
        raise ValueError("No file provided")
        
    if not file.filename:
        raise ValueError("No file selected")
        
    if not allowed_file(file.filename):
        raise ValueError("Invalid file type. Only PDF files are allowed.")
        
    # Check file size (max 10MB)
    if len(file.read()) > 10 * 1024 * 1024:  # 10MB in bytes
        raise ValueError("File too large. Maximum size is 10MB.")
        
    # Reset file pointer after reading
    file.seek(0)
    
    return True

class ReceiptFileSchema(Schema):
    """Schema for validating receipt file input"""
    receipt_file_id = fields.Integer(required=True)


class PaginationSchema(Schema):
    """Schema for validating pagination parameters"""
    page = fields.Integer(missing=1, validate=lambda n: n > 0)
    per_page = fields.Integer(missing=10, validate=lambda n: 0 < n <= 100)
    q = fields.String(missing="")


def validate_request(schema_class):
    """Decorator to validate request JSON data against a schema"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            schema = schema_class()
            
            try:
                # Handle GET requests with query parameters
                if request.method == 'GET':
                    data = schema.load(request.args)
                # Handle POST/PUT/DELETE requests with JSON body
                else:
                    if not request.is_json:
                        return jsonify({"error": "Missing JSON in request"}), 400
                    data = schema.load(request.get_json())
                
                # Add validated data to kwargs
                kwargs.update(data)
                return f(*args, **kwargs)
                
            except ValidationError as err:
                return jsonify({"error": "Validation error", "messages": err.messages}), 400
                
            except Exception as e:
                return jsonify({"error": f"Request validation failed: {str(e)}"}), 400
                
        return decorated_function
    return decorator


def require_file(file_key='file'):
    """Decorator to validate file upload requests"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if file_key not in request.files:
                return jsonify({"error": f"No '{file_key}' file part in the request"}), 400
                
            file = request.files[file_key]
            
            if file.filename == '':
                return jsonify({"error": "No selected file"}), 400
                
            # Add file to kwargs
            kwargs[file_key] = file
            return f(*args, **kwargs)
                
        return decorated_function
    return decorator