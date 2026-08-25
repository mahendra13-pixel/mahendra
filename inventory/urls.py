# inventory/urls.py

from django.urls import path
from . import views

app_name = 'inventory'

urlpatterns = [
    # ============================================================
    # MANAGEMENT (All-in-One Page)
    # ============================================================
    path('', views.inventory_management, name='management'),
    path('manage/', views.inventory_management, name='management'),
    
    # ============================================================
    # CATEGORY URLs
    # ============================================================
    path('categories/', views.category_list, name='category_list'),
    path('categories/create/', views.category_create, name='category_create'),
    path('categories/<int:pk>/edit/', views.category_edit, name='category_edit'),
    path('categories/<int:pk>/delete/', views.category_delete, name='category_delete'),
    
    # ============================================================
    # INVENTORY ITEM URLs
    # ============================================================
    # List view (redirects to management)
    path('items/', views.inventory_list, name='inventory_list'),
    
    # Create
    path('items/create/', views.inventory_create, name='inventory_create'),
    path('create/', views.inventory_create, name='inventory_create'),  # Shortcut
    
    # Detail
    path('items/<int:pk>/', views.inventory_detail, name='inventory_detail'),
    path('<int:pk>/', views.inventory_detail, name='inventory_detail'),  # Shortcut
    
    # Edit
    path('items/<int:pk>/edit/', views.inventory_edit, name='inventory_edit'),
    path('<int:pk>/edit/', views.inventory_edit, name='inventory_edit'),  # Shortcut
    
    # Delete
    path('items/<int:pk>/delete/', views.inventory_delete, name='inventory_delete'),
    path('<int:pk>/delete/', views.inventory_delete, name='inventory_delete'),  # Shortcut
    
    # ============================================================
    # BULK OPERATIONS
    # ============================================================
    path('bulk-action/', views.inventory_bulk_action, name='bulk_action'),
]

# ============================================================
# API-style URLs (Optional - for AJAX/JSON responses)
# ============================================================
# You can uncomment these if you want separate API endpoints
"""
api_urlpatterns = [
    path('api/categories/', views.category_list, name='api_category_list'),
    path('api/items/', views.inventory_list, name='api_inventory_list'),
    path('api/items/<int:pk>/', views.inventory_detail, name='api_inventory_detail'),
]

urlpatterns += api_urlpatterns
"""