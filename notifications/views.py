from django.shortcuts import render

# Create your views here.

# notifications/views.py

from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from core.models import Contact

@login_required(login_url='/admin/login/')
def pending_issues_api(request):
    """
    API endpoint for pending issues
    Returns list of pending issues with details for voice notification
    """
    pending_issues = Contact.objects.filter(
        is_resolved=False,
        is_stored=False,
        status__in=['Pending', 'In Progress']
    ).order_by('-priority', '-created_at')
    
    issues_data = []
    for issue in pending_issues:
        issues_data.append({
            'id': issue.id,
            'name': issue.name,
            'department': issue.department or 'Unknown',
            'priority': issue.priority or 'Medium',
            'status': issue.status,
            'message': issue.message[:50] if issue.message else '',
            'created_at': issue.created_at.strftime('%Y-%m-%d %H:%M'),
        })
    
    # Get counts by department
    departments = {}
    for issue in issues_data:
        dept = issue['department']
        departments[dept] = departments.get(dept, 0) + 1
    
    high_priority_count = len([i for i in issues_data if i['priority'] in ['High', 'Urgent']])
    
    return JsonResponse({
        'count': len(issues_data),
        'issues': issues_data,
        'departments': departments,
        'high_priority_count': high_priority_count,
        'has_pending': len(issues_data) > 0
    })