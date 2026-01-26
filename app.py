from flask import Flask, render_template, request, jsonify
import os
import base64
import re
from datetime import datetime, timedelta
from anthropic import Anthropic
from database import db, Tag, init_db

app = Flask(__name__)

# Initialize database
init_db(app)

# Initialize Anthropic client
client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

@app.route('/')
def index():
    """Main page with camera interface"""
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_image():
    """Process uploaded tag image"""
    try:
        # Get image data from request
        data = request.get_json()
        image_data = data.get('image')
        
        # Remove data URL prefix if present
        if ',' in image_data:
            image_data = image_data.split(',')[1]
        
        # Call Claude Vision API to extract tag data
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1000,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/jpeg",
                                "data": image_data,
                            },
                        },
                        {
                            "type": "text",
                            "text": "This is a clothing tag label. Please extract ONLY these three pieces of information in this exact format:\n\nStyle Number: [first line - the style/item number]\nDescription: [second line - the product description]\nPO Number: [last line - the PO/order number]\n\nBe precise and extract exactly what you see on the tag."
                        }
                    ],
                }
            ],
        )
        
        # Extract the response text
        response_text = message.content[0].text
        
        return jsonify({
            'success': True,
            'data': response_text,
            'image_data': image_data  # Send back for saving
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/save', methods=['POST'])
def save_tag():
    """Save a tag to the database"""
    try:
        data = request.get_json()
        style_number = data.get('style_number')
        description = data.get('description')
        po_number = data.get('po_number')
        scan_date_str = data.get('scan_date')  # Format: YYYY-MM-DD
        return_date_str = data.get('return_date')  # Optional, can be provided by user
        image_data = data.get('image_data')
        
        # Parse scan date
        scan_date = datetime.strptime(scan_date_str, '%Y-%m-%d').date()
        
        # Use provided return date or calculate it
        if return_date_str:
            return_date = datetime.strptime(return_date_str, '%Y-%m-%d').date()
        else:
            # Calculate return date (30 days from scan date)
            return_date = scan_date + timedelta(days=30)
        
        # Reconstruct raw text
        raw_text = f"Style Number: {style_number}\nDescription: {description}\nPO Number: {po_number}"
        
        # Create new tag record
        new_tag = Tag(
            style_number=style_number,
            description=description,
            po_number=po_number,
            scan_date=scan_date,
            return_date=return_date,
            raw_text=raw_text,
            image_data=base64.b64decode(image_data) if image_data else None
        )
        
        db.session.add(new_tag)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Tag saved successfully!',
            'id': new_tag.id,
            'return_date': return_date.isoformat()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/tracker')
def tracker():
    """View all stored tags, sorted by return date"""
    from datetime import date
    tags = Tag.query.order_by(Tag.return_date.asc()).all()
    return render_template('tracker.html', tags=tags, today=date.today())

@app.route('/api/tags', methods=['GET'])
def get_tags():
    """API endpoint to get all tags as JSON"""
    tags = Tag.query.order_by(Tag.return_date.asc()).all()
    return jsonify({
        'success': True,
        'tags': [t.to_dict() for t in tags]
    })

@app.route('/api/tag/<int:tag_id>', methods=['DELETE'])
def delete_tag(tag_id):
    """Delete a tag by ID"""
    try:
        tag = Tag.query.get_or_404(tag_id)
        db.session.delete(tag)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Tag deleted successfully'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/tag/<int:tag_id>', methods=['PUT'])
def update_tag(tag_id):
    """Update a tag by ID"""
    try:
        tag = Tag.query.get_or_404(tag_id)
        data = request.get_json()
        
        # Update fields
        tag.style_number = data.get('style_number', tag.style_number)
        tag.description = data.get('description', tag.description)
        tag.po_number = data.get('po_number', tag.po_number)
        
        # Update scan date if provided
        if 'scan_date' in data:
            scan_date = datetime.strptime(data['scan_date'], '%Y-%m-%d').date()
            tag.scan_date = scan_date
            # Recalculate return date
            tag.return_date = scan_date + timedelta(days=30)
        
        # Update raw_text
        tag.raw_text = f"Style Number: {tag.style_number}\nDescription: {tag.description}\nPO Number: {tag.po_number}"
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Tag updated successfully',
            'tag': tag.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    app.run(debug=True)
