from accounts.views import is_normal_user, normal_user_required
from filemanager.utils import save_file_hybrid, sanitize_filename
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import user_passes_test
from django.http import HttpResponse, Http404
from django.utils import timezone
from .models import Contact
from django.db import models
from django.db import transaction
import pandas as pd
from io import BytesIO
from datetime import datetime
import socket
import getpass
import requests
from django.urls import reverse 
from django.core.paginator import Paginator
from .models import StoredFile
from django.http import JsonResponse
from filemanager.telegram_storage import (
    upload_to_telegram,
    delete_telegram_message,
    get_telegram_file_url,
)


# Helper function to check if user is admin
def is_admin(user):
    return user.is_staff or user.is_superuser


def get_client_ip(request):
    """Get the real client IP address even behind proxies"""
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


def get_client_hostname(request):
    """Get the client hostname"""
    try:
        # First try to get from request
        hostname = request.META.get("HTTP_HOST", "").split(":")[0]
        if hostname:
            return hostname
    except:
        pass

    try:
        # Fallback to socket.gethostname()
        return socket.gethostname()
    except:
        return "Unknown"


def get_client_username(request):
    """Get the client username (who am i)"""
    try:
        # Try to get from request user if authenticated
        if request.user.is_authenticated:
            return request.user.username
    except:
        pass

    try:
        # Fallback to getpass.getuser()
        return getpass.getuser()
    except:
        return "Unknown"


def get_client_os(request):
    """Detect client operating system from user agent"""
    user_agent = request.META.get("HTTP_USER_AGENT", "").lower()

    if "windows" in user_agent:
        if "windows nt 10.0" in user_agent:
            return "Windows 10/11"
        elif "windows nt 6.3" in user_agent:
            return "Windows 8.1"
        elif "windows nt 6.2" in user_agent:
            return "Windows 8"
        elif "windows nt 6.1" in user_agent:
            return "Windows 7"
        else:
            return "Windows"
    elif "mac" in user_agent or "darwin" in user_agent:
        return "macOS"
    elif "linux" in user_agent:
        if "android" in user_agent:
            return "Android"
        else:
            return "Linux"
    elif "iphone" in user_agent or "ipad" in user_agent:
        return "iOS"
    else:
        return "Unknown OS"


# About Page (Public)
def about(request):
    return render(request, "core/about.html")


# Blog Page (Public)
def blog(request):
    return render(request, "core/blog.html")


# Function to generate Ticket ID - OPTIMIZED VERSION
def generate_ticket_id(contact):
    """Generate Ticket ID in format IT-001, IT-002, etc. (only for resolved issues)"""
    if not contact.is_resolved:
        return f"IT-{str(contact.id).zfill(3)}"

    # Count resolved contacts with ID less than or equal to current
    count = Contact.objects.filter(
        is_resolved=True, is_stored=False, id__lte=contact.id
    ).count()

    return f"IT-{str(count).zfill(3)}"


