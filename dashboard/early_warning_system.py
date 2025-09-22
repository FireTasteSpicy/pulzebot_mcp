"""
Early Warning System for Team Health Issues
Proactive notification system for negative team health trends.
Research requirement: "early warning systems for team health issues"
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from django.utils import timezone
from config.demo_time import now as demo_now
from django.db.models import Avg, Count, Q, Max, Min
from django.contrib.auth.models import User
from collections import defaultdict, Counter

from .models import (
    StandupSession, Project, TeamMember, TeamHealthAlert, 
    UserProfile, WorkItemReference
)

logger = logging.getLogger(__name__)


class EarlyWarningSystem:
    """
    Early warning system for proactive team health monitoring.
    Research requirement: "early warning systems for team health issues"
    """
    
    # Alert thresholds
    SENTIMENT_DECLINE_THRESHOLD = -0.3  # Sentiment below this triggers alert
    SENTIMENT_TREND_THRESHOLD = -0.2    # Declining trend threshold
    BLOCKER_FREQUENCY_THRESHOLD = 0.5   # 50% of sessions having blockers
    PARTICIPATION_THRESHOLD = 0.6       # 60% participation rate
    BURNOUT_INDICATOR_THRESHOLD = 3     # Number of negative indicators for burnout
    
    def __init__(self):
        self.alert_processors = {
            'sentiment_decline': self._check_sentiment_decline,
            'engagement_drop': self._check_engagement_drop,
            'blocker_increase': self._check_blocker_increase,
            'productivity_concern': self._check_productivity_concern,
            'team_member_burnout': self._check_team_member_burnout,
            'communication_gap': self._check_communication_gap,
        }
        
    def run_health_monitoring(self, project: Project = None) -> Dict[str, Any]:
        """
        Run comprehensive health monitoring for projects.
        """
        projects_to_monitor = [project] if project else Project.objects.filter(status='active')
        
        monitoring_results = {
            'projects_monitored': len(projects_to_monitor),
            'alerts_generated': 0,
            'critical_alerts': 0,
            'warnings_issued': 0,
            'projects_at_risk': [],
            'detailed_results': []
        }
        
        for proj in projects_to_monitor:
            try:
                project_results = self._monitor_project_health(proj)
                monitoring_results['detailed_results'].append(project_results)
                
                # Aggregate statistics
                alerts_generated = len(project_results['alerts_generated'])
                monitoring_results['alerts_generated'] += alerts_generated
                
                critical_alerts = len([a for a in project_results['alerts_generated'] 
                                     if a.get('severity') == 'critical'])
                monitoring_results['critical_alerts'] += critical_alerts
                
                if alerts_generated > 0:
                    monitoring_results['projects_at_risk'].append({
                        'project': proj.name,
                        'alerts': alerts_generated,
                        'critical': critical_alerts
                    })
                    
            except Exception as e:
                logger.error(f"Error monitoring project {proj.name}: {e}")
                
        return monitoring_results
    
    def _monitor_project_health(self, project: Project) -> Dict[str, Any]:
        """Monitor health for a specific project."""
        project_results = {
            'project': project.name,
            'project_id': project.id,
            'monitoring_timestamp': demo_now(),
            'alerts_generated': [],
            'risk_indicators': [],
            'team_status': {}
        }
        
        # Run all alert checks
        for alert_type, checker_func in self.alert_processors.items():
            try:
                alerts = checker_func(project)
                if alerts:
                    project_results['alerts_generated'].extend(alerts)
                    
            except Exception as e:
                logger.error(f"Error running {alert_type} check for {project.name}: {e}")
        
        # Analyse overall team status
        project_results['team_status'] = self._analyse_team_status(project)
        
        return project_results
    
    def _check_sentiment_decline(self, project: Project) -> List[Dict[str, Any]]:
        """Check for declining team sentiment."""
        alerts = []
        
        # Get recent sentiment data (last 14 days)
        end_date = demo_now().date()
        start_date = end_date - timedelta(days=14)
        
        recent_sessions = StandupSession.objects.filter(
            project=project,
            date__gte=start_date,
            status='completed',
            sentiment_score__isnull=False
        )
        
        if recent_sessions.count() < 5:  # Need minimum data
            return alerts
        
        # Calculate current average sentiment
        avg_sentiment = recent_sessions.aggregate(avg=Avg('sentiment_score'))['avg']
        
        # Calculate trend (first half vs second half)
        mid_date = start_date + timedelta(days=7)
        older_sentiment = recent_sessions.filter(date__lt=mid_date).aggregate(avg=Avg('sentiment_score'))['avg']
        newer_sentiment = recent_sessions.filter(date__gte=mid_date).aggregate(avg=Avg('sentiment_score'))['avg']
        
        # Check for absolute low sentiment
        if avg_sentiment and avg_sentiment < self.SENTIMENT_DECLINE_THRESHOLD:
            severity = 'critical' if avg_sentiment < -0.5 else 'high'
            
            alert = self._create_alert(
                project=project,
                alert_type='sentiment_decline',
                severity=severity,
                title=f"Team Sentiment Critical: {avg_sentiment:.2f}",
                description=f"Team sentiment has dropped to {avg_sentiment:.2f}, indicating potential morale issues requiring immediate attention.",
                confidence_score=min(1.0, abs(avg_sentiment) * 2),
                context_data={
                    'avg_sentiment': avg_sentiment,
                    'sessions_analysed': recent_sessions.count(),
                    'trending': 'declining' if newer_sentiment and older_sentiment and newer_sentiment < older_sentiment else 'stable'
                }
            )
            alerts.append(alert)
        
        # Check for declining trend even if not critically low
        elif (older_sentiment and newer_sentiment and 
              newer_sentiment < older_sentiment - self.SENTIMENT_TREND_THRESHOLD):
            
            alert = self._create_alert(
                project=project,
                alert_type='sentiment_decline',
                severity='medium',
                title="Team Sentiment Declining Trend",
                description=f"Team sentiment trending downward from {older_sentiment:.2f} to {newer_sentiment:.2f} over the past week.",
                confidence_score=min(1.0, (older_sentiment - newer_sentiment) * 3),
                context_data={
                    'older_sentiment': older_sentiment,
                    'newer_sentiment': newer_sentiment,
                    'trend_magnitude': older_sentiment - newer_sentiment
                }
            )
            alerts.append(alert)
        
        return alerts
    
    def _check_engagement_drop(self, project: Project) -> List[Dict[str, Any]]:
        """Check for drops in team engagement and participation."""
        alerts = []
        
        # Get team size
        team_size = TeamMember.objects.filter(project=project, is_active=True).count()
        if team_size == 0:
            return alerts
        
        # Check participation rate over last 14 days
        end_date = demo_now().date()
        start_date = end_date - timedelta(days=14)
        
        expected_sessions = team_size * 14  # Max possible sessions
        actual_sessions = StandupSession.objects.filter(
            project=project,
            date__gte=start_date,
            status='completed'
        ).count()
        
        participation_rate = actual_sessions / max(expected_sessions, 1)
        
        if participation_rate < self.PARTICIPATION_THRESHOLD:
            severity = 'high' if participation_rate < 0.4 else 'medium'
            
            alert = self._create_alert(
                project=project,
                alert_type='engagement_drop',
                severity=severity,
                title=f"Low Team Participation: {participation_rate:.1%}",
                description=f"Team participation rate has dropped to {participation_rate:.1%} ({actual_sessions}/{expected_sessions} sessions). Team may be disengaging from standup process.",
                confidence_score=1.0 - participation_rate,
                context_data={
                    'participation_rate': participation_rate,
                    'actual_sessions': actual_sessions,
                    'expected_sessions': expected_sessions,
                    'team_size': team_size
                }
            )
            alerts.append(alert)
        
        return alerts
    
    def _check_blocker_increase(self, project: Project) -> List[Dict[str, Any]]:
        """Check for increasing blocker frequency."""
        alerts = []
        
        # Analyse blocker patterns over last 14 days
        end_date = demo_now().date()
        start_date = end_date - timedelta(days=14)
        
        recent_sessions = StandupSession.objects.filter(
            project=project,
            date__gte=start_date,
            status='completed'
        )
        
        if recent_sessions.count() < 5:
            return alerts
        
        blocker_sessions = recent_sessions.filter(
            blockers__isnull=False
        ).exclude(blockers='')
        
        blocker_frequency = blocker_sessions.count() / recent_sessions.count()
        
        if blocker_frequency > self.BLOCKER_FREQUENCY_THRESHOLD:
            # Analyse blocker themes
            blocker_themes = self._extract_blocker_themes(blocker_sessions)
            
            severity = 'critical' if blocker_frequency > 0.7 else 'high'
            
            alert = self._create_alert(
                project=project,
                alert_type='blocker_increase',
                severity=severity,
                title=f"High Blocker Frequency: {blocker_frequency:.1%}",
                description=f"Team experiencing blockers in {blocker_frequency:.1%} of standups. Common themes: {', '.join(blocker_themes[:3])}",
                confidence_score=min(1.0, blocker_frequency * 1.5),
                context_data={
                    'blocker_frequency': blocker_frequency,
                    'blocker_sessions': blocker_sessions.count(),
                    'total_sessions': recent_sessions.count(),
                    'common_themes': blocker_themes
                }
            )
            alerts.append(alert)
        
        return alerts
    
    def _check_productivity_concern(self, project: Project) -> List[Dict[str, Any]]:
        """Check for productivity and output concerns."""
        alerts = []
        
        # Analyse work item patterns and content quality
        end_date = demo_now().date()
        start_date = end_date - timedelta(days=14)
        
        recent_sessions = StandupSession.objects.filter(
            project=project,
            date__gte=start_date,
            status='completed'
        )
        
        if recent_sessions.count() < 5:
            return alerts
        
        # Check for low content quality indicators
        low_content_sessions = 0
        for session in recent_sessions:
            content_quality = self._assess_content_quality(session)
            if content_quality < 0.3:  # Low quality threshold
                low_content_sessions += 1
        
        low_content_rate = low_content_sessions / recent_sessions.count()
        
        if low_content_rate > 0.4:  # More than 40% low-quality updates
            alert = self._create_alert(
                project=project,
                alert_type='productivity_concern',
                severity='medium',
                title=f"Content Quality Concern: {low_content_rate:.1%} Low-Quality Updates",
                description=f"High rate of low-quality standup updates detected, potentially indicating productivity issues or lack of meaningful work progress.",
                confidence_score=low_content_rate,
                context_data={
                    'low_content_rate': low_content_rate,
                    'low_content_sessions': low_content_sessions,
                    'total_sessions': recent_sessions.count()
                }
            )
            alerts.append(alert)
        
        return alerts
    
    def _check_team_member_burnout(self, project: Project) -> List[Dict[str, Any]]:
        """Check for individual team member burnout indicators."""
        alerts = []
        
        team_members = TeamMember.objects.filter(project=project, is_active=True)
        
        for member in team_members:
            burnout_score = self._calculate_burnout_score(member)
            
            if burnout_score >= self.BURNOUT_INDICATOR_THRESHOLD:
                severity = 'critical' if burnout_score >= 5 else 'high'
                
                alert = self._create_alert(
                    project=project,
                    team_member=member,
                    alert_type='team_member_burnout',
                    severity=severity,
                    title=f"Burnout Risk: {member.user.username}",
                    description=f"Team member showing multiple burnout indicators (score: {burnout_score}). Requires immediate management attention.",
                    confidence_score=min(1.0, burnout_score / 5),
                    context_data={
                        'burnout_score': burnout_score,
                        'member_id': member.id,
                        'member_username': member.user.username
                    }
                )
                alerts.append(alert)
        
        return alerts
    
    def _check_communication_gap(self, project: Project) -> List[Dict[str, Any]]:
        """Check for communication gaps or patterns."""
        alerts = []
        
        # Check for team members who haven't submitted standups recently
        end_date = demo_now().date()
        inactive_threshold = end_date - timedelta(days=5)  # 5 days without standup
        
        team_members = TeamMember.objects.filter(project=project, is_active=True)
        inactive_members = []
        
        for member in team_members:
            last_standup = StandupSession.objects.filter(
                user=member.user,
                project=project,
                status='completed'
            ).aggregate(last_date=Max('date'))['last_date']
            
            if not last_standup or last_standup < inactive_threshold:
                inactive_members.append(member)
        
        if len(inactive_members) > 0:
            severity = 'high' if len(inactive_members) > len(team_members) * 0.3 else 'medium'
            
            alert = self._create_alert(
                project=project,
                alert_type='communication_gap',
                severity=severity,
                title=f"Communication Gap: {len(inactive_members)} Inactive Members",
                description=f"{len(inactive_members)} team members haven't submitted standups in 5+ days: {', '.join([m.user.username for m in inactive_members])}",
                confidence_score=len(inactive_members) / max(len(team_members), 1),
                context_data={
                    'inactive_members': [m.user.username for m in inactive_members],
                    'inactive_count': len(inactive_members),
                    'team_size': len(team_members)
                }
            )
            alerts.append(alert)
        
        return alerts
    
    def _create_alert(self, project: Project, alert_type: str, severity: str, 
                     title: str, description: str, confidence_score: float,
                     context_data: Dict, team_member: TeamMember = None) -> Dict[str, Any]:
        """Create and save a team health alert."""
        
        # Check if similar alert already exists (avoid duplicates)
        existing_alert = TeamHealthAlert.objects.filter(
            project=project,
            alert_type=alert_type,
            status='active',
            created_at__gte=demo_now() - timedelta(hours=24)
        ).first()
        
        if existing_alert:
            return {'alert': 'duplicate', 'existing_id': existing_alert.id}
        
        # Create new alert
        alert = TeamHealthAlert.objects.create(
            project=project,
            team_member=team_member,
            alert_type=alert_type,
            severity=severity,
            title=title,
            description=description,
            context_data=context_data,
            confidence_score=confidence_score
        )
        
        logger.info(f"Generated {severity} alert for {project.name}: {title}")
        
        return {
            'alert': 'created',
            'id': alert.id,
            'severity': severity,
            'title': title,
            'description': description,
            'confidence': confidence_score
        }
    
    def _analyse_team_status(self, project: Project) -> Dict[str, Any]:
        """Analyse overall team status."""
        end_date = demo_now().date()
        start_date = end_date - timedelta(days=14)
        
        recent_sessions = StandupSession.objects.filter(
            project=project,
            date__gte=start_date,
            status='completed'
        )
        
        team_size = TeamMember.objects.filter(project=project, is_active=True).count()
        
        return {
            'team_size': team_size,
            'recent_sessions': recent_sessions.count(),
            'avg_sentiment': recent_sessions.aggregate(avg=Avg('sentiment_score'))['avg'] or 0,
            'participation_rate': recent_sessions.count() / max(team_size * 14, 1),
            'active_alerts': TeamHealthAlert.objects.filter(project=project, status='active').count()
        }
    
    def _calculate_burnout_score(self, member: TeamMember) -> int:
        """Calculate burnout risk score for a team member."""
        score = 0
        end_date = demo_now().date()
        start_date = end_date - timedelta(days=14)
        
        user_sessions = StandupSession.objects.filter(
            user=member.user,
            project=member.project,
            date__gte=start_date,
            status='completed'
        )
        
        if user_sessions.count() == 0:
            return 0
        
        # Check sentiment indicators
        avg_sentiment = user_sessions.aggregate(avg=Avg('sentiment_score'))['avg']
        if avg_sentiment and avg_sentiment < -0.3:
            score += 2
        
        # Check blocker frequency
        blocker_sessions = user_sessions.filter(blockers__isnull=False).exclude(blockers='')
        blocker_rate = blocker_sessions.count() / user_sessions.count()
        if blocker_rate > 0.5:
            score += 1
        
        # Check content quality decline
        low_quality_count = sum(1 for session in user_sessions 
                               if self._assess_content_quality(session) < 0.3)
        if low_quality_count > user_sessions.count() * 0.4:
            score += 1
        
        # Check participation decline
        expected_sessions = 14  # 14 days
        if user_sessions.count() < expected_sessions * 0.6:
            score += 1
        
        return score
    
    def _assess_content_quality(self, session: StandupSession) -> float:
        """Assess the quality/meaningfulness of standup content."""
        score = 0.0
        
        # Check yesterday work content
        if session.yesterday_work and len(session.yesterday_work.strip()) > 20:
            score += 0.4
        
        # Check today plan content
        if session.today_plan and len(session.today_plan.strip()) > 20:
            score += 0.4
        
        # Check for specific work items or details
        content = f"{session.yesterday_work} {session.today_plan}".lower()
        quality_indicators = ['ticket', 'bug', 'feature', 'test', 'review', 'deploy', 'fix', 'implement']
        if any(indicator in content for indicator in quality_indicators):
            score += 0.2
        
        return min(1.0, score)
    
    def _extract_blocker_themes(self, blocker_sessions) -> List[str]:
        """Extract common themes from blocker descriptions."""
        blocker_texts = []
        for session in blocker_sessions:
            if session.blockers:
                blocker_texts.append(session.blockers.lower())
        
        # Simple keyword extraction
        common_words = Counter()
        for text in blocker_texts:
            words = text.split()
            relevant_words = [w for w in words if len(w) > 4 and 
                            w not in ['with', 'that', 'this', 'have', 'been', 'need', 'still']]
            common_words.update(relevant_words)
        
        return [word for word, count in common_words.most_common(5) if count > 1]


class AlertNotificationService:
    """
    Service for sending notifications about team health alerts.
    """
    
    def __init__(self):
        self.email_service = None  # Would integrate with email service
        
    def send_alert_notifications(self, alerts: List[TeamHealthAlert]) -> Dict[str, Any]:
        """Send notifications for critical alerts to managers."""
        results = {
            'notifications_sent': 0,
            'errors': [],
            'recipients': []
        }
        
        critical_alerts = [alert for alert in alerts if alert.severity in ['critical', 'high']]
        
        for alert in critical_alerts:
            try:
                managers = self._get_project_managers(alert.project)
                for manager in managers:
                    self._send_alert_notification(manager, alert)
                    results['notifications_sent'] += 1
                    results['recipients'].append(manager.user.email)
                    
            except Exception as e:
                results['errors'].append(f"Failed to notify for alert {alert.id}: {e}")
                logger.error(f"Alert notification error: {e}")
        
        return results
    
    def _get_project_managers(self, project: Project) -> List[UserProfile]:
        """Get managers who should receive alerts for this project."""
        # Get team members with management roles
        team_members = TeamMember.objects.filter(project=project, is_active=True)
        managers = []
        
        for member in team_members:
            try:
                profile = UserProfile.objects.get(user=member.user)
                if profile.is_manager:
                    managers.append(profile)
            except UserProfile.DoesNotExist:
                continue
        
        # If no project-specific managers, get the first manager in the system (single project demo)
        if not managers:
            managers = UserProfile.objects.filter(
                role__in=UserProfile.MANAGEMENT_ROLES
            )[:1]  # Single manager for demo
        
        return managers
    
    def _send_alert_notification(self, manager: UserProfile, alert: TeamHealthAlert):
        """Send individual alert notification."""
        # This would integrate with actual email/notification system
        logger.info(
            f"Alert notification: {alert.severity.upper()} - {alert.title} "
            f"sent to {manager.user.email} for project {alert.project.name}"
        )
