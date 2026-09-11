from django.urls import path
from . import views

app_name = "visits"

urlpatterns = [
    path("", views.visits_list, name="visits_list"),
    path("delete-all/", views.delete_all_visits, name="delete_all_visits"),
]