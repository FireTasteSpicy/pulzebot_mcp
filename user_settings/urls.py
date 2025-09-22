from django.urls import path
from . import views

app_name = 'user_settings'

urlpatterns = [
    path('', views.user_settings_view, name='settings'),
    path('export/', views.data_export_view, name='export-data'),
    path('revoke-ai-consent/', views.revoke_ai_consent_view, name='revoke-ai-consent'),
    path('save-integrations/', views.save_integrations_view, name='save-integrations'),
    path('api/check-consent/', views.check_consent_api, name='check-consent-api'),
]
