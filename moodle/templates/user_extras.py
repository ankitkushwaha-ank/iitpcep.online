from django import template

register = template.Library()

@register.filter
def user_initials(username):
    """
    Generate initials from username.
    Example:
        "Ankit" -> "A"
        "Ankit Kumar" -> "AK"
        None or empty -> "I"
    """
    if not username:
        return "I"

    # Split username and extract first letters
    parts = username.strip().split()
    if len(parts) == 1:
        return parts[0][0].upper()
    else:
        return (parts[0][0] + parts[1][0]).upper()
