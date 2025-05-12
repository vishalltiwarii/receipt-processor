from flask import current_app
from app import db
from app.models.receipt import ReceiptFile, Receipt, ReceiptItem
from app.services.file_service import save_file, validate_pdf, move_to_processed_folder
from app.services.ocr_service import extract_text_from_pdf, parse_receipt
import os


def create_receipt_file(file):
    """Creates a new receipt file record in the database and saves the file."""
    filename = file.filename
    file_path = save_file(file)
    
    receipt_file = ReceiptFile(
        file_name=filename,
        file_path=file_path,
        is_valid=False,
        invalid_reason=None,
        is_processed=False
    )
    
    db.session.add(receipt_file)
    db.session.commit()
    
    return receipt_file


def validate_receipt_file(receipt_file_id):
    """Validates a receipt file by checking if it's a valid PDF and can be processed."""
    receipt_file = ReceiptFile.query.get(receipt_file_id)
    if not receipt_file:
        raise ValueError("Receipt file not found")
        
    # Validate PDF
    is_valid, reason = validate_pdf(receipt_file.file_path)
    
    # Update receipt file record
    receipt_file.is_valid = is_valid
    receipt_file.invalid_reason = reason if not is_valid else None
    db.session.commit()
    
    return {
        'receipt_file_id': receipt_file.id,
        'is_valid': is_valid,
        'invalid_reason': reason
    }


def process_receipt_file(receipt_file_id):
    """Processes a receipt file by extracting text and creating a receipt record with items."""
    receipt_file = ReceiptFile.query.get(receipt_file_id)
    if not receipt_file:
        raise ValueError("Receipt file not found")
        
    if not receipt_file.is_valid:
        raise ValueError(f"Invalid receipt file: {receipt_file.invalid_reason}")
        
    # Extract text from PDF
    text, confidence = extract_text_from_pdf(receipt_file.file_path)
    
    # Parse receipt data
    receipt_data = parse_receipt(text)
    
    # Create receipt record
    receipt = Receipt(
        receipt_file_id=receipt_file_id,
        merchant_name=receipt_data['merchant_name'],
        purchased_at=receipt_data['purchased_at'],
        total_amount=receipt_data['total_amount'],
        currency=receipt_data['currency'],
        tax_amount=receipt_data['tax_amount'],
        receipt_number=receipt_data['receipt_number'],
        payment_method=receipt_data['payment_method'],
        ocr_text=text,
        confidence_score=confidence
    )
    
    db.session.add(receipt)
    
    # Create receipt items
    for item_data in receipt_data['items']:
        item = ReceiptItem(
            receipt=receipt,
            description=item_data['description'],
            quantity=item_data['quantity'],
            unit_price=item_data['unit_price'],
            total_price=item_data['total_price']
        )
        db.session.add(item)
    
    # Move file to processed folder
    try:
        new_path = move_to_processed_folder(receipt_file.file_path)
        receipt_file.file_path = new_path
    except Exception as e:
        current_app.logger.error(f"Error moving file to processed folder: {str(e)}")
    
    # Mark receipt file as processed
    receipt_file.is_processed = True
    db.session.commit()
    
    return receipt


def get_receipt_by_id(receipt_id):
    """Gets a receipt by ID or returns the base query if no ID is provided."""
    if receipt_id is None:
        return Receipt.query
    return Receipt.query.get(receipt_id)


def get_all_receipts(page=1, per_page=10):
    """Get all receipts with pagination"""
    return Receipt.query.order_by(Receipt.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )


def search_receipts(query, page=1, per_page=10):
    """Search receipts by merchant name or OCR text"""
    return Receipt.query.filter(
        (Receipt.merchant_name.ilike(f'%{query}%')) | 
        (Receipt.ocr_text.ilike(f'%{query}%'))
    ).order_by(Receipt.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )