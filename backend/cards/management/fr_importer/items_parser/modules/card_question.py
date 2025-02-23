from cards.management.fr_importer.items_parser.modules.card_side import CardSide


class Question(CardSide):
    definition = property(lambda self: self._get_line(0))
    examples = property(lambda self: self._get_examples(from_line=1))
