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
        from io import BytesIO
        import zipfile
        from django.core.files.base import ContentFile
        
        multiple_files = request.FILES.getlist('multiple_files')
        media_file = None
        is_multiple = False
        file_count = 0
        
        if multiple_files and len(multiple_files) > 0:
            if len(multiple_files) == 1:
                # Only one file, save directly (no ZIP)
                media_file = multiple_files[0]
                is_multiple = False
                file_count = 1
            else:
                # Multiple files, create ZIP
                zip_buffer = BytesIO()
                with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
                    for file in multiple_files:
                        zip_file.writestr(file.name, file.read())
                zip_buffer.seek(0)
                media_file = ContentFile(zip_buffer.read())
                media_file.name = f"files_{now.strftime('%Y%m%d_%H%M%S')}.zip"
                is_multiple = True
                file_count = len(multiple_files)
        else:
            single_file = request.FILES.get('media_file')
            if single_file:
                media_file = single_file
                is_multiple = False
                file_count = 1
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

            if action == 'resolve':
                messages.success(request, f"Hi {name}, your issue has been created and marked as Resolved!")
            else:
                messages.success(request, f"Hi {name}, your message has been submitted successfully.")
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
        
    return render(request, 'core/contact.html', {
        'contacts': contacts,
        'resolved_contacts': resolved_contacts,
        'pending_contacts': pending_contacts,
        'is_admin_user': is_admin_user,
        'user_ip': ip_address,
        'user_hostname': hostname,
        'user_username': username,
    })

# Issue Detail - Anyone can view
def issue_detail(request, pk):
    contact = get_object_or_404(Contact, pk=pk,is_stored=False)
    return render(request, 'core/issue_detail.html', {'contact': contact})

# Edit Issue - Admin Only
@login_required(login_url='/admin/login/')
@user_passes_test(is_admin)
def issue_edit(request, pk):
    contact = get_object_or_404(Contact, pk=pk, is_stored=False)
    if request.method == 'POST':
        contact.name = request.POST.get('name')
        contact.department = request.POST.get('department')
        contact.phone = request.POST.get('phone')
        contact.ip_address = request.POST.get('ip_address')
        contact.hostname = request.POST.get('hostname')
        contact.username = request.POST.get('username')
        contact.priority = request.POST.get('priority')
        contact.message = request.POST.get('message')
        
        # Get multiple selections and join them with comma
        contact.call_attended_by = ', '.join(request.POST.getlist('call_attended_by'))
        contact.handover_to = ', '.join(request.POST.getlist('handover_to'))
        contact.solved_by = ', '.join(request.POST.getlist('solved_by'))
        
        # NEW: Get assigned_to and remarks
        contact.assigned_to = ', '.join(request.POST.getlist('assigned_to'))
        contact.remarks = request.POST.get('remarks', '')
        
        # Handle media file upload
        if request.FILES.get('media_file'):
            contact.media_file = request.FILES.get('media_file')
        elif request.POST.get('media_clear') == 'on':
            if contact.media_file:
                contact.media_file.delete(save=False)
                contact.media_file = None
        
        contact.status = request.POST.get('status')
        
        # Get current time in Asia/Kathmandu
        now = timezone.localtime(timezone.now())
        contact.updated_at = now
        
        # If status is set to Closed, mark as resolved
        if contact.status == 'Closed' and not contact.is_resolved:
            contact.is_resolved = True
            contact.resolved_at = now
        elif contact.status != 'Closed' and contact.is_resolved:
            contact.is_resolved = False
            contact.resolved_at = None
            
        contact.save()
        messages.success(request, "Issue updated successfully.")
        return redirect('core:issue_detail', pk=contact.pk)
    return render(request, 'core/issue_edit.html', {'contact': contact})

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
            if len(multiple_files) == 1:
                # Only one file, save directly (no ZIP)
                media_file = multiple_files[0]
                is_multiple = False
                file_count = 1
            else:
                # Multiple files, create ZIP
                zip_buffer = BytesIO()
                with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
                    for file in multiple_files:
                        zip_file.writestr(file.name, file.read())
                zip_buffer.seek(0)
                media_file = ContentFile(zip_buffer.read())
                media_file.name = f"store_files_{now.strftime('%Y%m%d_%H%M%S')}.zip" 
                is_multiple = True
                file_count = len(multiple_files)
        
      
        
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
            
            messages.success(request, f"✅ Issue '{name}' stored successfully!")
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
    return render(request, 'core/storage_view.html', {'stored_items': stored_items})

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
    """View for stored items - shows only name, department, description, remarks"""
    item = get_object_or_404(Contact, pk=pk, is_stored=True)
    return render(request, 'core/stored_item_detail.html', {'item': item})


# Edit Stored Item - Admin Only
@login_required(login_url='/admin/login/')
@user_passes_test(is_admin)
def store_edit(request, pk):
    """Edit a stored item - ADMIN ONLY"""
    item = get_object_or_404(Contact, pk=pk, is_stored=True)
    
    if request.method == 'POST':
        # Get form data
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
        
        # Handle file upload
        if request.FILES.get('media_file'):
            # Delete old file if exists
            if item.media_file:
                item.media_file.delete(save=False)
            
            # Get the new file
            multiple_files = request.FILES.getlist('media_file')
            media_file = None
            is_multiple = False
            file_count = 0
            
            if multiple_files and len(multiple_files) > 0:
                if len(multiple_files) == 1:
                    media_file = multiple_files[0]
                    is_multiple = False
                    file_count = 1
                else:
                    zip_buffer = BytesIO()
                    with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
                        for file in multiple_files:
                            zip_file.writestr(file.name, file.read())
                    zip_buffer.seek(0)
                    media_file = ContentFile(zip_buffer.read())
                    now = timezone.localtime(timezone.now())
                    media_file.name = f"store_files_{now.strftime('%Y%m%d_%H%M%S')}.zip"
                    is_multiple = True
                    file_count = len(multiple_files)
                
                item.media_file = media_file
                item.is_multiple = is_multiple
                item.file_count = file_count
        
        # Remove file if checkbox checked
        elif request.POST.get('media_clear') == 'on':
            if item.media_file:
                item.media_file.delete(save=False)
                item.media_file = None
                item.is_multiple = False
                item.file_count = 0
        
        # Update timestamp
        item.updated_at = timezone.localtime(timezone.now())
        item.save()
        
        messages.success(request, f"✅ Stored item '{name}' updated successfully!")
        return redirect('core:storage_view')
    
    return render(request, 'core/store_edit.html', {'item': item})