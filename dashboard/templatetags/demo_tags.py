from django import template
from django.conf import settings

register = template.Library()

@register.simple_tag
def demo_mode():
    """Return True if demo mode is enabled."""
    return getattr(settings, 'DEMO_MODE', False)








