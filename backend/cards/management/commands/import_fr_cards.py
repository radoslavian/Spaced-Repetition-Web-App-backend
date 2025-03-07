from django.core.management.base import BaseCommand

from cards.management.fr_importer.items_importer.modules.items_importer import \
    PendingItemsImporter, MemorizedItemsImporter
from users.models import User


class Command(BaseCommand):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.items_importer = None

    def handle(self, *args, **kwargs):
        self._set_items_importer(kwargs)
        self._set_template(kwargs)
        self._import_from_category(kwargs)
        self._import_into_category(kwargs)
        self.items_importer.import_cards_into_db()

    def _set_template(self, main_options):
        if main_options.get("template_by_id", None):
            self.items_importer.set_template_by_uuid(
                main_options["template_by_id"])
        elif main_options.get("template_by_title", None):
            self.items_importer.set_template_by_title(
                main_options["template_by_title"])

    def _set_items_importer(self, main_options):
        user = self._get_user(main_options)
        if user:
            self.items_importer = MemorizedItemsImporter(
                main_options["elements_path"], user)
        else:
            self.items_importer = PendingItemsImporter(
                main_options["elements_path"])

    @staticmethod
    def _get_user(main_options):
        user = None
        options = Command._get_user_options(main_options)
        if options:
            user = User.objects.get(**options)
        return user

    @staticmethod
    def _get_user_options(main_options):
        """
        Options for getting a user instance from the database.
        """
        options = {}
        if main_options.get("user_id", None):
            options = {"id": main_options["user_id"]}
        elif main_options.get("username", None):
            options = {"username": main_options["username"]}
        return options

    def _import_from_category(self, main_options):
        if main_options.get("import_from_category", None):
            self.items_importer.set_import_category(
                main_options["import_from_category"])

    def _import_into_category(self, main_options):
        if main_options.get("import_into_category", None):
            self.items_importer.set_categories(
                [main_options["import_into_category"]])

    def add_arguments(self, parser):
        parser.add_argument("elements_path", type=str,
                            help="Path to an elements.xml file.")
        parser.add_argument("--user-id", type=str,
                            help="Import cards for a user"
                                 " identified by an id (UUIDv4).")
        parser.add_argument("--username", type=str,
                            help="Import cards for a user"
                                 " identified by a username.")
        parser.add_argument("--template-by-id", type=str,
                            help="Specify a card template with an id (UUIDv4)/")
        parser.add_argument("--template-by-title", type=str,
                            help="Set up a template by a title.")
        parser.add_argument("--import-from-category", type=str,
                            help="Select category in elements.xml from which "
                                 "items should be imported")
        parser.add_argument("--import-into-category", type=str,
                            help="Import into categories in the database"
                                 "identified by their UUIDs.")
