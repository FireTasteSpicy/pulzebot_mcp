# AI Processing Directory

This directory contains the AI processing functionality for the PulzeBot application.

## Directory Structure

```
ai_processing/
├── README.md                    # This file
├── __init__.py                  # Package initialization
├── admin.py                     # Django admin configuration
├── apps.py                      # Django app configuration
├── models.py                    # Database models
├── services.py                  # Main services interface
├── sentiment_service.py         # Sentiment analysis service
├── summary_service.py           # AI summary generation service
├── speech_service.py            # Speech-to-text processing
├── parsing_service.py           # Standup parsing service
├── orchestration_service.py     # Main AI orchestration service
├── utils.py                     # Utility functions
├── views.py                     # API views
├── urls.py                      # URL routing
├── tests.py                     # Test suite
└── migrations/
    ├── __init__.py
    └── 0001_initial.py          # Initial database migration
```

## Main Components

- **Models**: `AIProcessingResult` for storing AI processing outcomes
- **Services**: Modular AI services for sentiment analysis, summarization, speech processing, and parsing
- **Views**: REST API endpoints for AI processing requests
- **Tests**: Comprehensive test suite covering all AI processing functionality
