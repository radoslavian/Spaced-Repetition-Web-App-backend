from cards.management.fr_importer.modules.card_side import CardSide


class Question(CardSide):
    def __init__(self, question):
        """
        question - contents of <item><q></q></item> (without <q></q> tags).
        """
        super().__init__(question)

    def _get_examples(self, from_line=1) -> list[str]:
        return list(filter(None, self.side_contents.split("\n")[from_line:]))

    definition = property(lambda self: self._get_line(0))
    examples = property(lambda self: self._get_examples(from_line=1))
