from django.conf import settings

def global_user_context(request):
    """
    Adds username (from session) to all templates automatically.
    """
    username = request.session.get('username', None)
    return {
        'username': username if username else 'IITians',  # Default fallback
        'SYSTEM': getattr(settings, 'SYSTEM', {}),        # Optional system info
    }
