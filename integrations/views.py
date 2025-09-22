"""
Views for external integrations API endpoints.
"""
import logging
from datetime import datetime
from typing import Dict, Any

from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .services import JiraService, GitHubService, IntegrationOrchestrationService
from .models import ExternalIntegration, JiraIntegration, GitHubIntegration

logger = logging.getLogger(__name__)




@api_view(['GET'])
@permission_classes([AllowAny])
def jira_user_issues(request):
    """
    API endpoint to get Jira issues for a specific user.
    """
    try:
        user_email = request.GET.get('user_email', 'john.doe@company.com')
        project_key = request.GET.get('project_key')
        use_mock = request.GET.get('use_mock', 'true').lower() == 'true'
        
        jira_service = JiraService(use_mock_data=use_mock)
        issues = jira_service.get_issues_for_user(user_email, project_key)
        
        return Response({
            'success': True,
            'user_email': user_email,
            'project_key': project_key,
            'issues_count': len(issues),
            'issues': issues,
            'using_mock_data': use_mock
        })
        
    except Exception as e:
        logger.error(f"Error fetching Jira user issues: {e}")
        return Response({
            'success': False,
            'error': str(e),
            'issues': []
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def jira_sprint_info(request):
    """
    API endpoint to get current sprint information.
    """
    try:
        board_id = request.GET.get('board_id')
        use_mock = request.GET.get('use_mock', 'true').lower() == 'true'
        
        jira_service = JiraService(use_mock_data=use_mock)
        sprint_info = jira_service.get_sprint_info(
            board_id=int(board_id) if board_id else None
        )
        
        return Response({
            'success': True,
            'board_id': board_id,
            'sprint_info': sprint_info,
            'using_mock_data': use_mock
        })
        
    except Exception as e:
        logger.error(f"Error fetching sprint info: {e}")
        return Response({
            'success': False,
            'error': str(e),
            'sprint_info': {}
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def jira_project_metrics(request):
    """
    API endpoint to get project-level metrics.
    """
    try:
        project_key = request.GET.get('project_key', 'DEV')
        use_mock = request.GET.get('use_mock', 'true').lower() == 'true'
        
        jira_service = JiraService(use_mock_data=use_mock)
        metrics = jira_service.get_project_metrics(project_key)
        
        return Response({
            'success': True,
            'project_key': project_key,
            'metrics': metrics,
            'using_mock_data': use_mock
        })
        
    except Exception as e:
        logger.error(f"Error fetching project metrics: {e}")
        return Response({
            'success': False,
            'error': str(e),
            'metrics': {}
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def unified_context(request):
    """
    API endpoint to get unified context from all integrated services.
    """
    try:
        data = request.data
        jira_ticket_ids = data.get('jira_ticket_ids', [])
        github_repo = data.get('github_repo')
        github_pr_numbers = data.get('github_pr_numbers', [])
        user_email = data.get('user_email', 'john.doe@company.com')
        use_mock = data.get('use_mock', True)
        
        orchestration_service = IntegrationOrchestrationService(use_mock_data=use_mock)
        context = orchestration_service.get_unified_context(
            jira_ticket_ids=jira_ticket_ids,
            github_repo=github_repo,
            github_pr_numbers=github_pr_numbers,
            user_email=user_email
        )
        
        return Response({
            'success': True,
            'context': context,
            'using_mock_data': use_mock
        })
        
    except Exception as e:
        logger.error(f"Error fetching unified context: {e}")
        return Response({
            'success': False,
            'error': str(e),
            'context': {}
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def team_productivity_metrics(request):
    """
    API endpoint to get team productivity metrics across platforms.
    """
    try:
        team_emails = request.GET.getlist('team_emails')
        if not team_emails:
            team_emails = [
                'john.doe@company.com',
                'jane.smith@company.com', 
                'bob.wilson@company.com'
            ]
        
        days = int(request.GET.get('days', 30))
        use_mock = request.GET.get('use_mock', 'true').lower() == 'true'
        
        orchestration_service = IntegrationOrchestrationService(use_mock_data=use_mock)
        metrics = orchestration_service.get_team_productivity_metrics(team_emails, days)
        
        return Response({
            'success': True,
            'team_emails': team_emails,
            'period_days': days,
            'metrics': metrics,
            'using_mock_data': use_mock
        })
        
    except Exception as e:
        logger.error(f"Error fetching team productivity metrics: {e}")
        return Response({
            'success': False,
            'error': str(e),
            'metrics': {}
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def integration_status(request):
    """
    API endpoint to get status of all configured integrations including user-specific Jira and GitHub settings.
    """
    try:
        # Get user-specific integrations if authenticated
        user = request.user if request.user.is_authenticated else None
        
        # Initialise response data
        integrations_data = {
            'jira': {
                'enabled': False,
                'connected': False,
                'serverUrl': '',
                'username': '',
                'projectKey': ''
            },
            'github': {
                'enabled': False,
                'connected': False,
                'org': '',
                'defaultRepo': '',
                'branchFilter': 'main,develop'
            }
        }
        
        if user:
            # Get user settings for integration status
            try:
                from user_settings.models import UserSettings
                user_settings = UserSettings.objects.get(user=user)
                integrations_data['jira'] = {
                    'enabled': user_settings.jira_integration_enabled,
                    'connected': user_settings.jira_connected,
                    'serverUrl': '',  # Not stored in UserSettings
                    'username': '',   # Not stored in UserSettings
                    'projectKey': ''  # Not stored in UserSettings
                }
                integrations_data['github'] = {
                    'enabled': user_settings.github_integration_enabled,
                    'connected': user_settings.github_connected,
                    'org': '',        # Not stored in UserSettings
                    'defaultRepo': '', # Not stored in UserSettings
                    'branchFilter': 'main,develop'
                }
            except UserSettings.DoesNotExist:
                pass
        
        # Legacy support for old ExternalIntegration model
        integrations = ExternalIntegration.objects.all()
        integration_status = []
        
        for integration in integrations:
            status_data = {
                'id': integration.id,
                'platform': integration.platform,
                'name': integration.name,
                'status': integration.status,
                'is_active': integration.is_active,
                'last_sync': integration.last_sync.isoformat() if integration.last_sync else None,
                'error_message': integration.error_message,
                'created_at': integration.created_at.isoformat(),
                'updated_at': integration.updated_at.isoformat()
            }
            
            # Add platform-specific data
            if integration.platform == 'jira' and hasattr(integration, 'jira_integration'):
                status_data['jira_config'] = {
                    'project_key': integration.jira_integration.project_key,
                    'username': integration.jira_integration.username,
                    'board_id': integration.jira_integration.board_id
                }
            elif integration.platform == 'github' and hasattr(integration, 'github_integration'):
                status_data['github_config'] = {
                    'repository': integration.github_integration.repository,
                    'owner': integration.github_integration.owner,
                    'branch': integration.github_integration.branch
                }
            
            integration_status.append(status_data)
        
        return Response({
            'success': True,
            'jira': integrations_data['jira'],
            'github': integrations_data['github'],
            'integrations': integration_status,  # Legacy support
            'total_integrations': len(integration_status),
            'active_integrations': len([i for i in integrations_data.values() if i.get('enabled')]) + len([i for i in integration_status if i['is_active']])
        })
        
    except Exception as e:
        logger.error(f"Error fetching integration status: {e}")
        return Response({
            'success': False,
            'error': str(e),
            'integrations': []
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)






@api_view(['POST'])
@permission_classes([AllowAny])
def github_test(request):
    """
    Test GitHub connection endpoint.
    """
    try:
        data = request.data if hasattr(request, 'data') else {}
        
        # For now, return a mock success response
        # In a real implementation, this would test the GitHub API connection
        return Response({
            'success': True,
            'message': 'GitHub connection test successful (mock)',
            'data': {
                'org': data.get('org', ''),
                'repo_count': 42,  # Mock data
                'user_info': 'Mock GitHub User'
            }
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"GitHub connection test failed: {e}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
