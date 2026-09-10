from django.shortcuts import render

# Create your views here.
from django.contrib.auth.decorators import user_passes_test


def is_normal_user(user):
    """Check if user is a normal user (not staff/superuser)"""
    return user.is_authenticated and not (user.is_staff or user.is_superuser)


# Optional: Create a reusable decorator
def normal_user_required(view_func):
    """Decorator to allow only normal users"""
    return user_passes_test(is_normal_user, login_url="/accounts/login/")(view_func)