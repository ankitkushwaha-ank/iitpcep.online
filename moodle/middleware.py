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


# moodle/middleware.py
from django.shortcuts import render
from django.urls import reverse
from django.conf import settings


class CustomAdminAccessMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        # Get the path to the admin (e.g., /admin/)
        try:
            self.admin_path = reverse('admin:index')
        except:
            self.admin_path = getattr(settings, 'ADMIN_URL', '/admin/')

    def __call__(self, request):

        # Check if the request is for the admin panel
        if request.path.startswith(self.admin_path):

            # --- This is the new logic ---
            # Check if user is logged in AND has your custom 'is_admin' = True
            is_allowed = (
                    request.user.is_authenticated and
                    hasattr(request.user, 'is_admin') and
                    request.user.is_admin
            )

            if is_allowed:
                # The user is your custom admin.
                # We MUST set 'is_staff' to True for this request,
                # otherwise the Django admin panel will still block them.
                request.user.is_staff = True

            else:
                # User is not logged in OR is not a custom admin.
                # Show the offline page as requested.
                return render(request, 'offline.html')

        # Let the request continue as normal for all other pages
        response = self.get_response(request)
        return response


from django.utils import timezone
from .models import UserTable
from django.core.cache import cache


class ActiveUserMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        if request.user.is_authenticated:
            # Cache key to prevent database spam (update once per minute)
            cache_key = f'last_seen_{request.user.id}'
            if not cache.get(cache_key):
                try:
                    # Update the UserTable entry
                    user_profile = UserTable.objects.get(username=request.user.username)
                    user_profile.update_activity()  # Updates timestamp

                    # Set cache for 60 seconds
                    cache.set(cache_key, timezone.now(), 60)
                except UserTable.DoesNotExist:
                    pass

        return response