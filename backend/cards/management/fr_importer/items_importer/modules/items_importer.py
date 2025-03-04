from typing import Sequence
from uuid import UUID

from cards.management.fr_importer.items_importer.modules.imported_card import \
    ImportedCard
from cards.management.fr_importer.items_parser.items_parser import ItemsParser
from cards.models import Category, CardTemplate


class ItemsImporter:
    SingleImportedCard = ImportedCard

    def __init__(self, elements_path: str):
        self._category_xpath = None
        self._template = None
        self._categories = None
        self._items_parser = ItemsParser(elements_path)

    def import_cards_into_db(self):
        """
        Uploads items from FullRecall's elements.xml into the database.
        """
        if self._category_xpath:
            self._items_parser.import_xpath = self._category_xpath

        for cart_to_import in self._items_parser:
            imported_card = self.SingleImportedCard(cart_to_import)
            self.configure_imported_card(imported_card)
            imported_card.save()

    def configure_imported_card(self, imported_card):
        if self._categories:
            imported_card.set_categories(self._categories)
        if self._template:
            imported_card.set_template(self._template)

    def set_template(self, template: CardTemplate):
        self._template = template

    def set_template_by_uuid(self, template_uuid: UUID | str):
        template = CardTemplate.objects.get(id=template_uuid)
        self.set_template(template)

    def set_template_by_title(self, template_title: str):
        template = CardTemplate.objects.get(title=template_title)
        self.set_template(template)

    def set_categories(self, categories: Sequence[Category | UUID | str]):
        """
        Set categories into which cards should be imported.
        """
        self._categories = categories

    def set_import_category(self, category_path: str):
        """
        Set category from which items are imported into db.
        Path format: category1.category2.category3
        """
        categories = category_path.split(".")
        xpath = "./" + "/".join(f"category[@name='{category}']"
                                for category in categories)
        self.set_import_category_xpath(xpath)

    def set_import_category_xpath(self, xpath: str):
        """
        Set category (in elements.xml) xpath from which items are imported.
        """
        self._category_xpath = xpath
