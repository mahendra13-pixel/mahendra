from django.urls import path
from . import views

app_name = 'personal_store'

urlpatterns = [
    path('', views.personal_storage_view, name='storage_view'),
    path('store/', views.personal_store_submit, name='store_submit'),
    path('edit/<int:pk>/', views.personal_store_edit, name='store_edit'),
    path('delete/<int:pk>/', views.personal_storage_delete, name='storage_delete'),
    path('toggle/<int:pk>/', views.toggle_completion, name='toggle_completion'),
    path('detail/<int:pk>/', views.personal_item_detail, name='item_detail'),
    path('<int:pk>/file/delete/<int:file_index>/', views.personal_delete_file, name='delete_personal_file'),
    path('<int:pk>/file/<str:slot_key>/', views.serve_personal_telegram_file, name='serve_personal_file'),
]