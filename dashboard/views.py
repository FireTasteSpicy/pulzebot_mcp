from django.views.generic import TemplateView, View
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.shortcuts import redirect
from django.utils import timezone
from django.db import models
from datetime import timedelta
import csv
import json

from integrations.services import IntegrationOrchestrationService
from .services import MVPTeamHealthService
from .models import Project, TeamHealthTrend, StandupSession, TeamMember, WorkItemReference, UserProfile, TeamHealthAlert, Blocker


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "dashboard/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Demo inputs for MVP
        demo_jira_ticket_ids = ['DEV-123', 'DEV-124', 'DEV-125']
        demo_github_repo = 'demo/project'
        demo_github_pr_numbers = [42]

        service = IntegrationOrchestrationService(use_mock_data=True)
        unified_context = service.get_unified_context(
            jira_ticket_ids=demo_jira_ticket_ids,
            github_repo=demo_github_repo,
            github_pr_numbers=demo_github_pr_numbers,
            user_email='john.doe@company.com',
        )

        # Surface summary counts for template cards
        jira_issues = unified_context.get('jira_data', {}).get('issues', []) or []
        github_prs = unified_context.get('github_data', {}).get('pull_requests', []) or []

        context.update({
            'integration_overview': {
                'jira_issues_count': len(jira_issues),
                'github_prs_count': len(github_prs),
                'sprint_info': unified_context.get('jira_data', {}).get('sprint_info', {}),
            },
            'jira_issues_sample': jira_issues[:3],
            'github_prs_sample': github_prs[:3],
        })

        # Stable UI metrics for header summary cards (no randomness)
        ui_metrics = {
            'totalStandups': 0,
            'avgSentiment': 0,
            'activeBlockers': 0,
            'teamMood': 7,
            'sprintProgress': 0,
        }

        try:
            if self.request.user.is_authenticated:
                # For demo: Always use the single active demo project
                project = Project.objects.filter(status='active').first()
                if not project:
                    project = Project.objects.filter(name='MVP Team Health Project').first()
                
                if project:
                    # Use daily data instead of 30-day data
                    today = timezone.now().date()
                    week_ago = today - timedelta(days=7)

                    # Today's standup sessions
                    today_sessions = StandupSession.objects.filter(
                        project=project,
                        date=today
                    )
                    
                    # Weekly sessions for broader context
                    weekly_sessions = StandupSession.objects.filter(
                        project=project,
                        date__gte=week_ago
                    )

                    ui_metrics['totalStandups'] = today_sessions.count()
                    # Count actual active Blocker objects (persistent across dates) for consistency
                    ui_metrics['activeBlockers'] = Blocker.objects.filter(
                        standup_session__project=project, 
                        status='active'
                    ).count()
                    
                    # Enhanced metrics from weekly data
                    ui_metrics['weeklyStandups'] = weekly_sessions.count()
                    ui_metrics['weeklyBlockers'] = weekly_sessions.exclude(blockers='').exclude(blockers__isnull=True).count()
                    
                    # Work items from past week
                    weekly_work_items = WorkItemReference.objects.filter(
                        standup_session__project=project,
                        standup_session__date__gte=week_ago
                    ).count()
                    ui_metrics['weeklyWorkItems'] = weekly_work_items

                    # Use BERT sentiment scores for Team Health (individual scores averaged)
                    bert_sessions = today_sessions.filter(sentiment_score__isnull=False)
                    
                    if bert_sessions.exists():
                        # Use individual BERT scores (already 0-1 scale) and convert to 0-10
                        individual_scores = [float(s.sentiment_score) for s in bert_sessions]
                        team_health_score = round(sum(individual_scores) / len(individual_scores) * 10, 1)
                        
                        ui_metrics['teamMood'] = team_health_score
                        ui_metrics['avgSentiment'] = team_health_score / 10
                        
                        # Team Health calculated from BERT individual scores
                        # print(f"Team Health from BERT: {team_health_score}/10 (from {len(individual_scores)} individual scores)")
                        # print(f"Individual BERT scores: {[round(s, 2) for s in individual_scores]}")
                    else:
                        # Fallback to mood labels if no BERT scores available
                        mood_mapping = {
                            'excited': 0.9, 'productive': 0.8, 'focused': 0.7, 'neutral': 0.5,
                            'tired': 0.35, 'frustrated': 0.25, 'blocked': 0.2, 'overwhelmed': 0.15,
                        }
                        mood_scores = [mood_mapping.get((s.sentiment_label or 'neutral').lower(), 0.5) * 10 
                                     for s in today_sessions]
                        if mood_scores:
                            ui_metrics['teamMood'] = round(sum(mood_scores) / len(mood_scores), 1)
                            ui_metrics['avgSentiment'] = ui_metrics['teamMood'] / 10
                        else:
                            ui_metrics['teamMood'] = 7.0
                            ui_metrics['avgSentiment'] = 0.7

            # Sprint progress from integration context if available
            sprint = context['integration_overview'].get('sprint_info') or {}
            total_sp = sprint.get('total_story_points') or 0
            completed_sp = sprint.get('completed_story_points') or 0
            if total_sp:
                ui_metrics['sprintProgress'] = int(round((completed_sp / total_sp) * 100))
        except Exception:
            # Keep defaults if any issue
            pass

        context['ui_metrics'] = ui_metrics
        context['now'] = timezone.now()
        
        # Add enhanced real data utilization
        if project:
            context.update(self._get_enhanced_dashboard_data(project))
        
        return context

    def _get_enhanced_dashboard_data(self, project):
        """Get enhanced dashboard data utilizing existing database content."""
        today = timezone.now().date()
        week_ago = today - timedelta(days=7)
        
        # Recent activity from actual standup sessions
        recent_sessions = StandupSession.objects.filter(
            project=project,
            date__gte=week_ago
        ).select_related('user').order_by('-date', '-created_at')[:10]
        
        # Work items from actual database
        recent_work_items = WorkItemReference.objects.filter(
            standup_session__project=project,
            standup_session__date__gte=week_ago
        ).select_related('standup_session__user').order_by('-created_at')[:8]
        
        
        # Team participation tracking
        team_members = TeamMember.objects.filter(project=project, is_active=True)
        team_size = team_members.count()
        
        # Today's participation
        today_participants = StandupSession.objects.filter(
            project=project,
            date=today
        ).values_list('user_id', flat=True)
        
        today_participation_rate = (len(today_participants) / max(team_size, 1)) * 100
        
        # Weekly participation
        weekly_sessions = StandupSession.objects.filter(
            project=project,
            date__gte=week_ago
        ).count()
        expected_weekly_sessions = team_size * 7  # Assuming daily standups
        weekly_participation_rate = (weekly_sessions / max(expected_weekly_sessions, 1)) * 100
        
        # Sentiment trends from actual data
        sentiment_data = StandupSession.objects.filter(
            project=project,
            date__gte=week_ago,
            sentiment_score__isnull=False
        ).values('date', 'sentiment_score', 'user__username')
        
        return {
            'recent_activity': recent_sessions,
            'recent_work_items': recent_work_items,
            'team_participation': {
                'today_rate': round(today_participation_rate, 1),
                'weekly_rate': round(weekly_participation_rate, 1),
                'team_size': team_size,
                'today_participants': len(today_participants),
            },
            'sentiment_trends': list(sentiment_data),
        }