# Contact Page - Main Form (Landing Page - Public)
@login_required(login_url="/accounts/login/")
def contact(request):
    ip_address = get_client_ip(request)
    hostname = request.user.username if request.user.is_authenticated else get_client_hostname(request)
    username = get_client_username(request)
    os_info = get_client_os(request)
    is_admin_user = request.user.is_authenticated and request.user.is_staff

    if request.method == "POST":
        # Check which button was clicked
        if "resolve" in request.POST:
            action = "resolve"
        else:
            action = "send"

        name = request.POST.get("name")
        phone = request.POST.get("phone")
        priority = request.POST.get("priority")
        message = request.POST.get("message")
        department = request.POST.get("department", "General")
        link = request.POST.get("link") or None

        # Get multiple selections and join them with comma
        call_attended_by = ", ".join(request.POST.getlist("call_attended_by"))
        handover_to = ", ".join(request.POST.getlist("handover_to"))
        solved_by = ", ".join(request.POST.getlist("solved_by"))

        # NEW: Get assigned_to and remarks
        assigned_to = ", ".join(request.POST.getlist("assigned_to"))
        remarks = request.POST.get("remarks", "")

        status = request.POST.get("status", "Pending")

        now = timezone.localtime(timezone.now())

        is_resolved = False
        if action == "resolve":
            is_resolved = True
            status = "Closed"

        # ============================================================
        # HANDLE FILES - Single vs Multiple
        # ============================================================

        multiple_files = request.FILES.getlist("multiple_files")
        media_file = None
        is_multiple = False
        file_count = 0

        if multiple_files and len(multiple_files) > 0:
            file_count = len(multiple_files)
            if file_count == 1:
                media_file = multiple_files[0]
                is_multiple = False
            else:
                media_file = multiple_files[0]  # First file as cover
                is_multiple = True
        # ============================================================
        
        # ✅ NEW: enforce 20 MB per file (matches personal_store)
        MAX_FILE_SIZE = 20 * 1024 * 1024
        for f in multiple_files:
            if f.size > MAX_FILE_SIZE:
                messages.error(
                    request,
                    f"❌ '{f.name}' is {f.size / 1024 / 1024:.1f} MB. Max allowed: 20 MB."
                )
                return redirect("core:contact")
            
        try:
            with transaction.atomic():
                contact = Contact.objects.create(
                    name=name,
                    department=department,
                    phone=phone,
                    ip_address=ip_address,
                    hostname=hostname,
                    username=username,
                    os_info=os_info,
                    priority=priority,
                    message=message,
                    link=link,        
                    call_attended_by=call_attended_by,
                    handover_to=handover_to,
                    solved_by=solved_by,
                    assigned_to=assigned_to,
                    remarks=remarks,
                    media_file=None,
                    is_multiple=is_multiple,
                    file_count=file_count,
                    status=status,
                    is_resolved=is_resolved,
                    date=now.date(),
                    time=now.time(),
                    created_at=now,
                    resolved_at=now if is_resolved else None,
                    updated_at=now,
                    created_by=request.user,      
                )
                # ✅ Telegram-only upload (no local disk save)
                for idx, file in enumerate(multiple_files):
                    slot_key = str(idx + 1)
                    try:
                        info = upload_to_telegram(
                            file, filename=sanitize_filename(file.name)
                        )
                        if info:
                            contact.set_telegram_file(slot_key, info)
                        else:
                            messages.warning(
                                request,
                                f"⚠️ '{file.name}' could not be uploaded to Telegram."
                            )
                    except Exception as tg_err:
                        messages.warning(
                            request,
                            f"⚠️ '{file.name}' Telegram upload failed: {tg_err}"
                        )
                contact.save(update_fields=["telegram_files"])

            if action == "resolve":
                messages.success(
                    request,
                    f"Hi {name}, your issue has been created and marked as Resolved! - {file_count} file(s)",
                )
            else:
                messages.success(
                    request,
                    f"Hi {name}, your message has been submitted successfully! - {file_count} file(s)",
                )
        except Exception as e:
            messages.error(request, f"Error submitting issue: {str(e)}")

        return redirect("core:contact")

    # Get all unresolved issues
    contacts = Contact.objects.filter(is_resolved=False, is_stored=False).order_by(
        "-id"
    )

    # IP FILTERING: If not admin, only show issues with matching IP OR public issues
    if not is_admin_user:
        contacts = contacts.filter(
            models.Q(created_by=request.user) |
            models.Q(is_public=True) |
            # Fallback for old issues without created_by — use IP
            models.Q(created_by__isnull=True, ip_address=ip_address)
        )

    resolved_contacts = Contact.objects.filter(
        is_resolved=True, is_stored=False
    ).order_by("-id")

    # IP FILTERING: If not admin, only show resolved issues with matching IP OR public issues
    if not is_admin_user:
        resolved_contacts = resolved_contacts.filter(
            models.Q(created_by=request.user) |
            models.Q(is_public=True) |
            models.Q(created_by__isnull=True, ip_address=ip_address)
        )

    # Get pending and in-progress issues for the modal
    pending_contacts = Contact.objects.filter(
        is_resolved=False, is_stored=False, status__in=["Pending", "In Progress"]
    ).order_by("-created_at")

    # IP FILTERING: If not admin, only show pending issues with matching IP OR public issues
    if not is_admin_user:
        pending_contacts = pending_contacts.filter(
            models.Q(created_by=request.user) |
            models.Q(is_public=True) |
            models.Q(created_by__isnull=True, ip_address=ip_address)
        )

    # Date filter for Issue Slider (uses 'date' parameter)
    slider_date = request.GET.get("date")
    if slider_date:
        try:
            # Try to parse as date if it's a string
            slider_date_obj = datetime.strptime(slider_date, "%Y-%m-%d").date()
            contacts = contacts.filter(date=slider_date_obj)
            pending_contacts = pending_contacts.filter(date=slider_date_obj)
        except (ValueError, TypeError):
            # If it's already a date object or can't parse, try direct filter
            contacts = contacts.filter(date=slider_date)
            pending_contacts = pending_contacts.filter(date=slider_date)

    # Date filter for Resolved Modal (uses 'resolved_date' parameter)
    resolved_date = request.GET.get("resolved_date")
    if resolved_date:
        try:
            resolved_date_obj = datetime.strptime(resolved_date, "%Y-%m-%d").date()
            resolved_contacts = resolved_contacts.filter(date=resolved_date_obj)
        except (ValueError, TypeError):
            resolved_contacts = resolved_contacts.filter(date=resolved_date)

    resolved_paginator = Paginator(resolved_contacts, 15)
    resolved_page = request.GET.get("resolved_page", 1)
    resolved_page_obj = resolved_paginator.get_page(resolved_page)

    slider_paginator = Paginator(contacts, 20)  # 20 issues per page
    slider_page = request.GET.get("page", 1)  # Get page from URL (?page=2)
    slider_page_obj = slider_paginator.get_page(slider_page)

    pending_paginator = Paginator(pending_contacts, 10)  # 10 per page for modal
    pending_page = request.GET.get(
        "pending_page", 1
    )  # Get page from URL (?pending_page=2)
    pending_page_obj = pending_paginator.get_page(pending_page)

    return render(
        request,
        "core/contact.html",
        {
            "slider_page_obj": slider_page_obj,
            "resolved_page_obj": resolved_page_obj,
            "pending_page_obj": pending_page_obj,
            "is_admin_user": is_admin_user,
            "user_ip": ip_address,
            "user_hostname": hostname,
            "user_username": username,
        },
    )


# Issue Detail - Anyone can view
@login_required(login_url="/admin/login/")
@user_passes_test(is_admin)
def issue_detail(request, pk):
    """View issue details with all files"""
    contact = get_object_or_404(Contact, pk=pk, is_stored=False)

    # Get files for this issue (if any)
    stored_files = StoredFile.objects.filter(contact=contact)

    return render(
        request,
        "core/issue_detail.html",
        {
            "contact": contact,
            "stored_files": stored_files,
        },
    )


