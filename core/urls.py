from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.contact, name='contact'),  # contact is the landing page
    path('issue/<int:pk>/', views.issue_detail, name='issue_detail'),
    path('issue/<int:pk>/edit/', views.issue_edit, name='issue_edit'),
    path('issue/<int:pk>/delete/', views.issue_delete, name='issue_delete'),
    path('issue/<int:pk>/done/', views.issue_mark_done, name='issue_mark_done'),
    path('resolved-excel/', views.resolved_issues_excel, name='resolved_issues_excel'),
    path('resolved-excel-compact/', views.resolved_issues_excel_compact, name='resolved_issues_excel_compact'),
    path('toggle-public/<int:pk>/', views.toggle_public_issue, name='toggle_public_issue'),
    path('store/', views.store_issue, name='store_issue'),  # Store form (everyone)
    path('store-submit/', views.store_submit, name='store_submit'),  # Submit store (everyone)
    path('storage/', views.storage_view, name='storage_view'),  # Storage view (admin only)
    path('storage-delete/<int:pk>/', views.storage_delete, name='storage_delete'),  # Delete from storage (admin only)
    path('storage-restore/<int:pk>/', views.storage_restore, name='storage_restore'),  # Restore from storage (admin only)
    path('stored-item/<int:pk>/', views.stored_item_detail, name='stored_item_detail'),
    # Store edit (admin only)
    path('store/edit/<int:pk>/', views.store_edit, name='store_edit'),
]