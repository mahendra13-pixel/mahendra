from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from django.urls import reverse
from .models import PersonalItem, PersonalStoredFile

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

    # Search
    search_query = request.GET.get('search')
    if search_query:
        items = items.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(remarks__icontains=search_query)
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
        # ✅ NEW FIELDS
        due_date = request.POST.get("due_date") or None
        status = request.POST.get("status", "Pending")
        now = timezone.localtime(timezone.now())
        
        multiple_files = request.FILES.getlist("media_file")
        
        try:
            with transaction.atomic():
                item = PersonalItem.objects.create(
                    name=name,
                    description=description,
                    priority=priority,
                    remarks=remarks,
                    # ✅ NEW FIELDS SAVED
                    due_date=due_date,
                    status=status,
                    created_at=now,
                    updated_at=now,
                )
                
                for file in multiple_files:
                    PersonalStoredFile.objects.create(
                        item=item,
                        file=file,
                        file_name=file.name,
                        file_size=file.size,
                    )
                
                item.file_count = len(multiple_files)
                item.is_multiple = len(multiple_files) > 1
                if multiple_files:
                    item.media_file = multiple_files[0]
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
        # Delete associated files first (calls custom delete method)
        for stored_file in item.stored_files.all():
            stored_file.delete()
        
        # Delete the item itself (calls custom delete method)
        item.delete()
        
        messages.success(request, "✅ Item permanently deleted from disk.")
        
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
    
    if request.method == "POST":
        item.name = request.POST.get("name")
        item.description = request.POST.get("description")
        item.priority = request.POST.get("priority")
        item.remarks = request.POST.get("remarks")
        item.is_completed = request.POST.get("is_completed") == "on"
        # ✅ NEW FIELDS
        item.due_date = request.POST.get("due_date") or None
        item.status = request.POST.get("status", "Pending")

        # Handle file operations
        if request.POST.get("media_clear") == "on":
            for sf in stored_files:
                sf.delete()
            item.media_file = None
            item.file_count = 0
            item.is_multiple = False
        
        elif request.FILES.getlist("media_file"):
            action = request.POST.get("file_action", "replace")
            multiple_files = request.FILES.getlist("media_file")
            
            if action == "replace":
                for sf in stored_files:
                    sf.delete()
                item.file_count = 0
            
            for file in multiple_files:
                PersonalStoredFile.objects.create(
                    item=item,
                    file=file,
                    file_name=file.name,
                    file_size=file.size,
                )
            
            item.file_count = item.stored_files.count()
            item.is_multiple = item.file_count > 1
            if item.stored_files.exists():
                item.media_file = item.stored_files.first().file

        item.updated_at = timezone.localtime(timezone.now())
        item.save()
        messages.success(request, "✅ Item updated successfully.")
        return redirect("personal_store:storage_view")

    return render(request, 'personal_store/personal_store_edit.html', {
        'item': item,
        'stored_files': stored_files,
    })

# --- Detail View ---
@login_required(login_url="/admin/login/")
@user_passes_test(is_admin)
def personal_item_detail(request, pk):
    item = get_object_or_404(PersonalItem, pk=pk)
    stored_files = item.stored_files.all()
    return render(request, 'personal_store/personal_item_detail.html', {
        'item': item,
        'stored_files': stored_files,
    })