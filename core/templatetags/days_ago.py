from django import template
from datetime import datetime

register = template.Library()


@register.filter
def days_ago(value):
    now = datetime.now().date()  # Get the current date
    diff = now - value
    days = diff.days
    if days == 1:
        return "1 day ago"
    elif days == 0:
        return "Today"
    else:
        return f"{days} days ago"