class ManagerDashboardView(LoginRequiredMixin, TemplateView):
    """
    Manager-specific dashboard with aggregated insights, team health metrics, and productivity analytics.
    Research requirement: "Manager Dashboard, providing leadership with aggregated insights"
    """
    template_name = "dashboard/manager_dashboard.html"
    
    def dispatch(self, request, *args, **kwargs):
        """Ensure auth, then check manager privileges."""
        if not request.user.is_authenticated:
            return redirect('authentication:login')
        try:
            profile = UserProfile.objects.get(user=request.user)
            if not profile.is_manager:
                messages.error(request, "Access denied. Manager privileges required.")
                return redirect('dashboard:dashboard')
        except UserProfile.DoesNotExist:
            messages.error(request, "User profile not found. Please contact administrator.")
            return redirect('dashboard:dashboard')
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        try:
            profile = UserProfile.objects.get(user=user)
            
            # For demo: Always use the single demo project
            demo_project = Project.objects.filter(status='active').first()
            if not demo_project:
                demo_project = Project.objects.filter(name='MVP Team Health Project').first()
            
            if demo_project:
                projects = [demo_project]
            else:
                projects = []
            
            # Aggregate team health metrics
            team_health_summary = self._get_team_health_summary(projects)
            
            # Active alerts requiring management attention
            active_alerts = TeamHealthAlert.objects.filter(
                project__in=projects,
                status='active'
            ).order_by('-severity', '-created_at')
            
            # Critical metrics across teams
            critical_metrics = self._get_critical_metrics(projects)
            
            # Productivity trends
            productivity_trends = self._get_productivity_trends(projects)
            
            # Team performance comparison
            team_comparison = self._get_team_comparison(projects)
            
            context.update({
                'user_profile': profile,
                'managed_projects': projects,
                'team_health_summary': team_health_summary,
                'active_alerts': active_alerts,
                'critical_alerts_count': active_alerts.filter(severity__in=['high', 'critical']).count(),
                'critical_metrics': critical_metrics,
                'productivity_trends': productivity_trends,
                'team_comparison': team_comparison,
                'can_view_cross_team': False,  # Single project management - no cross-team view needed
            })
            
        except (UserProfile.DoesNotExist, TeamMember.DoesNotExist):
            context['access_error'] = True
            
        return context
    
    def _get_team_health_summary(self, projects):
        """Get aggregated team health metrics."""
        if not projects:
            return {}
            
        # Get today's standup sessions across all managed projects (daily data)
        today = timezone.now().date()
        recent_sessions = StandupSession.objects.filter(
            project__in=projects,
            date=today
        )
        
        # Calculate aggregated metrics using BERT sentiment scores
        total_sessions = recent_sessions.count()
        bert_sessions = recent_sessions.filter(sentiment_score__isnull=False)
        
        if bert_sessions.exists():
            # Use individual BERT scores (already 0-1 scale) and convert to 0-10
            individual_scores = [float(s.sentiment_score) for s in bert_sessions]
            team_mood = round(sum(individual_scores) / len(individual_scores) * 10, 1)
            avg_sentiment = team_mood / 10
        else:
            # Fallback to mood labels if no BERT scores available
            mood_mapping = {
                'excited': 0.9, 'productive': 0.8, 'focused': 0.7, 'neutral': 0.5,
                'tired': 0.35, 'frustrated': 0.25, 'blocked': 0.2, 'overwhelmed': 0.15,
            }
            mood_scores = [mood_mapping.get((s.sentiment_label or 'neutral').lower(), 0.5) * 10 
                         for s in recent_sessions]
            if mood_scores:
                team_mood = round(sum(mood_scores) / len(mood_scores), 1)
                avg_sentiment = team_mood / 10
            else:
                team_mood = 7.0
                avg_sentiment = 0.7
            
        active_blockers = recent_sessions.filter(blockers__isnull=False).exclude(blockers='').count()
        
        # Team engagement metrics
        team_members_count = TeamMember.objects.filter(project__in=projects, is_active=True).count()
        participation_rate = (total_sessions / max(team_members_count * 30, 1)) * 100 if team_members_count > 0 else 0
        
        return {
            'total_sessions': total_sessions,
            'avg_sentiment': round(avg_sentiment, 2),
            'sentiment_score': team_mood,  # Use consistent team mood calculation
            'active_blockers': active_blockers,
            'team_members_count': team_members_count,
            'participation_rate': round(participation_rate, 1),
            'projects_count': len(projects),
        }
    
    def _get_critical_metrics(self, projects):
        """Get metrics requiring immediate attention."""
        if not projects:
            return []
            
        metrics = []
        
        for project in projects:
            recent_sessions = StandupSession.objects.filter(
                project=project,
                date__gte=timezone.now().date() - timedelta(days=7),
                status='completed'
            )
            
            if recent_sessions.count() == 0:
                continue
                
            # Check for concerning trends
            avg_sentiment = recent_sessions.aggregate(avg_sentiment=models.Avg('sentiment_score'))['avg_sentiment']
            blocker_sessions = recent_sessions.filter(blockers__isnull=False).exclude(blockers='').count()
            
            if avg_sentiment and avg_sentiment < -0.3:  # Negative sentiment
                metrics.append({
                    'project': project.name,
                    'type': 'sentiment',
                    'value': round(avg_sentiment, 2),
                    'description': 'Team sentiment declining',
                    'severity': 'high' if avg_sentiment < -0.5 else 'medium'
                })
            
            if blocker_sessions > recent_sessions.count() * 0.5:  # >50% sessions have blockers
                metrics.append({
                    'project': project.name,
                    'type': 'blockers',
                    'value': blocker_sessions,
                    'description': f'{blocker_sessions} sessions with blockers',
                    'severity': 'high'
                })
        
        return metrics
    
    def _get_productivity_trends(self, projects):
        """Get productivity trend data for charts."""
        if not projects:
            return {}
            
        # Get last 30 days of data
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=30)
        
        trends = {}
        for project in projects:
            daily_data = []
            for i in range(30):
                date = start_date + timedelta(days=i)
                sessions = StandupSession.objects.filter(
                    project=project,
                    date=date,
                    status='completed'
                )
                
                daily_data.append({
                    'date': date.strftime('%Y-%m-%d'),
                    'sessions_count': sessions.count(),
                    'avg_sentiment': sessions.aggregate(avg=models.Avg('sentiment_score'))['avg'] or 0,
                    'blockers_count': sessions.filter(blockers__isnull=False).exclude(blockers='').count()
                })
            
            trends[project.name] = daily_data
            
        return trends
    
    def _get_team_comparison(self, projects):
        """Compare performance across teams."""
        if not projects:
            return []
            
        comparison = []
        for project in projects:
            recent_sessions = StandupSession.objects.filter(
                project=project,
                date__gte=timezone.now().date() - timedelta(days=14),
                status='completed'
            )
            
            team_size = TeamMember.objects.filter(project=project, is_active=True).count()
            avg_sentiment = recent_sessions.aggregate(avg=models.Avg('sentiment_score'))['avg'] or 0
            blocker_rate = (recent_sessions.filter(blockers__isnull=False).exclude(blockers='').count() / 
                          max(recent_sessions.count(), 1)) * 100
            
            comparison.append({
                'project_name': project.name,
                'team_size': team_size,
                'sessions_count': recent_sessions.count(),
                'avg_sentiment': round(avg_sentiment, 2),
                'sentiment_score': max(0, min(10, (avg_sentiment + 1) * 5)),
                'blocker_rate': round(blocker_rate, 1),
                'health_score': max(0, min(100, 50 + (avg_sentiment * 30) - (blocker_rate * 0.5)))
            })
            
        return sorted(comparison, key=lambda x: x['health_score'], reverse=True)





