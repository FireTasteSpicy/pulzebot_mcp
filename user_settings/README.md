# User Settings Directory

This directory contains user preferences, privacy controls, and settings management for the PulzeBot application.

## Directory Structure

```
user_settings/
├── README.md                    # This file
├── __init__.py                  # Package initialization
├── admin.py                     # Django admin configuration
├── apps.py                      # Django app configuration
├── models.py                    # User settings data models
├── privacy_service.py           # Privacy and consent management
├── forms.py                     # Django forms for settings
├── signals.py                   # Django signal handlers
├── views.py                     # Settings management views
├── urls.py                      # URL routing
├── tests.py                     # Test suite
└── migrations/
    ├── __init__.py
    └── 0001_initial.py          # Initial database migration
```

## Main Components

- **Models**: `UserSettings` model for privacy preferences and integration controls
- **Services**: `PrivacyEnforcementService` for consent management and data protection
- **Forms**: User-friendly forms for settings configuration
- **Tests**: Comprehensive test suite covering user settings and privacy functionality