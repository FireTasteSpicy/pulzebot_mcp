"""
Database models for the dashboard app.
"""
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinLengthValidator, MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta

class Team(models.Model):
    """
    Team model for organizing users into groups.
    """
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class UserProfile(models.Model):
    """
    Extended user profile with team membership support and role-based access control.
    """
    ROLE_CHOICES = [
        ('developer', 'Developer'),
        ('manager', 'Manager'),
    ]
    
    MANAGEMENT_ROLES = ['manager']
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    team = models.ForeignKey(Team, on_delete=models.SET_NULL, null=True, blank=True)
    role = models.CharField(max_length=50, choices=ROLE_CHOICES, default='developer')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'dashboard_user_profile'
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'
        
    def __str__(self):
        return f"{self.user.username} - {self.get_role_display()} - {self.team.name if self.team else 'No Team'}"
    
    @property
    def is_manager(self):
        """Check if user has management privileges."""
        return self.role in self.MANAGEMENT_ROLES
    
    @property
    def can_view_team_analytics(self):
        """Check if user can view detailed team analytics."""
        return self.role == 'manager'
    
    @property
    def can_view_cross_team_data(self):
        """Check if user can view data across multiple teams."""
        return self.role == 'manager'


class Project(models.Model):
    """
    Project model for organizing standup sessions.
    """
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('archived', 'Archived'),
    ]

    name = models.CharField(max_length=200, unique=True)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'dashboard_project'
        verbose_name = 'Project'
        verbose_name_plural = 'Projects'

    def __str__(self):
        return self.name


class TeamMember(models.Model):
    """
    Team member model for managing team relationships.
    """
    ROLE_CHOICES = [
        ('developer', 'Developer'),
        ('manager', 'Manager'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='team_member')
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='team_members')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    is_active = models.BooleanField(default=True)
    joined_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'dashboard_team_member'
        verbose_name = 'Team Member'
        verbose_name_plural = 'Team Members'

    def __str__(self):
        return f"{self.user.username} - {self.project.name} ({self.role})"

    def clean(self):
        """Validate the team member model."""
        super().clean()
        if self.role not in dict(self.ROLE_CHOICES):
            raise ValidationError('Invalid role selected.')


