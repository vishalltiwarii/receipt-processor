from datetime import datetime
from app import db


class ReceiptFile(db.Model):
    """Model for storing uploaded receipt file metadata"""
    __tablename__ = 'receipt_file'

    id = db.Column(db.Integer, primary_key=True)
    file_name = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(512), nullable=False)
    is_valid = db.Column(db.Boolean, default=True)
    invalid_reason = db.Column(db.String(255), nullable=True)
    is_processed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Define relationship with Receipt model
    receipt = db.relationship('Receipt', backref='receipt_file', lazy=True, uselist=False)

    def to_dict(self):
        """Convert model instance to dictionary"""
        return {
            'id': self.id,
            'file_name': self.file_name,
            'file_path': self.file_path,
            'is_valid': self.is_valid,
            'invalid_reason': self.invalid_reason,
            'is_processed': self.is_processed,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


class Receipt(db.Model):
    """Model for storing extracted receipt information"""
    __tablename__ = 'receipt'

    id = db.Column(db.Integer, primary_key=True)
    receipt_file_id = db.Column(db.Integer, db.ForeignKey('receipt_file.id'), nullable=False)
    merchant_name = db.Column(db.String(255))
    purchased_at = db.Column(db.DateTime, nullable=True)
    total_amount = db.Column(db.Float, nullable=True)
    currency = db.Column(db.String(10), nullable=True)
    tax_amount = db.Column(db.Float, nullable=True)
    receipt_number = db.Column(db.String(100), nullable=True)
    payment_method = db.Column(db.String(50), nullable=True)
    ocr_text = db.Column(db.Text, nullable=True)  # Store the full extracted text
    confidence_score = db.Column(db.Float, nullable=True)  # OCR confidence score
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Define relationship with ReceiptItem model
    items = db.relationship('ReceiptItem', backref='receipt', lazy=True, cascade="all, delete-orphan")

    def to_dict(self):
        """Convert model instance to dictionary"""
        return {
            'id': self.id,
            'receipt_file_id': self.receipt_file_id,
            'merchant_name': self.merchant_name,
            'purchased_at': self.purchased_at.isoformat() if self.purchased_at else None,
            'total_amount': self.total_amount,
            'currency': self.currency,
            'tax_amount': self.tax_amount,
            'receipt_number': self.receipt_number,
            'payment_method': self.payment_method,
            'confidence_score': self.confidence_score,
            'items': [item.to_dict() for item in self.items],
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


class ReceiptItem(db.Model):
    """Model for storing individual items from a receipt"""
    __tablename__ = 'receipt_item'

    id = db.Column(db.Integer, primary_key=True)
    receipt_id = db.Column(db.Integer, db.ForeignKey('receipt.id'), nullable=False)
    description = db.Column(db.String(255), nullable=False)
    quantity = db.Column(db.Float, default=1.0)
    unit_price = db.Column(db.Float, nullable=True)
    total_price = db.Column(db.Float, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        """Convert model instance to dictionary"""
        return {
            'id': self.id,
            'receipt_id': self.receipt_id,
            'description': self.description,
            'quantity': self.quantity,
            'unit_price': self.unit_price,
            'total_price': self.total_price,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }