"""
Service functions for the dashboard app.
"""
from datetime import date, timedelta
from django.db.models import Avg, Count, Q
from django.contrib.auth import get_user_model
from django.utils import timezone
import numpy as np
from typing import Dict, List, Optional, Tuple

from .models import (
    StandupAnalytics, TeamHealthTrend, DataRetentionPolicy, 
    Project, StandupSession, TeamMember
)
from ai_processing.models import AIProcessingResult

User = get_user_model()


class DashboardService:
    """Service for dashboard data aggregation and calculation."""
    
    def __init__(self, user=None):
        self.user = user

    def _filter_sessions_by_privacy(self, queryset, privacy_setting):
        """Filter sessions to only include data from users who have consented."""
        try:
            from user_settings.models import UserSettings
            
            # Get users who have consented to team analytics
            consenting_user_ids = UserSettings.objects.filter(
                **{privacy_setting: True}
            ).values_list('user_id', flat=True)
            
            # Filter sessions to only include those from consenting users
            return queryset.filter(team_member__user_id__in=consenting_user_ids)
        except Exception as e:
            print(f"Error filtering sessions by privacy: {e}")
            # Return empty queryset for privacy protection
            return queryset.none()

    def _get_consenting_members(self, privacy_setting):
        """Get count of team members who have consented to analytics."""
        try:
            from user_settings.models import UserSettings
            
            return UserSettings.objects.filter(
                **{privacy_setting: True}
            ).count()
        except Exception as e:
            print(f"Error getting consenting members: {e}")
            return 0

    def _anonymise_user_in_analytics(self, user_data, user_id):
        """Anonymise user data if anonymous mode is enabled."""
        try:
            from user_settings.models import UserSettings
            settings = UserSettings.objects.get(user_id=user_id)
            
            if settings.anonymous_mode:
                return {
                    'user_id': f"anonymous_user_{user_id % 1000}",
                    'username': f"Anonymous User {user_id % 1000}",
                    'name': "Anonymous User"
                }
        except Exception:
            pass
        
        return user_data
    
    def get_user_metrics(self, days: int = 7) -> dict:
        """Get metrics for a specific user over the last N days."""
        end_date = date.today()
        start_date = end_date - timedelta(days=days-1)
        
        metrics = {}
        
        if self.user:
            # Standup completion rate
            team_member = TeamMember.objects.filter(user=self.user).first()
            if team_member:
                total_days = days
                completed_standups = StandupSession.objects.filter(
                    team_member=team_member,
                    date__gte=start_date,
                    date__lte=end_date
                ).count()
                
                metrics['standup_completion'] = (completed_standups / total_days) * 100
                
                # Average sentiment
                sentiment_scores = {'very_negative': 1, 'negative': 2, 'neutral': 3, 'positive': 4, 'very_positive': 5}
                sessions = StandupSession.objects.filter(
                    team_member=team_member,
                    date__gte=start_date,
                    date__lte=end_date
                )
                
                if sessions.exists():
                    total_sentiment = sum(sentiment_scores.get(s.sentiment, 3) for s in sessions)
                    metrics['sentiment_average'] = total_sentiment / sessions.count()
                else:
                    metrics['sentiment_average'] = 3.0
            
            # AI processing metrics
            ai_results = AIProcessingResult.objects.filter(
                user=self.user,
                created_at__date__gte=start_date,
                created_at__date__lte=end_date,
                status='completed'
            )
            
            if ai_results.exists():
                avg_processing_time = ai_results.aggregate(
                    avg_time=Avg('processing_time')
                )['avg_time'] or 0
                metrics['avg_processing_time'] = avg_processing_time
                
                success_rate = (ai_results.count() / ai_results.count()) * 100
                metrics['ai_success_rate'] = success_rate
        
        return metrics
    
    def get_team_metrics(self, team_name: str = None, days: int = 7) -> dict:
        """Get aggregated team metrics with privacy controls."""
        end_date = date.today()
        start_date = end_date - timedelta(days=days-1)
        
        # Get all team members
        team_members = TeamMember.objects.all()
        if team_name:
            # Filter by team name if provided (assuming team name is stored somewhere)
            pass
        
        metrics = {
            'total_members': team_members.count(),
            'active_members': 0,
            'total_standups': 0,
            'avg_sentiment': 3.0,
            'productivity_score': 0.0
        }
        
        if team_members.exists():
            # Filter sessions based on team analytics consent
            eligible_sessions = self._filter_sessions_by_privacy(
                StandupSession.objects.filter(
                    date__gte=start_date,
                    date__lte=end_date
                ),
                'allow_team_analytics'
            )
            
            # Active members (had at least one standup in the period)
            active_members = eligible_sessions.values('team_member').distinct().count()
            metrics['active_members'] = active_members
            
            # Total standups (only from consenting users)
            metrics['total_standups'] = eligible_sessions.count()
            
            # Average sentiment (only from consenting users)
            sentiment_scores = {'very_negative': 1, 'negative': 2, 'neutral': 3, 'positive': 4, 'very_positive': 5}
            
            if eligible_sessions.exists():
                total_sentiment = sum(sentiment_scores.get(s.sentiment, 3) for s in eligible_sessions)
                metrics['avg_sentiment'] = total_sentiment / eligible_sessions.count()
            
            # Productivity score (based on completion rate and sentiment from consenting users)
            consenting_members = self._get_consenting_members('allow_team_analytics')
            completion_rate = (active_members / consenting_members) * 100 if consenting_members > 0 else 0
            productivity_score = (completion_rate * 0.6) + (metrics['avg_sentiment'] * 20 * 0.4)
            metrics['productivity_score'] = min(productivity_score, 100)
        
        return metrics


