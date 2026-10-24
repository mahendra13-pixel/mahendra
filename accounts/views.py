from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test

# ============================================================
# HELPER FUNCTIONS
# ============================================================

def is_normal_user(user):
    """Check if user is a normal user (not staff/superuser)"""
    return user.is_authenticated and not (user.is_staff or user.is_superuser)


# Optional: Create a reusable decorator
def normal_user_required(view_func):
    """Decorator to allow only normal users"""
    return user_passes_test(is_normal_user, login_url="/accounts/login/")(view_func)


# ============================================================
# REGISTRATION VIEW
# ============================================================

def register(request):
    """Handle new user registration"""
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f"Account created for {username}! You can now log in.")
            return redirect('accounts:login')
    else:
        form = UserCreationForm()
    
    return render(request, 'accounts/register.html', {'form': form})