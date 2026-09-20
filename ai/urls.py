from django.urls import path
from . import views

app_name = 'ai'

urlpatterns = [
    path('tools/', views.ai_links, name='ai_links'),
]