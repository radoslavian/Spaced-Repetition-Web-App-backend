from django.test import TestCase
from django.contrib.auth import get_user_model
from cards.models import Category


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

    def setting_default_category_test_data(self):
        self.root_category = Category(name="Root Category")
        self.root_category.save()
        self.sub_category = Category(
            name="sub category",
            parent=self.root_category
        )
        self.sub_category.save()

    def test_setting_default_category(self):
        """Selecting root category as a default for new user.
        """
        self.setting_default_category_test_data()
        User = get_user_model()
        self.user = User(
            username="superuser",
            email="superuser@email.com",
            password="testpass123"
        )
        self.user.save()
        selected_categories = self.user.selected_categories.all()

        NUMBER_OF_SELECTED_CATEGORIES = 1
        self.assertEqual(selected_categories.count(),
                         NUMBER_OF_SELECTED_CATEGORIES)
        self.assertEqual(selected_categories[0], self.root_category)

    def test_default_no_category(self):
        """Selecting default category when there are no categories.
        """
        User = get_user_model()
        user = User(
            username="superuser",
            email="superuser@email.com",
            password="testpass123"
        )
        user.save()

        NUMBER_OF_SELECTED_CATEGORIES = 0
        selected_categories = user.selected_categories.all()
        self.assertEqual(selected_categories.count(),
                         NUMBER_OF_SELECTED_CATEGORIES)

    def test_setting_multiple_default_categories(self):
        """When there are multiple root categories, all should be
        set as selected.
        """
        self.setting_default_category_test_data()
        self.second_root_category = Category(name="Root 2 category")
        self.second_root_category.save()
        User = get_user_model()
        self.user = User(
            username="superuser",
            email="superuser@email.com",
            password="testpass123"
        )
        self.user.save()
        user_categories = self.user.selected_categories.all()

        NUMBER_OF_SELECTED_CATEGORIES = 2
        self.assertEqual(self.user.selected_categories.count(),
                         NUMBER_OF_SELECTED_CATEGORIES)
        self.assertIn(self.root_category, user_categories)
        self.assertIn(self.second_root_category, user_categories)

    def test_list_selected_categories_ids(self):
        UserModel = get_user_model()
        user = UserModel.objects.create(username="user",
                                        email="user@userdomain.com",
                                        password="testpass")
        category = Category.objects.create(name="Category")
        user.selected_categories.add(category)
        user.save()

        self.assertTrue(type(user.selected_categories_ids) is list)
        self.assertEqual(len(user.selected_categories_ids), 1)
        self.assertEqual(user.selected_categories_ids[0],
                         str(category.id))
