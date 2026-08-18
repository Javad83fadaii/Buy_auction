from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse

from .constants import ADMIN_ROLE, OPERATOR_ROLE, VIEWER_ROLE
from .services import ensure_default_roles

User = get_user_model()


class AccountsTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        ensure_default_roles()
        cls.password = 'StrongPass123!'
        cls.admin_group = Group.objects.get(name=ADMIN_ROLE)
        cls.operator_group = Group.objects.get(name=OPERATOR_ROLE)
        cls.viewer_group = Group.objects.get(name=VIEWER_ROLE)

        cls.admin_user = cls.create_user('admin_user', cls.admin_group, is_staff=True, is_superuser=True)
        cls.staff_admin_user = cls.create_user('staff_admin_user', cls.admin_group)
        cls.operator_user = cls.create_user('operator_user', cls.operator_group)
        cls.viewer_user = cls.create_user('viewer_user', cls.viewer_group)
        cls.inactive_user = cls.create_user('inactive_user', cls.operator_group, is_active=False)

    @classmethod
    def create_user(cls, username, group, **extra_fields):
        user = User.objects.create_user(
            username=username,
            password=cls.password,
            email=f'{username}@example.com',
            **extra_fields,
        )
        user.groups.add(group)
        user.refresh_from_db()
        return user

    def test_successful_login(self):
        response = self.client.post(
            reverse('accounts:login'),
            {'username': self.operator_user.username, 'password': self.password},
            follow=True,
        )

        self.assertRedirects(response, reverse('dashboard'))
        self.assertTrue(response.context['user'].is_authenticated)

    def test_failed_login(self):
        response = self.client.post(
            reverse('accounts:login'),
            {'username': self.operator_user.username, 'password': 'wrong-password'},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'نام کاربری یا رمز عبور صحیح نیست.')

    def test_logout(self):
        self.client.force_login(self.operator_user)
        response = self.client.post(reverse('accounts:logout'), follow=True)

        self.assertRedirects(response, reverse('accounts:login'))
        self.assertFalse('_auth_user_id' in self.client.session)

    def test_anonymous_user_redirected_from_dashboard(self):
        response = self.client.get(reverse('dashboard'))
        self.assertRedirects(
            response,
            f"{reverse('accounts:login')}?next={reverse('dashboard')}",
        )

    def test_inactive_user_cannot_login(self):
        response = self.client.post(
            reverse('accounts:login'),
            {'username': self.inactive_user.username, 'password': self.password},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'نام کاربری یا رمز عبور صحیح نیست.')
        self.assertFalse('_auth_user_id' in self.client.session)

    def test_admin_has_admin_access(self):
        self.client.force_login(self.admin_user)
        response = self.client.get(reverse('admin:index'))

        self.assertEqual(response.status_code, 200)

    def test_admin_role_user_gets_staff_access(self):
        self.assertTrue(self.staff_admin_user.is_staff)
        self.client.force_login(self.staff_admin_user)
        response = self.client.get(reverse('admin:index'))

        self.assertEqual(response.status_code, 200)

    def test_operator_cannot_access_admin(self):
        self.client.force_login(self.operator_user)
        response = self.client.get(reverse('admin:index'))

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('admin:login'), response.url)

    def test_operator_can_access_operator_dashboard(self):
        self.client.force_login(self.operator_user)
        response = self.client.get(reverse('operator_dashboard'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'داشبورد اپراتور')

    def test_viewer_cannot_access_operator_dashboard(self):
        self.client.force_login(self.viewer_user)
        response = self.client.get(reverse('operator_dashboard'))

        self.assertEqual(response.status_code, 403)

    def test_viewer_can_access_general_dashboard(self):
        self.client.force_login(self.viewer_user)
        response = self.client.get(reverse('dashboard'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.viewer_user.username)
