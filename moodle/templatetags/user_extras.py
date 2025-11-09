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



@register.filter(name="to_chr")
def to_chr(value):
    """
    Convert an integer (65) → 'A' for option lettering.
    Example: {{ 65|to_chr }} → A
    """
    try:
        import builtins
        return builtins.chr(int(value))  # ✅ use the real chr()
    except Exception:
        return ''
