from django.shortcuts import get_object_or_404, render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import user_passes_test
from django.http import HttpResponse
from django.utils import timezone
from .models import Contact
from django.db import models  # ADD THIS IMPORT
import pandas as pd
from io import BytesIO
from datetime import datetime
import socket
import os
import getpass
import zipfile
from django.core.files.base import ContentFile
from django.core.paginator import Paginator
from .models import StoredFile
from django.http import JsonResponse


# Helper function to check if user is admin
def is_admin(user):
    return user.is_staff or user.is_superuser

def get_client_ip(request):
    """Get the real client IP address even behind proxies"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    
    if ip in ('127.0.0.1', '::1', 'localhost'):
        try:
            hostname = socket.gethostname()
            ip = socket.gethostbyname(hostname)
        except:
            ip = '127.0.0.1'
    
    if ip == '::1':
        ip = '127.0.0.1'
    
    return ip

def get_client_hostname(request):
    """Get the client hostname"""
    try:
        # First try to get from request
        hostname = request.META.get('HTTP_HOST', '').split(':')[0]
        if hostname:
            return hostname
    except:
        pass
    
    try:
        # Fallback to socket.gethostname()
        return socket.gethostname()
    except:
        return 'Unknown'

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
        return 'Unknown'

def get_client_os(request):
    """Detect client operating system from user agent"""
    user_agent = request.META.get('HTTP_USER_AGENT', '').lower()
    
    if 'windows' in user_agent:
        if 'windows nt 10.0' in user_agent:
            return 'Windows 10/11'
        elif 'windows nt 6.3' in user_agent:
            return 'Windows 8.1'
        elif 'windows nt 6.2' in user_agent:
            return 'Windows 8'
        elif 'windows nt 6.1' in user_agent:
            return 'Windows 7'
        else:
            return 'Windows'
    elif 'mac' in user_agent or 'darwin' in user_agent:
        return 'macOS'
    elif 'linux' in user_agent:
        if 'android' in user_agent:
            return 'Android'
        else:
            return 'Linux'
    elif 'iphone' in user_agent or 'ipad' in user_agent:
        return 'iOS'
    else:
        return 'Unknown OS'

# About Page (Public)
def about(request):
    return render(request, 'core/about.html')

# Blog Page (Public)
def blog(request):
    return render(request, 'core/blog.html')

# Function to generate Ticket ID - OPTIMIZED VERSION
def generate_ticket_id(contact):
    """Generate Ticket ID in format IT-001, IT-002, etc. (only for resolved issues)"""
    if not contact.is_resolved:
        return f"IT-{str(contact.id).zfill(3)}"
    
    # Count resolved contacts with ID less than or equal to current
    count = Contact.objects.filter(
        is_resolved=True,
        is_stored=False,
        id__lte=contact.id
    ).count()
    
    return f"IT-{str(count).zfill(3)}"

# Contact Page - Main Form (Landing Page - Public)
def contact(request):
    ip_address = get_client_ip(request)
    
    # Try to get hostname from POST (client-side JavaScript via hidden input)
    # Fallback to server-side method
    if request.method == 'POST':
        hostname_from_hidden = request.POST.get('hostname_hidden', '')
        if hostname_from_hidden and hostname_from_hidden not in ['Unknown', 'localhost', '127.0.0.1', '']:
            hostname = hostname_from_hidden
        else:
            hostname = get_client_hostname(request)
    else:
        hostname = get_client_hostname(request)
    
    username = get_client_username(request)
    os_info = get_client_os(request)
    is_admin_user = request.user.is_authenticated and request.user.is_staff

    if request.method == 'POST':
        # Check which button was clicked
        if 'resolve' in request.POST:
            action = 'resolve'
        else:
            action = 'send'
        
        name = request.POST.get('name')
        phone = request.POST.get('phone')
        priority = request.POST.get('priority')
        message = request.POST.get('message')
        department = request.POST.get('department', 'General')
        
        # Get multiple selections and join them with comma
        call_attended_by = ', '.join(request.POST.getlist('call_attended_by'))
        handover_to = ', '.join(request.POST.getlist('handover_to'))
        solved_by = ', '.join(request.POST.getlist('solved_by'))
        
        # NEW: Get assigned_to and remarks
        assigned_to = ', '.join(request.POST.getlist('assigned_to'))
        remarks = request.POST.get('remarks', '')
        
        status = request.POST.get('status', 'Pending')
        
        now = timezone.localtime(timezone.now())
        
        is_resolved = False
        if action == 'resolve':
            is_resolved = True
            status = 'Closed'
        
        # ============================================================
        # HANDLE FILES - Single vs Multiple
        # ============================================================
        
        
        multiple_files = request.FILES.getlist('multiple_files')
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
        
        try:
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
                call_attended_by=call_attended_by,
                handover_to=handover_to,
                solved_by=solved_by,
                assigned_to=assigned_to,
                remarks=remarks,
                media_file=media_file,
                is_multiple=is_multiple,
                file_count=file_count,
                status=status,
                is_resolved=is_resolved,
                date=now.date(),
                time=now.time(),
                created_at=now,
                resolved_at=now if is_resolved else None,
                updated_at=now
            )
            for file in multiple_files:
                StoredFile.objects.create(
                    contact=contact,
                    file=file,
                    file_name=file.name,
                    file_size=file.size
                )

            if action == 'resolve':
                messages.success(request, f"Hi {name}, your issue has been created and marked as Resolved! - {file_count} file(s)")
            else:
                messages.success(request, f"Hi {name}, your message has been submitted successfully! - {file_count} file(s)")
        except Exception as e:
            messages.error(request, f"Error submitting issue: {str(e)}")
        
        return redirect('core:contact')
    
    # Get all unresolved issues
    contacts = Contact.objects.filter(is_resolved=False,is_stored=False).order_by('-id')
    
    # IP FILTERING: If not admin, only show issues with matching IP OR public issues
    if not is_admin_user:
        contacts = contacts.filter(
            models.Q(ip_address=ip_address) | models.Q(is_public=True)
        )
    
    resolved_contacts = Contact.objects.filter(is_resolved=True,is_stored=False).order_by('-id')
    
    # IP FILTERING: If not admin, only show resolved issues with matching IP OR public issues
    if not is_admin_user:
        resolved_contacts = resolved_contacts.filter(
            models.Q(ip_address=ip_address) | models.Q(is_public=True)
        )
    
    # Get pending and in-progress issues for the modal
    pending_contacts = Contact.objects.filter(
        is_resolved=False,is_stored=False,
        status__in=['Pending', 'In Progress']
    ).order_by('-created_at')
    
    # IP FILTERING: If not admin, only show pending issues with matching IP OR public issues
    if not is_admin_user:
        pending_contacts = pending_contacts.filter(
            models.Q(ip_address=ip_address) | models.Q(is_public=True)
        )

    # Date filter for Issue Slider (uses 'date' parameter)
    slider_date = request.GET.get('date')
    if slider_date:
        try:
            # Try to parse as date if it's a string
            slider_date_obj = datetime.strptime(slider_date, '%Y-%m-%d').date()
            contacts = contacts.filter(date=slider_date_obj)
            pending_contacts = pending_contacts.filter(date=slider_date_obj)
        except (ValueError, TypeError):
            # If it's already a date object or can't parse, try direct filter
            contacts = contacts.filter(date=slider_date)
            pending_contacts = pending_contacts.filter(date=slider_date)

    # Date filter for Resolved Modal (uses 'resolved_date' parameter)
    resolved_date = request.GET.get('resolved_date')
    if resolved_date:
        try:
            resolved_date_obj = datetime.strptime(resolved_date, '%Y-%m-%d').date()
            resolved_contacts = resolved_contacts.filter(date=resolved_date_obj)
        except (ValueError, TypeError):
            resolved_contacts = resolved_contacts.filter(date=resolved_date)

    resolved_paginator = Paginator(resolved_contacts, 15)
    resolved_page = request.GET.get('resolved_page', 1)
    resolved_page_obj = resolved_paginator.get_page(resolved_page) 

    slider_paginator = Paginator(contacts, 20)  # 20 issues per page
    slider_page = request.GET.get('page', 1)    # Get page from URL (?page=2)
    slider_page_obj = slider_paginator.get_page(slider_page)   

    pending_paginator = Paginator(pending_contacts, 10)  # 10 per page for modal
    pending_page = request.GET.get('pending_page', 1)    # Get page from URL (?pending_page=2)
    pending_page_obj = pending_paginator.get_page(pending_page)

    return render(request, 'core/contact.html', {
        'slider_page_obj': slider_page_obj,
        'resolved_page_obj': resolved_page_obj,
        'pending_page_obj': pending_page_obj,
        'is_admin_user': is_admin_user,
        'user_ip': ip_address,
        'user_hostname': hostname,
        'user_username': username,
    })

# Issue Detail - Anyone can view
def issue_detail(request, pk):
    """View issue details with all files"""
    contact = get_object_or_404(Contact, pk=pk, is_stored=False)
    
    # Get files for this issue (if any)
    stored_files = StoredFile.objects.filter(contact=contact)
    
    return render(request, 'core/issue_detail.html', {
        'contact': contact,
        'stored_files': stored_files,
    })
## Edit Issue - Admin Only
@login_required(login_url='/admin/login/')
@user_passes_test(is_admin)
def issue_edit(request, pk):
    contact = get_object_or_404(Contact, pk=pk, is_stored=False)
    
    # ============================================================
    # ✅ GET ALL FILES - BOTH OLD AND NEW
    # ============================================================
    
    # Get new files from StoredFile model
    stored_files_qs = StoredFile.objects.filter(contact=contact)
    stored_files = list(stored_files_qs)
    
    # Check for old legacy file in media_file
    has_legacy_file = False
    legacy_file = None
    
    if contact.media_file:
        # Check if this file is already in stored_files (by checking if any stored_file has same file name)
        # If not, it's a legacy file
        file_name = contact.media_file.name.split('/')[-1]
        exists_in_stored = any(sf.file_name == file_name for sf in stored_files)
        
        if not exists_in_stored:
            has_legacy_file = True
            legacy_file = {
                'name': file_name,
                'size': contact.media_file.size,
                'url': contact.media_file.url,
            }
            # Also add to stored_files list so it appears in the list
            # Create a virtual object with the same attributes
            class VirtualFile:
                pass
            virtual = VirtualFile()
            virtual.file_name = file_name
            virtual.file_size = contact.media_file.size
            virtual.file_url = contact.media_file.url
            virtual.file = contact.media_file
            virtual.is_legacy = True
            stored_files.append(virtual)
    
    # Total file count
    total_files = len(stored_files)
    
    # ============================================================
    
    if request.method == 'POST':   
        contact.name = request.POST.get('name')
        contact.department = request.POST.get('department')
        contact.phone = request.POST.get('phone')
        contact.ip_address = request.POST.get('ip_address')
        contact.hostname = request.POST.get('hostname')
        contact.username = request.POST.get('username')
        contact.priority = request.POST.get('priority')
        contact.message = request.POST.get('message')
        
        contact.call_attended_by = ', '.join(request.POST.getlist('call_attended_by'))
        contact.handover_to = ', '.join(request.POST.getlist('handover_to'))
        contact.solved_by = ', '.join(request.POST.getlist('solved_by'))
        contact.assigned_to = ', '.join(request.POST.getlist('assigned_to'))
        contact.remarks = request.POST.get('remarks', '')
        
        # ============================================================
        # ✅ HANDLE FILE OPERATIONS
        # ============================================================
        
        # Check if user wants to remove all files
        if request.POST.get('remove_all_files') == 'on':
            # Delete all StoredFile records
            StoredFile.objects.filter(contact=contact).delete()
            # Delete legacy media_file
            if contact.media_file:
                contact.media_file.delete(save=False)
                contact.media_file = None
            contact.is_multiple = False
            contact.file_count = 0
        
        # Check if new files were uploaded
        elif request.FILES.getlist('edit_multiple_files'):
            multiple_files = request.FILES.getlist('edit_multiple_files')
            
            # Validate file sizes (500 MB limit)
            MAX_SIZE = 1024 * 1024 * 1024
            for file in multiple_files:
                if file.size > MAX_SIZE:
                    messages.error(request, f"File '{file.name}' exceeds 1 GB limit.")
                    return render(request, 'core/issue_edit.html', {
                        'contact': contact,
                        'stored_files': stored_files,
                        'total_files': total_files,
                    })
            
            # ✅ If there's a legacy media_file, migrate it to StoredFile first
            if contact.media_file:
                # Check if legacy file already exists in StoredFile
                existing = StoredFile.objects.filter(
                    contact=contact,
                    file_name=contact.media_file.name.split('/')[-1]
                )
                if not existing:
                    StoredFile.objects.create(
                        contact=contact,
                        file=contact.media_file,
                        file_name=contact.media_file.name.split('/')[-1],
                        file_size=contact.media_file.size
                    )
                # Don't delete media_file yet, keep for backward compatibility
                # But we'll update it later
            
            # Create StoredFile records for each new file
            for file in multiple_files:
                StoredFile.objects.create(
                    contact=contact,
                    file=file,
                    file_name=file.name,
                    file_size=file.size
                )
            
            # Update contact's media_file (point to first file for backward compatibility)
            all_files = StoredFile.objects.filter(contact=contact)
            if all_files.exists():
                contact.media_file = all_files.first().file
            
            # Update file count
            contact.file_count = StoredFile.objects.filter(contact=contact).count()
            contact.is_multiple = contact.file_count > 1
        
        # ============================================================
        # ✅ HANDLE SINGLE FILE UPLOAD (Backward compatibility)
        # ============================================================
        elif request.FILES.get('media_file'):
            # Delete all existing files
            StoredFile.objects.filter(contact=contact).delete()
            if contact.media_file:
                contact.media_file.delete(save=False)
            
            file = request.FILES.get('media_file')
            contact.media_file = file
            contact.is_multiple = False
            contact.file_count = 1
            
            StoredFile.objects.create(
                contact=contact,
                file=file,
                file_name=file.name,
                file_size=file.size
            )
        
        elif request.POST.get('media_clear') == 'on':
            if contact.media_file:
                contact.media_file.delete(save=False)
                contact.media_file = None
            StoredFile.objects.filter(contact=contact).delete()
            contact.is_multiple = False
            contact.file_count = 0
        
        # ============================================================
        
        contact.status = request.POST.get('status')
        
        now = timezone.localtime(timezone.now())
        contact.updated_at = now
        
        if contact.status == 'Closed' and not contact.is_resolved:
            contact.is_resolved = True
            contact.resolved_at = now
        elif contact.status != 'Closed' and contact.is_resolved:
            contact.is_resolved = False
            contact.resolved_at = None
            
        contact.save()
        messages.success(request, "Issue updated successfully.")
        return redirect('core:issue_detail', pk=contact.pk)
    
    return render(request, 'core/issue_edit.html', {
        'contact': contact,
        'stored_files': stored_files,  # Contains BOTH old and new files
        'total_files': total_files,
        'has_legacy_file': has_legacy_file,
        'legacy_file': legacy_file,
    })


# Delete Issue - Admin Only
@login_required(login_url='/admin/login/')
@user_passes_test(is_admin)
def issue_delete(request, pk):
    contact = get_object_or_404(Contact, pk=pk, is_stored=False)
    if request.method == 'POST':
        contact.delete()
        messages.success(request, "Issue deleted successfully.")
        return redirect('core:contact')
    return render(request, 'core/issue_confirm_delete.html', {'contact': contact})

# Mark as Resolved - Admin Only
@login_required(login_url='/admin/login/')
@user_passes_test(is_admin)
def issue_mark_done(request, pk):
    contact = get_object_or_404(Contact, pk=pk, is_stored=False)
    now = timezone.localtime(timezone.now())
    contact.is_resolved = True
    contact.status = 'Closed'
    contact.resolved_at = now
    contact.updated_at = now
    contact.save()
    messages.success(request, "Issue marked as resolved.")
    return redirect('core:issue_detail', pk=contact.pk)

# Toggle Public/Private Issue - Admin Only
@login_required(login_url='/admin/login/')
@user_passes_test(is_admin)
def toggle_public_issue(request, pk):
    """Toggle the public visibility of an issue"""
    contact = get_object_or_404(Contact, pk=pk,is_stored=False)
    contact.is_public = not contact.is_public
    contact.save()
    
    if contact.is_public:
        messages.success(request, f"✅ Issue #{pk} is now PUBLIC - visible to everyone!")
    else:
        messages.warning(request, f"🔒 Issue #{pk} is now PRIVATE - only visible to the original IP")
    
    return redirect('core:contact')


# Store Issue - Open Store Form (Anyone can access)
def store_issue(request):
    """Open the store form page - Anyone can access"""
    return render(request, 'core/store_form.html')

# Submit Store Issue (Anyone can submit)
def store_submit(request):
    """Submit an issue to storage - Anyone can submit"""
    if request.method == 'POST':
        name = request.POST.get('name')
        department = request.POST.get('department')
        phone = request.POST.get('phone')
        priority = request.POST.get('priority')
        remarks = request.POST.get('remarks', '')
        description = request.POST.get('description')
        now = timezone.localtime(timezone.now())
      
        
        # Get file
        multiple_files = request.FILES.getlist('media_file')
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
        
      
        
        try:
            contact = Contact.objects.create(
                name=name,
                department=department,
                phone=phone,
                ip_address=get_client_ip(request),
                priority=priority,
                message=None,
                description=description, 
                remarks=remarks,
                media_file=media_file,
                is_multiple=is_multiple,  # ← ADD THIS
                file_count=file_count,     # ← ADD THIS
                status='Stored',
                is_stored=True,
                stored_at=now,
                created_at=now,
                updated_at=now
            )
            
            for file in multiple_files:
                StoredFile.objects.create(
                    contact=contact,
                    file=file,
                    file_name=file.name,
                    file_size=file.size
                )
            
            if file_count == 0:
                messages.success(request, f"✅ Issue '{name}' stored successfully!")
            elif file_count == 1:
                messages.success(request, f"✅ Issue '{name}' stored with 1 file!")
            else:
                messages.success(request, f"✅ Issue '{name}' stored with {file_count} files!")
        except Exception as e:
            messages.error(request, f"Error storing issue: {str(e)}")
        
        return redirect('core:contact')
    
    return redirect('core:contact')


# Storage View - Show all stored items (ADMIN ONLY)
@login_required(login_url='/admin/login/')
@user_passes_test(is_admin)
def storage_view(request):
    """View all stored issues - ADMIN ONLY"""
    stored_items = Contact.objects.filter(is_stored=True).order_by('-stored_at')
    search_query = request.GET.get('search')
    if search_query:
        stored_items = stored_items.filter(
            models.Q(name__icontains=search_query) |
            models.Q(department__icontains=search_query) |
            models.Q(description__icontains=search_query) |
            models.Q(remarks__icontains=search_query)
        )

    paginator = Paginator(stored_items, 20)  # 20 items per page
    page_number = request.GET.get('page', 1)  # Get page from URL (?page=2)
    page_obj = paginator.get_page(page_number)    

    return render(request, 'core/storage_view.html', {'page_obj': page_obj,})

# Delete stored item (ADMIN ONLY)
@login_required(login_url='/admin/login/')
@user_passes_test(is_admin)
def storage_delete(request, pk):
    """Delete a stored item - ADMIN ONLY"""
    item = get_object_or_404(Contact, pk=pk, is_stored=True)
    if request.method == 'POST':
        item.delete()
        messages.success(request, "✅ Item removed from storage")
        return redirect('core:storage_view')
    return redirect('core:storage_view')

# Restore stored item (ADMIN ONLY)
@login_required(login_url='/admin/login/')
@user_passes_test(is_admin)
def storage_restore(request, pk):
    """Restore a stored item back to main issues - ADMIN ONLY"""
    item = get_object_or_404(Contact, pk=pk, is_stored=True)
    item.is_stored = False
    item.is_resolved = False
    item.status = 'Pending'
    item.save()
    messages.success(request, f"✅ Item '{item.name}' restored to main issues")
    return redirect('core:storage_view')


# Resolved Issues Excel Export (Full) - Admin Only
@login_required(login_url='/admin/login/')
@user_passes_test(is_admin)
def resolved_issues_excel(request):
    selected_date = request.GET.get('date')
    resolved_contacts = Contact.objects.filter(is_resolved=True, is_stored=False).order_by('id')
    
    if selected_date:
        try:
            selected_date_obj = datetime.strptime(selected_date, '%Y-%m-%d').date()
            resolved_contacts = resolved_contacts.filter(date=selected_date_obj)
        except (ValueError, TypeError):
            resolved_contacts = resolved_contacts.filter(date=selected_date)

    data = []
    for contact in resolved_contacts:
        created_at_local = timezone.localtime(contact.created_at) if contact.created_at else None
        updated_at_local = timezone.localtime(contact.updated_at) if contact.updated_at else None
        resolved_at_local = timezone.localtime(contact.resolved_at) if contact.resolved_at else None
        
        ticket_id = generate_ticket_id(contact)
        
        data.append({
            'Date': created_at_local.strftime('%d-%b-%Y') if created_at_local else '',
            'Ticket ID': ticket_id,
            'Department': contact.department,
            'Name': contact.name,
            'Issue/Message': contact.message,
            'Priority': contact.priority,
            'Call Attended By': contact.call_attended_by or '',
            'Assigned To': contact.assigned_to or '',
            'Handover To': contact.handover_to or '',
            'Solved By': contact.solved_by or '',
            'Status': contact.status,
            'Remarks': contact.remarks or '',
            'Time': created_at_local.strftime('%H:%M:%S') if created_at_local else '',
            'Extension': contact.phone,
            'IP Address': contact.ip_address or '',
            'OS': contact.os_info or 'N/A',
            'Created At': created_at_local.strftime('%Y-%m-%d %H:%M:%S') if created_at_local else '',
            'Updated At': updated_at_local.strftime('%Y-%m-%d %H:%M:%S') if updated_at_local else '',
            'Resolved At': resolved_at_local.strftime('%Y-%m-%d %H:%M:%S') if resolved_at_local else '',
            'Is Resolved': 'Yes' if contact.is_resolved else 'No',
        })
    
    df = pd.DataFrame(data)
    
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Resolved Issues', index=False)
        
        worksheet = writer.sheets['Resolved Issues']
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
        header_fill = PatternFill(start_color="1f6f4a", end_color="1f6f4a", fill_type="solid")
        header_alignment = Alignment(horizontal="center", vertical="center")
        
        for cell in worksheet[1]:
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = header_alignment
    
    output.seek(0)
    
    response = HttpResponse(
        output.read(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    filename = f"resolved_issues_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
     
    return response

# Resolved Issues Excel Export (Compact) - Admin Only
@login_required(login_url='/admin/login/')
@user_passes_test(is_admin)
def resolved_issues_excel_compact(request):
    selected_date = request.GET.get('date')
    resolved_contacts = Contact.objects.filter(is_resolved=True, is_stored=False).order_by('id')
    
    if selected_date:
        try:
            selected_date_obj = datetime.strptime(selected_date, '%Y-%m-%d').date()
            resolved_contacts = resolved_contacts.filter(date=selected_date_obj)
        except (ValueError, TypeError):
            resolved_contacts = resolved_contacts.filter(date=selected_date)

    data = []
    for contact in resolved_contacts:
        created_at_local = timezone.localtime(contact.created_at) if contact.created_at else None
        
        ticket_id = generate_ticket_id(contact)
        
        data.append({
            'Date': created_at_local.strftime('%d-%b-%Y') if created_at_local else '',
            'Ticket ID': ticket_id,
            'Department': contact.department,
            'Name': contact.name,
            'Issue/Message': contact.message,
            'Priority': contact.priority,
            'Call Attended By': contact.call_attended_by or '',
            'Assigned To': contact.assigned_to or '',
            'Handover To': contact.handover_to or '',
            'Solved By': contact.solved_by or '',
            'Status': contact.status,
            'Remarks': contact.remarks or '',
        })
    
    df = pd.DataFrame(data)
    
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Resolved Issues (Compact)', index=False)
        
        worksheet = writer.sheets['Resolved Issues (Compact)']
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
        header_fill = PatternFill(start_color="1f6f4a", end_color="1f6f4a", fill_type="solid")
        header_alignment = Alignment(horizontal="center", vertical="center")
        
        for cell in worksheet[1]:
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = header_alignment
    
    output.seek(0)
    
    response = HttpResponse(
        output.read(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    filename = f"resolved_issues_compact_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
     
    return response


# Stored Item Detail - Shows limited fields for stored items
def stored_item_detail(request, pk):
    """View for stored items - shows all files with preview"""
    item = get_object_or_404(Contact, pk=pk, is_stored=True)
    stored_files = StoredFile.objects.filter(contact=item)
    
    return render(request, 'core/stored_item_detail.html', {
        'item': item,
        'stored_files': stored_files,
    })

### Edit Stored Item - Admin Only
@login_required(login_url='/admin/login/')
@user_passes_test(is_admin)
def store_edit(request, pk):
    item = get_object_or_404(Contact, pk=pk, is_stored=True)
    
    # ✅ Get ALL files - BOTH old and new
    stored_files_qs = StoredFile.objects.filter(contact=item)
    stored_files = list(stored_files_qs)
    
    # Check for legacy media_file
    has_legacy_file = False
    legacy_file = None
    
    if item.media_file:
        file_name = item.media_file.name.split('/')[-1]
        exists_in_stored = any(sf.file_name == file_name for sf in stored_files)
        
        if not exists_in_stored:
            has_legacy_file = True
            legacy_file = {
                'name': file_name,
                'size': item.media_file.size,
                'url': item.media_file.url,
            }
            # Add to stored_files list
            class VirtualFile:
                pass
            virtual = VirtualFile()
            virtual.file_name = file_name
            virtual.file_size = item.media_file.size
            virtual.file_url = item.media_file.url
            virtual.file = item.media_file
            virtual.is_legacy = True
            stored_files.append(virtual)
    
    total_files = len(stored_files)
    
    if request.method == 'POST':
        # ============================================================
        # ✅ GET FORM DATA
        # ============================================================
        name = request.POST.get('name')
        department = request.POST.get('department')
        phone = request.POST.get('phone')
        priority = request.POST.get('priority')
        remarks = request.POST.get('remarks', '')
        description = request.POST.get('description')
        
        # Update the item
        item.name = name
        item.department = department
        item.phone = phone
        item.priority = priority
        item.remarks = remarks
        item.description = description
        
        # ============================================================
        # ✅ HANDLE FILE OPERATIONS (ADD/REPLACE/DELETE)
        # ============================================================
        
        # Check if user wants to remove all files
        if request.POST.get('media_clear') == 'on':
            StoredFile.objects.filter(contact=item).delete()
            if item.media_file:
                item.media_file.delete(save=False)
                item.media_file = None
            item.is_multiple = False
            item.file_count = 0
        
        # REPLACE: Delete ALL existing files and upload new ones
        elif request.FILES.getlist('media_file') and request.POST.get('replace_files') == 'on':
            # Delete all existing files
            StoredFile.objects.filter(contact=item).delete()
            if item.media_file:
                item.media_file.delete(save=False)
                item.media_file = None
            
            multiple_files = request.FILES.getlist('media_file')
            media_file = None
            is_multiple = False
            file_count = 0
            
            # Validate file sizes
            MAX_SIZE = 1024 * 1024 * 1024
            for file in multiple_files:
                if file.size > MAX_SIZE:
                    messages.error(request, f"File '{file.name}' exceeds 1 GB limit.")
                    return render(request, 'core/store_edit.html', {
                        'item': item,
                        'stored_files': stored_files,
                        'total_files': total_files,
                        'has_legacy_file': has_legacy_file,
                        'legacy_file': legacy_file,
                    })
            
            if multiple_files and len(multiple_files) > 0:
                file_count = len(multiple_files)
                if file_count == 1:
                    media_file = multiple_files[0]
                    is_multiple = False
                else:
                    media_file = multiple_files[0]
                    is_multiple = True

                item.media_file = media_file
                item.is_multiple = is_multiple
                item.file_count = file_count

                for file in multiple_files:
                    StoredFile.objects.create(
                        contact=item,
                        file=file,
                        file_name=file.name,
                        file_size=file.size
                    )
        
        # ADD: Keep existing files and upload new ones
        elif request.FILES.getlist('media_file') and request.POST.get('add_files') == 'on':
            multiple_files = request.FILES.getlist('media_file')
            
            # Validate file sizes
            MAX_SIZE = 1024 * 1024 * 1024
            for file in multiple_files:
                if file.size > MAX_SIZE:
                    messages.error(request, f"File '{file.name}' exceeds 1 GB limit.")
                    return render(request, 'core/store_edit.html', {
                        'item': item,
                        'stored_files': stored_files,
                        'total_files': total_files,
                        'has_legacy_file': has_legacy_file,
                        'legacy_file': legacy_file,
                    })
            
            # Migrate legacy media_file to StoredFile if exists
            if item.media_file:
                file_name = item.media_file.name.split('/')[-1]
                existing = StoredFile.objects.filter(
                    contact=item,
                    file_name=file_name
                )
                if not existing.exists():
                    StoredFile.objects.create(
                        contact=item,
                        file=item.media_file,
                        file_name=file_name,
                        file_size=item.media_file.size
                    )
            
            # Create StoredFile records for each new file
            for file in multiple_files:
                StoredFile.objects.create(
                    contact=item,
                    file=file,
                    file_name=file.name,
                    file_size=file.size
                )
            
            # Update contact's media_file (point to first file)
            all_files = StoredFile.objects.filter(contact=item)
            if all_files.exists():
                item.media_file = all_files.first().file
            
            # Update file count
            item.file_count = StoredFile.objects.filter(contact=item).count()
            item.is_multiple = item.file_count > 1
        
        # Single file upload (backward compatibility - REPLACE)
        elif request.FILES.get('media_file'):
            # Delete all existing files
            StoredFile.objects.filter(contact=item).delete()
            if item.media_file:
                item.media_file.delete(save=False)
                item.media_file = None
            
            file = request.FILES.get('media_file')
            item.media_file = file
            item.is_multiple = False
            item.file_count = 1
            
            StoredFile.objects.create(
                contact=item,
                file=file,
                file_name=file.name,
                file_size=file.size
            )
        
        # ============================================================
        # ✅ SAVE AND REDIRECT
        # ============================================================
        item.updated_at = timezone.localtime(timezone.now())
        item.save()
        
        # Get final file count for success message
        final_count = StoredFile.objects.filter(contact=item).count()
        if final_count > 0:
            messages.success(request, f"✅ Stored item '{name}' updated successfully! ({final_count} file(s))")
        else:
            messages.success(request, f"✅ Stored item '{name}' updated successfully!")
        
        return redirect('core:storage_view')
    
    return render(request, 'core/store_edit.html', {
        'item': item,
        'stored_files': stored_files,
        'total_files': total_files,
        'has_legacy_file': has_legacy_file,
        'legacy_file': legacy_file,
    })


def get_zip_contents(request, pk):
    """Get contents of a stored item (individual files)"""
    item = get_object_or_404(Contact, pk=pk, is_stored=True)
    
    # Get individual files from StoredFile model
    stored_files = StoredFile.objects.filter(contact=item)
    
    files = []
    for sf in stored_files:
        files.append({
            'name': sf.file_name,
            'size': sf.file_size,
            'url': sf.file.url  # Direct URL to the file
        })
    
    return JsonResponse({'files': files})



  # core/views.py - Add these functions

@login_required(login_url='/admin/login/')
@user_passes_test(is_admin)
def delete_stored_file(request, pk, file_index):
    """
    Delete a specific file from a stored item
    - Deletes from database (StoredFile)
    - Deletes physical file from storage
    """
    item = get_object_or_404(Contact, pk=pk, is_stored=True)
    stored_files = StoredFile.objects.filter(contact=item)
    
    if file_index < len(stored_files):
        file_to_delete = stored_files[file_index]
        file_name = file_to_delete.file_name
        
        # Delete from database (this also removes the physical file)
        file_to_delete.delete()
        
        # Update file count
        item.file_count = StoredFile.objects.filter(contact=item).count()
        item.is_multiple = item.file_count > 1
        item.save()
        
        return JsonResponse({
            'status': 'success',
            'message': f'Deleted: {file_name}',
            'file_count': item.file_count
        })
    
    return JsonResponse({'status': 'error', 'message': 'File not found'}, status=404)

@login_required(login_url='/admin/login/')
@user_passes_test(is_admin)
def delete_stored_all_files(request, pk):
    """
    Delete ALL files from a stored item
    - Deletes all StoredFile records from database
    - Deletes all physical files from storage
    """
    item = get_object_or_404(Contact, pk=pk, is_stored=True)
    
    # Delete all StoredFile records
    StoredFile.objects.filter(contact=item).delete()
    
    # Delete legacy media_file
    if item.media_file:
        item.media_file.delete(save=False)
        item.media_file = None
    
    # Update flags
    item.is_multiple = False
    item.file_count = 0
    item.save()
    
    return JsonResponse({
        'status': 'success',
        'message': 'All files deleted successfully!'
    })

@login_required(login_url='/admin/login/')
@user_passes_test(is_admin)
def delete_issue_file(request, pk, file_index):
    """
    Delete a specific file from a regular issue
    - Deletes from database (StoredFile)
    - Deletes physical file from storage
    """
    contact = get_object_or_404(Contact, pk=pk, is_stored=False)
    stored_files = StoredFile.objects.filter(contact=contact)
    
    if file_index < len(stored_files):
        file_to_delete = stored_files[file_index]
        file_name = file_to_delete.file_name
        
        # Delete from database (this also removes the physical file)
        file_to_delete.delete()
        
        # Update file count
        contact.file_count = StoredFile.objects.filter(contact=contact).count()
        contact.is_multiple = contact.file_count > 1
        contact.save()
        
        return JsonResponse({
            'status': 'success',
            'message': f'Deleted: {file_name}',
            'file_count': contact.file_count
        })
    
    return JsonResponse({'status': 'error', 'message': 'File not found'}, status=404)

@login_required(login_url='/admin/login/')
@user_passes_test(is_admin)
def delete_issue_all_files(request, pk):
    """
    Delete ALL files from a regular issue
    - Deletes all StoredFile records from database
    - Deletes all physical files from storage
    """
    contact = get_object_or_404(Contact, pk=pk, is_stored=False)
    
    # Delete all StoredFile records
    StoredFile.objects.filter(contact=contact).delete()
    
    # Delete legacy media_file
    if contact.media_file:
        contact.media_file.delete(save=False)
        contact.media_file = None
    
    # Update flags
    contact.is_multiple = False
    contact.file_count = 0
    contact.save()
    
    return JsonResponse({
        'status': 'success',
        'message': 'All files deleted successfully!'
    })  