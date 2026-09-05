# filemanager/utils.py

from django.core.files.storage import default_storage
import os
import re

def sanitize_filename(filename):
    """Remove invalid Windows characters from filename"""
    if not filename:
        return filename
    name, ext = os.path.splitext(filename)
    name = re.sub(r'[<>:"/\\|?*]', '_', name)
    name = name.strip(' .')
    if len(name) > 90:
        name = name[:90]
    return f"{name}{ext}"

def save_file_hybrid(file, upload_path="stored_files"):
    """
    Hybrid file upload:
    - ≤25MB: Direct upload (fast)
    - >25MB: 10MB chunked upload (safe)
    """
    safe_filename = sanitize_filename(file.name)
    file_path = f"{upload_path}/{safe_filename}"
    
    # Small files: Direct upload
    if file.size <= 25 * 1024 * 1024:
        return default_storage.save(file_path, file)
    
    # Large files: 10MB chunks
    CHUNK_SIZE = 10 * 1024 * 1024
    with default_storage.open(file_path, 'wb+') as destination:
        for chunk in file.chunks(chunk_size=CHUNK_SIZE):
            destination.write(chunk)
    return file_path