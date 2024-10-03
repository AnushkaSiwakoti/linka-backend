from django.test import TestCase
from django.core.exceptions import ObjectDoesNotExist
from .models import BaseUser, CustomUserManager

class TestCustomUserManager(TestCase):
    def test_create_user_success(self):
        user_manager = CustomUserManager()
        user = user_manager.create_user('test@example.com', 'testuser', 'password123')
        self.assertEqual(user.email, 'test@example.com')
        self.assertTrue(user.check_password('password123'))

    def test_create_user_no_email(self):
        user_manager = CustomUserManager()
        with self.assertRaises(ValueError):
            user_manager.create_user(None, 'testuser', 'password123')

    def test_create_user_no_username(self):
        user_manager = CustomUserManager()
        with self.assertRaises(ValueError):
            user_manager.create_user('test@example.com', None, 'password123')

class TestAccountViews(TestCase):
    def setUp(self):
        self.user_manager = CustomUserManager()
        self.user_manager.create_user('existing@example.com', 'existinguser', 'password123')

    def test_create_account(self):
        response = self.client.post('/create-account/', {
            'email': 'newuser@example.com',
            'username': 'newuser',
            'password': 'password123'
        })
        self.assertEqual(response.status_code, 201)

    def test_verify_account(self):
        response = self.client.post('/verify-account/', {
            'username': 'existinguser',
            'password': 'password123'
        })
        self.assertEqual(response.status_code, 200)
