from django.shortcuts import render, redirect
from .models import SystemConfig


class SystemStatusMiddleware:
    """
    Middleware to show offline page when system_status = OFFLINE.
    Allows access only to /admin and static/media URLs.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # ✅ Allow admin, static, and media routes
        if request.path.startswith("/admin") or request.path.startswith("/static") or request.path.startswith("/media"):
            return self.get_response(request)

        # ✅ Get system configuration
        config = SystemConfig.objects.first()

        # ✅ If system is OFFLINE
        if config and config.system_status == "OFFLINE":
            # Redirect any non-root URL to home
            # Render offline page at root
            return render(request, "offline.html", {"system_status": "OFFLINE"}, status=503)

        # ✅ Otherwise continue normally
        return self.get_response(request)