class ExportReportView(LoginRequiredMixin, View):
    """View to export a CSV report of the dashboard data."""
    def get(self, request, *args, **kwargs):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="standup_report.csv"'

        writer = csv.writer(response)
        writer.writerow(['Type', 'ID', 'Title', 'Status'])

        # In a real application, we would fetch this data from the service
        jira_issues = [{"key": "PROJ-1", "summary": "Test Issue 1", "status": "In Progress"}]
        github_prs = [{"number": 1, "title": "Test PR 1", "state": "open"}]

        for issue in jira_issues:
            writer.writerow(['Jira', issue['key'], issue['summary'], issue['status']])
        for pr in github_prs:
            writer.writerow(['GitHub', pr['number'], pr['title'], pr['state']])

        return response











class ExportReportView(LoginRequiredMixin, View):
    """View to export a CSV report of the dashboard data."""
    def get(self, request, *args, **kwargs):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="standup_report.csv"'

        writer = csv.writer(response)
        writer.writerow(['Type', 'ID', 'Title', 'Status'])

        # In a real application, we would fetch this data from the service
        jira_issues = [{"key": "PROJ-1", "summary": "Test Issue 1", "status": "In Progress"}]
        github_prs = [{"number": 1, "title": "Test PR 1", "state": "open"}]

        for issue in jira_issues:
            writer.writerow(['Jira', issue['key'], issue['summary'], issue['status']])
        for pr in github_prs:
            writer.writerow(['GitHub', pr['number'], pr['title'], pr['state']])

        return response

















