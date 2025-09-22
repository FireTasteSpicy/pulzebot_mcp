from django.contrib import admin
from .models import AIProcessingResult

@admin.register(AIProcessingResult)
class AIProcessingResultAdmin(admin.ModelAdmin):
    """Admin interface for AI Processing Results."""
    list_display = ('user', 'processing_type', 'status', 'created_at', 'processing_time')
    list_filter = ('processing_type', 'status', 'created_at')
    search_fields = ('user__username', 'user__email', 'processing_type')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'processing_type', 'status')
        }),
        ('Processing Data', {
            'fields': ('input_text', 'result_data', 'processing_time', 'model_version')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
