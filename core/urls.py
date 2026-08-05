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
]