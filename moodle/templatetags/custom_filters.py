from django import template

register = template.Library()

@register.filter
def chr(value):
    """
    Converts an integer (like 65) into a character (A, B, C...).
    Example: {{ 65|chr }} => A
    """
    try:
        return chr(int(value))
    except (ValueError, TypeError):
        return ''
