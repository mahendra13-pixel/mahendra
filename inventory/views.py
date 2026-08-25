# inventory/views.py

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.core.exceptions import ValidationError
from django.db import models
from django.conf import settings
from .models import Category, InventoryItem, MAX_UPLOAD_SIZE, validate_file_size

def is_admin(user):
    return user.is_staff or user.is_superuser

# ============================================================
# HELPER FUNCTIONS
# ============================================================

def handle_file_upload(file):
    """Handle file upload with validation"""
    if not file:
        return None, None
    
    # Validate file size
    try:
        validate_file_size(file)
    except ValidationError as e:
        raise ValidationError(str(e))
    
    return file

def get_media_type_from_filename(filename):
    """Determine media type from file extension"""
    if not filename:
        return 'none'
    
    ext = filename.lower().split('.')[-1] if '.' in filename else ''
    
    # Image extensions
    image_exts = ['jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp', 'svg', 'ico', 'tiff']
    if ext in image_exts:
        return 'image'
    
    # Video extensions
    video_exts = ['mp4', 'webm', 'ogg', 'mov', 'avi', 'mkv', 'flv', 'wmv', 'm4v', '3gp']
    if ext in video_exts:
        return 'video'
    
    # Audio extensions
    audio_exts = ['mp3', 'wav', 'ogg', 'flac', 'aac', 'wma', 'm4a', 'opus']
    if ext in audio_exts:
        return 'audio'
    
    return 'other'

def json_response(success, message, data=None, status=200):
    """Standard JSON response helper"""
    response = {
        'success': success,
        'message': message
    }
    if data:
        response['data'] = data
    return JsonResponse(response, status=status)

# ============================================================
# CATEGORY VIEWS
# ============================================================

@login_required(login_url='/admin/login/')
@user_passes_test(is_admin)
def category_list(request):
    """List all categories"""
    categories = Category.objects.all().order_by('name')
    
    # Check for AJAX request
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        data = [{'id': cat.id, 'name': cat.name, 'description': cat.description, 'item_count': cat.items.count()} 
                for cat in categories]
        return json_response(True, 'Categories loaded', data)
    
    return redirect('inventory:management')

@login_required(login_url='/admin/login/')
@user_passes_test(is_admin)
def category_create(request):
    """Create a new category"""
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        
        if not name:
            error_msg = "Category name is required!"
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return json_response(False, error_msg)
            messages.error(request, error_msg)
            return redirect('inventory:management')
        
        if Category.objects.filter(name__iexact=name).exists():
            error_msg = f"Category '{name}' already exists!"
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return json_response(False, error_msg)
            messages.error(request, error_msg)
            return redirect('inventory:management')
        
        category = Category.objects.create(name=name, description=description)
        success_msg = f"✅ Category '{name}' created successfully!"
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return json_response(True, success_msg, {'id': category.id, 'name': category.name})
        
        messages.success(request, success_msg)
        return redirect('inventory:management')
    
    return redirect('inventory:management')

@login_required(login_url='/admin/login/')
@user_passes_test(is_admin)
def category_edit(request, pk):
    """Edit a category"""
    category = get_object_or_404(Category, pk=pk)
    
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        
        if not name:
            error_msg = "Category name is required!"
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return json_response(False, error_msg)
            messages.error(request, error_msg)
            return redirect('inventory:management')
        
        # Check for duplicate name (excluding current)
        if Category.objects.filter(name__iexact=name).exclude(pk=pk).exists():
            error_msg = f"Category '{name}' already exists!"
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return json_response(False, error_msg)
            messages.error(request, error_msg)
            return redirect('inventory:management')
        
        category.name = name
        category.description = description
        category.save()
        success_msg = f"✅ Category '{name}' updated successfully!"
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return json_response(True, success_msg, {'id': category.id, 'name': category.name})
        
        messages.success(request, success_msg)
        return redirect('inventory:management')
    
    return redirect('inventory:management')

