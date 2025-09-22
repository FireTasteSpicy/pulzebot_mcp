"""
Database models for the integrations app.
"""
from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model

User = get_user_model()


class ExternalIntegration(models.Model):
    """
    Model for storing external platform integration configurations.
    """
    PLATFORM_CHOICES = [
        ('jira', 'Jira'),
        ('github', 'GitHub'),
        ('slack', 'Slack'),
        ('teams', 'Microsoft Teams'),
        ('gitlab', 'GitLab'),
        ('bitbucket', 'Bitbucket'),
    ]

    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('error', 'Error'),
        ('testing', 'Testing'),
    ]

    platform = models.CharField(max_length=20, choices=PLATFORM_CHOICES)
    name = models.CharField(max_length=100)
    api_key = models.CharField(max_length=500, blank=True)
    api_secret = models.CharField(max_length=500, blank=True)
    base_url = models.URLField(blank=True)
    webhook_url = models.URLField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='inactive')
    is_active = models.BooleanField(default=False)
    last_sync = models.DateTimeField(null=True, blank=True)
    sync_interval = models.IntegerField(default=300)  # in seconds
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'integrations_external_integration'
        verbose_name = 'External Integration'
        verbose_name_plural = 'External Integrations'
        unique_together = ['platform', 'name']

    def __str__(self):
        return f"{self.name} ({self.platform})"

    def clean(self):
        """Validate the external integration model."""
        super().clean()
        if self.platform not in dict(self.PLATFORM_CHOICES):
            raise ValidationError('Invalid platform selected.')
        if self.status not in dict(self.STATUS_CHOICES):
            raise ValidationError('Invalid status selected.')


class JiraIntegration(models.Model):
    """
    Model for Jira-specific integration data.
    """
    integration = models.OneToOneField(
        ExternalIntegration, 
        on_delete=models.CASCADE, 
        related_name='jira_integration'
    )
    project_key = models.CharField(max_length=20)
    username = models.CharField(max_length=100)
    board_id = models.IntegerField(null=True, blank=True)
    sprint_field = models.CharField(max_length=50, default='Sprint')
    story_points_field = models.CharField(max_length=50, default='Story Points')
    epic_field = models.CharField(max_length=50, default='Epic Link')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'integrations_jira_integration'
        verbose_name = 'Jira Integration'
        verbose_name_plural = 'Jira Integrations'

    def __str__(self):
        return f"Jira - {self.project_key}"


class GitHubIntegration(models.Model):
    """
    Model for GitHub-specific integration data.
    """
    integration = models.OneToOneField(
        ExternalIntegration, 
        on_delete=models.CASCADE, 
        related_name='github_integration'
    )
    repository = models.CharField(max_length=200)
    owner = models.CharField(max_length=100)
    branch = models.CharField(max_length=100, default='main')
    webhook_secret = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'integrations_github_integration'
        verbose_name = 'GitHub Integration'
        verbose_name_plural = 'GitHub Integrations'

    def __str__(self):
        return f"GitHub - {self.owner}/{self.repository}"


class GitHubRepository(models.Model):
    """
    Model for storing GitHub repository information.
    """
    integration = models.ForeignKey(GitHubIntegration, on_delete=models.CASCADE, related_name='repositories')
    full_name = models.CharField(max_length=200)  # e.g., "owner/repo"
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    private = models.BooleanField(default=False)
    default_branch = models.CharField(max_length=50, default='main')
    language = models.CharField(max_length=50, blank=True)
    stars_count = models.IntegerField(default=0)
    forks_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'integrations_github_repository'
        unique_together = ['integration', 'full_name']

    def __str__(self):
        return self.full_name


class ExternalTicket(models.Model):
    """
    Model for storing external tickets from Jira, GitHub, etc.
    """
    integration = models.ForeignKey(
        ExternalIntegration, 
        on_delete=models.CASCADE, 
        related_name='external_tickets'
    )
    external_id = models.CharField(max_length=100)
    title = models.CharField(max_length=500)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=50)
    priority = models.CharField(max_length=20, blank=True)
    assignee = models.CharField(max_length=100, blank=True)
    reporter = models.CharField(max_length=100, blank=True)
    created_date = models.DateTimeField(null=True, blank=True)
    updated_date = models.DateTimeField(null=True, blank=True)
    due_date = models.DateTimeField(null=True, blank=True)
    labels = models.JSONField(default=list, blank=True)
    custom_fields = models.JSONField(default=dict, blank=True)
    last_synced = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'integrations_external_ticket'
        verbose_name = 'External Ticket'
        verbose_name_plural = 'External Tickets'
        unique_together = ['integration', 'external_id']

    def __str__(self):
        return f"{self.integration.platform} - {self.external_id}"


