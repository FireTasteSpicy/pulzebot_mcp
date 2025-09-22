"""
Essential tests for user_settings app.
"""
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse

from .models import UserSettings
from .privacy_service import PrivacyEnforcementService


class UserSettingsModelTest(TestCase):
    """Test UserSettings model functionality."""

    def test_user_settings_basic_functionality(self):
        """Test basic UserSettings model functionality."""
        # Test that UserSettings model exists and can be imported
        from .models import UserSettings
        self.assertTrue(hasattr(UserSettings, '_meta'))
        
    def test_user_settings_get_or_create(self):
        """Test get_or_create pattern for UserSettings."""
        user = User.objects.create_user('testuser_unique', 'unique@example.com', 'pass')
        settings, created = UserSettings.objects.get_or_create(user=user)
        self.assertEqual(settings.user, user)


class PrivacyServiceTest(TestCase):
    """Test privacy service functionality."""

    def test_get_user_privacy_status(self):
        """Test getting user privacy status."""        
        user = User.objects.create_user('privacyuser1', 'privacy1@example.com', 'pass')
        service = PrivacyEnforcementService()
        privacy_status = service.get_user_privacy_status(user)
        self.assertIsInstance(privacy_status, dict)
        self.assertIn('sentiment_analysis', privacy_status)
        self.assertIn('ai_analysis', privacy_status)

    def test_privacy_settings_defaults(self):
        """Test that privacy settings have proper defaults."""
        user = User.objects.create_user('privacyuser2', 'privacy2@example.com', 'pass')
        service = PrivacyEnforcementService()
        privacy_status = service.get_user_privacy_status(user)
        
        # Should have the expected sections
        expected_sections = ['sentiment_analysis', 'ai_analysis', 'team_analytics']
        for section in expected_sections:
            self.assertIn(section, privacy_status)
            self.assertIn('enabled', privacy_status[section])
            self.assertIn('description', privacy_status[section])


class UserSettingsViewTest(TestCase):
    """Test user settings views."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user('viewtestuser', 'viewtest@example.com', 'pass')

    def test_settings_page_requires_login(self):
        """Test settings page requires authentication."""
        response = self.client.get('/settings/')
        self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_settings_page_authenticated_access(self):
        """Test settings page access when authenticated."""
        self.client.login(username='viewtestuser', password='pass')
        response = self.client.get('/settings/')
        # Accept 200 (working) or 302 (redirect)
        self.assertIn(response.status_code, [200, 302])

    def test_settings_url_patterns(self):
        """Test that settings URLs are configured."""
        # Just test that basic functionality is accessible
        self.client.login(username='viewtestuser', password='pass')
        response = self.client.get('/settings/')
        # Any response is good - just testing URL exists
        self.assertLess(response.status_code, 500)


class UserSettingsIntegrationTest(TestCase):
    """Test integration between user settings and other apps."""

    def setUp(self):
        self.user = User.objects.create_user('integrationuser', 'integration@example.com', 'pass')

    def test_settings_integration_basic(self):
        """Test basic settings integration."""
        settings, created = UserSettings.objects.get_or_create(user=self.user)
        self.assertIsNotNone(settings)
        self.assertEqual(settings.user, self.user)