"""
Standup-specific services moved from dashboard.automation_service
"""
from datetime import date, time, datetime, timedelta
from django.utils import timezone
from django.urls import reverse
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.conf import settings
from typing import Dict, Any, List
import logging

from dashboard.models import StandupSession, Project, TeamMember

logger = logging.getLogger(__name__)


class EmailNotificationService:
    """Simple email notification service for standup reminders."""
    
    def send_email(self, to_email: str, subject: str, message: str) -> bool:
        """Send email using Django's email backend."""
        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[to_email],
                fail_silently=False
            )
            return True
        except Exception as e:
            logger.error(f"Email send error: {str(e)}")
            return False


class StandupReminderService:
    """Service for handling standup reminders and notifications."""
    
    def __init__(self):
        self.email_service = EmailNotificationService()
    
    def send_automated_standup_reminders(self, send_time: time = time(9, 0)) -> Dict[str, Any]:
        """
        Send automated standup reminders based on team schedules and time zones.
        
        Args:
            send_time: Time to send reminders (default 9:00 AM)
            
        Returns:
            Dict with reminder statistics and results
        """
        results = {
            'reminders_sent': 0,
            'reminders_skipped': 0,
            'errors': [],
            'details': []
        }
        
        today = timezone.now().date()
        
        # Skip weekends
        if today.weekday() >= 5:  # Saturday = 5, Sunday = 6
            results['reminders_skipped'] = 'weekend'
            return results
        
        try:
            # Get all active team members across projects
            active_members = TeamMember.objects.filter(
                is_active=True,
                project__status='active'
            ).select_related('user', 'project')
            
            for member in active_members:
                try:
                    # Check if reminder should be sent
                    should_send = self._should_send_reminder(member, today)
                    
                    if should_send['send']:
                        reminder_sent = self._send_standup_reminder(member, today)
                        
                        if reminder_sent:
                            results['reminders_sent'] += 1
                            results['details'].append({
                                'user': member.user.username,
                                'project': member.project.name,
                                'status': 'sent'
                            })
                            logger.info(f"Standup reminder sent to {member.user.username}")
                        else:
                            results['reminders_skipped'] += 1
                            results['details'].append({
                                'user': member.user.username,
                                'project': member.project.name,
                                'status': 'failed'
                            })
                    else:
                        results['reminders_skipped'] += 1
                        results['details'].append({
                            'user': member.user.username,
                            'project': member.project.name,
                            'status': 'skipped',
                            'reason': should_send['reason']
                        })
                        
                except Exception as member_error:
                    error_msg = f"Error processing reminder for {member.user.username}: {str(member_error)}"
                    results['errors'].append(error_msg)
                    logger.error(error_msg)
                    
        except Exception as e:
            error_msg = f"Error in automated reminder process: {str(e)}"
            results['errors'].append(error_msg)
            logger.error(error_msg)
        
        return results
    
    def _should_send_reminder(self, member: TeamMember, today: date) -> Dict[str, Any]:
        """Determine if a standup reminder should be sent to a team member."""
        
        # Check if user already submitted standup today
        existing_standup = StandupSession.objects.filter(
            user=member.user,
            project=member.project,
            date=today,
            status='completed'
        ).first()
        
        if existing_standup:
            return {'send': False, 'reason': 'Already completed today'}
        
        # Check if user has a pending standup session from earlier today
        pending_standup = StandupSession.objects.filter(
            user=member.user,
            project=member.project,
            date=today,
            status='pending'
        ).first()
        
        if pending_standup and pending_standup.created_at.date() == today:
            return {'send': False, 'reason': 'Pending session exists'}
        
        # Check if it's weekend
        if today.weekday() >= 5:
            return {'send': False, 'reason': 'Weekend - no standup required'}
        
        return {'send': True, 'reason': 'Reminder needed'}
    
    def _send_standup_reminder(self, member: TeamMember, today: date) -> bool:
        """Send a standup reminder to a team member."""
        try:
            # Create or get pending standup session
            standup_session, created = StandupSession.objects.get_or_create(
                user=member.user,
                project=member.project,
                date=today,
                defaults={'status': 'pending'}
            )
            
            # Prepare reminder content
            reminder_data = self._prepare_reminder_content(member, standup_session)
            
            # Send email notification
            email_sent = self._send_email_reminder(member.user, reminder_data)
            
            # Send in-app notification (placeholder for future implementation)
            notification_sent = self._send_in_app_notification(member.user, reminder_data)
            
            # Log the reminder attempt
            logger.info(f"Standup reminder processed for {member.user.username} - Email: {email_sent}, Notification: {notification_sent}")
            
            return email_sent or notification_sent
            
        except Exception as e:
            logger.error(f"Failed to send standup reminder to {member.user.username}: {str(e)}")
            return False
    
    def _prepare_reminder_content(self, member: TeamMember, standup_session: StandupSession) -> Dict[str, Any]:
        """Prepare reminder content with context and personalization."""
        
        # Get recent team activity for context
        recent_sessions = StandupSession.objects.filter(
            project=member.project,
            date__gte=timezone.now().date() - timedelta(days=7),
            status='completed'
        ).count()
        
        team_size = TeamMember.objects.filter(
            project=member.project,
            is_active=True
        ).count()
        
        participation_rate = (recent_sessions / max(team_size * 7, 1)) * 100 if team_size > 0 else 0
        
        # Get user's previous standup for context
        previous_standup = StandupSession.objects.filter(
            user=member.user,
            project=member.project,
            date__lt=timezone.now().date(),
            status='completed'
        ).order_by('-date').first()
        
        previous_context = None
        if previous_standup:
            previous_context = {
                'date': previous_standup.date.isoformat(),
                'had_blockers': bool(previous_standup.blockers),
                'work_items_mentioned': previous_standup.work_item_refs.count(),
                'sentiment': previous_standup.sentiment_label or 'Unknown'
            }
        
        return {
            'user_name': member.user.first_name or member.user.username,
            'project_name': member.project.name,
            # Build standup URL via reverse to avoid hardcoding
            'standup_url': reverse('standup:standup'),
            'team_context': {
                'recent_activity': recent_sessions,
                'team_size': team_size,
                'participation_rate': round(participation_rate, 1)
            },
            'previous_standup': previous_context,
            'session_id': standup_session.id
        }
    
    def _send_email_reminder(self, user: User, reminder_data: Dict[str, Any]) -> bool:
        """Send email reminder to user."""
        try:
            base_message = f"Good morning, {reminder_data['user_name']}! Time for your daily standup."
            
            if reminder_data['previous_standup']:
                prev = reminder_data['previous_standup']
                if prev['had_blockers']:
                    base_message += " Don't forget to update us on yesterday's blockers."
                if prev['work_items_mentioned'] > 0:
                    base_message += f" You mentioned {prev['work_items_mentioned']} work items last time."
            
            team_context = reminder_data['team_context']
            if team_context['participation_rate'] < 80:
                base_message += f" Your team participation is at {team_context['participation_rate']}% - your input helps!"
            
            subject = f"Daily Standup Reminder - {reminder_data['project_name']}"
            
            email_body = f"""
            {base_message}
            
            Project: {reminder_data['project_name']}
            Team Activity: {team_context['recent_activity']} standups completed this week
            Team Size: {team_context['team_size']} members
            
            Submit your standup at: {reminder_data['standup_url']}
            
            Questions to consider:
            - What did you accomplish yesterday?
            - What are you working on today?
            - Are there any blockers or challenges?
            
            Best regards,
            PulzeBot Team
            """
            
            return self.email_service.send_email(
                to_email=user.email,
                subject=subject,
                message=email_body
            )
            
        except Exception as e:
            logger.error(f"Failed to send email reminder to {user.email}: {str(e)}")
            return False
    
    def _send_in_app_notification(self, user: User, reminder_data: Dict[str, Any]) -> bool:
        """Send in-app notification (placeholder for future implementation)."""
        # This would integrate with a notification system
        # For now, return True to indicate the system is ready
        return True
    
    def get_standup_statistics(self, project: Project = None, days_back: int = 7) -> Dict[str, Any]:
        """Get standup completion statistics for a project or all projects."""
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days_back)
        
        if project:
            projects = [project]
        else:
            projects = Project.objects.filter(status='active')
        
        stats = {
            'overall': {
                'total_expected': 0,
                'total_completed': 0,
                'completion_rate': 0
            },
            'by_project': {}
        }
        
        for proj in projects:
            team_size = TeamMember.objects.filter(project=proj, is_active=True).count()
            
            # Calculate expected standups (excluding weekends)
            expected_days = 0
            current_date = start_date
            while current_date <= end_date:
                if current_date.weekday() < 5:  # Monday = 0, Friday = 4
                    expected_days += 1
                current_date += timedelta(days=1)
            
            expected_standups = team_size * expected_days
            
            completed_standups = StandupSession.objects.filter(
                project=proj,
                date__range=[start_date, end_date],
                status='completed'
            ).count()
            
            completion_rate = (completed_standups / max(expected_standups, 1)) * 100
            
            project_stats = {
                'team_size': team_size,
                'expected_standups': expected_standups,
                'completed_standups': completed_standups,
                'completion_rate': round(completion_rate, 1),
                'days_analysed': expected_days
            }
            
            stats['by_project'][proj.name] = project_stats
            stats['overall']['total_expected'] += expected_standups
            stats['overall']['total_completed'] += completed_standups
        
        if stats['overall']['total_expected'] > 0:
            stats['overall']['completion_rate'] = round(
                (stats['overall']['total_completed'] / stats['overall']['total_expected']) * 100, 1
            )
        
        return stats
