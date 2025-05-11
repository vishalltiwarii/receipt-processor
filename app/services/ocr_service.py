import os
import re
import pytesseract
from PIL import Image
from datetime import datetime
from pdf2image import convert_from_path
import pdfplumber
from flask import current_app
import tempfile
from pypdf import PdfReader
import io

# Optional import for Google Cloud Vision API
try:
    from google.cloud import vision
    GOOGLE_VISION_AVAILABLE = True
except ImportError:
    GOOGLE_VISION_AVAILABLE = False


def extract_text_from_pdf_with_tesseract(pdf_path):
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


def extract_text_from_pdf_with_pdfplumber(pdf_path):
    """Extracts text from PDF using pdfplumber. Works best for text-based PDFs, not scanned documents."""
    try:
        all_text = ""
        with pdfplumber.open(pdf_path) as pdf:
            for i, page in enumerate(pdf.pages):
                text = page.extract_text() or ""
                all_text += f"--- PAGE {i+1} ---\n{text}\n\n"
                
        return all_text, 0.95 if all_text.strip() else 0.0
    
    except Exception as e:
        current_app.logger.error(f"pdfplumber extraction error: {str(e)}")
        return "", 0.0


def extract_text_from_pdf_with_google_vision(pdf_path):
    """Extracts text from PDF using Google Cloud Vision API. Converts PDF to images and processes each page."""
    if not GOOGLE_VISION_AVAILABLE:
        return "Google Cloud Vision API not available", 0.0
    
    try:
        client = vision.ImageAnnotatorClient()
        all_text = ""
        confidence_sum = 0
        page_count = 0
        
        with tempfile.TemporaryDirectory() as temp_dir:
            images = convert_from_path(pdf_path, output_folder=temp_dir)
            
            for i, image in enumerate(images):
                page_count += 1
                image_path = os.path.join(temp_dir, f"page_{i}.jpg")
                image.save(image_path, "JPEG")
                
                with open(image_path, "rb") as image_file:
                    content = image_file.read()
                
                image = vision.Image(content=content)
                response = client.text_detection(image=image)
                
                if response.error.message:
                    raise Exception(f"Error from Google Vision API: {response.error.message}")
                
                text = response.text_annotations[0].description if response.text_annotations else ""
                all_text += f"--- PAGE {i+1} ---\n{text}\n\n"
                
                if response.text_annotations:
                    if response.full_text_annotation.pages:
                        page_confidence = 0
                        block_count = 0
                        for page in response.full_text_annotation.pages:
                            for block in page.blocks:
                                page_confidence += block.confidence
                                block_count += 1
                        if block_count > 0:
                            confidence_sum += page_confidence / block_count
                    else:
                        confidence_sum += 0.9
        
        avg_confidence = confidence_sum / page_count if page_count > 0 else 0
        return all_text, avg_confidence
    
    except Exception as e:
        current_app.logger.error(f"Google Vision API error: {str(e)}")
        return "", 0.0


def extract_text_from_pdf(file_path):
    """Extracts text from PDF using PyPDF. Simple text extraction without OCR."""
    try:
        reader = PdfReader(file_path)
        text = ""
        
        for page in reader.pages:
            text += page.extract_text() + "\n"
            
        return text, 1.0
    except Exception as e:
        raise ValueError(f"Error extracting text from PDF: {str(e)}")


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


def extract_date(text):
    """Extracts date from receipt text. Handles common date formats like DD/MM/YYYY, MM/DD/YYYY, etc."""
    date_patterns = [
        r'(\d{1,2})[/\-\.](\d{1,2})[/\-\.](\d{2,4})',
        r'(\d{4})[/\-\.](\d{1,2})[/\-\.](\d{1,2})',
        r'(\d{1,2})(?:st|nd|rd|th)?\s(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*[\s,]+(\d{2,4})',
        r'(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s(\d{1,2})(?:st|nd|rd|th)?[\s,]+(\d{2,4})'
    ]
    
    for pattern in date_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            match = matches[0]
            try:
                if len(match) == 3:
                    try:
                        day, month, year = match
                        if len(year) == 2:
                            year = f"20{year}" if int(year) < 50 else f"19{year}"
                        return datetime(int(year), int(month), int(day))
                    except ValueError:
                        try:
                            month, day, year = match
                            if len(year) == 2:
                                year = f"20{year}" if int(year) < 50 else f"19{year}"
                            return datetime(int(year), int(month), int(day))
                        except ValueError:
                            continue
            except ValueError:
                continue
    
    return None


