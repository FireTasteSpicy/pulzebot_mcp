# PulzeBot - AI-Powered Standup Meeting Assistant

PulzeBot is an intelligent standup meeting facilitation system that orchestrates multiple AI models (Whisper, BERT, Gemini 2.0 Flash) to enhance daily agile standup meetings for remote and hybrid development teams. Built with Django 5.0.2 and featuring a clean, modular architecture with comprehensive test coverage.

## Key Features

### AI-Powered Processing
- **Speech-to-Text**: OpenAI Whisper integration for voice standup submissions
- **Sentiment Analysis**: BERT-based mood detection and team health monitoring  
- **Smart Summaries**: Gemini 2.0 Flash generates contextual AI insights
- **Work Item Intelligence**: Automatic GitHub/Jira ticket extraction and correlation

### Team Analytics & Insights
- **Real-time Dashboard**: Interactive team health monitoring with trend analysis
- **Predictive Analytics**: Early warning system for burnout and productivity risks
- **Integration Hub**: Unified GitHub and Jira context gathering
- **Privacy Controls**: GDPR-compliant consent management and data protection

### Demo & Development Features
- **Demo Mode**: Fixed date/time (September 22, 2025 23:59) for consistent demonstrations
- **Mock Data Integration**: Realistic GitHub/Jira simulation when APIs not configured
- **Visual Demo Indicators**: Clear UI indicators when demo mode is active

## Architecture Overview

### Clean Django Structure
```
pulzebot_mcp/
├── ai_processing/          # AI model orchestration (Whisper, BERT, Gemini)
├── dashboard/             # Core data models and team analytics
├── integrations/          # GitHub/Jira external service connectors
├── standup/              # Standup meeting management
├── user_settings/        # Privacy controls and user preferences
├── authentication/       # Role-based access and security
├── config/               # Django project configuration
├── templates/            # Frontend templates (Bootstrap 5 + Alpine.js)
└── static/               # CSS, JavaScript, and asset files
```

### AI Processing Pipeline
1. **Input Processing** - Multi-modal input (text/voice) validation
2. **AI Analysis** - Parallel Whisper, BERT, and Gemini processing
3. **Work Item Extraction** - Intelligent GitHub/Jira reference parsing
4. **Context Aggregation** - Historical data and team metrics compilation
5. **Dashboard Updates** - Real-time analytics and health monitoring
6. **Notification System** - Automated alerts and early warning triggers

## Prerequisites

### System Requirements
- **Python 3.11+** (3.10+ supported)
- **Node.js 16+** (for frontend development)
- **Git** for version control

### Required API Keys
- **Google Gemini API Key** - For AI summary generation
- **OpenAI API Key**: For Whisper processing

### Database Options
- **SQLite** (default, no setup required)
- **PostgreSQL** (recommended for production)

## Quick Start

### 1. Clone and Setup

```bash
git clone https://github.com/firetastespicy/pulzebot_mcp.git
cd pulzebot_mcp
```

### 2. Environment Setup

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configuration

Create `.env` file with your API keys:

```bash
# Django Settings
SECRET_KEY=django-insecure-development-key-change-in-production
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Demo Mode - Fix date to September 22, 2025 23:59
DEMO_MODE_ENABLED=True

# Database
DATABASE_URL=sqlite:///db.sqlite3

# AI API Keys (Required for full functionality)
GEMINI_API_KEY=your-gemini-api-key-here
OPENAI_API_KEY=your-openai-api-key-here
WHISPER_MODEL=base.en

# Development Settings
DJANGO_SETTINGS_MODULE=pulzebot.settings

# External Integrations (Optional - uses mock data if not provided)
GITHUB_TOKEN=your-github-token
JIRA_SERVER=https://your-jira-instance.atlassian.net
JIRA_USERNAME=your-email@example.com
JIRA_API_TOKEN=your-api-token
```

### 4. Initialise Database

```bash
# Run migrations
python manage.py migrate

# Create admin user
python manage.py createsuperuser

# Load sample data (optional)
python manage.py loaddata sample_data.json
```

### 5. Launch Application

```bash
# Start development server
python manage.py runserver

# Access the application
# Main App: http://localhost:8000
# Admin Panel: http://localhost:8000/admin/
```

## Configuration

### Environment Variables

Key environment variables to configure in your `.env` file:

