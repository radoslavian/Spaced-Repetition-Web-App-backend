from django.core.management.base import BaseCommand

from cards.management.fr_importer.items_importer.modules.items_importer import \
    PendingItemsImporter, MemorizedItemsImporter
from users.models import User


class Command(BaseCommand):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.items_importer = None

    def handle(self, *args, **kwargs):
        main_options = {
            "elements_path": kwargs.get("elements", None),
            "user_id": kwargs.get("user_id", None),
            "username":  kwargs.get("username", None),
            "template_by_id": kwargs.get("template_by_id", None),
            "template_by_title": kwargs.get("template_by_title", None),
            "import_from_category": kwargs.get("import_from_category", None),
            "import_into_categories": kwargs.get("import_into_categories",
                                                 None)
        }
        self._set_items_importer(main_options)
        self._set_template(main_options)
        self._import_from_category(main_options)
        self._import_into_categories(main_options)

    def _set_template(self, main_options):
        if main_options["template_by_id"]:
            self.items_importer.set_template_by_uuid(
                main_options["template_by_id"])
        elif main_options["template_by_title"]:
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
        if main_options["user_id"]:
            options = {"id": main_options["user_id"]}
        elif main_options["username"]:
            options = {"username": main_options["username"]}
        return options

    def _import_from_category(self, main_options):
        if main_options["import_from_category"]:
            self.items_importer.set_import_category(
                main_options["import_from_category"])

    def _import_into_categories(self, main_options):
        if main_options["import_into_categories"]:
            self.items_importer.set_categories(
                main_options["import_into_categories"])

    def add_arguments(self, parser):
        parser.add_argument("elements", type=str,
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
        parser.add_argument("--import-into-categories", type=str,
                            help="Import into categories in the database"
                                 "identified by their UUIDs.")
