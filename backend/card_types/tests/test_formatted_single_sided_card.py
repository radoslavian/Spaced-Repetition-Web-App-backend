from unittest import skip

from django.db import IntegrityError
from django.test import TestCase

from card_types.models import CardNote
from card_types.tests.test_front_back_back_front import NoteFromCard
from cards.models import CardTemplate, Card


class SpecificFields(TestCase):
    """
    Case for fields unique for the single-sided card type.
    """

    @classmethod
    def setUpTestData(cls):
        cls._setup_front_template()
        cls._setup_back_template()
        cls.example_sentences = [
            "sentence one",
            "sentence two"
        ]

    @classmethod
    def _setup_back_template(cls):
        cls.found_answer_example_sentences = "example answer sentences found!"
        back_template_body = """
        {% load phonetics_converter %}
        {{ side.answer }}
        {{ side.phonetics.key }}
        {% if side.example_sentences %}
         """ + cls.found_answer_example_sentences + """
        {% endif %}
        {% for sentence in side.example_sentences %}
              <p class="example-sentence">{{ sentence }}</p>
        {% endfor %}
        {{ side.phonetics.value|convert_ascii_phonetics|safe }}
        """
        cls.back_template_title = "database template for back side"
        cls.back_template = CardTemplate.objects.create(
            title=cls.back_template_title,
            body=back_template_body)

    @classmethod
    def _setup_front_template(cls):
        cls.found_question_example_sentences = ("example question sentences "
                                                "found!")
        front_template_body = """
            {{ side.card_question_definition }}
            {% if side.example_sentences %}
             """ + cls.found_question_example_sentences + """
            {% endif %}
            {% for sentence in side.example_sentences %}
              <p class="example-sentence">{{ sentence }}</p>
            {% endfor %}
            """
        cls.front_template_title = "database template for front side"
        cls.db_front_template = CardTemplate.objects.create(
            title=cls.front_template_title,
            body=front_template_body)

    def setUp(self):
        self.question_definition = "question definition"
        self.card_answer = "card answer"
        self.card_description = {
            "_front": {
                "card_question_definition": self.question_definition,
                "formatting_template_db": self.front_template_title
            },
            "_back": {
                "answer": self.card_answer,
                "formatting_template_db": self.back_template_title,
            }
        }
        self.note = CardNote.objects.create(
            card_description=self.card_description,
            card_type="single-sided-formatted")

    def tearDown(self):
        CardNote.objects.all().delete()

    def test_number_of_cards(self):
        """
        Note should create a single card.
        """
        expected_number = 1
        self.assertEqual(expected_number, self.note.cards.count())
        self.assertEqual(expected_number, Card.objects.count())

    def test_definition(self):
        """
        Rendering definition of the word/phrase (obligatory field).
        """
        card_front = self.note.cards.first().front
        self.assertIn(self.question_definition, card_front)

    @skip("Requires non-nullable Card.front field; will be updated in "
          "a different branch.")
    def test_empty_front(self):
        """
        Should fail if no definition is given.
        """
        card_description = {
            **self.card_description,
            "_front": {}
        }
        self.note.card_description = card_description
        self.assertRaises(IntegrityError, self.note.save)

    @skip("Requires non-nullable Card.back field; will be updated in "
          "a different branch.")
    def test_empty_back(self):
        card_description = {
            **self.card_description,
            "_back": {}
        }
        self.note.card_description = card_description
        self.assertRaises(IntegrityError, self.note.save)

    def test_question_example_sentences(self):
        """
        Should render one or more example sentences under the definition.
        """
        card_description = {
            **self.card_description,
            "_front": {
                **self.card_description["_front"],
                "example_sentences": self.example_sentences
            }
        }
        self.note.card_description = card_description
        self.note.save()
        card = self.note.cards.first()

        self.assertIn(self.example_sentences[0], card.front)
        self.assertIn(self.example_sentences[1], card.front)

    def test_question_no_example_sentences(self):
        """
        Shouldn't render any block for example sentences if they aren't present.
        """
        card = self.note.cards.first()
        excluded_paragraph = 'class="example-sentence"'

        self.assertNotIn(excluded_paragraph, card.front)
        self.assertNotIn(self.found_question_example_sentences, card.front)

    def test_answer(self):
        """
        Should render an (obligatory) answer field.
        """
        card = self.note.cards.first()
        self.assertIn(self.card_answer, card.back)

    def test_phonetics(self):
        """
        Should render phonetics key-word along with phonetics string.
        Currently only ASCII "Techland" to IPA conversion is available.
        """
        phonetics_key = 'phonetics key'
        phonetics_value = 'I'
        phonetics = {
            'key': phonetics_key,
            'format': 'ASCII',
            'value': phonetics_value
        }
        card_description = {
            **self.card_description,
            "_back": {
                **self.card_description["_back"],
                "phonetics": phonetics
            }
        }
        ipa_phonetics = ('<span class="phonetic-entity" title="ɪ - i - as in '
                         'pit, hill or y - as in happy">ɪ</span>')
        self.note.card_description = card_description
        self.note.save()
        card = self.note.cards.first()

        self.assertIn(phonetics_key, card.back)
        self.assertIn(ipa_phonetics, card.back)

    def test_answer_example_sentences(self):
        """
        Should render example sentences in an answer field.
        """
        card_description = {
            **self.card_description,
            "_back": {
                **self.card_description["_back"],
                "example_sentences": self.example_sentences
            }
        }
        self.note.card_description = card_description
        self.note.save()
        card = self.note.cards.first()

        self.assertIn(self.example_sentences[0], card.back)
        self.assertIn(self.example_sentences[1], card.back)

    def test_answer_no_example_sentences(self):
        """
        Shouldn't render any block for example sentences if they are absent.
        """
        card = self.note.cards.first()
        self.assertNotIn(self.example_sentences[0], card.back)
        self.assertNotIn(self.example_sentences[1], card.back)
        self.assertNotIn(self.found_answer_example_sentences, card.back)


