from django.test import TestCase
from card_types.models import CardNote
from card_types.tests.test_front_back_back_front import RelatedFieldsTestData
from cards.models import Card


class GeneratingCorrectCards(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.cloze_id_one = "one"
        cls.cloze_id_two = "two"
        cls.cloze_id_three = "three"
        cls.text = (f'<cloze id="{cls.cloze_id_one}">cloze one</cloze> '
                    f'<cloze id="{cls.cloze_id_two}">cloze two</cloze> '
                    f'<cloze id="{cls.cloze_id_three}">cloze three</cloze>')
        card_description = {
            "text": cls.text
        }
        card_type = "occluded-cloze-deletion"
        cls.note = CardNote.objects.create(card_description=card_description,
                                           card_type=card_type)
        cls._get_cards_from_note_metadata()

    @classmethod
    def _get_cards_from_note_metadata(cls):
        """
        Fetches cards from note metadata.
        For this reason, though not a test itself, it is important for metadata
        testing.
        """
        cls.cloze_one_card_details = [
            card for card in
            cls.note.metadata["managed-cards-mapping"]
            if card["cloze-id"] == cls.cloze_id_one]
        cls.cloze_two_card_details = [card for card in
                                      cls.note.metadata[
                                          "managed-cards-mapping"]
                                      if card["cloze-id"] == cls.cloze_id_two]
        cloze_one_card_id = cls.cloze_one_card_details[0]["card-id"]
        cls.cloze_one_card = cls.note.cards.get(id=cloze_one_card_id)
        cloze_two_card_id = cls.cloze_two_card_details[0]["card-id"]
        cls.cloze_two_card = cls.note.cards.get(id=cloze_two_card_id)

    def test_metadata_card_mapping_count(self):
        """
        Metadata should list two managed cards.
        """
        card_metadata_count = len(self.note.metadata["managed-cards-mapping"])
        expected_number = 3
        self.assertEqual(card_metadata_count, expected_number)

    def test_number_created_cards(self):
        """
        A single card for each cloze should be created.
        """
        expected_number = 3
        received_number = self.note.cards.count()
        self.assertEqual(expected_number, received_number)

    # for testing purposes:
    # [...] - gap for an actual question
    # {...} - occluded text that is not part of a question

    def test_question_answer_cloze_one(self):
        """
        Note metadata should correctly indicate card for a given cloze.
        Cards are obtained using note metadata in the _get_cards_from_note_metadata
        helper method.
        """
        expected_question = '[...] {...} {...}'
        expected_answer = '[cloze one] cloze two cloze three'

        self.assertEqual(expected_question, self.cloze_one_card.front)
        self.assertEqual(expected_answer, self.cloze_one_card.back)

    def test_question_answer_cloze_two(self):
        expected_question = '{...} [...] {...}'
        expected_answer = 'cloze one [cloze two] cloze three'

        self.assertEqual(expected_question, self.cloze_two_card.front)
        self.assertEqual(expected_answer, self.cloze_two_card.back)


class NoteUpdate(TestCase):
    """
    Updating a note without altering card description.
    """
    card_description_text = ('<cloze id="one">cloze one</cloze> '
                             '<cloze id="two">cloze two</cloze>')
    card_description = {
        "text": card_description_text
    }

    @classmethod
    def setUpTestData(cls):
        # 1st save
        cls.card_note = CardNote.objects.create(
            card_description=cls.card_description,
            card_type="occluded-cloze-deletion")
        cards = cls.card_note.cards.all()

        cls.card1_id = cards[0].id
        cls.card1_front = cards[0].front
        cls.card2_id = cards[1].id
        cls.card2_front = cards[1].front

        # 2nd save
        cls.card_note.save()

    def test_keeping_card_ids(self):
        """
        Saving a note shouldn't change the ids of existing cards.
        """
        card1 = self.card_note.cards.all()[0]
        card2 = self.card_note.cards.all()[1]

        self.assertSetEqual({card1.id, card2.id},
                            {self.card1_id, self.card2_id})

    def test_card_identity(self):
        """
        Cards can't be swapped between updates.
        * Questions/answers for given clozes can't get swapped between
        different cards during calls to CardNote.save() - if cloze_id remains
        the same.
        * Test is simplified and only compares card fronts (current and saved
        before a second call to .save() ).
        """
        card1 = self.card_note.cards.filter(id__exact=self.card1_id).first()
        card2 = self.card_note.cards.filter(id__exact=self.card2_id).first()

        self.assertEqual(card1.front, self.card1_front)
        self.assertEqual(card2.front, self.card2_front)

    def test_card_number(self):
        """
        Number of cards should remain the same after an update.
        """
        expected_number = 2
        received_number = self.card_note.cards.count()

        self.assertEqual(expected_number, received_number)


class ManagingClozes(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.cloze_id = "one"
        cls.cloze_text = "cloze one"
        cls.card_description_text = (f'<cloze id="{cls.cloze_id}">'
                                     f'{cls.cloze_text}</cloze>')

    def setUp(self):
        self.card_note = CardNote.objects.create(
            card_description={"text": self.card_description_text},
            card_type="occluded-cloze-deletion")

    def tearDown(self):
        self.card_note.delete()

    def test_cloze_id_collision(self):
        """
        Raising an exception in case of a cloze ids collision.
        Should raise an exception if there are two (or more) clozes with
        the same id.
        """
        double_cloze = 2
        card_description = {
            "text": self.card_description_text * double_cloze
        }
        expected_error_message = ('<cloze> id collision '
                                  f'detected: the "{self.cloze_id}"'
                                  f' count is "{double_cloze}"')
        self.card_note.card_description = card_description

        with self.assertRaisesMessage(ValueError, expected_error_message):
            self.card_note.save()

    def test_deleting_cloze(self):
        """
        Deleting a cloze with a given id should cause dropping off a card.
        Updating the card_description should cause deletion of the cards for
        which there are no related clozes.
        """
        card_description = {"text": '<cloze id="new-one">new cloze</cloze>'}
        card_for_deletion = self.card_note.cards.first()
        self.card_note.card_description = card_description
        self.card_note.save()
        expected_cards_count = 1

        self.assertRaises(Card.DoesNotExist, card_for_deletion.refresh_from_db)
        self.assertEqual(expected_cards_count, Card.objects.count())

    def test_adding_new_cloze(self):
        """
        Adding a new cloze should keep the card for the first one intact.
        """
        new_cloze_text = '<cloze id="new-cloze-id">new cloze</cloze>'
        card = self.card_note.cards.first()
        original_card_id = card.id
        original_card_back = card.back

        self.card_note.card_description["text"] += new_cloze_text
        self.card_note.save()
        card.refresh_from_db()

        self.assertIn(original_card_back, card.back)
        self.assertEqual(original_card_id, card.id)

    def test_no_cloze_id(self):
        """
        Cloze without an id should raise an exception.
        """
        cloze_text = "no id cloze"
        card_description = {"text": f'<cloze>{cloze_text}</cloze>'}
        self.card_note.card_description = card_description
        expected_exception_message = 'One or more clozes has no id.'

        with self.assertRaisesMessage(KeyError, expected_exception_message):
            self.card_note.save()


class ReferencedFields(TestCase, RelatedFieldsTestData):
    """
    Audio, images; template.
    """
    @classmethod
    def setUpTestData(cls):
        cls._prepare_images()
        cls._prepare_audio_entries()
        cls._prepare_template()
        cls.card_description = {
            "text": '<cloze id="one">cloze one</cloze>'
                    '<cloze id="two">cloze two</cloze>',
            "front": {
                "audio": cls.front_audio.id.hex,
                "images": [cls.front_image.id.hex]
            },
            "back": {
                "audio": cls.back_audio.id.hex,
                "images": [cls.back_image.id.hex]
            },
            "template_title": cls.template_description["title"]
        }
        card_note_details = dict(card_description=cls.card_description,
                                 card_type="occluded-cloze-deletion")
        cls.card_note = CardNote.objects.create(**card_note_details)

        cls.card1: Card = cls.card_note.cards.all()[0]
        cls.card2: Card = cls.card_note.cards.all()[1]

    def test_front_audio(self):
        """
        Both cards should reference the same front audio entry.
        """
        self.assertEqual(self.card1.front_audio.id.hex,
                         self.front_audio.id.hex)
        self.assertEqual(self.card2.front_audio.id.hex,
                         self.front_audio.id.hex)

    def test_back_audio(self):
        """
        Both cards should reference the same back audio entry.
        """
        self.assertEqual(self.card1.back_audio.id.hex,
                         self.back_audio.id.hex)
        self.assertEqual(self.card2.back_audio.id.hex,
                         self.back_audio.id.hex)

    def test_front_image(self):
        expected_number = 1
        self.assertEqual(len(self.card1.front_images), expected_number)
        self.assertEqual(len(self.card2.front_images), expected_number)
        self.assertEqual(self.card1.front_images[0].id.hex,
                         self.front_image.id.hex)
        self.assertEqual(self.card2.front_images[0].id.hex,
                         self.front_image.id.hex)

    def test_back_image(self):
        expected_number = 1
        self.assertEqual(len(self.card1.back_images), expected_number)
        self.assertEqual(len(self.card2.back_images), expected_number)
        self.assertEqual(self.card1.back_images[0].id.hex,
                         self.back_image.id.hex)
        self.assertEqual(self.card2.back_images[0].id.hex,
                         self.back_image.id.hex)

    def test_template(self):
        self.assertEqual(self.card1.template, self.template)