## Edit Issue - Admin Only
@login_required(login_url="/admin/login/")
@user_passes_test(is_admin)
def issue_edit(request, pk):
    contact = get_object_or_404(Contact, pk=pk, is_stored=False)

    # ============================================================
    # ✅ GET ALL FILES - BOTH OLD AND NEW
    # ============================================================

    # Get new files from StoredFile model
    stored_files_qs = StoredFile.objects.filter(contact=contact).order_by("id")
    stored_files = list(stored_files_qs)

    # Check for old legacy file in media_file
    has_legacy_file = False
    legacy_file = None

    if contact.media_file:
        # Check if this file is already in stored_files (by checking if any stored_file has same file name)
        # If not, it's a legacy file
        file_name = contact.media_file.name.split("/")[-1]
        exists_in_stored = any(sf.file_name == file_name for sf in stored_files)

        if not exists_in_stored:
            has_legacy_file = True

            try:
                safe_size = contact.media_file.size
            except (FileNotFoundError, OSError, ValueError):
                safe_size = 0
            try:
                safe_url = contact.media_file.url
            except (ValueError, OSError):
                safe_url = ""

            legacy_file = {
                "name": file_name,
                "size": safe_size,
                "url": safe_url,
            }

            # Also add to stored_files list so it appears in the list
            # Create a virtual object with the same attributes
            class VirtualFile:
                pass

            virtual = VirtualFile()
            virtual.file_name = file_name
            virtual.file_size = safe_size
            virtual.file_url = safe_url
            virtual.file = contact.media_file
            virtual.is_legacy = True
            stored_files.append(virtual)

    # Total file count
    total_files = len(stored_files) + len(contact.get_telegram_map())
    # ============================================================

    if request.method == "POST":
        contact.name = request.POST.get("name")
        contact.department = request.POST.get("department")
        contact.phone = request.POST.get("phone")
        contact.ip_address = request.POST.get("ip_address")
        contact.hostname = request.POST.get("hostname")
        contact.username = request.POST.get("username")
        contact.priority = request.POST.get("priority")
        contact.message = request.POST.get("message")

        contact.call_attended_by = ", ".join(request.POST.getlist("call_attended_by"))
        contact.handover_to = ", ".join(request.POST.getlist("handover_to"))
        contact.solved_by = ", ".join(request.POST.getlist("solved_by"))
        contact.assigned_to = ", ".join(request.POST.getlist("assigned_to"))
        contact.remarks = request.POST.get("remarks", "")
        contact.link = request.POST.get("link") or None

        # ============================================================
        # ✅ HANDLE FILE OPERATIONS
        # ============================================================

        # Check if user wants to remove all files
        if request.POST.get("remove_all_files") == "on":
            # Delete all StoredFile records
            StoredFile.objects.filter(contact=contact).delete()
            # Delete legacy media_file
            if contact.media_file:
                contact.media_file.delete(save=False)
                contact.media_file = None

            # ✅ NEW: delete all Telegram files
            for _sk, _info in contact.get_telegram_map().items():
                if _info and _info.get('message_id'):
                    delete_telegram_message(_info.get('message_id'))
            contact.telegram_files = ''

            contact.is_multiple = False
            contact.file_count = 0

        # Check if new files were uploaded
        elif request.FILES.getlist("edit_multiple_files"):
            multiple_files = request.FILES.getlist("edit_multiple_files")

            # Validate file sizes (20 MB limit)
            MAX_SIZE = 20 * 1024 * 1024
            for file in multiple_files:
                if file.size > MAX_SIZE:
                    messages.error(request, f"File '{file.name}' exceeds 1 GB limit.")
                    return render(
                        request,
                        "core/issue_edit.html",
                        {
                            "contact": contact,
                            "stored_files": stored_files,
                            "total_files": total_files,
                        },
                    )

            # ✅ If there's a legacy media_file, migrate it to StoredFile first
            with transaction.atomic():
                if contact.media_file:
                    # Check if legacy file already exists in StoredFile
                    existing = StoredFile.objects.filter(
                        contact=contact,
                        file_name=contact.media_file.name.split("/")[-1],
                    )
                    if not existing:
                        try:
                            legacy_size = contact.media_file.size
                        except (FileNotFoundError, OSError, ValueError):
                            legacy_size = 0
                        StoredFile.objects.create(
                            contact=contact,
                            file=contact.media_file,
                            file_name=contact.media_file.name.split("/")[-1],
                            file_size=legacy_size,
                        )
                        contact.media_file = None  
                # Don't delete media_file yet, keep for backward compatibility
                # But we'll update it later

                existing_keys = list(contact.get_telegram_map().keys())
                next_index = 1
                for file in multiple_files:
                    # ✅ Telegram-only upload (next free slot)
                    while str(next_index) in existing_keys:
                        next_index += 1
                    slot_key = str(next_index)
                    next_index += 1
                    try:
                        info = upload_to_telegram(
                            file, filename=sanitize_filename(file.name)
                        )
                        if info:
                            contact.set_telegram_file(slot_key, info)
                        else:
                            messages.warning(
                                request,
                                f"⚠️ '{file.name}' could not be uploaded to Telegram."
                            )
                    except Exception as tg_err:
                        messages.warning(
                            request,
                            f"⚠️ '{file.name}' Telegram upload failed: {tg_err}"
                        )

            # Update file count from Telegram map
            contact.file_count = len(contact.get_telegram_map())
            contact.is_multiple = contact.file_count > 1

        # ============================================================
        # ✅ HANDLE SINGLE FILE UPLOAD (Backward compatibility)
        elif request.FILES.get("media_file"):
            # Delete all existing files
            StoredFile.objects.filter(contact=contact).delete()
            if contact.media_file:
                contact.media_file.delete(save=False)

            # ✅ NEW: clear Telegram map
            for _sk, _info in contact.get_telegram_map().items():
                if _info and _info.get('message_id'):
                    delete_telegram_message(_info.get('message_id'))
            contact.telegram_files = ''

            file = request.FILES.get("media_file")
            contact.is_multiple = False
            contact.file_count = 1

            # ✅ Telegram-only upload as slot "1"
            try:
                info = upload_to_telegram(
                    file, filename=sanitize_filename(file.name)
                )
                if info:
                    contact.set_telegram_file("1", info)
                else:
                    messages.warning(
                        request,
                        f"⚠️ '{file.name}' could not be uploaded to Telegram."
                    )
            except Exception as tg_err:
                messages.warning(
                    request,
                    f"⚠️ '{file.name}' Telegram upload failed: {tg_err}"
                )

        elif request.POST.get("media_clear") == "on":
            if contact.media_file:
                contact.media_file.delete(save=False)
                contact.media_file = None
            StoredFile.objects.filter(contact=contact).delete()

            # ✅ NEW: clear Telegram map
            for _sk, _info in contact.get_telegram_map().items():
                if _info and _info.get('message_id'):
                    delete_telegram_message(_info.get('message_id'))
            contact.telegram_files = ''

            contact.is_multiple = False
            contact.file_count = 0
        # ============================================================

        contact.status = request.POST.get("status")

        now = timezone.localtime(timezone.now())
        contact.updated_at = now

        if contact.status == "Closed" and not contact.is_resolved:
            contact.is_resolved = True
            contact.resolved_at = now
        elif contact.status != "Closed" and contact.is_resolved:
            contact.is_resolved = False
            contact.resolved_at = None

        contact.save()
        messages.success(request, "Issue updated successfully.")
        return redirect("core:issue_detail", pk=contact.pk)

    return render(
        request,
        "core/issue_edit.html",
        {
            "contact": contact,
            "stored_files": stored_files,  # Contains BOTH old and new files
            "total_files": total_files,
            "has_legacy_file": has_legacy_file,
            "legacy_file": legacy_file,
        },
    )


# Delete Issue - Admin Only
@login_required(login_url="/admin/login/")
@user_passes_test(is_admin)
def issue_delete(request, pk):
    contact = get_object_or_404(Contact, pk=pk, is_stored=False)
    if request.method == "POST":
        contact.delete()
        messages.success(request, "Issue deleted successfully.")
        return redirect("core:contact")
    return render(request, "core/issue_confirm_delete.html", {"contact": contact})


# Mark as Resolved - Admin Only
@login_required(login_url="/admin/login/")
@user_passes_test(is_admin)
def issue_mark_done(request, pk):
    contact = get_object_or_404(Contact, pk=pk, is_stored=False)
    now = timezone.localtime(timezone.now())
    contact.is_resolved = True
    contact.status = "Closed"
    contact.resolved_at = now
    contact.updated_at = now
    contact.save()
    messages.success(request, "Issue marked as resolved.")
    return redirect("core:issue_detail", pk=contact.pk)


