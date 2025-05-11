# Receipt Processor

A Flask-based application for processing and managing receipts. The application provides APIs for uploading, validating, and processing receipt files, as well as retrieving receipt information.

## Features

- Upload receipt files (PDF)
- Validate receipt files
- Process receipts to extract information
- List and search receipts
- Get detailed receipt information

## API Endpoints

- `GET /health` - Health check endpoint
- `POST /api/upload` - Upload a receipt file
- `POST /api/validate` - Validate an uploaded receipt file
- `POST /api/process` - Process a validated receipt file
- `GET /api/receipts` - List all receipts (with pagination)
- `GET /api/receipts/{id}` - Get details of a specific receipt

## Setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Initialize the database:
```bash
flask db upgrade
```

4. Run the application:
```bash
flask run
```

## Environment Variables

Create a `.env` file with the following variables:
```
FLASK_APP=app
FLASK_ENV=development
SECRET_KEY=your-secret-key
```

## Dependencies

- Flask
- SQLAlchemy
- PyPDF2
- pytesseract (for OCR)
- pdf2image
- pdfplumber
- Google Cloud Vision API (optional)

## License

MIT 