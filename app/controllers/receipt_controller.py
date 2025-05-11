from flask import Blueprint, request, jsonify
from app.services.receipt_service import (
    create_receipt_file,
    validate_receipt_file,
    process_receipt_file,
    get_receipt_by_id
)
from app.utils.validators import validate_receipt_file_upload

receipt_bp = Blueprint('receipt', __name__)

@receipt_bp.route('/upload', methods=['POST'])
def upload_receipt():
    """Handles receipt file upload and creates a receipt file record."""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
        
    file = request.files['file']
    if not file.filename:
        return jsonify({'error': 'No file selected'}), 400
        
    try:
        validate_receipt_file_upload(file)
        receipt_file = create_receipt_file(file)
        
        return jsonify({
            'message': 'File uploaded successfully',
            'receipt_file_id': receipt_file.id
        }), 201
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': f'Error uploading file: {str(e)}'}), 500

@receipt_bp.route('/validate', methods=['POST'])
def validate_receipt():
    """Validates an uploaded receipt file to ensure it can be processed."""
    data = request.get_json()
    if not data or 'receipt_file_id' not in data:
        return jsonify({'error': 'Receipt file ID is required'}), 400
        
    try:
        result = validate_receipt_file(data['receipt_file_id'])
        return jsonify(result), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': f'Error validating receipt: {str(e)}'}), 500

@receipt_bp.route('/process', methods=['POST'])
def process_receipt():
    """Processes a validated receipt file to extract and store receipt data."""
    data = request.get_json()
    if not data or 'receipt_file_id' not in data:
        return jsonify({'error': 'Receipt file ID is required'}), 400
        
    try:
        receipt = process_receipt_file(data['receipt_file_id'])
        return jsonify({
            'message': 'Receipt processed successfully',
            'receipt_id': receipt.id
        }), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': f'Error processing receipt: {str(e)}'}), 500

@receipt_bp.route('/receipts', methods=['GET'])
def list_receipts():
    """Lists all receipts with pagination support."""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        query = get_receipt_by_id(None)
        pagination = query.paginate(page=page, per_page=per_page)
        
        return jsonify({
            'receipts': [receipt.to_dict() for receipt in pagination.items],
            'total': pagination.total,
            'pages': pagination.pages,
            'current_page': page
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Error listing receipts: {str(e)}'}), 500

@receipt_bp.route('/receipts/<int:receipt_id>', methods=['GET'])
def get_receipt(receipt_id):
    """Gets details of a specific receipt by its ID."""
    try:
        receipt = get_receipt_by_id(receipt_id)
        if not receipt:
            return jsonify({'error': 'Receipt not found'}), 404
            
        return jsonify(receipt.to_dict()), 200
        
    except Exception as e:
        return jsonify({'error': f'Error getting receipt: {str(e)}'}), 500