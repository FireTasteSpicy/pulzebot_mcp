# Authentication Directory

This directory contains authentication and authorization functionality for the PulzeBot application.

## Directory Structure

```
authentication/
├── README.md                    # This file
├── __init__.py                  # Package initialization
├── apps.py                      # Django app configuration
├── views.py                     # Authentication views and logic
├── urls.py                      # URL routing patterns
└── tests.py                     # Test suite
```

## Main Components

- **Views**: `CustomLoginView`, `RoleBasedRedirectView` for role-based authentication and redirection
- **Authentication**: Enhanced login/logout with automatic dashboard routing based on user roles
- **Access Control**: Permission handling and access denied error pages
- **Tests**: Comprehensive test suite covering authentication functionality