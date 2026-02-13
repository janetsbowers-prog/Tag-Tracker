from flask import Flask, render_template, request, jsonify
import os
import base64
import re
from datetime import datetime, timedelta
from anthropic import Anthropic
from database import db, Tag, Folder, init_db

app = Flask(__name__)

# Initialize database
init_db(app)

# Initialize Anthropic client
client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

@app.route('/')
def index():
    """Folder selection / home page"""
    folders = Folder.query.order_by(Folder.name.asc()).all()
    return render_template('folders.html', folders=folders)

@app.route('/scan/<int:folder_id>')
def scan(folder_id):
    """Scanner page for a specific folder"""
    folder = Folder.query.get_or_404(folder_id)
    return render_template('index.html', folder=folder)

@app.route('/api/folders', methods=['GET'])
def get_folders():
    """Get all folders"""
    folders = Folder.query.order_by(Folder.name.asc()).all()
    return jsonify({
        'success': True,
        'folders': [f.to_dict() for f in folders]
    })

@app.route('/api/folders', methods=['POST'])
def create_folder():
    """Create a new folder"""
    try:
        data = request.get_json()
        name = data.get('name', '').strip()
        
        if not name:
            return jsonify({'success': False, 'error': 'Folder name is required'}), 400
        
        # Check for duplicate
        existing = Folder.query.filter_by(name=name).first()
        if existing:
            return jsonify({'success': False, 'error': 'A folder with that name already exists'}), 400
        
        folder = Folder(name=name)
        db.session.add(folder)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'folder': folder.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/folders/<int:folder_id>', methods=['PUT'])
def rename_folder(folder_id):
    """Rename a folder"""
    try:
        folder = Folder.query.get_or_404(folder_id)
        data = request.get_json()
        name = data.get('name', '').strip()
        
        if not name:
            return jsonify({'success': False, 'error': 'Folder name is required'}), 400
        
        existing = Folder.query.filter(Folder.name == name, Folder.id != folder_id).first()
        if existing:
            return jsonify({'success': False, 'error': 'A folder with that name already exists'}), 400
        
        folder.name = name
        db.session.commit()
        
        return jsonify({'success': True, 'folder': folder.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/folders/<int:folder_id>', methods=['DELETE'])
def delete_folder(folder_id):
    """Delete a folder and all its tags"""
    try:
        folder = Folder.query.get_or_404(folder_id)
        # Delete all tags in this folder
        Tag.query.filter_by(folder_id=folder_id).delete()
        db.session.delete(folder)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Folder deleted'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/upload', methods=['POST'])
def upload_image():
    """Process uploaded tag image"""
    try:
        data = request.get_json()
        image_data = data.get('image')
        
        if ',' in image_data:
            image_data = image_data.split(',')[1]
        
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
        
        response_text = message.content[0].text
        
        return jsonify({
            'success': True,
            'data': response_text,
            'image_data': image_data
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
        scan_date_str = data.get('scan_date')
        return_date_str = data.get('return_date')
        image_data = data.get('image_data')
        folder_id = data.get('folder_id')
        
        scan_date = datetime.strptime(scan_date_str, '%Y-%m-%d').date()
        
        if return_date_str:
            return_date = datetime.strptime(return_date_str, '%Y-%m-%d').date()
        else:
            return_date = scan_date + timedelta(days=30)
        
        raw_text = f"Style Number: {style_number}\nDescription: {description}\nPO Number: {po_number}"
        
        new_tag = Tag(
            style_number=style_number,
            description=description,
            po_number=po_number,
            scan_date=scan_date,
            return_date=return_date,
            raw_text=raw_text,
            image_data=base64.b64decode(image_data) if image_data else None,
            folder_id=folder_id
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
    folder_id = request.args.get('folder_id', type=int)
    
    query = Tag.query
    folder = None
    if folder_id:
        query = query.filter_by(folder_id=folder_id)
        folder = Folder.query.get(folder_id)
    
    tags = query.order_by(Tag.return_date.asc()).all()
    folders = Folder.query.order_by(Folder.name.asc()).all()
    return render_template('tracker.html', tags=tags, today=date.today(), 
                         current_folder=folder, folders=folders)

@app.route('/api/tags', methods=['GET'])
def get_tags():
    """API endpoint to get all tags as JSON"""
    folder_id = request.args.get('folder_id', type=int)
    
    query = Tag.query
    if folder_id:
        query = query.filter_by(folder_id=folder_id)
    
    tags = query.order_by(Tag.return_date.asc()).all()
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
        
        tag.style_number = data.get('style_number', tag.style_number)
        tag.description = data.get('description', tag.description)
        tag.po_number = data.get('po_number', tag.po_number)
        
        if 'scan_date' in data:
            scan_date = datetime.strptime(data['scan_date'], '%Y-%m-%d').date()
            tag.scan_date = scan_date
        
        if 'return_date' in data:
            return_date = datetime.strptime(data['return_date'], '%Y-%m-%d').date()
            tag.return_date = return_date
        else:
            tag.return_date = tag.scan_date + timedelta(days=30)
        
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