class StandupSession(models.Model):
    """
    Standup session model for tracking daily standup meetings.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='standup_sessions')
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='standup_sessions')
    date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Standup content
    yesterday_work = models.TextField(blank=True, default='')
    today_plan = models.TextField(blank=True, default='')
    blockers = models.TextField(blank=True, default='')
    
    # AI processing results
    sentiment_score = models.FloatField(null=True, blank=True)
    sentiment_label = models.CharField(max_length=20, blank=True, default='')
    transcription_text = models.TextField(blank=True, default='')
    summary_text = models.TextField(blank=True, default='')
    ai_summary = models.TextField(blank=True, default='')  # AI-generated summary
    
    # Pipeline processing
    pipeline_completed = models.BooleanField(default=False)
    pipeline_completed_at = models.DateTimeField(null=True, blank=True)
    
    # Work item tracking
    work_items = models.ManyToManyField('WorkItemReference', blank=True, related_name='standup_sessions')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'dashboard_standup_session'
        verbose_name = 'Standup Session'
        verbose_name_plural = 'Standup Sessions'
        unique_together = ['user', 'date', 'project']

    def __str__(self):
        return f"{self.user.username} - {self.project.name} - {self.date}"

    def clean(self):
        """Validate the standup session model."""
        super().clean()
        if self.status not in dict(self.STATUS_CHOICES):
            raise ValidationError('Invalid status selected.')


class StandupAnalytics(models.Model):
    """
    Analytics model for tracking standup metrics and insights.
    """
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='analytics')
    date = models.DateField()
    
    # Team metrics
    total_participants = models.IntegerField(default=0)
    active_participants = models.IntegerField(default=0)
    average_sentiment = models.FloatField(null=True, blank=True)
    
    # Content metrics
    total_blockers = models.IntegerField(default=0)
    resolved_blockers = models.IntegerField(default=0)
    average_session_duration = models.FloatField(null=True, blank=True)  # in minutes
    
    # AI insights
    common_themes = models.JSONField(default=dict, blank=True)
    risk_indicators = models.JSONField(default=dict, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'dashboard_standup_analytics'
        verbose_name = 'Standup Analytics'
        verbose_name_plural = 'Standup Analytics'
        unique_together = ['project', 'date']

    def __str__(self):
        return f"{self.project.name} - {self.date}"

    @property
    def participation_rate(self):
        """Calculate participation rate."""
        if self.total_participants > 0:
            return (self.active_participants / self.total_participants) * 100
        return 0

    @property
    def blocker_resolution_rate(self):
        """Calculate blocker resolution rate."""
        if self.total_blockers > 0:
            return (self.resolved_blockers / self.total_blockers) * 100
        return 0


class Blocker(models.Model):
    """
    Model for tracking individual blockers and their resolution status.
    """
    CATEGORY_CHOICES = [
        ('technical', 'Technical'),
        ('dependencies', 'Dependencies'),
        ('resources', 'Resources'),
        ('communication', 'Communication'),
        ('other', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('resolved', 'Resolved'),
        ('cancelled', 'Cancelled'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    standup_session = models.ForeignKey(StandupSession, on_delete=models.CASCADE, related_name='individual_blockers')
    title = models.CharField(max_length=200)  # Short description/title of the blocker
    description = models.TextField()  # Full blocker description
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='technical')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')
    
    # Resolution tracking
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='resolved_blockers')
    resolution_notes = models.TextField(blank=True)
    
    # AI-generated insights
    ai_category_confidence = models.FloatField(null=True, blank=True)  # Confidence score for auto-categorization
    ai_suggested_actions = models.JSONField(default=list, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'dashboard_blocker'
        verbose_name = 'Blocker'
        verbose_name_plural = 'Blockers'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.get_status_display()}"
    
    @property
    def is_active(self):
        """Check if blocker is currently active."""
        return self.status == 'active'
    
    @property
    def days_active(self):
        """Calculate how many days this blocker has been active."""
        # Use standup session date as the logical start date for the blocker
        start_date = None
        try:
            # Prefer the standup session's date if available
            if self.standup_session and self.standup_session.date:
                start_date = self.standup_session.date
        except Exception:
            start_date = None

        if not start_date:
            # Fallback to creation date
            start_date = self.created_at.date()

        if self.status == 'resolved' and self.resolved_at:
            end_date = self.resolved_at.date()
        else:
            end_date = timezone.now().date()

        delta = (end_date - start_date).days
        # Ensure non-negative
        return max(0, delta)
    
    @property
    def color_class(self):
        """Return Bootstrap color class based on priority and status."""
        if self.status == 'resolved':
            return 'success'
        elif self.status == 'cancelled':
            return 'secondary'
        else:
            priority_colors = {
                'low': 'info',
                'medium': 'warning', 
                'high': 'danger',
                'critical': 'danger'
            }
            return priority_colors.get(self.priority, 'warning')
    
    def resolve(self, resolved_by_user, resolution_notes=''):
        """Mark this blocker as resolved."""
        self.status = 'resolved'
        self.resolved_at = timezone.now()
        self.resolved_by = resolved_by_user
        self.resolution_notes = resolution_notes
        self.save()
    
    def unresolve(self):
        """Mark this blocker as active again."""
        self.status = 'active'
        self.resolved_at = None
        self.resolved_by = None
        self.resolution_notes = ''
        self.save()


class WorkItemReference(models.Model):
    """
    Model for tracking work item references (GitHub PRs, Issues, Jira tickets) in standup sessions.
    """
    ITEM_TYPE_CHOICES = [
        ('github_pr', 'GitHub Pull Request'),
        ('github_issue', 'GitHub Issue'),
        ('jira_ticket', 'Jira Ticket'),
        ('branch', 'Git Branch'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('blocked', 'Blocked'),
        ('cancelled', 'Cancelled'),
    ]
    
    standup_session = models.ForeignKey(StandupSession, on_delete=models.CASCADE, related_name='work_item_refs')
    item_type = models.CharField(max_length=20, choices=ITEM_TYPE_CHOICES)
    item_id = models.CharField(max_length=100)  # PR number, issue number, ticket key, etc.
    item_url = models.URLField(blank=True)  # Full URL to the work item
    title = models.CharField(max_length=500, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    # Metadata from external systems
    external_data = models.JSONField(default=dict, blank=True)
    last_synced = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'dashboard_work_item_reference'
        verbose_name = 'Work Item Reference'
        verbose_name_plural = 'Work Item References'
        unique_together = ['standup_session', 'item_type', 'item_id']
    
    def __str__(self):
        return f"{self.get_item_type_display()} {self.item_id} - {self.title[:50]}"
    
    @property
    def display_name(self):
        """Return a user-friendly display name for the work item."""
        if self.item_type == 'github_pr':
            return f"PR #{self.item_id}"
        elif self.item_type == 'github_issue':
            return f"Issue #{self.item_id}"
        elif self.item_type == 'jira_ticket':
            return self.item_id  # Jira tickets already have readable keys like ABC-123
        elif self.item_type == 'branch':
            return f"Branch: {self.item_id}"
        return self.item_id


class TeamHealthTrend(models.Model):
    """
    Model for tracking team health trends over time with advanced analytics.
    """
    METRIC_TYPE_CHOICES = [
        ('participation', 'Participation Rate'),
        ('sentiment', 'Average Sentiment'),
        ('blockers', 'Blocker Resolution Rate'),
        ('work_items', 'Work Item Progress'),
    ]
    
    TREND_DIRECTION_CHOICES = [
        ('improving', 'Improving'),
        ('stable', 'Stable'),
        ('declining', 'Declining'),
        ('volatile', 'Volatile'),
    ]
    
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='health_trends')
    metric_type = models.CharField(max_length=20, choices=METRIC_TYPE_CHOICES)
    date = models.DateField()
    
    # Trend data
    current_value = models.FloatField()
    previous_value = models.FloatField(null=True, blank=True)
    change_percentage = models.FloatField(null=True, blank=True)
    trend_direction = models.CharField(max_length=20, choices=TREND_DIRECTION_CHOICES)
    
    # Statistical analysis
    rolling_average_7d = models.FloatField(null=True, blank=True)
    rolling_average_30d = models.FloatField(null=True, blank=True)
    standard_deviation = models.FloatField(null=True, blank=True)
    confidence_score = models.FloatField(null=True, blank=True)  # 0-1 scale
    
    # Insights and predictions
    predicted_next_value = models.FloatField(null=True, blank=True)
    anomaly_detected = models.BooleanField(default=False)
    alert_threshold_breached = models.BooleanField(default=False)
    
    # Contextual factors
    contributing_factors = models.JSONField(default=dict, blank=True)
    recommended_actions = models.JSONField(default=list, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'dashboard_team_health_trend'
        verbose_name = 'Team Health Trend'
        verbose_name_plural = 'Team Health Trends'
        unique_together = ['project', 'metric_type', 'date']
        indexes = [
            models.Index(fields=['project', 'metric_type', 'date']),
            models.Index(fields=['trend_direction', 'anomaly_detected']),
        ]
    
    def __str__(self):
        return f"{self.project.name} - {self.get_metric_type_display()} - {self.date}"
    
    @classmethod
    def calculate_trend(cls, project, metric_type, current_value, date=None):
        """Calculate trend analysis for a given metric."""
        if date is None:
            date = timezone.now().date()
        
        # Get previous data point
        previous_trend = cls.objects.filter(
            project=project,
            metric_type=metric_type,
            date__lt=date
        ).order_by('-date').first()
        
        previous_value = previous_trend.current_value if previous_trend else None
        change_percentage = None
        trend_direction = 'stable'
        
        if previous_value is not None and previous_value != 0:
            change_percentage = ((current_value - previous_value) / previous_value) * 100
            if change_percentage > 5:
                trend_direction = 'improving'
            elif change_percentage < -5:
                trend_direction = 'declining'
            elif abs(change_percentage) > 15:
                trend_direction = 'volatile'
        
        # Calculate rolling averages
        date_7d_ago = date - timedelta(days=7)
        date_30d_ago = date - timedelta(days=30)
        
        recent_trends = cls.objects.filter(
            project=project,
            metric_type=metric_type,
            date__gte=date_7d_ago,
            date__lt=date
        )
        
        rolling_7d = recent_trends.aggregate(
            avg=models.Avg('current_value')
        )['avg']
        
        monthly_trends = cls.objects.filter(
            project=project,
            metric_type=metric_type,
            date__gte=date_30d_ago,
            date__lt=date
        )
        
        rolling_30d = monthly_trends.aggregate(
            avg=models.Avg('current_value')
        )['avg']
        
        # Create or update trend record
        trend, created = cls.objects.update_or_create(
            project=project,
            metric_type=metric_type,
            date=date,
            defaults={
                'current_value': current_value,
                'previous_value': previous_value,
                'change_percentage': change_percentage,
                'trend_direction': trend_direction,
                'rolling_average_7d': rolling_7d,
                'rolling_average_30d': rolling_30d,
            }
        )
        
        return trend
    
    @property
    def is_concerning(self):
        """Check if this trend indicates concerning team health."""
        concerning_conditions = [
            self.trend_direction == 'declining' and self.change_percentage and self.change_percentage < -10,
            self.anomaly_detected,
            self.alert_threshold_breached,
            self.metric_type == 'participation' and self.current_value < 50,  # Low participation
            self.metric_type == 'sentiment' and self.current_value < -0.3,  # Negative sentiment
            self.metric_type == 'blockers' and self.current_value < 70,  # Low blocker resolution
        ]
        return any(concerning_conditions)


class DataRetentionPolicy(models.Model):
    """
    Model for managing data retention policies and automated cleanup.
    """
    POLICY_TYPE_CHOICES = [
        ('standup_sessions', 'Standup Sessions'),
        ('voice_recordings', 'Voice Recordings'),
        ('analytics_data', 'Analytics Data'),
        ('chat_history', 'Chat History'),
        ('error_logs', 'Error Logs'),
        ('audit_trails', 'Audit Trails'),
    ]
    
    policy_type = models.CharField(max_length=30, choices=POLICY_TYPE_CHOICES, unique=True)
    retention_days = models.IntegerField(default=365)
    auto_cleanup_enabled = models.BooleanField(default=True)
    anonymise_before_deletion = models.BooleanField(default=False)
    
    # Cleanup schedule
    last_cleanup_run = models.DateTimeField(null=True, blank=True)
    next_cleanup_due = models.DateTimeField(null=True, blank=True)
    cleanup_frequency_days = models.IntegerField(default=7)  # Run weekly
    
    # Compliance
    legal_hold_exemption = models.BooleanField(default=False)
    compliance_notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'dashboard_data_retention_policy'
        verbose_name = 'Data Retention Policy'
        verbose_name_plural = 'Data Retention Policies'
    
    def __str__(self):
        return f"{self.get_policy_type_display()} - {self.retention_days} days"
    
    @classmethod
    def cleanup_expired_data(cls):
        """Run cleanup for all policies that are due."""
        policies = cls.objects.filter(
            auto_cleanup_enabled=True,
            next_cleanup_due__lte=timezone.now()
        )
        
        results = {}
        for policy in policies:
            results[policy.policy_type] = policy.run_cleanup()
        
        return results
    
    def run_cleanup(self):
        """Run cleanup for this specific policy."""
        cutoff_date = timezone.now().date() - timedelta(days=self.retention_days)
        deleted_count = 0
        
        if self.policy_type == 'standup_sessions':
            if self.anonymise_before_deletion:
                # Anonymise before deletion
                sessions = StandupSession.objects.filter(date__lt=cutoff_date)
                for session in sessions:
                    session.yesterday_work = '[ANONYMIZED]'
                    session.today_plan = '[ANONYMIZED]'
                    session.blockers = '[ANONYMIZED]'
                    session.transcription_text = '[ANONYMIZED]'
                    session.save()
            else:
                deleted_count = StandupSession.objects.filter(
                    date__lt=cutoff_date
                ).delete()[0]
        
        # Update cleanup timestamps
        self.last_cleanup_run = timezone.now()
        self.next_cleanup_due = timezone.now() + timedelta(days=self.cleanup_frequency_days)
        self.save()
        
        return {
            'deleted_count': deleted_count,
            'cutoff_date': cutoff_date,
            'anonymised': self.anonymise_before_deletion,
        }


class DashboardMetrics(models.Model):
    """
    Model for storing dashboard metrics for analytics and tracking.
    """
    METRIC_TYPE_CHOICES = [
        ('standup_completion', 'Standup Completion Rate'),
        ('sentiment_average', 'Average Sentiment'),
        ('productivity_score', 'Productivity Score'),
        ('team_health', 'Team Health Score'),
        ('issue_resolution_time', 'Issue Resolution Time'),
        ('ai_processing_success', 'AI Processing Success Rate'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='dashboard_metrics')
    metric_type = models.CharField(max_length=50, choices=METRIC_TYPE_CHOICES)
    value = models.FloatField()
    date = models.DateField()
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'dashboard_metrics'
        ordering = ['-date', '-created_at']
        unique_together = ['user', 'metric_type', 'date']

    def __str__(self):
        return f"{self.user.username} - {self.metric_type} - {self.date}"


class TeamMetrics(models.Model):
    """
    Model for storing team-level metrics and analytics.
    """
    METRIC_TYPE_CHOICES = [
        ('team_velocity', 'Team Velocity'),
        ('collaboration_score', 'Collaboration Score'),
        ('communication_frequency', 'Communication Frequency'),
        ('productivity_trend', 'Productivity Trend'),
        ('satisfaction_score', 'Team Satisfaction'),
    ]

    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='team_metrics')
    metric_type = models.CharField(max_length=50, choices=METRIC_TYPE_CHOICES)
    value = models.FloatField()
    date = models.DateField()
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'dashboard_team_metrics'
        ordering = ['-date', '-created_at']
        unique_together = ['team', 'metric_type', 'date']

    def __str__(self):
        return f"{self.team.name} - {self.metric_type} - {self.date}"


class TeamHealthAlert(models.Model):
    """
    Model for tracking team health alerts and early warning notifications.
    """
    SEVERITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    ALERT_TYPE_CHOICES = [
        ('sentiment_decline', 'Sentiment Decline'),
        ('engagement_drop', 'Engagement Drop'),
        ('blocker_increase', 'Blocker Increase'),
        ('productivity_concern', 'Productivity Concern'),
        ('team_member_burnout', 'Team Member Burnout'),
        ('communication_gap', 'Communication Gap'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('acknowledged', 'Acknowledged'),
        ('resolved', 'Resolved'),
        ('dismissed', 'Dismissed'),
    ]
    
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='health_alerts')
    team_member = models.ForeignKey(TeamMember, on_delete=models.CASCADE, null=True, blank=True, 
                                  help_text="Specific team member if alert is individual-focused")
    alert_type = models.CharField(max_length=50, choices=ALERT_TYPE_CHOICES)
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default='medium')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    context_data = models.JSONField(default=dict, help_text="Additional context and metrics")
    
    # Analytics fields
    confidence_score = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        help_text="AI confidence in this alert (0.0 - 1.0)"
    )
    
    # Management fields
    created_at = models.DateTimeField(auto_now_add=True)
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    acknowledged_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                      related_name='acknowledged_alerts')
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                  related_name='resolved_alerts')
    
    class Meta:
        db_table = 'dashboard_team_health_alert'
        verbose_name = 'Team Health Alert'
        verbose_name_plural = 'Team Health Alerts'
        ordering = ['-created_at', '-severity']
        
    def __str__(self):
        return f"{self.get_severity_display()} Alert: {self.title} - {self.project.name}"
    
    @property
    def is_active(self):
        """Check if alert is currently active."""
        return self.status == 'active'
    
    @property
    def requires_action(self):
        """Check if alert requires immediate management action."""
        return self.severity in ['high', 'critical'] and self.status == 'active'
    
    def acknowledge(self, user):
        """Mark alert as acknowledged by a manager."""
        self.status = 'acknowledged'
        self.acknowledged_by = user
        self.acknowledged_at = timezone.now()
        self.save()
    
    def resolve(self, user):
        """Mark alert as resolved."""
        self.status = 'resolved'
        self.resolved_by = user
        self.resolved_at = timezone.now()
        self.save()
