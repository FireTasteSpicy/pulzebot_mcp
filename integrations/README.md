# Integrations Directory

This directory contains external service integrations for GitHub and Jira in the PulzeBot application.

## Directory Structure

```
integrations/
├── README.md                    # This file
├── __init__.py                  # Package initialization
├── admin.py                     # Django admin configuration
├── apps.py                      # Django app configuration
├── models.py                    # Integration data models
├── services.py                  # Consolidated integration services
├── views.py                     # Integration API views
├── urls.py                      # URL routing
├── tests.py                     # Test suite
└── migrations/
    ├── __init__.py
    └── 0001_initial.py          # Initial database migration
```

## Main Components

- **Models**: Integration models for external service connections and work item tracking
- **Services**: `GitHubService`, `JiraService`, and `WorkItemExtractor` for external API integration
- **Views**: API endpoints for integration management and status checking
- **Tests**: Comprehensive test suite covering integration functionality