# ===== HEALTH CHECK VIEWS =====
# Consolidated from health_views.py

import logging

logger = logging.getLogger(__name__)


@csrf_exempt
@require_http_methods(["GET"])
def health_check(request):
    """
    Comprehensive health check endpoint.
    
    Returns:
        JsonResponse: Health status of various components
    """
    from django.db import connections
    from django.core.cache import cache
    
    health_data = {
        'status': 'healthy',
        'version': '1.0.0',
        'timestamp': timezone.now().isoformat(),
        'checks': {
            'database': False,
            'cache': False
        }
    }
    
    # Database check
    try:
        db_conn = connections['default']
        db_conn.cursor()
        health_data['checks']['database'] = True
        logger.info("Database health check passed")
    except Exception as e:
        health_data['checks']['database'] = False
        health_data['status'] = 'unhealthy'
        logger.error(f"Database health check failed: {str(e)}")
    
    # Cache check (dummy cache always works)
    try:
        cache.set('health_check', 'test', 10)
        cache.get('health_check')
        health_data['checks']['cache'] = True
        logger.info("Cache health check passed")
    except Exception as e:
        health_data['checks']['cache'] = False
        health_data['status'] = 'degraded'
        logger.error(f"Cache health check failed: {str(e)}")
    
    # Determine overall status
    if not health_data['checks']['database']:
        status_code = 503  # Service Unavailable
    elif not health_data['checks']['cache']:
        status_code = 503  # Service Unavailable (degraded)
        health_data['status'] = 'degraded'
    else:
        status_code = 200
    
    return JsonResponse(health_data, status=status_code)