@login_required(login_url='/admin/login/')
@user_passes_test(is_admin)
def category_delete(request, pk):
    """Delete a category"""
    category = get_object_or_404(Category, pk=pk)
    
    if request.method == 'POST':
        name = category.name
        item_count = category.items.count()
        category.delete()
        success_msg = f"✅ Category '{name}' deleted successfully! ({item_count} items removed)"
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return json_response(True, success_msg)
        
        messages.success(request, success_msg)
        return redirect('inventory:management')
    
    return redirect('inventory:management')

# ============================================================
# INVENTORY MANAGEMENT VIEW (All-in-One)
# ============================================================

@login_required(login_url='/admin/login/')
@user_passes_test(is_admin)
def inventory_management(request):
    """Combined inventory management page"""
    items = InventoryItem.objects.select_related('category').all().order_by('category__name', 'name')
    
    # Filter by category
    category_filter = request.GET.get('category')
    if category_filter:
        items = items.filter(category__id=category_filter)
    
    # Filter by status
    status_filter = request.GET.get('status')
    if status_filter:
        items = items.filter(status=status_filter)
    
    # Filter by media type
    media_filter = request.GET.get('media_type')
    if media_filter:
        items = items.filter(media_type=media_filter)
    
    # Search
    search_query = request.GET.get('search')
    if search_query:
        items = items.filter(
            models.Q(name__icontains=search_query) |
            models.Q(model__icontains=search_query) |
            models.Q(specification__icontains=search_query) |
            models.Q(remarks__icontains=search_query) |
            models.Q(original_filename__icontains=search_query)
        )
    
    paginator = Paginator(items, 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    categories = Category.objects.all().order_by('name')
    
    return render(request, 'inventory/inventory_management.html', {
        'page_obj': page_obj,
        'categories': categories,
        'category_filter': category_filter,
        'status_filter': status_filter,
        'media_filter': media_filter,
        'search_query': search_query,
    })

# ============================================================
# INVENTORY ITEM VIEWS
# ============================================================

@login_required(login_url='/admin/login/')
@user_passes_test(is_admin)
def inventory_list(request):
    """List all inventory items - redirect to management"""
    return redirect('inventory:management')

@login_required(login_url='/admin/login/')
@user_passes_test(is_admin)
def inventory_create(request):
    """Create a new inventory item"""
    if request.method == 'POST':
        category_id = request.POST.get('category')
        name = request.POST.get('name', '').strip()
        model = request.POST.get('model', '').strip()
        status = request.POST.get('status', 'working')
        quantity = request.POST.get('quantity', 1)
        specification = request.POST.get('specification', '').strip()
        remarks = request.POST.get('remarks', '').strip()
        image = request.FILES.get('image')
        
        # Validate required fields
        if not name:
            error_msg = "Item name is required!"
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return json_response(False, error_msg)
            messages.error(request, error_msg)
            return redirect('inventory:management')
        
        try:
            category = Category.objects.get(id=category_id)
        except (Category.DoesNotExist, ValueError):
            error_msg = "Please select a valid category."
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return json_response(False, error_msg)
            messages.error(request, error_msg)
            return redirect('inventory:management')
        
        # Validate and handle file upload
        if image:
            try:
                handle_file_upload(image)
            except ValidationError as e:
                error_msg = str(e)
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return json_response(False, error_msg)
                messages.error(request, error_msg)
                return redirect('inventory:management')
        
        # Create item
        item = InventoryItem(
            category=category,
            name=name,
            model=model,
            status=status,
            quantity=quantity,
            specification=specification,
            remarks=remarks,
            image=image,
            created_by=request.user.username
        )
        item.save()  # This will auto-detect media type
        
        success_msg = f"✅ Item '{name}' added successfully!"
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return json_response(True, success_msg, {
                'id': item.id,
                'name': item.name,
                'media_type': item.media_type
            })
        
        messages.success(request, success_msg)
        return redirect('inventory:management')
    
    # GET request - redirect to management
    return redirect('inventory:management')

@login_required(login_url='/admin/login/')
@user_passes_test(is_admin)
def inventory_edit(request, pk):
    """Edit an inventory item"""
    item = get_object_or_404(InventoryItem, pk=pk)
    
    if request.method == 'POST':
        category_id = request.POST.get('category')
        name = request.POST.get('name', '').strip()
        model = request.POST.get('model', '').strip()
        status = request.POST.get('status', 'working')
        quantity = request.POST.get('quantity', 1)
        specification = request.POST.get('specification', '').strip()
        remarks = request.POST.get('remarks', '').strip()
        image = request.FILES.get('image')
        
        # Validate required fields
        if not name:
            error_msg = "Item name is required!"
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return json_response(False, error_msg)
            messages.error(request, error_msg)
            return redirect('inventory:management')
        
        try:
            category = Category.objects.get(id=category_id)
        except (Category.DoesNotExist, ValueError):
            error_msg = "Please select a valid category."
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return json_response(False, error_msg)
            messages.error(request, error_msg)
            return redirect('inventory:management')
        
        # Validate and handle file upload
        if image:
            try:
                handle_file_upload(image)
                # Delete old image if new one is uploaded
                if item.image:
                    item.image.delete(save=False)
                item.image = image
            except ValidationError as e:
                error_msg = str(e)
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return json_response(False, error_msg)
                messages.error(request, error_msg)
                return redirect('inventory:management')
        
        # Update item fields
        item.category = category
        item.name = name
        item.model = model
        item.status = status
        item.quantity = quantity
        item.specification = specification
        item.remarks = remarks
        item.save()  # This will re-detect media type if image changed
        
        success_msg = f"✅ Item '{name}' updated successfully!"
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return json_response(True, success_msg, {
                'id': item.id,
                'name': item.name,
                'media_type': item.media_type
            })
        
        messages.success(request, success_msg)
        return redirect('inventory:management')
    
    # GET request - redirect to management
    return redirect('inventory:management')

@login_required(login_url='/admin/login/')
@user_passes_test(is_admin)
def inventory_delete(request, pk):
    """Delete an inventory item"""
    item = get_object_or_404(InventoryItem, pk=pk)
    
    if request.method == 'POST':
        name = item.name
        if item.image:
            # Delete the image file from storage
            try:
                item.image.delete(save=False)
            except:
                pass  # File might not exist
        item.delete()
        success_msg = f"✅ Item '{name}' deleted successfully!"
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return json_response(True, success_msg)
        
        messages.success(request, success_msg)
        return redirect('inventory:management')
    
    return redirect('inventory:management')

@login_required(login_url='/admin/login/')
@user_passes_test(is_admin)
def inventory_detail(request, pk):
    """View inventory item details"""
    item = get_object_or_404(InventoryItem, pk=pk)
    
    # Check for AJAX request - return JSON data
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        data = {
            'id': item.id,
            'name': item.name,
            'category': item.category.name,
            'category_id': item.category.id,
            'model': item.model,
            'status': item.status,
            'status_display': item.get_status_display(),
            'quantity': item.quantity,
            'specification': item.specification,
            'remarks': item.remarks,
            'media_type': item.media_type,
            'file_size': item.get_file_size_display(),
            'original_filename': item.original_filename,
            'image_url': item.image.url if item.image else None,
            'created_by': item.created_by,
            'created_at': item.created_at.strftime('%Y-%m-%d %H:%M'),
            'updated_at': item.updated_at.strftime('%Y-%m-%d %H:%M'),
        }
        return json_response(True, 'Item details loaded', data)
    
    return redirect('inventory:management')

# ============================================================
# BULK OPERATIONS
# ============================================================

@login_required(login_url='/admin/login/')
@user_passes_test(is_admin)
def inventory_bulk_action(request):
    """Bulk actions for inventory items"""
    if request.method != 'POST':
        return json_response(False, 'Method not allowed', status=405)
    
    action = request.POST.get('action')
    item_ids = request.POST.getlist('item_ids')
    
    if not item_ids:
        return json_response(False, 'No items selected')
    
    items = InventoryItem.objects.filter(id__in=item_ids)
    
    if action == 'delete':
        count = items.count()
        for item in items:
            if item.image:
                try:
                    item.image.delete(save=False)
                except:
                    pass
        items.delete()
        return json_response(True, f'✅ {count} items deleted successfully!')
    
    elif action in ['working', 'not_working', 'repair', 'disposed']:
        count = items.update(status=action)
        return json_response(True, f'✅ {count} items marked as {action.replace("_", " ").title()}!')
    
    return json_response(False, 'Invalid action')