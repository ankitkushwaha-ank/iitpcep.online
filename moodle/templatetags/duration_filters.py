from django import template

register = template.Library()


@register.filter
def nice_duration(minutes):
    if not minutes:
        return "0 minutes"

    hours = minutes // 60
    mins = minutes % 60

    parts = []
    if hours > 0:
        parts.append(f"{hours} hour{'s' if hours > 1 else ''}")
    if mins > 0:
        parts.append(f"{mins} minute{'s' if mins > 1 else ''}")

    return " ".join(parts)