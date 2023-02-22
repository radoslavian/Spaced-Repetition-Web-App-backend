from django.test import TestCase
from django.contrib.auth import get_user_model

# Create your tests here.


class CustomUserTest(TestCase):
    def test_create_user(self):
        user_model = get_user_model()
        user = user_model.objects.create_user(
            username="will",
            email="will@email.com",
            password="testpass123"
        )

        self.assertEqual(user.username, "will")
        self.assertEqual(user.email, "will@email.com")
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_create_superuser(self):
        user_model = get_user_model()
        admin_user = user_model.objects.create_superuser(
            username="superadmin",
            email="superadmin@email.com",
            password="testpass123"
        )
        self.assertEqual(admin_user.username, "superadmin")
        self.assertEqual(admin_user.email, "superadmin@email.com")
        self.assertTrue(admin_user.is_active)
        self.assertTrue(admin_user.is_staff)
        self.assertTrue(admin_user.is_superuser)

    def test_add_template(self):
        pass