def extract_merchant_name(text):
    """Extracts merchant name from receipt text. Usually found in the first few non-empty lines."""
    lines = text.split('\n')
    start_idx = 0
    while start_idx < len(lines) and not lines[start_idx].strip():
        start_idx += 1
    
    potential_names = []
    for i in range(start_idx, min(start_idx + 5, len(lines))):
        line = lines[i].strip()
        if line and len(line) > 1:
            if not re.match(r'^[\d\-\./:\\]+$', line) and not re.search(r'(date|time|receipt|transaction|tel|fax)', line.lower()):
                potential_names.append(line)
    
    return potential_names[0] if potential_names else None


def extract_total_amount(text):
    """Extracts total amount from receipt text. Looks for lines containing 'total' or 'amount'."""
    patterns = [
        r'total[\s:]*[$€£]?\s*(\d+[,\.\d]+)',
        r'amount[\s:]*[$€£]?\s*(\d+[,\.\d]+)',
        r'[$€£]\s*(\d+[,\.\d]+)',
        r'(\d+[,\.\d]+)\s*[$€£]'
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, text.lower())
        if matches:
            try:
                amounts = [float(amount.replace(',', '.')) for amount in matches]
                return max(amounts)
            except (ValueError, TypeError):
                pass
    
    return None


def extract_currency(text):
    """Extracts currency from receipt text based on currency symbols."""
    if re.search(r'[$]', text):
        return 'USD'
    elif re.search(r'[€]', text):
        return 'EUR'
    elif re.search(r'[£]', text):
        return 'GBP'
    return None


def extract_tax_amount(text):
    """Extracts tax amount from receipt text. Looks for lines containing tax-related keywords."""
    patterns = [
        r'tax[:\s]*[$€£]?\s*(\d+[,\.\d]+)',
        r'vat[:\s]*[$€£]?\s*(\d+[,\.\d]+)',
        r'sales\s+tax[:\s]*[$€£]?\s*(\d+[,\.\d]+)',
        r'gst[:\s]*[$€£]?\s*(\d+[,\.\d]+)',
        r'hst[:\s]*[$€£]?\s*(\d+[,\.\d]+)'
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, text.lower())
        if matches:
            try:
                return float(matches[0].replace(',', '.'))
            except (ValueError, TypeError):
                pass
    
    return None


def extract_receipt_number(text):
    """Extracts receipt number from text. Looks for common receipt number patterns."""
    patterns = [
        r'receipt\s*(?:no|num|number)[.:\s#]*([a-zA-Z0-9\-]+)',
        r'(?:no|num|number)[.:\s#]*([a-zA-Z0-9\-]+)',
        r'transaction\s*(?:no|num|number|id)[.:\s#]*([a-zA-Z0-9\-]+)',
        r'order\s*(?:no|num|number|id)[.:\s#]*([a-zA-Z0-9\-]+)'
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, text.lower())
        if matches:
            return matches[0]
    
    return None


def extract_payment_method(text):
    """Extracts payment method from text. Looks for common payment method keywords."""
    payment_methods = [
        ('credit', 'Credit Card'),
        ('debit', 'Debit Card'),
        ('visa', 'Visa'),
        ('mastercard', 'Mastercard'),
        ('amex', 'American Express'),
        ('discover', 'Discover'),
        ('cash', 'Cash'),
        ('check', 'Check'),
        ('cheque', 'Cheque'),
        ('paypal', 'PayPal'),
        ('apple pay', 'Apple Pay'),
        ('google pay', 'Google Pay')
    ]
    
    text_lower = text.lower()
    for keyword, method in payment_methods:
        if keyword in text_lower:
            return method
    
    return None


def extract_items(text):
    """Extracts line items from receipt text. Looks for lines containing prices and descriptions."""
    items = []
    pattern = r"""
        ^
        (?P<name>[^\d\$€£]+?)
        [\s\d]*
        (?P<price>[$€£]?\s*\d+[,\.\d]+)
        $
    """.strip()
    
    qty_pattern = r"""
        ^
        (?P<name>.+?)\s+
        (?P<qty>\d+)\s+
        (?P<price>[$€£]?\s*\d+[,\.\d]+)
        $
    """.strip()
    
    for line in text.split('\n'):
        line = line.strip()
        if not line:
            continue
            
        match = re.match(qty_pattern, line, re.VERBOSE | re.IGNORECASE)
        if match:
            items.append({
                'name': match.group('name').strip(),
                'quantity': int(match.group('qty')),
                'price': float(match.group('price').replace(',', '').strip('$€£ '))
            })
            continue
            
        match = re.match(pattern, line, re.VERBOSE | re.IGNORECASE)
        if match:
            items.append({
                'name': match.group('name').strip(),
                'quantity': 1,
                'price': float(match.group('price').replace(',', '').strip('$€£ '))
            })
    
    return items