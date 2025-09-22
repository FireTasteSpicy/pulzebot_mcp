"""
Essential tests for the config module.

Tests cover critical functionality:
- URL routing works correctly
- Settings configuration is valid
- WSGI/ASGI applications can be loaded
- Root redirect behavior
"""
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse, resolve
from django.conf import settings
from django.core.wsgi import get_wsgi_application
from django.core.asgi import get_asgi_application


class URLConfigurationTest(TestCase):
    """Test URL routing configuration"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpass')
    
    def test_root_redirect_authenticated_user(self):
        """Test root redirects authenticated users to dashboard"""
        self.client.force_login(self.user)
        response = self.client.get('/')
        
        self.assertEqual(response.status_code, 302)
        self.assertIn('/dashboard/', response.url)
    
    def test_root_redirect_anonymous_user(self):
        """Test root redirects anonymous users to login"""
        response = self.client.get('/')
        
        self.assertEqual(response.status_code, 302)
        self.assertIn('/auth/login/', response.url)
    
    def test_admin_url_accessible(self):
        """Test admin URL is accessible"""
        response = self.client.get('/admin/')
        
        # Should redirect to admin login, not 404
        self.assertEqual(response.status_code, 302)
    
    def test_health_check_url(self):
        """Test health check endpoint exists"""
        response = self.client.get('/health/')
        
        # Should be accessible (may return error but not 404)
        self.assertNotEqual(response.status_code, 404)


class SettingsConfigurationTest(TestCase):
    """Test settings configuration is valid"""
    
    def test_secret_key_exists(self):
        """Test SECRET_KEY is configured"""
        self.assertIsNotNone(settings.SECRET_KEY)
        self.assertGreater(len(settings.SECRET_KEY), 0)
    
    def test_installed_apps_configured(self):
        """Test INSTALLED_APPS contains required Django apps"""
        required_apps = [
            'django.contrib.admin',
            'django.contrib.auth',
            'django.contrib.contenttypes',
            'django.contrib.sessions',
        ]
        
        for app in required_apps:
            self.assertIn(app, settings.INSTALLED_APPS)
    
    def test_database_configured(self):
        """Test database configuration exists"""
        self.assertIn('default', settings.DATABASES)
        self.assertIn('ENGINE', settings.DATABASES['default'])
    
    def test_debug_setting_is_boolean(self):
        """Test DEBUG setting is properly configured as boolean"""
        self.assertIsInstance(settings.DEBUG, bool)


class WSGIASGIConfigurationTest(TestCase):
    """Test WSGI and ASGI configuration"""
    
    def test_wsgi_application_loads(self):
        """Test WSGI application can be loaded"""
        import os
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
        
        # Should not raise an exception
        application = get_wsgi_application()
        self.assertIsNotNone(application)
    
    def test_asgi_application_loads(self):
        """Test ASGI application can be loaded"""
        import os
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
        
        # Should not raise an exception
        application = get_asgi_application()
        self.assertIsNotNone(application)


class URLResolutionTest(TestCase):
    """Test critical URL patterns resolve correctly"""
    
    def test_dashboard_namespace_resolves(self):
        """Test dashboard URLs can be resolved"""
        try:
            url = reverse('dashboard:dashboard')
            self.assertIsNotNone(url)
        except Exception:
            # If dashboard URLs don't exist, that's a configuration issue
            self.fail("Dashboard namespace not properly configured")
    
    def test_authentication_namespace_resolves(self):
        """Test authentication URLs can be resolved"""
        try:
            url = reverse('authentication:login')
            self.assertIsNotNone(url)
        except Exception:
            self.fail("Authentication namespace not properly configured")
    
    def test_health_check_resolves(self):
        """Test health check URL resolves"""
        try:
            url = reverse('health_check')
            self.assertEqual(url, '/health/')
        except Exception:
            self.fail("Health check URL not properly configured")


class ChromeDevToolsHandlerTest(TestCase):
    """Test Chrome DevTools handler"""
    
    def test_chrome_devtools_endpoint(self):
        """Test Chrome DevTools endpoint returns proper response"""
        response = self.client.get('/.well-known/appspecific/com.chrome.devtools.json')
        
        self.assertEqual(response.status_code, 204)
        self.assertEqual(response['Content-Type'], 'application/json')