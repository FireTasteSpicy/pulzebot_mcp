"""
URL patterns for the integrations app.
Handles external service integrations (Jira, GitHub, etc.)
"""
from django.urls import path, include
from . import views

app_name = 'integrations'

urlpatterns = [    
    # API endpoints only (dashboard moved to settings)
    path('status/', views.integration_status, name='integration_status'),
    path('unified-context/', views.unified_context, name='unified_context'),
    path('team-metrics/', views.team_productivity_metrics, name='team_productivity_metrics'),
    
    # Jira-specific endpoints
    path('jira/', include([
        path('user-issues/', views.jira_user_issues, name='jira_user_issues'),
        path('sprint-info/', views.jira_sprint_info, name='jira_sprint_info'),
        path('project-metrics/', views.jira_project_metrics, name='jira_project_metrics'),
    ])),
    
    # GitHub endpoints
    path('github/', include([
        path('test/', views.github_test, name='github_test'),
        # Future: path('repos/', views.github_repos, name='github_repos'),
        # Future: path('pull-requests/', views.github_prs, name='github_prs'),
    ])),
]
