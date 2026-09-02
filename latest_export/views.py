from django.shortcuts import render

# latest_export/views.py
import pandas as pd
from io import BytesIO
from datetime import datetime
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from core.models import Contact
from core.views import generate_ticket_id

@login_required(login_url='/admin/login/')
def export_latest_25_resolved(request):
    """Export latest 25 resolved issues as Excel (same as compact export)"""
    
    # ✅ SAME as compact export - ordered by created_at
    resolved_contacts = Contact.objects.filter(
        is_resolved=True, 
        is_stored=False
    ).order_by('-created_at')[:25][::-1]  # ← SAME as compact export!
    
    data = []
    for contact in resolved_contacts:
        created_at_local = timezone.localtime(contact.created_at) if contact.created_at else None
        ticket_id = generate_ticket_id(contact)
        
        # ✅ SAME fields as compact export
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
        df.to_excel(writer, sheet_name='Latest 25 Resolved Issues', index=False)
        
        worksheet = writer.sheets['Latest 25 Resolved Issues']
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
    filename = f"latest_25_resolved_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    return response