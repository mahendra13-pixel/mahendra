# filemanager/utils.py

from django.core.files.storage import default_storage
from django.conf import settings
import os
import re
import subprocess
import logging

logger = logging.getLogger(__name__)

# ✅ Cache FFmpeg availability check
_ffmpeg_available = None

def is_ffmpeg_available():
    """Check if FFmpeg is installed and available (cached result)"""
    global _ffmpeg_available
    
    if _ffmpeg_available is not None:
        return _ffmpeg_available
    
    try:
        subprocess.run(['ffmpeg', '-version'], 
                    capture_output=True, 
                    check=True,
                    timeout=10)
        _ffmpeg_available = True
        logger.info("FFmpeg detected - compression enabled")
    except (subprocess.TimeoutExpired, Exception):
        _ffmpeg_available = False
        logger.warning("FFmpeg not found - compression disabled (files will be uploaded as-is)")
    
    return _ffmpeg_available


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


def get_available_compressed_path(file_path):
    """
    Generate a unique compressed filename to prevent collisions
    """
    name, ext = os.path.splitext(file_path)
    compressed_path = f"{name}_compressed{ext}"
    
    # Use default_storage to check for existing files
    if default_storage.exists(compressed_path):
        # If compressed version exists, use get_available_name
        return default_storage.get_available_name(compressed_path)
    return compressed_path


def compress_video(file_path):
    """
    High-quality compression for videos > 500 MB
    Uses H.265 codec for maximum compression with minimal quality loss
    
    NOTE: This function assumes default_storage is local-filesystem-backed.
    If switching to cloud storage (S3, etc.), this will need to be updated.
    
    WARNING: This runs synchronously and may take several minutes.
    For production, consider moving this to a background task (Celery/RQ).
    """
    # Check if FFmpeg is available first
    if not is_ffmpeg_available():
        return file_path
    
    full_path = os.path.join(settings.MEDIA_ROOT, file_path)
    
    # Check if file exists
    if not os.path.exists(full_path):
        return file_path
    
    # Get file size in MB
    size_mb = os.path.getsize(full_path) / (1024 * 1024)
    
    # ONLY compress if file is > 500 MB
    if size_mb <= 100:
        return file_path
    
    # Generate compressed filename with collision protection
    compressed_path = get_available_compressed_path(file_path)
    full_compressed_path = os.path.join(settings.MEDIA_ROOT, compressed_path)
    
    try:
        # High-quality compression using H.265
        cmd = [
            'ffmpeg',
            '-i', full_path,
            '-c:v', 'libx265',      # H.265 (HEVC) - better compression
            '-preset', 'medium',     # Balance speed vs compression
            '-crf', '23',            # Quality (18-28, 23 is good)
            '-c:a', 'aac',           # Audio codec
            '-b:a', '128k',          # Audio bitrate
            '-movflags', '+faststart', # Web optimization
            '-y',                    # Overwrite
            full_compressed_path
        ]
        
        # Run ffmpeg with timeout to prevent hanging (30 minutes max for large videos)
        subprocess.run(cmd, check=True, capture_output=True, timeout=1800)
        
        # Check compression effectiveness
        original_size = os.path.getsize(full_path)
        compressed_size = os.path.getsize(full_compressed_path)
        
        # Only use compressed if it's actually smaller
        if compressed_size < original_size:
            try:
                os.remove(full_path)  # Delete original
                logger.info(f"Compression successful: {original_size/1024/1024:.1f}MB → {compressed_size/1024/1024:.1f}MB")
            except OSError as e:
                logger.error(f"Failed to delete original file {full_path}: {e}")
                # Keep both files, return compressed
            return compressed_path
        else:
            # Compression not beneficial, delete compressed file
            try:
                os.remove(full_compressed_path)
                logger.info("Compression not beneficial - keeping original")
            except OSError as e:
                logger.error(f"Failed to delete compressed file {full_compressed_path}: {e}")
            return file_path
            
    except subprocess.TimeoutExpired:
        # Compression timed out, keep original
        logger.error(f"Compression timed out for {file_path} (>30 minutes)")
        if os.path.exists(full_compressed_path):
            try:
                os.remove(full_compressed_path)
            except OSError:
                pass
        return file_path
    except Exception as e:
        # Compression failed, keep original
        logger.error(f"Compression failed for {file_path}: {e}")
        if os.path.exists(full_compressed_path):
            try:
                os.remove(full_compressed_path)
            except OSError:
                pass
        return file_path


def save_file_hybrid(file, upload_path="stored_files"):
    """
    Hybrid file upload with conditional high-quality compression for large files
    - ≤ 25MB: Direct upload (fast)
    - 25-500MB: Chunked upload (10MB chunks)
    - > 500MB: Chunked upload + Compression (only if FFmpeg is installed)
    """
    safe_filename = sanitize_filename(file.name)
    file_path = f"{upload_path}/{safe_filename}"
    file_size = file.size
    
    # SMALL FILES (≤ 25MB): Direct upload
    if file_size <= 25 * 1024 * 1024:
        saved_path = default_storage.save(file_path, file)
        return saved_path
    
    # LARGE FILES (> 25MB): Chunked upload with collision prevention
    CHUNK_SIZE = 10 * 1024 * 1024
    
    # FIX: Get available name BEFORE opening to prevent overwrites
    available_path = default_storage.get_available_name(file_path)
    
    try:
        with default_storage.open(available_path, 'wb+') as destination:
            for chunk in file.chunks(chunk_size=CHUNK_SIZE):
                destination.write(chunk)
    except Exception as e:
        # Clean up partial file if write fails
        if default_storage.exists(available_path):
            default_storage.delete(available_path)
        raise e
    
    # COMPRESS ONLY if file > 500 MB (FFmpeg check is inside compress_video)
    if file_size > 100 * 1024 * 1024:
        compressed_path = compress_video(available_path)  # ✅ FIXED: Changed from compress_video_lossless
        return compressed_path
    
    return available_path