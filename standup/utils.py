"""
Utility functions for the standup app.
"""
from datetime import date, timedelta
from typing import List, Dict, Any
from django.db.models import Avg, Count
from django.utils import timezone


def calculate_standup_completion_rate(project, start_date: date, end_date: date) -> float:
    """Calculate standup completion rate for a project over a date range."""
    from dashboard.models import StandupSession, TeamMember
    
    # Get all team members for the project
    team_members = TeamMember.objects.filter(project=project)
    
    if not team_members.exists():
        return 0.0
    
    # Calculate total expected standups (weekdays only)
    total_expected = 0
    current_date = start_date
    
    while current_date <= end_date:
        if current_date.weekday() < 5:  # Monday = 0, Friday = 4
            total_expected += team_members.count()
        current_date += timedelta(days=1)
    
    if total_expected == 0:
        return 0.0
    
    # Get actual completed standups
    completed_standups = StandupSession.objects.filter(
        project=project,
        date__gte=start_date,
        date__lte=end_date,
        status='completed'
    ).count()
    
    return (completed_standups / total_expected) * 100


def get_standup_statistics_for_user(user, days_back: int = 30) -> Dict[str, Any]:
    """Get standup statistics for a specific user."""
    from dashboard.models import StandupSession
    
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=days_back)
    
    sessions = StandupSession.objects.filter(
        user=user,
        date__gte=start_date,
        date__lte=end_date
    )
    
    total_sessions = sessions.count()
    completed_sessions = sessions.filter(status='completed').count()
    
    completion_rate = (completed_sessions / total_sessions * 100) if total_sessions > 0 else 0
    
    # Calculate average sentiment if available
    avg_sentiment = sessions.filter(
        sentiment__isnull=False
    ).aggregate(Avg('sentiment'))['sentiment__avg'] or 0
    
    return {
        'total_sessions': total_sessions,
        'completed_sessions': completed_sessions,
        'completion_rate': round(completion_rate, 1),
        'average_sentiment': round(avg_sentiment, 2),
        'date_range': {
            'start': start_date,
            'end': end_date
        }
    }


def format_standup_summary(standup_session) -> str:
    """Format a standup session into a readable summary."""
    if not standup_session:
        return "No standup data available"
    
    summary_parts = []
    
    if standup_session.yesterday_work:
        summary_parts.append(f"Yesterday: {standup_session.yesterday_work[:100]}...")
    
    if standup_session.today_plan:
        summary_parts.append(f"Today: {standup_session.today_plan[:100]}...")
    
    if standup_session.blockers:
        summary_parts.append(f"Blockers: {standup_session.blockers[:100]}...")
    
    return " | ".join(summary_parts) if summary_parts else "Empty standup"


def get_team_standup_insights(project, date_range: int = 7) -> Dict[str, Any]:
    """Get team-level insights from standup data."""
    from dashboard.models import StandupSession, TeamMember
    
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=date_range)
    
    # Get all standups for the project in the date range
    standups = StandupSession.objects.filter(
        project=project,
        date__gte=start_date,
        date__lte=end_date,
        status='completed'
    )
    
    # Count blockers
    blocker_count = standups.filter(blockers__isnull=False).exclude(blockers='').count()
    
    # Calculate team sentiment
    avg_sentiment = standups.filter(
        sentiment__isnull=False
    ).aggregate(Avg('sentiment'))['sentiment__avg'] or 0
    
    # Team participation
    team_size = TeamMember.objects.filter(project=project).count()
    unique_participants = standups.values('user').distinct().count()
    participation_rate = (unique_participants / team_size * 100) if team_size > 0 else 0
    
    return {
        'total_standups': standups.count(),
        'blocker_count': blocker_count,
        'average_sentiment': round(avg_sentiment, 2),
        'participation_rate': round(participation_rate, 1),
        'team_size': team_size,
        'date_range_days': date_range
    }


def categorize_mood(mood_value: str) -> Dict[str, Any]:
    """Categorize mood values for analytics."""
    mood_categories = {
        'positive': ['productive', 'motivated', 'happy', 'excited', 'focused'],
        'neutral': ['neutral', 'ok', 'steady'],
        'negative': ['tired', 'frustrated', 'blocked', 'overwhelmed', 'stressed']
    }
    
    for category, moods in mood_categories.items():
        if mood_value.lower() in moods:
            return {
                'category': category,
                'severity': moods.index(mood_value.lower()) + 1,
                'color_class': f'mood-{category}'
            }
    
    return {
        'category': 'neutral',
        'severity': 1,
        'color_class': 'mood-neutral'
    }
