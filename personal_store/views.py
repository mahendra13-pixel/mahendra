from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from django.urls import reverse
from .models import PersonalItem, PersonalStoredFile
from django.http import JsonResponse, Http404, HttpResponse
from filemanager.telegram_storage import (
    upload_to_telegram,
    delete_telegram_message,
    get_telegram_file_url,
)
from filemanager.utils import sanitize_filename
import requests
import socket


MAX_FILE_SIZE = 20 * 1024 * 1024  # 20 MB

def is_admin(user):
    return user.is_staff or user.is_superuser

# --- Main List View ---
@login_required(login_url="/admin/login/")
@user_passes_test(is_admin)
def personal_storage_view(request):
    items = PersonalItem.objects.all().order_by('-created_at')
    
    # Optional completion filter via URL
    status_filter = request.GET.get('status', 'all')
    if status_filter == 'pending':
        items = items.filter(is_completed=False)
    elif status_filter == 'completed':
        items = items.filter(is_completed=True)

    # Search — covers every text field on the PersonalItem card
    search_query = request.GET.get('search')
    if search_query:
        items = items.filter(
            # 1. Name
            Q(name__icontains=search_query)
            # 2. Description
            | Q(description__icontains=search_query)
            # 3. Remarks
            | Q(remarks__icontains=search_query)
            # 4. Priority
            | Q(priority__icontains=search_query)
            # 5. Status
            | Q(status__icontains=search_query)
            # 6. Link (URL)
            | Q(link__icontains=search_query)
            # 7. IP Address
            | Q(ip_address__icontains=search_query)
        )

    paginator = Paginator(items, 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    return render(request, 'personal_store/personal_storage_view.html', {
        'page_obj': page_obj,
    })

# --- Create/Store View ---
@login_required(login_url="/admin/login/")
@user_passes_test(is_admin)
def personal_store_submit(request):
    if request.method == "POST":
        name = request.POST.get("name")
        description = request.POST.get("description")
        priority = request.POST.get("priority")
        remarks = request.POST.get("remarks", "")
        link = request.POST.get("link") or None     
        # ✅ NEW FIELDS
        due_date = request.POST.get("due_date") or None
        status = request.POST.get("status", "Pending")
        now = timezone.localtime(timezone.now())
        
        multiple_files = request.FILES.getlist("media_file")

        # ============================================================
        # ENFORCE 20 MB UPLOAD LIMIT PER FILE
        # ============================================================
        for file in multiple_files:
            if file.size > MAX_FILE_SIZE:
                messages.error(
                    request,
                    f"❌ '{file.name}' is {file.size / 1024 / 1024:.1f} MB. Max allowed: 20 MB."
                )
                return redirect("personal_store:storage_view")

        try:
            with transaction.atomic():
                item = PersonalItem.objects.create(
                    name=name,
                    description=description,
                    priority=priority,
                    remarks=remarks,
                    link=link, 
                    # ✅ NEW FIELDS SAVED
                    due_date=due_date,
                    status=status,
                    ip_address=get_client_ip(request),  
                    created_at=now,
                    updated_at=now,
                )

                # Upload each file to Telegram (per-file try/except for resilience)
                for idx, file in enumerate(multiple_files):
                    slot_key = str(idx + 1)  # "1", "2", "3", ...
                    try:
                        info = upload_to_telegram(
                            file,
                            filename=sanitize_filename(file.name)
                        )
                        if info:
                            item.set_telegram_file(slot_key, info)
                        else:
                            messages.warning(
                                request,
                                f"⚠️ Could not upload '{file.name}' to Telegram."
                            )
                    except Exception as tg_err:
                        messages.warning(
                            request,
                            f"⚠️ '{file.name}' Telegram upload failed: {tg_err}"
                        )

                item.file_count = len(multiple_files)
                item.is_multiple = len(multiple_files) > 1
                item.save()

            messages.success(request, "✅ Personal item stored successfully!")
        except Exception as e:
            messages.error(request, f"Error storing item: {str(e)}")

        return redirect("personal_store:storage_view")
    
    # ✅ FIX: Render the form on GET instead of redirecting
    return render(request, 'personal_store/personal_store_form.html')

# --- Toggle Completion (No popup) ---
@login_required(login_url="/admin/login/")
@user_passes_test(is_admin)
def toggle_completion(request, pk):
    item = get_object_or_404(PersonalItem, pk=pk)
    item.is_completed = not item.is_completed
    item.save()
    
    status = "completed" if item.is_completed else "pending"
    messages.success(request, f"Item marked as {status}.")
    
    # Preserve page + search
    page = request.POST.get("page", 1)
    search = request.POST.get("search", "").strip()
    url = f"{reverse('personal_store:storage_view')}?page={page}"
    if search:
        url += f"&search={search}"
    return redirect(url)

# --- Delete View (Hard Delete from Disk) ---
@login_required(login_url="/admin/login/")
@user_passes_test(is_admin)
def personal_storage_delete(request, pk):
    item = get_object_or_404(PersonalItem, pk=pk)
    if request.method == "POST":
        # item.delete() handles: TG messages + legacy StoredFile rows + media_file + DB row
        item.delete()

        messages.success(request, "✅ Item permanently deleted.")
        
        # Preserve page + search
        page = request.POST.get("page", 1)
        search = request.POST.get("search", "").strip()
        url = f"{reverse('personal_store:storage_view')}?page={page}"
        if search:
            url += f"&search={search}"
        return redirect(url)
    
    return redirect("personal_store:storage_view")

# --- Edit View ---
@login_required(login_url="/admin/login/")
@user_passes_test(is_admin)
def personal_store_edit(request, pk):
    item = get_object_or_404(PersonalItem, pk=pk)
    stored_files = item.stored_files.all()
    tg_map = item.get_telegram_map()
    telegram_files = [
        {'slot_key': k, **v}
        for k, v in tg_map.items()
    ]
    
    if request.method == "POST":
        item.name = request.POST.get("name")
        item.description = request.POST.get("description")
        item.priority = request.POST.get("priority")
        item.remarks = request.POST.get("remarks")
        item.link = request.POST.get("link") or None 
        item.is_completed = request.POST.get("is_completed") == "on"
        # ✅ NEW FIELDS
        item.due_date = request.POST.get("due_date") or None
        item.status = request.POST.get("status", "Pending")

        # ============================================================
        # HANDLE TELEGRAM FILE OPERATIONS
        # ============================================================

        # Clear all Telegram files
        if request.POST.get("media_clear") == "on":
            for slot_key, info in item.get_telegram_map().items():
                if info and info.get('message_id'):
                    delete_telegram_message(info.get('message_id'))
            item.telegram_files = ''
            item.file_count = 0
            item.is_multiple = False

        # Upload new files
        elif request.FILES.getlist("media_file"):
            action = request.POST.get("file_action", "replace")
            multiple_files = request.FILES.getlist("media_file")

            # 20 MB size check
            for file in multiple_files:
                if file.size > MAX_FILE_SIZE:
                    messages.error(
                        request,
                        f"❌ '{file.name}' is {file.size / 1024 / 1024:.1f} MB. Max allowed: 20 MB."
                    )
                    return redirect("personal_store:storage_view")

            # REPLACE: delete all existing Telegram files first
            if action == "replace":
                for slot_key, info in item.get_telegram_map().items():
                    if info and info.get('message_id'):
                        delete_telegram_message(info.get('message_id'))
                item.telegram_files = ''

            # Upload each new file
            existing_keys = list(item.get_telegram_map().keys())
            next_index = 1

            for file in multiple_files:
                # Find next available slot key
                while str(next_index) in existing_keys:
                    next_index += 1
                slot_key = str(next_index)
                next_index += 1

                try:
                    info = upload_to_telegram(
                        file,
                        filename=sanitize_filename(file.name)
                    )
                    if info:
                        item.set_telegram_file(slot_key, info)
                    else:
                        messages.warning(
                            request,
                            f"⚠️ Could not upload '{file.name}' to Telegram."
                        )
                except Exception as tg_err:
                    messages.warning(
                        request,
                        f"⚠️ '{file.name}' Telegram upload failed: {tg_err}"
                    )

            item.file_count = len(item.get_telegram_map())
            item.is_multiple = item.file_count > 1

        item.updated_at = timezone.localtime(timezone.now())
        item.save()
        messages.success(request, "✅ Item updated successfully.")
        return redirect("personal_store:storage_view")

    return render(request, 'personal_store/personal_store_edit.html', {
        'item': item,
        'stored_files': stored_files,
        'telegram_files': telegram_files,
    })

# --- Detail View ---
@login_required(login_url="/admin/login/")
@user_passes_test(is_admin)
def personal_item_detail(request, pk):
    item = get_object_or_404(PersonalItem, pk=pk)
    stored_files = item.stored_files.all()
    tg_map = item.get_telegram_map()
    telegram_files = [
        {'slot_key': k, **v}
        for k, v in tg_map.items()
    ]
    return render(request, 'personal_store/personal_item_detail.html', {
        'item': item,
        'stored_files': stored_files,
        'telegram_files': telegram_files,
    })

def get_client_ip(request):
    """Get the real client IP address even behind proxies."""
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[0].strip()
    else:
        ip = request.META.get("REMOTE_ADDR")

    if ip in ("127.0.0.1", "::1", "localhost"):
        try:
            hostname = socket.gethostname()
            ip = socket.gethostbyname(hostname)
        except:
            ip = "127.0.0.1"

    if ip == "::1":
        ip = "127.0.0.1"

    return ip    

@login_required(login_url="/admin/login/")
@user_passes_test(is_admin)
def personal_delete_file(request, pk, slot_key):
    """Delete a specific Telegram file from a personal store item."""
    item = get_object_or_404(PersonalItem, pk=pk)
    tg_map = item.get_telegram_map()

    info = tg_map.get(slot_key)
    if not info:
        return JsonResponse({"status": "error", "message": "File not found"}, status=404)

    file_name = info.get('file_name', 'file')

    # Delete the Telegram message
    message_id = info.get('message_id')
    if message_id:
        delete_telegram_message(message_id)

    # Remove from map
    item.remove_telegram_file(slot_key)
    item.file_count = len(item.get_telegram_map())
    item.is_multiple = item.file_count > 1
    item.save()

    return JsonResponse({
        "status": "success",
        "message": f"Deleted: {file_name}",
        "file_count": item.file_count,
    })


@login_required(login_url="/admin/login/")
@user_passes_test(is_admin)
def serve_personal_telegram_file(request, pk, slot_key):
    """Proxy the Telegram file for a personal item through Django."""
    item = get_object_or_404(PersonalItem, pk=pk)
    tg_map = item.get_telegram_map()

    if slot_key not in tg_map:
        raise Http404("File not found")

    file_id = tg_map[slot_key].get('file_id')
    if not file_id:
        raise Http404("File ID missing")

    url = get_telegram_file_url(file_id)
    if not url:
        raise Http404("Could not resolve Telegram URL")

    try:
        r = requests.get(url, timeout=60)
        if r.status_code != 200:
            raise Http404("Telegram returned an error")
    except Exception:
        raise Http404("Could not fetch file from Telegram")

    content_type = r.headers.get('Content-Type', 'application/octet-stream')
    filename = tg_map[slot_key].get('file_name', 'file')
    ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''

    type_map = {
        'pdf': 'application/pdf',
        'jpg': 'image/jpeg',
        'jpeg': 'image/jpeg',
        'png': 'image/png',
        'gif': 'image/gif',
        'webp': 'image/webp',
        'svg': 'image/svg+xml',
        'mp4': 'video/mp4',
        'webm': 'video/webm',
        'mp3': 'audio/mpeg',
        'wav': 'audio/wav',
        'txt': 'text/plain; charset=utf-8',
        'html': 'text/html; charset=utf-8',
        'json': 'application/json',
    }

    if ext in type_map:
        content_type = type_map[ext]

    response = HttpResponse(r.content, content_type=content_type)
    response['Content-Disposition'] = f'inline; filename="{filename}"'
    return response