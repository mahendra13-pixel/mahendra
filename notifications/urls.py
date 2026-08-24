# notifications/urls.py

from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    path('api/pending/', views.pending_issues_api, name='pending_api'),
]