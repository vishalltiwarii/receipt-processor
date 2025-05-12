import os
import re
import pytesseract
from PIL import Image
from datetime import datetime
from pdf2image import convert_from_path
from flask import current_app
import tempfile

def extract_text_from_pdf(pdf_path):
    """Extracts text from PDF using Tesseract OCR. Converts PDF to images first, then uses OCR to get text and confidence scores."""
    try:
        all_text = ""
        confidence_sum = 0
        page_count = 0
        
        with tempfile.TemporaryDirectory() as temp_dir:
            images = convert_from_path(pdf_path, output_folder=temp_dir)
            
            for i, image in enumerate(images):
                page_count += 1
                data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
                
                conf_values = [int(conf) for conf in data['conf'] if conf != '-1']
                if conf_values:
                    confidence_sum += sum(conf_values) / len(conf_values)
                
                page_text = pytesseract.image_to_string(image)
                all_text += f"--- PAGE {i+1} ---\n{page_text}\n\n"
        
        avg_confidence = confidence_sum / page_count if page_count > 0 else 0
        return all_text, avg_confidence / 100.0
    
    except Exception as e:
        current_app.logger.error(f"Tesseract OCR error: {str(e)}")
        return "", 0.0

def parse_receipt(text):
    """Parses receipt text into structured data. Looks for merchant name, items, and total amount."""
    lines = text.split('\n')
    
    receipt_data = {
        'merchant_name': '',
        'purchased_at': datetime.now(),
        'total_amount': 0.0,
        'currency': 'USD',
        'tax_amount': 0.0,
        'receipt_number': '',
        'payment_method': '',
        'items': []
    }
    
    lines = [line.strip() for line in lines if line.strip() and not line.strip().startswith('--- PAGE')]
    
    for i in range(min(5, len(lines))):
        line = lines[i].strip()
        if line and len(line) > 3 and not any(x in line.lower() for x in ['date', 'time', 'receipt', 'total', 'amount']):
            receipt_data['merchant_name'] = line
            break
    
    in_items_section = False
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        if any(x in line.lower() for x in ['date', 'time', 'receipt', 'card', 'ref', 'tkt']):
            continue
            
        if 'total' in line.lower() or 'amount' in line.lower():
            try:
                amount = float(''.join(filter(lambda x: x.isdigit() or x == '.', line)))
                receipt_data['total_amount'] = amount
            except:
                pass
            continue
            
        if '$' in line or '€' in line or '£' in line:
            try:
                parts = line.split()
                if len(parts) >= 2:
                    price_str = None
                    for part in reversed(parts):
                        if any(c in part for c in '$€£') or part.replace('.', '').isdigit():
                            price_str = part
                            break
                    
                    if price_str:
                        price = float(''.join(filter(lambda x: x.isdigit() or x == '.', price_str)))
                        price_idx = line.rindex(price_str)
                        description = line[:price_idx].strip()
                        
                        if description and len(description) > 1 and not any(x in description.lower() for x in ['total', 'tax', 'subtotal', 'amount']):
                            receipt_data['items'].append({
                                'description': description,
                                'quantity': 1,
                                'unit_price': price,
                                'total_price': price
                            })
            except:
                pass
    
    return receipt_data