import socket
from .models import Visit


def get_client_ip(request):
    """Get real client IP even behind proxies"""
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[0].strip()
    else:
        ip = request.META.get("REMOTE_ADDR")
    if ip == "::1":
        ip = "127.0.0.1"
    return ip


def get_client_os(request):
    """Detect OS from User-Agent"""
    ua = request.META.get("HTTP_USER_AGENT", "").lower()
    if "windows" in ua:
        return "Windows"
    elif "mac" in ua or "darwin" in ua:
        return "macOS"
    elif "android" in ua:
        return "Android"
    elif "iphone" in ua or "ipad" in ua:
        return "iOS"
    elif "linux" in ua:
        return "Linux"
    return "Unknown"


class VisitTrackingMiddleware:
    """Records every visit to the site"""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Skip static, media, admin static, favicon
        path = request.path
        skip_prefixes = (
            "/static/",
            "/media/",
            "/favicon.ico",
            "/admin/jsi18n/",
        )
        should_skip = any(path.startswith(p) for p in skip_prefixes)

        # ✅ Skip logging for admins (staff / superuser)
        if request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser):
            return self.get_response(request)

        if not should_skip:
            try:
                ip_address = get_client_ip(request)
                os_info = get_client_os(request)

                if request.user.is_authenticated:
                    username = request.user.username
                    hostname = request.user.username
                    is_authenticated = True
                else:
                    username = None
                    hostname = None
                    is_authenticated = False

                # Get session key (may not exist yet)
                session_key = None
                try:
                    if request.session.session_key:
                        session_key = request.session.session_key
                except Exception:
                    pass

                Visit.objects.create(
                    ip_address=ip_address,
                    username=username,
                    hostname=hostname,
                    os_info=os_info,
                    user_agent=request.META.get("HTTP_USER_AGENT", "")[:1000],
                    path=path[:500],
                    method=request.method,
                    is_authenticated=is_authenticated,
                    referer=request.META.get("HTTP_REFERER", "")[:500],
                    session_key=session_key,
                )
            except Exception:
                # Never break the site if logging fails
                pass

        return self.get_response(request)