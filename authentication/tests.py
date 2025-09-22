"""
Sensible test suite for the authentication module.

Tests cover essential functionality:
- Login/logout flows
- Role-based redirection  
- URL routing
- Basic error handling
"""

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User

try:
    from dashboard.models import UserProfile
except ImportError:
    UserProfile = None


class AuthenticationTestCase(TestCase):
    """Base test case for authentication views"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        
        # Create basic test users
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        self.manager_user = User.objects.create_user(
            username='manager',
            password='testpass123'
        )
        
        # Create profiles if available
        if UserProfile:
            UserProfile.objects.get_or_create(
                user=self.user,
                defaults={'role': 'developer'}
            )
            UserProfile.objects.get_or_create(
                user=self.manager_user,
                defaults={'role': 'manager'}
            )


class LoginViewTests(AuthenticationTestCase):
    """Tests for login functionality"""
    
    def test_login_page_loads(self):
        """Test login page displays correctly"""
        response = self.client.get(reverse('authentication:login'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Username')
        self.assertContains(response, 'Password')
    
    def test_successful_login(self):
        """Test user can login successfully"""
        response = self.client.post(reverse('authentication:login'), {
            'username': 'testuser',
            'password': 'testpass123'
        })
        self.assertEqual(response.status_code, 302)  # Redirect after login
    
    def test_invalid_credentials(self):
        """Test login fails with wrong password"""
        response = self.client.post(reverse('authentication:login'), {
            'username': 'testuser',
            'password': 'wrongpass'
        })
        self.assertEqual(response.status_code, 200)  # Stay on login page
        self.assertContains(response, 'Please enter a correct username and password')


class LogoutViewTests(AuthenticationTestCase):
    """Tests for logout functionality"""
    
    def test_logout_redirects_to_login(self):
        """Test logout redirects to login page"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(reverse('authentication:logout'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)
    
    def test_logout_clears_session(self):
        """Test logout actually logs user out"""
        self.client.login(username='testuser', password='testpass123')
        self.client.post(reverse('authentication:logout'))
        
        # Try accessing protected view - should redirect to login
        response = self.client.get(reverse('authentication:role_redirect'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)


class RoleRedirectTests(AuthenticationTestCase):
    """Tests for role-based redirection"""
    
    def test_unauthenticated_user_redirected_to_login(self):
        """Test unauthenticated users go to login"""
        response = self.client.get(reverse('authentication:role_redirect'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)
    
    def test_authenticated_user_gets_redirected(self):
        """Test authenticated users get redirected somewhere"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('authentication:role_redirect'))
        self.assertEqual(response.status_code, 302)
        # Should redirect to some dashboard, not back to login
        self.assertNotIn('login', response.url)


class AccessDeniedTests(TestCase):
    """Tests for access denied view"""
    
    def test_access_denied_page_loads(self):
        """Test access denied page displays"""
        response = self.client.get(reverse('authentication:access_denied'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Access Denied')


class URLTests(TestCase):
    """Tests for URL routing"""
    
    def test_urls_resolve(self):
        """Test all authentication URLs resolve correctly"""
        urls_to_test = [
            ('authentication:login', '/auth/login/'),
            ('authentication:logout', '/auth/logout/'),
            ('authentication:role_redirect', '/auth/redirect/'),
            ('authentication:access_denied', '/auth/access-denied/'),
        ]
        
        for url_name, expected_path in urls_to_test:
            with self.subTest(url=url_name):
                url = reverse(url_name)
                self.assertEqual(url, expected_path)


if __name__ == '__main__':
    import sys
    from django.test.utils import get_runner
    from django.conf import settings
    
    if not settings.configured:
        import os
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
        import django
        django.setup()
    
    TestRunner = get_runner(settings)
    test_runner = TestRunner()
    failures = test_runner.run_tests(["authentication.tests"])
    sys.exit(bool(failures))