class FromCard(NoteFromCard):
    """
    Adding note to an already existing card.
    """
    @classmethod
    def _create_note(cls):
        cls.note = CardNote.from_card(cls.card, "single-sided-formatted")

    def test_note_created(self):
        self._test_note_created()

    def test_source_card_unchanged(self):
        """
        The source card shouldn't be overwritten.
        """
        self._test_source_card_unchanged()

    def test_source_card_references_note(self):
        self._test_source_card_references_note()

    def test_front_text(self):
        """
        front['text'] should be renamed to _front['card_question_definition'].
        """
        self.assertEqual(
            self.card.front,
            self.note.card_description["_front"]["card_question_definition"])

    def test_back_text(self):
        """
        back['text'] should be renamed _back['answer'].
        """
        self.assertEqual(
            self.card.back,
            self.note.card_description["_back"]["answer"])

    def test_front_images_field(self):
        """
        A field for card front images is kept.
        """
        self.assertNotRaises(
            KeyError, lambda: self.assertFalse(self.card["_front"]["images"]))

    def test_back_images_field(self):
        """
        A field for card back images is kept.
        """
        self.assertNotRaises(
            KeyError, lambda: self.assertFalse(self.card["_back"]["images"]))

    def test_front_audio_field(self):
        """
        A field for card front audio is kept.
        """
        self.assertNotRaises(
            KeyError, lambda: self.assertFalse(self.card["_front"]["audio"]))

    def test_back_audio_field(self):
        """
        A field for card back audio is kept.
        """
        self.assertNotRaises(
            KeyError, lambda: self.assertFalse(self.card["_back"]["audio"]))

    def test_template_field(self):
        """
        The template field should be kept.
        """
        self.assertNotRaises(
            KeyError, lambda: self.assertFalse(self.card["template"]))

    def test_categories_field(self):
        """
        The 'categories' field should be kept.
        """
        self.assertNotRaises(
            KeyError, lambda: self.assertFalse(self.card["categories"]))

    def assertNotRaises(self, exception, fn):
        try:
            fn()
        except exception:
            self.fail(f'{fn.__name__} raised {exception.__name__}')