class ExternalPullRequest(models.Model):
    """
    Model for storing external pull requests from GitHub, GitLab, etc.
    """
    integration = models.ForeignKey(
        ExternalIntegration, 
        on_delete=models.CASCADE, 
        related_name='external_pull_requests'
    )
    external_id = models.CharField(max_length=100)
    title = models.CharField(max_length=500)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20)  # open, closed, merged
    author = models.CharField(max_length=100)
    source_branch = models.CharField(max_length=100)
    target_branch = models.CharField(max_length=100)
    created_date = models.DateTimeField(null=True, blank=True)
    updated_date = models.DateTimeField(null=True, blank=True)
    merged_date = models.DateTimeField(null=True, blank=True)
    review_status = models.CharField(max_length=20, default='pending')
    files_changed = models.IntegerField(default=0)
    additions = models.IntegerField(default=0)
    deletions = models.IntegerField(default=0)
    labels = models.JSONField(default=list, blank=True)
    last_synced = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'integrations_external_pull_request'
        verbose_name = 'External Pull Request'
        verbose_name_plural = 'External Pull Requests'
        unique_together = ['integration', 'external_id']

    def __str__(self):
        return f"{self.integration.platform} - {self.external_id}"


class WorkItem(models.Model):
    """
    Model for storing work items from external platforms (issues, PRs, tickets).
    """
    ITEM_TYPE_CHOICES = [
        ('issue', 'Issue'),
        ('pull_request', 'Pull Request'),
        ('bug', 'Bug'),
        ('feature', 'Feature'),
        ('task', 'Task'),
        ('epic', 'Epic'),
    ]

    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]

    STATUS_CHOICES = [
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('closed', 'Closed'),
        ('resolved', 'Resolved'),
    ]

    integration = models.ForeignKey(ExternalIntegration, on_delete=models.CASCADE, related_name='work_items')
    external_id = models.CharField(max_length=100)  # ID from the external platform
    item_type = models.CharField(max_length=20, choices=ITEM_TYPE_CHOICES)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    assignee = models.CharField(max_length=100, blank=True)
    reporter = models.CharField(max_length=100, blank=True)
    labels = models.JSONField(default=list, blank=True)
    repository = models.ForeignKey(GitHubRepository, on_delete=models.SET_NULL, null=True, blank=True)
    external_url = models.URLField(blank=True)
    created_at_source = models.DateTimeField(null=True, blank=True)
    updated_at_source = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'integrations_work_item'
        unique_together = ['integration', 'external_id']

    def __str__(self):
        return f"{self.item_type}: {self.title}"


class IntegrationSyncLog(models.Model):
    """
    Model for logging integration synchronization activities.
    """
    SYNC_TYPES = [
        ('tickets', 'Tickets Sync'),
        ('pull_requests', 'Pull Requests Sync'),
        ('commits', 'Commits Sync'),
        ('users', 'Users Sync'),
        ('projects', 'Projects Sync'),
    ]

    STATUS_CHOICES = [
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('partial', 'Partial Success'),
    ]

    integration = models.ForeignKey(
        ExternalIntegration, 
        on_delete=models.CASCADE, 
        related_name='sync_logs'
    )
    sync_type = models.CharField(max_length=20, choices=SYNC_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    items_processed = models.IntegerField(default=0)
    items_created = models.IntegerField(default=0)
    items_updated = models.IntegerField(default=0)
    items_failed = models.IntegerField(default=0)
    error_message = models.TextField(blank=True)
    sync_duration = models.FloatField(null=True, blank=True)  # in seconds
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'integrations_sync_log'
        verbose_name = 'Integration Sync Log'
        verbose_name_plural = 'Integration Sync Logs'
        ordering = ['-started_at']

    def __str__(self):
        return f"{self.integration.platform} - {self.sync_type} - {self.started_at}"

    @property
    def success_rate(self):
        """Calculate success rate."""
        total = self.items_processed
        if total > 0:
            successful = self.items_created + self.items_updated
            return (successful / total) * 100
        return 0
