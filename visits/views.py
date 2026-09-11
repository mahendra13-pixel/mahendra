from django.shortcuts import render

# Create your views here.
from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator
from django.db import models
from .models import Visit


def is_admin(user):
    return user.is_staff or user.is_superuser


@login_required(login_url="/admin/login/")
@user_passes_test(is_admin)
def visits_list(request):
    """Show all visits — admin only"""
    visits = Visit.objects.all().order_by("-visited_at")

    # Filters
    search = request.GET.get("search")
    if search:
        visits = visits.filter(
            models.Q(ip_address__icontains=search)
            | models.Q(username__icontains=search)
            | models.Q(path__icontains=search)
            | models.Q(os_info__icontains=search)
        )

    filter_user = request.GET.get("user")
    if filter_user:
        visits = visits.filter(username=filter_user)

    filter_ip = request.GET.get("ip")
    if filter_ip:
        visits = visits.filter(ip_address=filter_ip)

    # Pagination
    paginator = Paginator(visits, 50)
    page_obj = paginator.get_page(request.GET.get("page", 1))

    return render(
        request,
        "visits/visits_list.html",
        {
            "page_obj": page_obj,
            "search": search or "",
            "filter_user": filter_user or "",
            "filter_ip": filter_ip or "",
        },
    )