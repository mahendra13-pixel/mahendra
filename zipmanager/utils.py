import os
import zipfile
import shutil
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

# ---- Hard limits ----
MAX_ZIP_SIZE        = 1 * 1024 * 1024 * 1024   # 1 GB upload
MAX_UNCOMPRESSED    = 3 * 1024 * 1024 * 1024   # 3 GB extracted (zip-bomb guard)
MAX_FILE_COUNT      = 5000                     # per archive


def is_admin(user):
    """Only staff/superusers may use zip upload."""
    return bool(user and user.is_authenticated and (user.is_staff or user.is_superuser))


def store_extract_dir(source: str, source_id: str) -> str:
    """
    Absolute path where this zip's contents are extracted.
    e.g.  MEDIA_ROOT/zip_uploads/store/216/
    """
    safe_source = ''.join(c for c in source if c.isalnum() or c in ('_', '-'))
    safe_id     = ''.join(c for c in str(source_id) if c.isalnum() or c in ('_', '-'))
    rel = os.path.join('zip_uploads', safe_source, safe_id)
    abs_path = os.path.join(settings.MEDIA_ROOT, rel)
    os.makedirs(abs_path, exist_ok=True)
    return abs_path


def safe_extract_zip(zip_path: str, dest_dir: str) -> dict:
    """
    Safely extract a zip, blocking path traversal (Zip Slip)
    and zip-bomb attacks. Returns a summary dict.
    """
    os.makedirs(dest_dir, exist_ok=True)
    dest_real = os.path.realpath(dest_dir)

    with zipfile.ZipFile(zip_path) as zf:
        infos = zf.infolist()

        if len(infos) > MAX_FILE_COUNT:
            raise ValueError(f"Too many files in zip ({len(infos)} > {MAX_FILE_COUNT})")

        total_uncompressed = sum(i.file_size for i in infos)
        if total_uncompressed > MAX_UNCOMPRESSED:
            raise ValueError(
                f"Uncompressed size too large "
                f"({total_uncompressed / 1024 / 1024:.1f} MB)"
            )

        # Path-traversal check before extracting anything
        for info in infos:
            target = os.path.realpath(os.path.join(dest_dir, info.filename))
            if not (target == dest_real or target.startswith(dest_real + os.sep)):
                raise ValueError(f"Unsafe path in zip: {info.filename}")

        zf.extractall(dest_dir)

    file_count = sum(len(files) for _, _, files in os.walk(dest_dir))
    total_size = sum(
        os.path.getsize(os.path.join(root, f))
        for root, _, files in os.walk(dest_dir) for f in files
    )
    return {
        'file_count': file_count,
        'total_size': total_size,
        'path': dest_dir,
    }


def zip_directory(dir_path: str, output_path: str) -> str:
    """
    Zip an entire directory tree for 'Download All'.
    Uses the directory's own name as the root folder inside the zip.
    """
    dir_path = os.path.realpath(dir_path)
    if not os.path.isdir(dir_path):
        raise FileNotFoundError(dir_path)

    root_name = os.path.basename(dir_path.rstrip(os.sep)) or 'archive'
    parent    = os.path.dirname(dir_path)

    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        for root, _dirs, files in os.walk(dir_path):
            for fname in files:
                full = os.path.join(root, fname)
                # arcname preserves folder structure relative to dir_path
                arcname = os.path.join(root_name, os.path.relpath(full, dir_path))
                zf.write(full, arcname)

    return output_path