# Toggle Public/Private Issue - Admin Only
@login_required(login_url="/admin/login/")
@user_passes_test(is_admin)
def toggle_public_issue(request, pk):
    contact = get_object_or_404(Contact, pk=pk, is_stored=False)
    contact.is_public = not contact.is_public
    contact.save()

    if contact.is_public:
        messages.success(request, f"✅ Issue #{pk} is now PUBLIC - visible to everyone!")
    else:
        messages.warning(request, f"🔒 Issue #{pk} is now PRIVATE - only visible to the original IP")

    # ✅ Preserve page + date after toggle
    page = request.POST.get("page", 1)
    date = request.POST.get("date", "").strip()
    url = f"{reverse('core:contact')}?page={page}"
    if date:
        url += f"&date={date}"
    return redirect(url)

# Store Issue - Open Store Form (Anyone can access)
@login_required(login_url="/accounts/login/")
def store_issue(request):
    """Open the store form page - Anyone can access"""
    return render(request, "core/store_form.html")


# Submit Store Issue (Anyone can submit)
@login_required(login_url="/accounts/login/")
def store_submit(request):
    """Submit an issue to storage - Anyone can submit"""
    if request.method == "POST":
        name = request.POST.get("name")
        department = request.POST.get("department")
        phone = request.POST.get("phone")
        priority = request.POST.get("priority")
        remarks = request.POST.get("remarks", "")
        description = request.POST.get("description")
        link = request.POST.get("link") or None
        now = timezone.localtime(timezone.now())

        # Get file
        multiple_files = request.FILES.getlist("media_file")
        media_file = None
        is_multiple = False
        file_count = 0

        if multiple_files and len(multiple_files) > 0:
            file_count = len(multiple_files)
            if file_count == 1:
                media_file = multiple_files[0]
                is_multiple = False
            else:
                media_file = multiple_files[0]  # First file as cover
                is_multiple = True
                
        MAX_FILE_SIZE = 20 * 1024 * 1024
        for f in multiple_files:
            if f.size > MAX_FILE_SIZE:
                messages.error(
                    request,
                    f"❌ '{f.name}' is {f.size / 1024 / 1024:.1f} MB. Max allowed: 20 MB."
                )
                return redirect("core:contact")
        
        try:
            with transaction.atomic():
                contact = Contact.objects.create(
                    name=name,
                    department=department,
                    phone=phone,
                    ip_address=get_client_ip(request),
                    priority=priority,
                    message=None,
                    description=description,
                    remarks=remarks,
                    link=link,   
                    media_file=None,
                    is_multiple=is_multiple,
                    file_count=file_count,
                    status="Stored",
                    is_stored=True,
                    created_by=request.user, 
                    stored_at=now,
                    created_at=now,
                    updated_at=now,
                )

                # ✅ Telegram-only upload (no local disk save)
                for idx, file in enumerate(multiple_files):
                    slot_key = str(idx + 1)
                    try:
                        info = upload_to_telegram(
                            file, filename=sanitize_filename(file.name)
                        )
                        if info:
                            contact.set_telegram_file(slot_key, info)
                        else:
                            messages.warning(
                                request,
                                f"⚠️ '{file.name}' could not be uploaded to Telegram."
                            )
                    except Exception as tg_err:
                        messages.warning(
                            request,
                            f"⚠️ '{file.name}' Telegram upload failed: {tg_err}"
                        )
                contact.save(update_fields=["telegram_files"])

            if file_count == 0:
                messages.success(request, f"✅ Issue '{name}' stored successfully!")
            elif file_count == 1:
                messages.success(request, f"✅ Issue '{name}' stored with 1 file!")
            else:
                messages.success(
                    request, f"✅ Issue '{name}' stored with {file_count} files!"
                )
        except Exception as e:
            messages.error(request, f"Error storing issue: {str(e)}")

        return redirect("core:contact")

    return redirect("core:contact")


# Storage View - Show all stored items (ADMIN ONLY)
@login_required(login_url="/accounts/login/")
def storage_view(request):
    is_admin_user = request.user.is_authenticated and (
        request.user.is_staff or request.user.is_superuser
    )
    stored_items = Contact.objects.filter(is_stored=True).order_by("-stored_at")
    if not is_admin_user:
        stored_items = stored_items.filter(
            models.Q(created_by=request.user) | 
            models.Q(is_public=True)
        )
    search_query = request.GET.get("search")
    if search_query:
        stored_items = stored_items.filter(
            # 1. Name
            models.Q(name__icontains=search_query)
            # 2. Department
            | models.Q(department__icontains=search_query)
            # 3. Description
            | models.Q(description__icontains=search_query)
            # 4. Remarks
            | models.Q(remarks__icontains=search_query)
            # 5. Extension / Phone
            | models.Q(phone__icontains=search_query)
            # 6. Link (URL)
            | models.Q(link__icontains=search_query)
            # 7. Priority
            | models.Q(priority__icontains=search_query)
            # 8. Status
            | models.Q(status__icontains=search_query)
            # 9. IP Address
            | models.Q(ip_address__icontains=search_query)
            # 10. Hostname
            | models.Q(hostname__icontains=search_query)
            # 11. Username
            | models.Q(username__icontains=search_query)
            # 12. OS Info
            | models.Q(os_info__icontains=search_query)
            # 13. Call Attended By
            | models.Q(call_attended_by__icontains=search_query)
            # 14. Handover To
            | models.Q(handover_to__icontains=search_query)
            # 15. Solved By
            | models.Q(solved_by__icontains=search_query)
            # 16. Assigned To
            | models.Q(assigned_to__icontains=search_query)
        )
    paginator = Paginator(stored_items, 20)  # 20 items per page
    page_number = request.GET.get("page", 1)  # Get page from URL (?page=2)
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        "core/storage_view.html",
        {
            "page_obj": page_obj,
            "is_admin_user": is_admin_user, 
        },
    )


# Delete stored item (ADMIN ONLY)
@login_required(login_url="/admin/login/")
@user_passes_test(is_admin)
def storage_delete(request, pk):
    """Delete a stored item - ADMIN ONLY"""
    item = get_object_or_404(Contact, pk=pk, is_stored=True)
    
    if not is_admin(request.user) and item.created_by != request.user:
        messages.error(request, "🔒 You do not have permission to delete this item.")
        return redirect("core:storage_view")
    
    if request.method == "POST":
        current_page = int(request.POST.get("page", 1) or 1)
        current_search = request.POST.get("search", "").strip()

        item.delete()
        messages.success(request, "✅ Item removed from storage")

            
        stored_items = Contact.objects.filter(is_stored=True).order_by("-stored_at")
        if current_search:
            stored_items = stored_items.filter(
                models.Q(name__icontains=current_search)
                | models.Q(department__icontains=current_search)
                | models.Q(description__icontains=current_search)
                | models.Q(remarks__icontains=current_search)
                | models.Q(phone__icontains=current_search)
                | models.Q(link__icontains=current_search)
                | models.Q(priority__icontains=current_search)
                | models.Q(status__icontains=current_search)
                | models.Q(ip_address__icontains=current_search)
                | models.Q(hostname__icontains=current_search)
                | models.Q(username__icontains=current_search)
                | models.Q(os_info__icontains=current_search)
                | models.Q(call_attended_by__icontains=current_search)
                | models.Q(handover_to__icontains=current_search)
                | models.Q(solved_by__icontains=current_search)
                | models.Q(assigned_to__icontains=current_search)
            )
        # ✅ Check if the current page is now empty
        paginator = Paginator(stored_items, 20)
        total_pages = paginator.num_pages or 1

        # If current page exceeds total pages, step back
        if current_page > total_pages:
            current_page = total_pages

        # ✅ Build redirect URL
        url = f"{reverse('core:storage_view')}?page={current_page}"
        if current_search:
            url += f"&search={current_search}"

        return redirect(url)

    return redirect("core:storage_view")

