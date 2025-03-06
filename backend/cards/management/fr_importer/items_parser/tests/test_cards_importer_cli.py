import uuid
from io import StringIO
from unittest import skip, mock
from unittest.mock import patch, MagicMock

from django.test import TestCase

from django.contrib.auth import get_user_model
from django.core.management import call_command, CommandError

from cards.models import CardTemplate


class CLIImportingCardsTestCase(TestCase):
    """
    Importing cards and their user review-data.
    """
    command = "import_fr_cards"

    @classmethod
    def setUpTestData(cls):
        cls.options = {"elements": "path/to/elements.xml"}
        cls.path_memorized_items_importer = (
            "cards.management.commands.import_fr_cards"
            ".MemorizedItemsImporter")
        cls.path_pending_items_importer = (
            "cards.management.commands.import_fr_cards"
            ".PendingItemsImporter")
        cls.User = get_user_model()
        cls.user = cls.User(username="test user")
        cls.user.save()
        cls.template = CardTemplate(title="template one")
        cls.template.save()

    def setUp(self):
        self.command_output = StringIO()

    def get_stripped_command_output(self):
        return self.command_output.getvalue().rstrip()

    def test_import_cards_no_review_data(self):
        """
        Calling a command with an elements.xml path and without user-id
        invokes PendingItemsImporter class.
        """
        with self.patch_pending_items_importer() as items_importer:
            call_command(self.command, self.options["elements"])
            items_importer.assert_called_once_with(self.options["elements"])

    def test_import_cards_for_user_id(self):
        """
        Path + user-uuid-MemorizedItemsImporter receives path
        and a user instance.
        """
        options = {"user_id": str(self.user.id)}
        with self.patch_memorized_items_importer() as memorized_items_importer:
            call_command(self.command,
                         self.options["elements"],
                         **options)
            memorized_items_importer.assert_called_once_with(
                self.options["elements"], self.user)

    def test_import_cards_for_user_by_username(self):
        options = {"username": self.user.username}
        with self.patch_memorized_items_importer() as memorized_items_importer:
            call_command(self.command,
                         self.options["elements"],
                         **options)
            memorized_items_importer.assert_called_once_with(
                self.options["elements"], self.user)

    def test_setting_template_by_uuid(self):
        options = {"template_by_id": str(self.template.id)}
        mocked_instance = MagicMock()

        with patch(self.path_pending_items_importer, autospec=True,
                   return_value=mocked_instance):
            call_command(self.command,
                         self.options["elements"],
                         **options)
            mocked_instance.set_template_by_uuid.assert_called_once_with(
                options["template_by_id"])

    def test_setting_template_by_title(self):
        options = {"template_by_title": self.template.title}
        mocked_instance = MagicMock()

        with patch(self.path_pending_items_importer, autospec=True,
                   return_value=mocked_instance):
            call_command(self.command,
                         self.options["elements"],
                         **options)
            mocked_instance.set_template_by_title.assert_called_once_with(
                options["template_by_title"])

    def test_import_from_category(self):
        options = {"import_from_category": "category 1.category 2.category 3"}
        mocked_instance = MagicMock()

        with patch(self.path_pending_items_importer, autospec=True,
                   return_value=mocked_instance):
            call_command(self.command,
                         self.options["elements"],
                         **options)
            mocked_instance.set_import_category.assert_called_once_with(
                options["import_from_category"])

    def test_into_categories(self):
        options = {"import_into_categories":
                       [uuid.uuid4(), uuid.uuid4(), uuid.uuid4()]}

        mocked_instance = MagicMock()

        with patch(self.path_pending_items_importer, autospec=True,
                   return_value=mocked_instance):
            call_command(self.command,
                         self.options["elements"],
                         **options)
            mocked_instance.set_categories.assert_called_once_with(
                options["import_into_categories"])

    def patch_pending_items_importer(self):
        return patch(self.path_pending_items_importer, autospec=True)

    def patch_memorized_items_importer(self):
        return patch(self.path_memorized_items_importer, autospec=True)

    def test_calling_from_cli(self):
        """
        An import command is available at all.
        """
        raise_error = lambda: call_command(
            self.command, stdout=self.command_output)
        self.assertRaises(CommandError, raise_error)