@csrf_exempt
@require_http_methods(["GET"])
def liveness_probe(request):
    """
    Kubernetes liveness probe endpoint.
    Simple check to verify the application is running.
    """
    return JsonResponse({
        'status': 'alive',
        'timestamp': timezone.now().isoformat()
    })


@csrf_exempt
@require_http_methods(["GET"])
def readiness_probe(request):
    """
    Kubernetes readiness probe endpoint.
    Check if the application is ready to serve traffic.
    """
    from django.db import connections
    
    try:
        # Quick database check
        db_conn = connections['default']
        db_conn.cursor()
        
        return JsonResponse({
            'status': 'ready',
            'timestamp': timezone.now().isoformat()
        })
    except Exception as e:
        return JsonResponse({
            'status': 'not_ready',
            'error': str(e),
            'timestamp': timezone.now().isoformat()
        }, status=503)


@csrf_exempt
@require_http_methods(["GET"])
def metrics(request):
    """
    Basic metrics endpoint for monitoring.
    """
    from django.db import connections
    
    try:
        # Get basic metrics
        metrics_data = {
            'timestamp': timezone.now().isoformat(),
            'application': 'pulzebot',
            'version': '1.0.0',
            'database_connections': len(connections.all()),
            'active_users': 0,  # Would implement actual user count
            'total_standups': 0,  # Would implement actual standup count
        }
        
        return JsonResponse(metrics_data)
    except Exception as e:
        return JsonResponse({
            'error': str(e),
            'timestamp': timezone.now().isoformat()
        }, status=500)

# TeamHealthDemoView removed - team_health app no longer used
