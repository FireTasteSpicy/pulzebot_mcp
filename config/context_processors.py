"""
Template context processor for demo mode.
Provides demo date and demo mode status to all templates.
"""
from config.demo_time import now as demo_now, is_demo_mode

def demo_context(request):
    """
    Context processor to provide demo date and mode to all templates.
    """
    return {
        'DEMO_MODE': is_demo_mode(),
        'DEMO_DATE': demo_now(),
        'DEMO_DATE_DISPLAY': demo_now().strftime('%B %d, %Y at %H:%M'),
    }