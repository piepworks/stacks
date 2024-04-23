from django import template
from datetime import datetime

register = template.Library()


@register.filter
def days_since(value):
    now = datetime.now().date()  # Get the current date
    diff = now - value
    days = diff.days
    if days == 1:
        return "1 day ago"
    else:
        return f"{days} days ago"
