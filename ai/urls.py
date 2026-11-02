from django.urls import path
from . import views

app_name = 'ai'

urlpatterns = [
    path('tools/', views.ai_links, name='ai_links'),
    path('developer/', views.developer, name='developer'),
    path('developer/cv/', views.serve_cv, name='developer_cv'),
    path(
        "developer/media/<str:model_key>/<int:pk>/<str:slot_key>/",
        views.serve_telegram_media,
        name="telegram_media",
    ),
]