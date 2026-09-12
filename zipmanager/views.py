from django.shortcuts import render
from django.urls import reverse

# Create your views here.
import os
import json
import tempfile
import shutil
import logging

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, FileResponse, Http404
from django.views.decorators.http import require_POST, require_GET

from .models import ZipUpload
from .utils import (
    is_admin, store_extract_dir, safe_extract_zip, zip_directory,
    MAX_ZIP_SIZE,
)

logger = logging.getLogger(__name__)


# ------------------------------------------------------------------
# 1. Receive + extract
# ------------------------------------------------------------------
@login_required
@require_POST
def upload_zip(request):
    # --- Admin only ---
    if not is_admin(request.user):
        return JsonResponse({'error': 'Administrator access required.'}, status=403)

    z = request.FILES.get('zip_file')
    source    = request.POST.get('source', 'store')          # 'store' or 'issue'
    source_id = request.POST.get('source_id', '') or 'default'

    if not z:
        return JsonResponse({'error': 'No file received.'}, status=400)

    if z.size > MAX_ZIP_SIZE:
        return JsonResponse(
            {'error': f'Zip too large ({z.size/1024/1024:.1f} MB). Max is 1024 MB.'},
            status=400,
        )

    # --- Save incoming zip to a temp file (streamed) ---
    tmpdir = tempfile.mkdtemp(prefix='zipmgr_')
    tmpzip = os.path.join(tmpdir, 'upload.zip')
    try:
        with open(tmpzip, 'wb') as out:
            for chunk in z.chunks():
                out.write(chunk)

        record = ZipUpload.objects.create(
            source=source,
            source_id=str(source_id),
            original_name=z.name[:255],
            zip_size=z.size,
            uploaded_by=request.user,
            status='pending',
        )

        # --- Extract into MEDIA_ROOT/zip_uploads/<source>/<source_id>/ ---
        dest = store_extract_dir(source, str(source_id))

        try:
            summary = safe_extract_zip(tmpzip, dest)
        except Exception as e:
            logger.exception("Extraction failed")
            record.status = 'failed'
            record.error_message = str(e)[:2000]
            record.save(update_fields=['status', 'error_message'])
            return JsonResponse({'error': str(e)}, status=400)

        record.status = 'extracted'
        record.extracted_path = os.path.relpath(dest, settings.MEDIA_ROOT).replace('\\', '/')
        record.save(update_fields=['status', 'extracted_path'])

        return JsonResponse({
            'ok': True,
            'upload_id': record.pk,
            'file_count': summary['file_count'],
            'total_size': summary['total_size'],
        })

    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


# ------------------------------------------------------------------
# 2. Download the whole extracted folder as a zip
# ------------------------------------------------------------------
@login_required
@require_GET
def download_all(request):
    if not is_admin(request.user):
        raise Http404()

    source    = request.GET.get('source', 'store')
    source_id = request.GET.get('source_id', '') or 'default'

    dest = store_extract_dir(source, str(source_id))
    if not os.path.isdir(dest) or not os.listdir(dest):
        raise Http404("Nothing to download yet.")

    tmpdir = tempfile.mkdtemp(prefix='zipmgr_dl_')
    zip_name = f"{source}_{source_id}.zip"
    zip_path = os.path.join(tmpdir, zip_name)

    try:
        zip_directory(dest, zip_path)
        response = FileResponse(
            open(zip_path, 'rb'),
            as_attachment=True,
            filename=zip_name,
            content_type='application/zip',
        )
        # Clean up temp dir after streaming completes
        response._resource_closers.append(
            lambda: shutil.rmtree(tmpdir, ignore_errors=True)
        )
        return response
    except Exception:
        shutil.rmtree(tmpdir, ignore_errors=True)
        raise


# ------------------------------------------------------------------
# 3. List extracted files (JSON) — for the view side
# ------------------------------------------------------------------
@login_required
@require_GET
def list_files(request):
    if not is_admin(request.user):
        return JsonResponse({'error': 'Administrator access required.'}, status=403)

    source    = request.GET.get('source', 'store')
    source_id = request.GET.get('source_id', '') or 'default'
    subpath   = request.GET.get('path', '')   # optional subfolder

    base = store_extract_dir(source, str(source_id))
    target = os.path.realpath(os.path.join(base, subpath))
    base_real = os.path.realpath(base)

    if not (target == base_real or target.startswith(base_real + os.sep)):
        return JsonResponse({'error': 'Invalid path'}, status=400)
    if not os.path.isdir(target):
        return JsonResponse({'error': 'Not found'}, status=404)

    entries = []
    for name in sorted(os.listdir(target)):
        full = os.path.join(target, name)
        rel  = os.path.relpath(full, base).replace('\\', '/')
        if os.path.isdir(full):
            entries.append({'name': name, 'type': 'dir', 'path': rel})
        else:
            entries.append({
                'name': name,
                'type': 'file',
                'path': rel,
                'size': os.path.getsize(full),
                'url': f"{settings.MEDIA_URL}zip_uploads/{source}/{source_id}/{rel}",
            })

    return JsonResponse({'entries': entries, 'path': subpath})


# ------------------------------------------------------------------
# Compact view — shows extracted files (no Contact/StoredFile)
# ------------------------------------------------------------------
@login_required
@require_GET
def view_files(request):
    """Renders a tiny standalone page listing the extracted folder."""
    if not is_admin(request.user):
        raise Http404()

    source    = request.GET.get('source', 'store')
    source_id = request.GET.get('source_id', '') or 'default'

    base = store_extract_dir(source, str(source_id))
    if not os.path.isdir(base):
        raise Http404("Nothing uploaded yet.")

    entries = []
    for root, _dirs, files in os.walk(base):
        for fname in files:
            full = os.path.join(root, fname)
            rel  = os.path.relpath(full, base).replace('\\', '/')
            entries.append({
                'name': rel,
                'size': os.path.getsize(full),
                'url':  f"{settings.MEDIA_URL}zip_uploads/{source}/{source_id}/{rel}",
            })

    return render(request, 'zipmanager/view_files.html', {
        'source': source,
        'source_id': source_id,
        'entries': entries,
        'download_url': f"{reverse('zipmanager:download_all')}?source={source}&source_id={source_id}",
    })


# ------------------------------------------------------------------
# Hard delete — wipe the extracted folder + DB records
# ------------------------------------------------------------------
@login_required
@require_POST
def delete_zip(request):
    """Hard-delete all extracted files + ZipUpload records for a source/id."""
    if not is_admin(request.user):
        return JsonResponse({'error': 'Administrator access required.'}, status=403)

    source    = request.POST.get('source', 'store')
    source_id = request.POST.get('source_id', '') or 'default'

    dest = store_extract_dir(source, str(source_id))

    # 1. Delete the extracted folder from disk
    deleted_files = 0
    if os.path.isdir(dest):
        for root, _dirs, files in os.walk(dest):
            deleted_files += len(files)
        try:
            shutil.rmtree(dest)
        except OSError as e:
            logger.error(f"Failed to delete {dest}: {e}")
            return JsonResponse({'error': f'Could not delete folder: {e}'}, status=500)

    # 2. Delete the DB records
    ZipUpload.objects.filter(source=source, source_id=str(source_id)).delete()

    return JsonResponse({
        'ok': True,
        'deleted_files': deleted_files,
    })