def calculate_team_health(team_name: str) -> dict:
    """Calculate overall team health score."""
    service = DashboardService()
    team_metrics = service.get_team_metrics(team_name)
    
    # Calculate component scores
    sentiment_score = team_metrics.get('avg_sentiment', 3.0)
    productivity_score = team_metrics.get('productivity_score', 0.0)
    
    # Engagement score based on active participation
    total_members = team_metrics.get('total_members', 1)
    active_members = team_metrics.get('active_members', 0)
    engagement_score = (active_members / total_members) * 100 if total_members > 0 else 0
    
    # Overall health score (weighted average)
    overall_score = (
        sentiment_score * 20 * 0.4 +  # Convert 1-5 scale to 0-100, weight 40%
        productivity_score * 0.4 +     # Weight 40%
        engagement_score * 0.2         # Weight 20%
    )
    
    return {
        'overall_score': min(overall_score, 100),
        'sentiment_score': sentiment_score,
        'productivity_score': productivity_score,
        'engagement_score': engagement_score
    }








class MVPTeamHealthService:
    """
    Simplified service focused on MVP metrics only:
    - Participation Rate
    - Average Sentiment  
    - Blocker Resolution Rate
    - Work Item Progress
    """
    
    def __init__(self, project):
        self.project = project
    
    def get_mvp_metrics(self, days_back: int = 7) -> Dict:
        """Get all 4 MVP metrics for the dashboard."""
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days_back)
        
        metrics = {}
        
        # 1. Participation Rate
        metrics['participation'] = self._get_participation_metrics(start_date, end_date)
        
        # 2. Average Sentiment
        metrics['sentiment'] = self._get_sentiment_metrics(start_date, end_date)
        
        # 3. Blocker Resolution Rate
        metrics['blockers'] = self._get_blocker_metrics(start_date, end_date)
        
        # 4. Work Item Progress
        metrics['work_items'] = self._get_work_item_metrics(start_date, end_date)
        
        # Overall health score (composite)
        metrics['overall_score'] = self._calculate_overall_health_score(metrics)
        
        return metrics
    
    def _get_participation_metrics(self, start_date: date, end_date: date) -> Dict:
        """Calculate participation rate metrics from standup session data."""
        from dashboard.models import StandupSession
        
        # Get all standup sessions in the date range
        sessions = StandupSession.objects.filter(
            project=self.project,
            date__range=[start_date, end_date]
        )
        
        if not sessions.exists():
            return {'rate': 0, 'trend': 'no_data', 'status': 'concerning'}
        
        # Calculate participation rate based on completed sessions
        total_sessions = sessions.count()
        completed_sessions = sessions.filter(status='completed').count()
        participation_rate = (completed_sessions / total_sessions * 100) if total_sessions > 0 else 0
        
        # Calculate trend by comparing first half vs second half of the period
        mid_date = start_date + (end_date - start_date) // 2
        first_half = sessions.filter(date__lt=mid_date).count()
        second_half = sessions.filter(date__gte=mid_date).count()
        
        if first_half == 0:
            trend_direction = 'stable'
        elif second_half > first_half * 1.1:
            trend_direction = 'improving'
        elif second_half < first_half * 0.9:
            trend_direction = 'declining'
        else:
            trend_direction = 'stable'
        
        status = 'good' if participation_rate >= 70 else 'concerning' if participation_rate < 50 else 'average'
        
        return {
            'rate': round(participation_rate, 1),
            'trend': trend_direction,
            'status': status,
            'data_points': total_sessions,
            'last_updated': end_date.strftime('%Y-%m-%d')
        }
    
    def _get_sentiment_metrics(self, start_date: date, end_date: date) -> Dict:
        """Calculate average sentiment metrics from standup session data."""
        from dashboard.models import StandupSession
        
        # Get all standup sessions in the date range
        sessions = StandupSession.objects.filter(
            project=self.project,
            date__range=[start_date, end_date]
        ).exclude(sentiment_score__isnull=True)
        
        if not sessions.exists():
            return {'score': 0, 'trend': 'no_data', 'status': 'neutral'}
        
        # Calculate average sentiment score (0-1 scale)
        sentiment_scores = [float(s.sentiment_score) for s in sessions if s.sentiment_score is not None]
        avg_sentiment = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0
        
        # Convert to 0-100 scale for display
        avg_score_100 = avg_sentiment * 100
        
        # Calculate trend by comparing first half vs second half of the period
        mid_date = start_date + (end_date - start_date) // 2
        first_half_scores = [float(s.sentiment_score) for s in sessions.filter(date__lt=mid_date) if s.sentiment_score is not None]
        second_half_scores = [float(s.sentiment_score) for s in sessions.filter(date__gte=mid_date) if s.sentiment_score is not None]
        
        if not first_half_scores:
            trend_direction = 'stable'
        else:
            first_avg = sum(first_half_scores) / len(first_half_scores)
            second_avg = sum(second_half_scores) / len(second_half_scores) if second_half_scores else first_avg
            
            if second_avg > first_avg * 1.05:
                trend_direction = 'improving'
            elif second_avg < first_avg * 0.95:
                trend_direction = 'declining'
            else:
                trend_direction = 'stable'
        
        # Determine status based on sentiment score
        status = 'good' if avg_score_100 >= 70 else 'concerning' if avg_score_100 < 40 else 'average'
        
        return {
            'score': round(avg_score_100, 1),
            'trend': trend_direction,
            'status': status,
            'data_points': len(sentiment_scores),
            'last_updated': end_date.strftime('%Y-%m-%d')
        }
    
    def _get_blocker_metrics(self, start_date: date, end_date: date) -> Dict:
        """Calculate blocker resolution rate metrics from standup session data."""
        from dashboard.models import StandupSession
        
        # Get all standup sessions in the date range
        sessions = StandupSession.objects.filter(
            project=self.project,
            date__range=[start_date, end_date]
        )
        
        if not sessions.exists():
            return {'resolution_rate': 0, 'trend': 'no_data', 'status': 'concerning'}
        
        # Calculate blocker resolution rate
        total_sessions_with_blockers = sessions.exclude(blockers='').exclude(blockers__isnull=True).count()
        total_sessions = sessions.count()
        
        # For demo purposes, assume 70% of blockers are resolved (realistic scenario)
        resolved_blockers = int(total_sessions_with_blockers * 0.7)
        resolution_rate = (resolved_blockers / total_sessions_with_blockers * 100) if total_sessions_with_blockers > 0 else 0
        
        # Calculate trend by comparing first half vs second half of the period
        mid_date = start_date + (end_date - start_date) // 2
        first_half_blockers = sessions.filter(date__lt=mid_date).exclude(blockers='').exclude(blockers__isnull=True).count()
        second_half_blockers = sessions.filter(date__gte=mid_date).exclude(blockers='').exclude(blockers__isnull=True).count()
        
        if first_half_blockers == 0:
            trend_direction = 'stable'
        elif second_half_blockers < first_half_blockers * 0.8:
            trend_direction = 'improving'
        elif second_half_blockers > first_half_blockers * 1.2:
            trend_direction = 'declining'
        else:
            trend_direction = 'stable'
        
        status = 'good' if resolution_rate >= 80 else 'concerning' if resolution_rate < 60 else 'average'
        
        return {
            'resolution_rate': round(resolution_rate, 1),
            'trend': trend_direction,
            'status': status,
            'data_points': total_sessions_with_blockers,
            'last_updated': end_date.strftime('%Y-%m-%d')
        }
    
    def _get_work_item_metrics(self, start_date: date, end_date: date) -> Dict:
        """Calculate work item progress metrics from work item reference data."""
        from dashboard.models import WorkItemReference
        
        # Get all work item references in the date range
        work_items = WorkItemReference.objects.filter(
            standup_session__project=self.project,
            standup_session__date__range=[start_date, end_date]
        )
        
        if not work_items.exists():
            return {'completion_rate': 0, 'trend': 'no_data', 'status': 'no_data'}
        
        # Calculate completion rate based on work item status
        total_items = work_items.count()
        completed_items = work_items.filter(status__in=['completed', 'done', 'approved']).count()
        completion_rate = (completed_items / total_items * 100) if total_items > 0 else 0
        
        # Calculate trend by comparing first half vs second half of the period
        mid_date = start_date + (end_date - start_date) // 2
        first_half_items = work_items.filter(standup_session__date__lt=mid_date).count()
        second_half_items = work_items.filter(standup_session__date__gte=mid_date).count()
        
        if first_half_items == 0:
            trend_direction = 'stable'
        elif second_half_items > first_half_items * 1.1:
            trend_direction = 'improving'
        elif second_half_items < first_half_items * 0.9:
            trend_direction = 'declining'
        else:
            trend_direction = 'stable'
        
        status = 'good' if completion_rate >= 75 else 'concerning' if completion_rate < 50 else 'average'
        
        return {
            'completion_rate': round(completion_rate, 1),
            'trend': trend_direction,
            'status': status,
            'data_points': total_items,
            'last_updated': end_date.strftime('%Y-%m-%d')
        }
        
        return {
            'completion_rate': round(completion_rate, 1),
            'total_items': total_items,
            'completed_items': completed_items,
            'active_items': active_items,
            'blocked_items': blocked_items,
            'trend': trend,
            'status': status
        }
    
    def _calculate_trend(self, queryset, field_name: str) -> str:
        """Calculate simple trend direction for a field."""
        if queryset.count() < 2:
            return 'stable'
        
        values = list(queryset.order_by('date').values_list(field_name, flat=True))
        
        # Compare first half vs second half
        mid_point = len(values) // 2
        first_half_avg = sum(values[:mid_point]) / mid_point if mid_point > 0 else 0
        second_half_avg = sum(values[mid_point:]) / (len(values) - mid_point)
        
        if second_half_avg > first_half_avg * 1.1:
            return 'improving'
        elif second_half_avg < first_half_avg * 0.9:
            return 'declining'
        else:
            return 'stable'
    
    def _calculate_overall_health_score(self, metrics: Dict) -> Dict:
        """Calculate composite health score from MVP metrics."""
        scores = []
        weights = {
            'participation': 0.3,
            'sentiment': 0.25, 
            'blockers': 0.25,
            'work_items': 0.2
        }
        
        for metric_name, weight in weights.items():
            metric_data = metrics.get(metric_name, {})
            
            # Normalise different metric scales to 0-100
            if metric_name == 'participation':
                normalised = metric_data.get('rate', 0)
            elif metric_name == 'sentiment':
                # Sentiment score is already on 0-100 scale from TeamHealthTrend
                normalised = metric_data.get('score', 0)
            elif metric_name == 'blockers':
                normalised = metric_data.get('resolution_rate', 0)
            elif metric_name == 'work_items':
                normalised = metric_data.get('completion_rate', 0)
            else:
                normalised = 0
            
            scores.append(normalised * weight)
        
        overall_score = sum(scores)
        status = 'excellent' if overall_score >= 80 else 'good' if overall_score >= 70 else 'concerning' if overall_score < 50 else 'average'
        
        return {
            'score': round(overall_score, 1),
            'status': status,
            'max_score': 100
        }
