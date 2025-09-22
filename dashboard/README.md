# Dashboard Directory

This directory contains the core dashboard functionality and data models for the PulzeBot application.

## Directory Structure

```
dashboard/
├── README.md                    # This file
├── __init__.py                  # Package initialization
├── admin.py                     # Django admin configuration
├── apps.py                      # Django app configuration
├── models.py                    # Core data models
├── services.py                  # Dashboard business logic
├── automation_service.py        # Automation and scheduling
├── early_warning_system.py      # Early warning alerts
├── health_views.py              # Health monitoring views
├── predictive_analytics.py      # Analytics and predictions
├── utils.py                     # Utility functions
├── views.py                     # Dashboard views
├── urls.py                      # URL routing
├── tests.py                     # Test suite
├── templatetags/                # Django template tags
└── migrations/
    ├── __init__.py
    └── 0001_initial.py          # Initial database migration
```

## Main Components

- **Models**: Core data models including `Project`, `StandupSession`, `TeamMember`, and analytics models
- **Services**: Business logic for dashboard operations and team analytics
- **Views**: Dashboard interfaces and team health monitoring
- **Tests**: Comprehensive test suite covering dashboard functionality