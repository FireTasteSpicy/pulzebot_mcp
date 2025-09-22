from config.demo_time import now as demo_now
from django.contrib import admin
from django.utils import timezone
from .models import (
    Team, UserProfile, Project, StandupSession, WorkItemReference,
    StandupAnalytics, TeamHealthTrend, TeamHealthAlert
)


@admin.register(StandupAnalytics)
class StandupAnalyticsAdmin(admin.ModelAdmin):
    """Admin interface for Standup Analytics - MVP metrics tracking."""
    list_display = [
        'project', 'date', 'participation_rate', 'average_sentiment', 
        'blocker_resolution_rate', 'total_participants', 'active_participants'
    ]
    list_filter = ['project', 'date', 'total_participants']
    search_fields = ['project__name']
    readonly_fields = ['created_at', 'updated_at', 'participation_rate', 'blocker_resolution_rate']
    date_hierarchy = 'date'
    
    fieldsets = (
        ('Project & Date', {
            'fields': ('project', 'date')
        }),
        ('Participation Metrics', {
            'fields': ('total_participants', 'active_participants', 'participation_rate'),
            'description': 'Track team participation in standup sessions'
        }),
        ('Sentiment Analysis', {
            'fields': ('average_sentiment',),
            'description': 'AI-derived sentiment from standup content'
        }),
        ('Blocker Tracking', {
            'fields': ('total_blockers', 'resolved_blockers', 'blocker_resolution_rate'),
            'description': 'Track blockers reported and resolved'
        }),
        ('Session Data', {
            'fields': ('average_session_duration',),
        }),
        ('AI Insights', {
            'fields': ('common_themes', 'risk_indicators'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def participation_rate(self, obj):
        return f"{obj.participation_rate:.1f}%" if obj.participation_rate else "N/A"
    participation_rate.short_description = "Participation %"
    participation_rate.admin_order_field = 'active_participants'
    
    def blocker_resolution_rate(self, obj):
        return f"{obj.blocker_resolution_rate:.1f}%" if obj.blocker_resolution_rate else "N/A"
    blocker_resolution_rate.short_description = "Blocker Resolution %"


@admin.register(TeamHealthTrend)
class TeamHealthTrendAdmin(admin.ModelAdmin):
    """Admin interface for Team Health Trends - MVP metrics only."""
    list_display = [
        'project', 'metric_type', 'date', 'current_value', 'trend_direction', 
        'change_percentage', 'anomaly_detected'
    ]
    list_filter = [
        'metric_type', 'trend_direction', 'anomaly_detected', 
        'alert_threshold_breached', 'project'
    ]
    search_fields = ['project__name']
    readonly_fields = [
        'created_at', 'updated_at', 'rolling_average_7d', 'rolling_average_30d',
        'change_percentage'
    ]
    date_hierarchy = 'date'
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('project', 'metric_type', 'date')
        }),
        ('Current Metrics', {
            'fields': ('current_value', 'previous_value', 'change_percentage', 'trend_direction'),
            'description': 'Current metric values and trend analysis'
        }),
        ('Statistical Analysis', {
            'fields': ('rolling_average_7d', 'rolling_average_30d', 'standard_deviation', 'confidence_score'),
            'description': '7-day and 30-day rolling averages'
        }),
        ('Predictions & Alerts', {
            'fields': ('predicted_next_value', 'anomaly_detected', 'alert_threshold_breached'),
            'description': 'AI predictions and alert status'
        }),
        ('Insights', {
            'fields': ('contributing_factors', 'recommended_actions'),
            'classes': ('collapse',),
            'description': 'AI-generated insights and recommendations'
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        # Filter to only show MVP metrics
        qs = super().get_queryset(request)
        return qs.filter(metric_type__in=['participation', 'sentiment', 'blockers', 'work_items'])


@admin.register(WorkItemReference)
class WorkItemReferenceAdmin(admin.ModelAdmin):
    """Admin interface for Work Item References - GitHub/Jira integration."""
    list_display = [
        'display_name', 'standup_session', 'item_type', 'status', 
        'title', 'last_synced', 'created_at'
    ]
    list_filter = ['item_type', 'status', 'created_at', 'last_synced']
    search_fields = ['item_id', 'title', 'item_url']
    readonly_fields = ['created_at', 'updated_at', 'display_name', 'last_synced']
    
    fieldsets = (
        ('Work Item Info', {
            'fields': ('standup_session', 'item_type', 'item_id', 'item_url', 'title', 'status')
        }),
        ('External Integration', {
            'fields': ('external_data', 'last_synced'),
            'description': 'Data synced from GitHub/Jira APIs'
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(StandupSession)
class StandupSessionAdmin(admin.ModelAdmin):
    """Admin interface for Standup Sessions."""
    list_display = [
        'user', 'project', 'date', 'status', 'sentiment_label', 
        'sentiment_score', 'created_at'
    ]
    list_filter = ['status', 'sentiment_label', 'project', 'date']
    search_fields = ['user__username', 'project__name', 'yesterday_work', 'today_plan']
    readonly_fields = [
        'created_at', 'updated_at', 'sentiment_score', 'sentiment_label',
        'transcription_text', 'summary_text'
    ]
    date_hierarchy = 'date'
    
    fieldsets = (
        ('Session Info', {
            'fields': ('user', 'project', 'date', 'status')
        }),
        ('Standup Content', {
            'fields': ('yesterday_work', 'today_plan', 'blockers'),
            'description': 'Core standup responses'
        }),
        ('AI Analysis', {
            'fields': ('sentiment_score', 'sentiment_label', 'transcription_text', 'summary_text'),
            'classes': ('collapse',),
            'description': 'AI-generated analysis and transcription'
        }),
        ('Work Items', {
            'fields': ('work_items',),
            'description': 'Referenced GitHub/Jira work items'
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    filter_horizontal = ['work_items']


# Basic admin registrations for core models (Team, UserProfile, Project)
# These use default admin interfaces since they're simple configuration models

@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'team', 'role', 'created_at']
    list_filter = ['team', 'role']
    search_fields = ['user__username', 'user__email', 'user__first_name', 'user__last_name']


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ['name', 'status', 'created_at']
    list_filter = ['status']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(TeamHealthAlert)
class TeamHealthAlertAdmin(admin.ModelAdmin):
    list_display = ['title', 'project', 'alert_type', 'severity', 'status', 'created_at', 'confidence_score']
    list_filter = ['alert_type', 'severity', 'status', 'created_at', 'project']
    search_fields = ['title', 'description', 'project__name']
    readonly_fields = ['created_at', 'confidence_score']
    
    fieldsets = (
        ('Alert Information', {
            'fields': ('project', 'team_member', 'alert_type', 'severity', 'status')
        }),
        ('Content', {
            'fields': ('title', 'description', 'context_data')
        }),
        ('Analytics', {
            'fields': ('confidence_score', 'created_at')
        }),
        ('Management', {
            'fields': ('acknowledged_by', 'acknowledged_at', 'resolved_by', 'resolved_at')
        }),
    )
    
    actions = ['acknowledge_alerts', 'resolve_alerts']
    
    def acknowledge_alerts(self, request, queryset):
        updated = queryset.filter(status='active').update(
            status='acknowledged',
            acknowledged_by=request.user,
            acknowledged_at=demo_now()
        )
        self.message_user(request, f'{updated} alerts acknowledged.')
    acknowledge_alerts.short_description = 'Acknowledge selected alerts'
    
    def resolve_alerts(self, request, queryset):
        updated = queryset.filter(status__in=['active', 'acknowledged']).update(
            status='resolved',
            resolved_by=request.user,
            resolved_at=demo_now()
        )
        self.message_user(request, f'{updated} alerts resolved.')
    resolve_alerts.short_description = 'Resolve selected alerts'
