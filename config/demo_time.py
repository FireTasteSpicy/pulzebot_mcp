"""
Demo time utility for fixing the application date to September 22, 2025 at 23:59.
This module provides a replacement for Django's timezone.now() for demo purposes.
"""
from datetime import datetime
import pytz
from django.utils import timezone
from django.conf import settings
import os

# Fixed demo date: September 22, 2025 at 23:59 Singapore time
DEMO_DATE = datetime(2025, 9, 22, 23, 59, 0)

def _get_demo_mode_setting():
    """Get demo mode setting from environment or Django settings."""
    # First try environment variable
    env_setting = os.getenv('DEMO_MODE_ENABLED', 'True')
    if env_setting.lower() in ('true', '1', 'yes'):
        return True
    
    # Then try Django settings if available
    try:
        return getattr(settings, 'DEMO_MODE_ENABLED', True)
    except:
        return True  # Default to demo mode enabled

# Enable/disable demo mode based on configuration
DEMO_MODE_ENABLED = _get_demo_mode_setting()

def now():
    """
    Returns the fixed demo datetime or current time based on DEMO_MODE_ENABLED.
    This replaces Django's timezone.now() for demo purposes.
    """
    if DEMO_MODE_ENABLED:
        # Return the fixed demo date in Singapore timezone
        singapore_tz = pytz.timezone('Asia/Singapore')
        demo_datetime = singapore_tz.localize(DEMO_DATE)
        return demo_datetime
    else:
        # Return actual current time
        return timezone.now()

def get_demo_date():
    """
    Returns the demo date as a date object (September 22, 2025).
    """
    if DEMO_MODE_ENABLED:
        return DEMO_DATE.date()
    else:
        return timezone.now().date()

def is_demo_mode():
    """
    Returns True if demo mode is enabled.
    """
    return DEMO_MODE_ENABLED

def enable_demo_mode():
    """
    Enable demo mode with fixed date.
    """
    global DEMO_MODE_ENABLED
    DEMO_MODE_ENABLED = True

def disable_demo_mode():
    """
    Disable demo mode and use real current time.
    """
    global DEMO_MODE_ENABLED
    DEMO_MODE_ENABLED = False