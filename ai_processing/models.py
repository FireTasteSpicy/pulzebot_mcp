"""
Database models for the AI processing app.
"""
from django.db import models
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

User = get_user_model()


class AIProcessingResult(models.Model):
    """
    Model for storing AI processing results with privacy controls.
    """
    PROCESSING_TYPES = [
        ('transcription', 'Speech to Text Transcription'),
        ('sentiment_analysis', 'Sentiment Analysis'),
        ('summary_generation', 'Summary Generation'),
        ('entity_extraction', 'Entity Extraction'),
        ('intent_classification', 'Intent Classification'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ai_processing_results')
    processing_type = models.CharField(max_length=30, choices=PROCESSING_TYPES)
    input_text = models.TextField()
    result_data = models.JSONField(default=dict)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    error_message = models.TextField(blank=True)
    processing_time = models.FloatField(null=True, blank=True)  # in seconds
    model_version = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'ai_processing_result'
        verbose_name = 'AI Processing Result'
        verbose_name_plural = 'AI Processing Results'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'processing_type']),
            models.Index(fields=['status', 'created_at']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.processing_type} - {self.created_at}"

    def clean(self):
        """Validate the AI processing result model."""
        super().clean()
        if self.processing_type not in dict(self.PROCESSING_TYPES):
            raise ValidationError('Invalid processing type selected.')
        if self.status not in dict(self.STATUS_CHOICES):
            raise ValidationError('Invalid status selected.')

    @property
    def is_successful(self):
        """Check if the processing was successful."""
        return self.status == 'completed' and not self.error_message

    @property
    def processing_time_ms(self):
        """Return processing time in milliseconds."""
        return self.processing_time * 1000 if self.processing_time else None
