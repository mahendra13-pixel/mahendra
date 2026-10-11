from django.urls import path
from . import views

app_name = 'link_store'

urlpatterns = [
    path('', views.link_store_view, name='storage_view'),
    path('<int:pk>/file/delete/<int:slot>/', views.link_delete_file, name='delete_link_file'),
    path('file/<int:pk>/<str:slot_key>/', views.serve_telegram_file, name='serve_telegram_file'),
]