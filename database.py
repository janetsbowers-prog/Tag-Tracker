import os
from datetime import datetime, timedelta
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Tag(db.Model):
    """Model for storing scanned clothing tags"""
    __tablename__ = 'tags'
    
    id = db.Column(db.Integer, primary_key=True)
    style_number = db.Column(db.String(200), nullable=False)
    description = db.Column(db.String(500), nullable=False)
    po_number = db.Column(db.String(200), nullable=False)
    scan_date = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    return_date = db.Column(db.Date, nullable=False)
    raw_text = db.Column(db.Text)  # Store the full extracted text
    image_data = db.Column(db.LargeBinary)  # Optional: store the actual image
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Tag {self.style_number}: {self.description}>'
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'style_number': self.style_number,
            'description': self.description,
            'po_number': self.po_number,
            'scan_date': self.scan_date.isoformat() if self.scan_date else None,
            'return_date': self.return_date.isoformat() if self.return_date else None,
            'raw_text': self.raw_text,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

def init_db(app):
    """Initialize the database"""
    # Use PostgreSQL on Heroku, SQLite locally
    database_url = os.environ.get('DATABASE_URL')
    
    if database_url:
        # Heroku provides postgres:// but SQLAlchemy needs postgresql://
        if database_url.startswith('postgres://'):
            database_url = database_url.replace('postgres://', 'postgresql://', 1)
        app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    else:
        # Local development - use SQLite
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tag_tracker.db'
    
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db.init_app(app)
    
    with app.app_context():
        db.create_all()
