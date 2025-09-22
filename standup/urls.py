from django.urls import path, include
from .views import (
    StandupView, submit_standup, get_work_items_context, StandupReportView,
    resolve_blocker, unresolve_blocker, parse_blockers_from_text
)

app_name = 'standup'

urlpatterns = [
    # Main standup interface
    path('', StandupView.as_view(), name='standup'),
    path('form/', StandupView.as_view(), name='standup_form'),  # alias for clarity
    
    # Standup submission and processing
    path('submit/', submit_standup, name='submit_standup'),
    path('process/', StandupView.as_view(), name='standup_process'),  # for tests
    
    # Reports and analytics
    path('reports/', include([
        path('', StandupReportView.as_view(), name='standup_report'),
        path('analytics/', StandupReportView.as_view(), name='standup_analytics'),  # alias
    ])),
    
    # API endpoints
    path('api/', include([
        path('work-items-context/', get_work_items_context, name='work_items_context'),
        path('blockers/', include([
            path('resolve/<int:blocker_id>/', resolve_blocker, name='resolve_blocker'),
            path('unresolve/<int:blocker_id>/', unresolve_blocker, name='unresolve_blocker'),
            path('parse/', parse_blockers_from_text, name='parse_blockers'),
        ])),
    ])),
]