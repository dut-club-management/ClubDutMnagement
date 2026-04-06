import os
import uuid
from datetime import datetime
from flask import Blueprint, request, jsonify, current_app, send_file
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app import db

uploads_bp = Blueprint('uploads', __name__, url_prefix='/uploads')

ALLOWED_EXTENSIONS = {
    'image': {'png', 'jpg', 'jpeg', 'gif', 'webp'},
    'document': {'pdf', 'doc', 'docx', 'txt', 'rtf'},
    'spreadsheet': {'xls', 'xlsx', 'csv'},
    'presentation': {'ppt', 'pptx'},
    'archive': {'zip', 'rar', '7z', 'tar', 'gz'},
    'other': {'mp4', 'mp3', 'avi', 'mov'}
}

MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB

def allowed_file(filename, file_type='document'):
    """Check if file extension is allowed"""
    if not filename:
        return False
    
    ext = filename.rsplit('.', 1)[1].lower()
    return ext in ALLOWED_EXTENSIONS.get(file_type, ALLOWED_EXTENSIONS['document'])

@uploads_bp.route('/upload', methods=['POST'])
@login_required
def upload_file():
    """Enhanced file upload with validation"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        file_type = request.form.get('file_type', 'document')
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Validate file
        if not allowed_file(file.filename, file_type):
            return jsonify({'error': 'File type not allowed'}), 400
        
        # Check file size
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)
        
        if file_size > MAX_FILE_SIZE:
            return jsonify({'error': 'File too large. Maximum size is 16MB'}), 413
        
        # Generate unique filename
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4().hex}_{filename}"
        
        # Create upload directory
        upload_dir = os.path.join(current_app.root_path, 'static', 'uploads', file_type)
        os.makedirs(upload_dir, exist_ok=True)
        
        # Save file
        file_path = os.path.join(upload_dir, unique_filename)
        file.save(file_path)
        
        # Return file info
        return jsonify({
            'success': True,
            'filename': unique_filename,
            'original_filename': filename,
            'file_size': file_size,
            'file_type': file_type,
            'upload_path': f"static/uploads/{file_type}/{unique_filename}",
            'download_url': f"/uploads/download/{file_type}/{unique_filename}"
        })
        
    except Exception as e:
        print(f"❌ Upload error: {e}")
        return jsonify({'error': 'Upload failed'}), 500

@uploads_bp.route('/download/<file_type>/<filename>')
@login_required
def download_file(file_type, filename):
    """Secure file download"""
    try:
        file_path = os.path.join(current_app.root_path, 'static', 'uploads', file_type, filename)
        
        if not os.path.exists(file_path):
            return jsonify({'error': 'File not found'}), 404
        
        return send_file(file_path, as_attachment=True)
        
    except Exception as e:
        print(f"❌ Download error: {e}")
        return jsonify({'error': 'Download failed'}), 500

@uploads_bp.route('/delete/<file_type>/<filename>', methods=['DELETE'])
@login_required
def delete_file(file_type, filename):
    """Delete uploaded file"""
    try:
        file_path = os.path.join(current_app.root_path, 'static', 'uploads', file_type, filename)
        
        if not os.path.exists(file_path):
            return jsonify({'error': 'File not found'}), 404
        
        os.remove(file_path)
        
        return jsonify({'success': True, 'message': 'File deleted successfully'})
        
    except Exception as e:
        print(f"❌ Delete error: {e}")
        return jsonify({'error': 'Delete failed'}), 500
