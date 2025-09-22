# Config Directory

This directory contains the core Django configuration and project setup for the PulzeBot application.

## Directory Structure

```
config/
├── README.md                    # This file
├── __init__.py                  # Package initialization
├── settings.py                  # Main Django settings
├── test_settings.py             # Test-specific settings
├── urls.py                      # Root URL configuration
├── wsgi.py                      # WSGI application entry point
├── asgi.py                      # ASGI application entry point
└── tests.py                     # Test suite
```

## Main Components

- **Settings**: Main Django configuration with environment-based setup
- **URL Configuration**: Root URL routing with all app integration
- **WSGI/ASGI**: Application entry points for deployment
- **Tests**: Configuration and routing validation test suite