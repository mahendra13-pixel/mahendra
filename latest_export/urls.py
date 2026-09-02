from django.urls import path
from . import views

app_name = 'latest_export'

urlpatterns = [
    path('latest-25/', views.export_latest_25_resolved, name='export_latest_25'),
]