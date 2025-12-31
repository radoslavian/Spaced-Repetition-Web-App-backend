from card_types.card_managers.cloze_occluder import ClozeOccluder
from card_types.card_managers.manager_abc import CardManager
from cards.models import Card


class OccludedClozeDeletion(CardManager):
    Occluder = ClozeOccluder

    def save_cards(self):
        cloze_occluder = self.Occluder(self.card_note.card_description["text"])
        cards_details = cloze_occluder.get_cards()
        card_note_metadata = {
            "managed-cards-mapping": []
        }

        for card_details in cards_details:
            card = self.get_card_by_cloze_id(card_details) or Card()
            self._save_card(card,
                            {"text": card_details["front"]},
                            {"text": card_details["back"]})
            card_note_metadata["managed-cards-mapping"].append(
                {
                    "card-id": card["id"],
                    "cloze-id": card_details["cloze-id"]
                }
            )
        self.card_note.metadata = card_note_metadata
        self._synchronize_cards_with_clozes(card_note_metadata)

    def _synchronize_cards_with_clozes(self, current_metadata):
        """
        Removes cards for which clozes had been removed.
        """
        metadata_card_ids = [card_details["card-id"] for card_details
                             in current_metadata["managed-cards-mapping"]]
        for card in self.card_note.cards.all():
            if card["id"] not in metadata_card_ids:
                card.delete()

    def get_card_by_cloze_id(self, card_details):
        cloze_id = card_details["cloze-id"]
        cards_mapping = self.card_note.metadata.get(
            "managed-cards-mapping", [])
        card_id = next((card_detail["card-id"] for card_detail in cards_mapping
                        if card_detail["cloze-id"] == cloze_id), None)
        return card_id and self.card_note.cards.filter(
            id__exact=card_id).first()