# Restore stored item (ADMIN ONLY)
@login_required(login_url="/admin/login/")
@user_passes_test(is_admin)
def storage_restore(request, pk):
    """Restore a stored item back to main issues - ADMIN ONLY"""
    item = get_object_or_404(Contact, pk=pk, is_stored=True)
    item.is_stored = False
    item.is_resolved = False
    item.status = "Pending"
    item.save()
    messages.success(request, f"✅ Item '{item.name}' restored to main issues")
    return redirect("core:storage_view")


# Resolved Issues Excel Export (Full) - Admin Only
@login_required(login_url="/admin/login/")
@user_passes_test(is_admin)
def resolved_issues_excel(request):
    selected_date = request.GET.get("date")
    resolved_contacts = Contact.objects.filter(
        is_resolved=True, is_stored=False
    ).order_by("id")

    if selected_date:
        try:
            selected_date_obj = datetime.strptime(selected_date, "%Y-%m-%d").date()
            resolved_contacts = resolved_contacts.filter(date=selected_date_obj)
        except (ValueError, TypeError):
            resolved_contacts = resolved_contacts.filter(date=selected_date)

    data = []
    for contact in resolved_contacts:
        created_at_local = (
            timezone.localtime(contact.created_at) if contact.created_at else None
        )
        updated_at_local = (
            timezone.localtime(contact.updated_at) if contact.updated_at else None
        )
        resolved_at_local = (
            timezone.localtime(contact.resolved_at) if contact.resolved_at else None
        )

        ticket_id = generate_ticket_id(contact)

        data.append(
            {
                "Date": (
                    created_at_local.strftime("%d-%b-%Y") if created_at_local else ""
                ),
                "Ticket ID": ticket_id,
                "Department": contact.department,
                "Name": contact.name,
                "Issue/Message": contact.message,
                "Priority": contact.priority,
                "Call Attended By": contact.call_attended_by or "",
                "Assigned To": contact.assigned_to or "",
                "Handover To": contact.handover_to or "",
                "Solved By": contact.solved_by or "",
                "Status": contact.status,
                "Remarks": contact.remarks or "",
                "Time": (
                    created_at_local.strftime("%H:%M:%S") if created_at_local else ""
                ),
                "Extension": contact.phone,
                "IP Address": contact.ip_address or "",
                "OS": contact.os_info or "N/A",
                "Created At": (
                    created_at_local.strftime("%Y-%m-%d %H:%M:%S")
                    if created_at_local
                    else ""
                ),
                "Updated At": (
                    updated_at_local.strftime("%Y-%m-%d %H:%M:%S")
                    if updated_at_local
                    else ""
                ),
                "Resolved At": (
                    resolved_at_local.strftime("%Y-%m-%d %H:%M:%S")
                    if resolved_at_local
                    else ""
                ),
                "Is Resolved": "Yes" if contact.is_resolved else "No",
            }
        )

    df = pd.DataFrame(data)

    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="Resolved Issues", index=False)

        worksheet = writer.sheets["Resolved Issues"]
        for column in worksheet.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 50)
            worksheet.column_dimensions[column_letter].width = adjusted_width

        from openpyxl.styles import Font, PatternFill, Alignment

        header_font = Font(bold=True, color="FFFFFF")
        header_fill = PatternFill(
            start_color="1f6f4a", end_color="1f6f4a", fill_type="solid"
        )
        header_alignment = Alignment(horizontal="center", vertical="center")

        for cell in worksheet[1]:
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = header_alignment

    output.seek(0)

    response = HttpResponse(
        output.read(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    filename = f"resolved_issues_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    response["Content-Disposition"] = f'attachment; filename="{filename}"'

    return response


# Resolved Issues Excel Export (Compact) - Admin Only
@login_required(login_url="/admin/login/")
@user_passes_test(is_admin)
def resolved_issues_excel_compact(request):
    selected_date = request.GET.get("date")
    resolved_contacts = Contact.objects.filter(
        is_resolved=True, is_stored=False
    ).order_by("id")

    if selected_date:
        try:
            selected_date_obj = datetime.strptime(selected_date, "%Y-%m-%d").date()
            resolved_contacts = resolved_contacts.filter(date=selected_date_obj)
        except (ValueError, TypeError):
            resolved_contacts = resolved_contacts.filter(date=selected_date)

    data = []
    for contact in resolved_contacts:
        created_at_local = (
            timezone.localtime(contact.created_at) if contact.created_at else None
        )

        ticket_id = generate_ticket_id(contact)

        data.append(
            {
                "Date": (
                    created_at_local.strftime("%d-%b-%Y") if created_at_local else ""
                ),
                "Ticket ID": ticket_id,
                "Department": contact.department,
                "Name": contact.name,
                "Issue/Message": contact.message,
                "Priority": contact.priority,
                "Call Attended By": contact.call_attended_by or "",
                "Assigned To": contact.assigned_to or "",
                "Handover To": contact.handover_to or "",
                "Solved By": contact.solved_by or "",
                "Status": contact.status,
                "Remarks": contact.remarks or "",
            }
        )

    df = pd.DataFrame(data)

    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="Resolved Issues (Compact)", index=False)

        worksheet = writer.sheets["Resolved Issues (Compact)"]
        for column in worksheet.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 50)
            worksheet.column_dimensions[column_letter].width = adjusted_width

        from openpyxl.styles import Font, PatternFill, Alignment

        header_font = Font(bold=True, color="FFFFFF")
        header_fill = PatternFill(
            start_color="1f6f4a", end_color="1f6f4a", fill_type="solid"
        )
        header_alignment = Alignment(horizontal="center", vertical="center")

        for cell in worksheet[1]:
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = header_alignment

    output.seek(0)

    response = HttpResponse(
        output.read(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    filename = (
        f"resolved_issues_compact_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    )
    response["Content-Disposition"] = f'attachment; filename="{filename}"'

    return response


@login_required(login_url="/accounts/login/")
def stored_item_detail(request, pk):
    """View for stored items - admins see all, normal users see only public ones"""
    is_admin_user = request.user.is_authenticated and (
        request.user.is_staff or request.user.is_superuser
    )

    item = get_object_or_404(Contact, pk=pk, is_stored=True)


    # Non-admins can only open their own items or public items
    if not is_admin_user:
        if not item.is_public and item.created_by != request.user:
            messages.error(request, "🔒 This item is private.")
            return redirect("core:storage_view")

    stored_files = StoredFile.objects.filter(contact=item)

    return render(
        request,
        "core/stored_item_detail.html",
        {
            "item": item,
            "stored_files": stored_files,
            "is_admin_user": is_admin_user,
        },
    )


@login_required(login_url="/accounts/login/")
def store_edit(request, pk):
    item = get_object_or_404(Contact, pk=pk, is_stored=True)

    # ✅ NEW: Normal users can only edit their own items. Admins can edit any.
    if not is_admin(request.user) and item.created_by != request.user:
        messages.error(request, "🔒 You do not have permission to edit this item.")
        return redirect("core:storage_view")

    # ✅ Get ALL files - BOTH old and new
    stored_files_qs = StoredFile.objects.filter(contact=item).order_by("id")
    stored_files = list(stored_files_qs)

    # Check for legacy media_file
    has_legacy_file = False
    legacy_file = None

    if item.media_file:
        file_name = item.media_file.name.split("/")[-1]
        exists_in_stored = any(sf.file_name == file_name for sf in stored_files)

        if not exists_in_stored:
            has_legacy_file = True

            try:
                safe_size = item.media_file.size
            except (FileNotFoundError, OSError, ValueError):
                safe_size = 0
            try:
                safe_url = item.media_file.url
            except (ValueError, OSError):
                safe_url = ""

            legacy_file = {
                "name": file_name,
                "size": safe_size,
                "url": safe_url,  
            }

            # Add to stored_files list
            class VirtualFile:
                pass

            virtual = VirtualFile()
            virtual.file_name = file_name
            virtual.file_size = safe_size
            virtual.file_url = safe_url
            virtual.file = item.media_file
            virtual.is_legacy = True
            stored_files.append(virtual)

    total_files = len(stored_files) + len(item.get_telegram_map())

    if request.method == "POST":
        # ============================================================
        # ✅ GET FORM DATA
        # ============================================================
        name = request.POST.get("name")
        department = request.POST.get("department")
        phone = request.POST.get("phone")
        priority = request.POST.get("priority")
        remarks = request.POST.get("remarks", "")
        description = request.POST.get("description")
        link_primary = request.POST.get("link_primary") or None
        link_secondary = request.POST.get("link_secondary") or None

        # Update the item
        item.name = name
        item.department = department
        item.phone = phone
        item.priority = priority
        item.remarks = remarks
        item.description = description
        item.link = link_primary or link_secondary

        # ============================================================
        # ✅ HANDLE FILE OPERATIONS (ADD/REPLACE/DELETE)
        # ============================================================

        # Check if user wants to remove all files
        if request.POST.get("media_clear") == "on":
            StoredFile.objects.filter(contact=item).delete()
            if item.media_file:
                item.media_file.delete(save=False)
                item.media_file = None

            # ✅ NEW: clear Telegram map
            for _sk, _info in item.get_telegram_map().items():
                if _info and _info.get('message_id'):
                    delete_telegram_message(_info.get('message_id'))
            item.telegram_files = ''

            item.is_multiple = False
            item.file_count = 0

        # REPLACE: Delete ALL existing files and upload new ones
        elif (
            request.FILES.getlist("media_file")
            and request.POST.get("replace_files") == "on"
        ):
            # Delete all existing files
            StoredFile.objects.filter(contact=item).delete()
            if item.media_file:
                item.media_file.delete(save=False)
                item.media_file = None

            multiple_files = request.FILES.getlist("media_file")
            media_file = None
            is_multiple = False
            file_count = 0

            # Validate file sizes
            MAX_SIZE = 20 * 1024 * 1024
            for file in multiple_files:
                if file.size > MAX_SIZE:
                    messages.error(request, f"File '{file.name}' exceeds 1 GB limit.")
                    return render(
                        request,
                        "core/store_edit.html",
                        {
                            "item": item,
                            "stored_files": stored_files,
                            "total_files": total_files,
                            "has_legacy_file": has_legacy_file,
                            "legacy_file": legacy_file,
                        },
                    )

            if multiple_files and len(multiple_files) > 0:
                file_count = len(multiple_files)
                is_multiple = file_count > 1

                item.is_multiple = is_multiple
                item.file_count = file_count

                # ✅ NEW: clear old Telegram map (replace semantics)
                for _sk, _info in item.get_telegram_map().items():
                    if _info and _info.get('message_id'):
                        delete_telegram_message(_info.get('message_id'))
                item.telegram_files = ''

                # ✅ Telegram-only upload (replace mode)
                for idx, file in enumerate(multiple_files):
                    slot_key = str(idx + 1)
                    try:
                        info = upload_to_telegram(
                            file, filename=sanitize_filename(file.name)
                        )
                        if info:
                            item.set_telegram_file(slot_key, info)
                        else:
                            messages.warning(
                                request,
                                f"⚠️ '{file.name}' could not be uploaded to Telegram."
                            )
                    except Exception as tg_err:
                        messages.warning(
                            request,
                            f"⚠️ '{file.name}' Telegram upload failed: {tg_err}"
                        )

        # ADD: Keep existing files and upload new ones
        elif (
            request.FILES.getlist("media_file")
            and request.POST.get("add_files") == "on"
        ):
            multiple_files = request.FILES.getlist("media_file")

            # Validate file sizes
            MAX_SIZE = 20 * 1024 * 1024
            for file in multiple_files:
                if file.size > MAX_SIZE:
                    messages.error(request, f"File '{file.name}' exceeds 1 GB limit.")
                    return render(
                        request,
                        "core/store_edit.html",
                        {
                            "item": item,
                            "stored_files": stored_files,
                            "total_files": total_files,
                            "has_legacy_file": has_legacy_file,
                            "legacy_file": legacy_file,
                        },
                    )

            # Migrate legacy media_file to StoredFile if exists
            if item.media_file:
                file_name = item.media_file.name.split("/")[-1]
                existing = StoredFile.objects.filter(contact=item, file_name=file_name)
                if not existing.exists():
                    try:
                        legacy_size = item.media_file.size
                    except (FileNotFoundError, OSError, ValueError):
                        legacy_size = 0
                    StoredFile.objects.create(
                        contact=item,
                        file=item.media_file,
                        file_name=file_name,
                        file_size=legacy_size,
                    )
                    item.media_file = None   

            # Create StoredFile records for each new file
            existing_keys = list(item.get_telegram_map().keys())
            next_index = 1
            with transaction.atomic():
                for file in multiple_files:
                    # ✅ Telegram-only upload (next free slot)
                    while str(next_index) in existing_keys:
                        next_index += 1
                    slot_key = str(next_index)
                    next_index += 1
                    try:
                        info = upload_to_telegram(
                            file, filename=sanitize_filename(file.name)
                        )
                        if info:
                            item.set_telegram_file(slot_key, info)
                        else:
                            messages.warning(
                                request,
                                f"⚠️ '{file.name}' could not be uploaded to Telegram."
                            )
                    except Exception as tg_err:
                        messages.warning(
                            request,
                            f"⚠️ '{file.name}' Telegram upload failed: {tg_err}"
                        )

            # Update file count from Telegram map
            item.file_count = len(item.get_telegram_map())
            item.is_multiple = item.file_count > 1

        elif request.FILES.get("media_file"):
            # Delete all existing files
            StoredFile.objects.filter(contact=item).delete()
            if item.media_file:
                item.media_file.delete(save=False)
                item.media_file = None

            # ✅ NEW: clear Telegram map
            for _sk, _info in item.get_telegram_map().items():
                if _info and _info.get('message_id'):
                    delete_telegram_message(_info.get('message_id'))
            item.telegram_files = ''

            file = request.FILES.get("media_file")
            item.is_multiple = False
            item.file_count = 1

            # ✅ Telegram-only upload as slot "1"
            try:
                info = upload_to_telegram(
                    file, filename=sanitize_filename(file.name)
                )
                if info:
                    item.set_telegram_file("1", info)
                else:
                    messages.warning(
                        request,
                        f"⚠️ '{file.name}' could not be uploaded to Telegram."
                    )
            except Exception as tg_err:
                messages.warning(
                    request,
                    f"⚠️ '{file.name}' Telegram upload failed: {tg_err}"
                )

        # ============================================================
        # ✅ SAVE AND REDIRECT
        # ============================================================
        item.updated_at = timezone.localtime(timezone.now())
        item.save()

        # Get final file count for success message
        final_count = StoredFile.objects.filter(contact=item).count()
        if final_count > 0:
            messages.success(
                request,
                f"✅ Stored item '{name}' updated successfully! ({final_count} file(s))",
            )
        else:
            messages.success(request, f"✅ Stored item '{name}' updated successfully!")

        return redirect("core:storage_view")

    return render(
        request,
        "core/store_edit.html",
        {
            "item": item,
            "stored_files": stored_files,
            "total_files": total_files,
            "has_legacy_file": has_legacy_file,
            "legacy_file": legacy_file,
        },
    )


@login_required(login_url="/accounts/login/")
def get_zip_contents(request, pk):
    is_admin_user = request.user.is_authenticated and (
        request.user.is_staff or request.user.is_superuser
    )
    item = get_object_or_404(Contact, pk=pk, is_stored=True)
    if not is_admin_user and not item.is_public:
        return JsonResponse({"files": [], "error": "private"})

    files = []

    # ✅ Legacy local files (for old cards)
    for sf in StoredFile.objects.filter(contact=item):
        files.append({
            "name": sf.file_name,
            "size": sf.file_size,
            "url": sf.file.url,
        })

    # ✅ Telegram files (for new cards)
    for slot_key, info in item.get_telegram_map().items():
        files.append({
            "name": info.get("file_name", "file"),
            "size": info.get("file_size", 0),
            "url": reverse("core:serve_stored_telegram_file", args=[item.pk, slot_key]),
        })

    return JsonResponse({"files": files})

# core/views.py - Add these functions


@login_required(login_url="/admin/login/")
@user_passes_test(is_admin)
def delete_stored_file(request, pk, file_index):
    """
    Delete a specific file from a stored item
    - Deletes from database (StoredFile)
    - Deletes physical file from storage
    """
    item = get_object_or_404(Contact, pk=pk, is_stored=True)
    stored_files = StoredFile.objects.filter(contact=item).order_by("id")

    if file_index < len(stored_files):
        file_to_delete = stored_files[file_index]
        file_name = file_to_delete.file_name

        # Delete from database (this also removes the physical file)
        file_to_delete.delete()

        # Re-sync media_file and update file count
        remaining = StoredFile.objects.filter(contact=item).order_by("id")
        item.media_file = remaining.first().file if remaining.exists() else None
        item.file_count = remaining.count()
        item.is_multiple = item.file_count > 1
        item.save()

        return JsonResponse(
            {
                "status": "success",
                "message": f"Deleted: {file_name}",
                "file_count": item.file_count,
            }
        )

    return JsonResponse({"status": "error", "message": "File not found"}, status=404)


@login_required(login_url="/admin/login/")
@user_passes_test(is_admin)
def delete_stored_all_files(request, pk):
    """
    Delete ALL files from a stored item
    - Deletes all StoredFile records from database (signal cleans disk files)
    - Deletes legacy media_file
    - Deletes all Telegram files
    """
    item = get_object_or_404(Contact, pk=pk, is_stored=True)

    # Delete all local StoredFile rows (signal cleans disk files)
    StoredFile.objects.filter(contact=item).order_by("id").delete()

    # Delete legacy media_file
    if item.media_file:
        item.media_file.delete(save=False)
        item.media_file = None

    # ✅ NEW: delete all Telegram files
    for _sk, _info in item.get_telegram_map().items():
        if _info and _info.get('message_id'):
            delete_telegram_message(_info.get('message_id'))
    item.telegram_files = ''

    # Update flags
    item.is_multiple = False
    item.file_count = 0
    item.save()

    return JsonResponse(
        {"status": "success", "message": "All files deleted successfully!"}
    )


@login_required(login_url="/admin/login/")
@user_passes_test(is_admin)
def delete_issue_file(request, pk, file_index):
    """
    Delete a specific file from a regular issue
    - Deletes from database (StoredFile)
    - Deletes physical file from storage
    """
    contact = get_object_or_404(Contact, pk=pk, is_stored=False)
    stored_files = StoredFile.objects.filter(contact=contact).order_by("id")

    if file_index < len(stored_files):
        file_to_delete = stored_files[file_index]
        file_name = file_to_delete.file_name

        # Delete from database (this also removes the physical file)
        file_to_delete.delete()

        # Re-sync media_file and update file count
        remaining = StoredFile.objects.filter(contact=contact).order_by("id")
        contact.media_file = remaining.first().file if remaining.exists() else None
        contact.file_count = remaining.count()
        contact.is_multiple = contact.file_count > 1
        contact.save()

        return JsonResponse(
            {
                "status": "success",
                "message": f"Deleted: {file_name}",
                "file_count": contact.file_count,
            }
        )

    return JsonResponse({"status": "error", "message": "File not found"}, status=404)


@login_required(login_url="/admin/login/")
@user_passes_test(is_admin)
def delete_issue_all_files(request, pk):
    """
    Delete ALL files from a regular issue
    - Deletes all StoredFile records from database (signal cleans disk files)
    - Deletes legacy media_file
    - Deletes all Telegram files
    """
    contact = get_object_or_404(Contact, pk=pk, is_stored=False)

    # Delete all local StoredFile rows (signal cleans disk files)
    StoredFile.objects.filter(contact=contact).order_by("id").delete()

    # Delete legacy media_file
    if contact.media_file:
        contact.media_file.delete(save=False)
        contact.media_file = None

    # ✅ NEW: delete all Telegram files
    for _sk, _info in contact.get_telegram_map().items():
        if _info and _info.get('message_id'):
            delete_telegram_message(_info.get('message_id'))
    contact.telegram_files = ''

    # Update flags
    contact.is_multiple = False
    contact.file_count = 0
    contact.save()

    return JsonResponse(
        {"status": "success", "message": "All files deleted successfully!"}
    )

    # AUTOCOMPLETE SUGGESTION YOU CAN DELETE LATER


def autocomplete_suggestions(request):
    """
    Return autocomplete suggestions for text fields - only 3 suggestions
    Used for Message and Remarks fields
    """
    field = request.GET.get("field", "")
    query = request.GET.get("q", "").strip()

    if not query or not field:
        return JsonResponse({"success": False, "suggestions": []})

    # Map field names to model fields
    field_map = {
        "message": "message",
        "remarks": "remarks",
        "name": "name",
        "department": "department",
        "phone": "phone",
    }

    model_field = field_map.get(field)
    if not model_field:
        return JsonResponse({"success": False, "suggestions": []})

    # Get distinct values from database - limit to 3
    suggestions = (
        Contact.objects.filter(**{f"{model_field}__icontains": query})
        .exclude(**{f"{model_field}__isnull": True})
        .exclude(**{f"{model_field}__exact": ""})
        .values_list(model_field, flat=True)
        .distinct()[:3]
    )

    return JsonResponse({"success": True, "suggestions": list(suggestions)})


@login_required(login_url="/admin/login/")
@user_passes_test(is_admin)
def toggle_public_storage(request, pk):
    """Toggle the public visibility of a stored item - ADMIN ONLY"""
    item = get_object_or_404(Contact, pk=pk, is_stored=True)
    item.is_public = not item.is_public
    item.save(update_fields=["is_public"])

    if item.is_public:
        messages.success(request, f"✅ Stored item #{pk} is now PUBLIC - visible to everyone!")
    else:
        messages.warning(request, f"🔒 Stored item #{pk} is now PRIVATE - only visible to admins")

    # ✅ Preserve page + search after toggle
    page = request.POST.get("page", 1)
    search = request.POST.get("search", "").strip()
    url = f"{reverse('core:storage_view')}?page={page}"
    if search:
        url += f"&search={search}"
    return redirect(url)


# ============================================================
# ✅ NEW: Telegram file serving + deletion for core
# ============================================================

def _serve_telegram_file(contact, slot_key):
    """Shared helper: fetch Telegram file and return HttpResponse."""
    tg_map = contact.get_telegram_map()
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
    except Http404:
        raise
    except Exception:
        raise Http404("Could not fetch file from Telegram")

    content_type = r.headers.get('Content-Type', 'application/octet-stream')
    filename = tg_map[slot_key].get('file_name', 'file')
    ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
    type_map = {
        'pdf': 'application/pdf', 'jpg': 'image/jpeg', 'jpeg': 'image/jpeg',
        'png': 'image/png', 'gif': 'image/gif', 'webp': 'image/webp',
        'svg': 'image/svg+xml', 'mp4': 'video/mp4', 'webm': 'video/webm',
        'mp3': 'audio/mpeg', 'wav': 'audio/wav',
        'txt': 'text/plain; charset=utf-8',
        'html': 'text/html; charset=utf-8', 'json': 'application/json',
    }
    if ext in type_map:
        content_type = type_map[ext]
    response = HttpResponse(r.content, content_type=content_type)
    response['Content-Disposition'] = f'inline; filename="{filename}"'
    return response


@login_required(login_url="/accounts/login/")
def serve_stored_telegram_file(request, pk, slot_key):
    item = get_object_or_404(Contact, pk=pk, is_stored=True)
    
    # ✅ NEW: Normal users can only serve their own or public files
    if not is_admin(request.user) and not item.is_public and item.created_by != request.user:
        raise Http404("You do not have permission to view this file.")
        
    return _serve_telegram_file(item, slot_key)

@login_required(login_url="/accounts/login/")
def serve_issue_telegram_file(request, pk, slot_key):
    contact = get_object_or_404(Contact, pk=pk, is_stored=False)
    
    # ✅ NEW: Normal users can only serve their own or public files
    # (Assuming issues have the same logic)
    if not is_admin(request.user) and not contact.is_public and contact.created_by != request.user:
        raise Http404("You do not have permission to view this file.")
        
    return _serve_telegram_file(contact, slot_key)

@login_required(login_url="/admin/login/")
@user_passes_test(is_admin)
def delete_stored_telegram_file(request, pk, slot_key):
    item = get_object_or_404(Contact, pk=pk, is_stored=True)
    tg_map = item.get_telegram_map()
    info = tg_map.get(slot_key)
    if not info:
        return JsonResponse({"status": "error", "message": "File not found"}, status=404)
    file_name = info.get('file_name', 'file')
    if info.get('message_id'):
        delete_telegram_message(info['message_id'])
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
def delete_issue_telegram_file(request, pk, slot_key):
    contact = get_object_or_404(Contact, pk=pk, is_stored=False)
    tg_map = contact.get_telegram_map()
    info = tg_map.get(slot_key)
    if not info:
        return JsonResponse({"status": "error", "message": "File not found"}, status=404)
    file_name = info.get('file_name', 'file')
    if info.get('message_id'):
        delete_telegram_message(info['message_id'])
    contact.remove_telegram_file(slot_key)
    contact.file_count = len(contact.get_telegram_map())
    contact.is_multiple = contact.file_count > 1
    contact.save()
    return JsonResponse({
        "status": "success",
        "message": f"Deleted: {file_name}",
        "file_count": contact.file_count,
    })