```bash
# Django Core Settings
SECRET_KEY=django-insecure-development-key-change-in-production
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1,your-domain.com
DJANGO_SETTINGS_MODULE=pulzebot.settings

# Demo Mode Configuration (NEW)
DEMO_MODE_ENABLED=True  # Fixes date to September 22, 2025 23:59 for demos

# Database Configuration
DATABASE_URL=sqlite:///db.sqlite3  # Development default
# DATABASE_URL=postgresql://username:password@localhost:5432/pulzebot  # Production

# AI Service APIs (Required)
GEMINI_API_KEY=your-gemini-api-key-here     # Required for AI summaries
OPENAI_API_KEY=your-openai-api-key-here     # Required for Whisper transcription
WHISPER_MODEL=base.en                        # Options: base, small, medium, large

# External Integrations (Optional - uses mock data when not configured)
GITHUB_TOKEN=your-github-token                              # For GitHub integration
JIRA_SERVER=https://your-jira-instance.atlassian.net      # Your Jira instance URL
JIRA_USERNAME=your-email@example.com                       # Jira account email
JIRA_API_TOKEN=your-api-token                             # Jira API token
```

### MVP Configuration Notes
- **Database**: Uses SQLite by default
- **Caching**: Uses dummy cache
- **Tasks**: Synchronous processing
- **Sessions**: Database-backed
- **Demo Mode**: Enabled by default - fixes date to September 22, 2025 at 23:59 for consistent demos
- **Mock Integration**: Uses simulated GitHub/Jira data when API tokens not configured 

### AI Models Configuration

- **Whisper**: Uses OpenAI Whisper for speech-to-text conversion
- **BERT**: nlptown/bert-base-multilingual-uncased-sentiment for sentiment analysis
- **Gemini**: Google's Gemini 2.0 Flash for intelligent summarization

## API Reference

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/auth/login/` | User authentication with credentials |
| `POST` | `/auth/logout/` | Secure user logout |
| `GET` | `/auth/status/` | Authentication status check |

### Health Monitoring
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health/` | Complete system health check |
| `GET` | `/health/live/` | Kubernetes liveness probe |
| `GET` | `/health/ready/` | Kubernetes readiness probe |
| `GET` | `/metrics/` | Application performance metrics |

### AI Processing Pipeline
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/ai/transcribe/` | Convert audio to text using Whisper |
| `POST` | `/api/ai/analyse-sentiment/` | BERT-powered sentiment analysis |
| `POST` | `/api/ai/generate-summary/` | Gemini 2.0 Flash summarization |
| `GET` | `/api/ai/status/` | AI service health status |

### Dashboard & Analytics
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/dashboard/` | Main interactive dashboard |
| `GET` | `/dashboard/metrics/` | Real-time dashboard metrics |
| `GET` | `/standup/reports/` | Standup meeting reports |
| `GET` | `/dashboard/analytics/` | Team performance analytics |

### Integration Management
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/integrations/slack/webhook/` | Slack event handler |
| `POST` | `/integrations/teams/webhook/` | Microsoft Teams integration |
| `GET` | `/integrations/status/` | Integration connectivity status |
| `POST` | `/integrations/configure/` | Setup new platform integration |

## Deployment Options

### Docker Development
```bash
# Quick start with Docker Compose
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Production Deployment

#### Railway Platform
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login and deploy
railway login
railway link
railway up
```

#### Manual Docker
```bash
# Build production image
docker build -t pulzebot:latest .

# Run with production settings
docker run -d \
  -p 8000:8000 \
  -e DJANGO_SETTINGS_MODULE=config.settings \
  -e DATABASE_URL=your-db-url \
  -e GEMINI_API_KEY=your-api-key \
  pulzebot:latest
```

#### Environment Variables
```bash
# Required for production
SECRET_KEY=your-secret-key
GEMINI_API_KEY=your-gemini-api-key
DATABASE_URL=postgresql://user:pass@host:port/db

# Production configuration
DEBUG=False
DEMO_MODE_ENABLED=False  # Disable demo mode for production
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
CORS_ALLOWED_ORIGINS=https://yourdomain.com
## Testing

### Run Test Suite
```bash
# Run all tests (87 comprehensive tests)
python manage.py test

# Run with coverage reporting
pip install coverage
coverage run --source='.' manage.py test
coverage report -m

# Run specific app tests
python manage.py test ai_processing
python manage.py test dashboard
python manage.py test integrations
python manage.py test standup
python manage.py test user_settings
```

### Test Categories
- **Unit Tests**: Model and service layer validation
- **Integration Tests**: API endpoint functionality 
- **AI Pipeline Tests**: Transcription, sentiment, summarization
- **Dashboard Tests**: Metrics and analytics validation
- **Authentication Tests**: Security and user management

## Project Documentation

### Directory Documentation
- [`ai_processing/`](ai_processing/README.md) - AI pipeline and processing services
- [`authentication/`](authentication/README.md) - User authentication system
- [`dashboard/`](dashboard/README.md) - Analytics dashboard and metrics
- [`integrations/`](integrations/README.md) - Third-party platform integrations
- [`standup/`](standup/README.md) - Standup meeting management
- [`user_settings/`](user_settings/README.md) - User preferences and privacy