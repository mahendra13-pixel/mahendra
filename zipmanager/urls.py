from django.urls import path
from . import views

app_name = 'zipmanager'

urlpatterns = [
    path('upload/',       views.upload_zip,   name='upload_zip'),
    path('download-all/', views.download_all, name='download_all'),
    path('list/',         views.list_files,   name='list_files'),
    path('view/', views.view_files, name='view_files'),
    path('delete/', views.delete_zip, name='delete_zip'),
]