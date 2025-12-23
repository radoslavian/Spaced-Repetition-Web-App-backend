from django.test import TestCase

from card_types.models import CardNote
from cards.models import CardTemplate


class TestData(TestCase):
    @classmethod
    def _setUpTestData(cls):
        cls.card_description = {
            '_front': {
                'text': 'front text'
            },
            '_back': {
                'text': ''
            },
            'extra_content': {
                'phonetics_key': '',
                'phonetics': {
                    'format': '',
                    # valid values are 'IPA' or 'ASCII' (Techland)
                    'value': ''  # actual phonetic string
                },
                'example_sentences': []
            },
            # template used to render each side
            "formatting_template_db": 'vocabulary_with_extra_content',
            'template': None,  # should use fallback
            'categories': []
        }
        cls.template_string = ""

    @classmethod
    def create_objects(cls):
        cls.template = CardTemplate.objects.create(
            title="vocabulary_with_extra_content",
            description="for testing purposes",
            body=cls.template_string)
        cls.note = CardNote.objects.create(
            card_description=cls.card_description,
            card_type="formatted-vocabulary")
        cls.front_back_card = cls.note.cards.get(
            id__exact=cls.note.metadata["front-back-card-id"])
        cls.back_front_card = cls.note.cards.get(
            id__exact=cls.note.metadata["back-front-card-id"])


class BasicFieldsRendering(TestData):
    @classmethod
    def setUpTestData(cls):
        cls._setUpTestData()
        cls.extra_content_text = "extra content goes here"
        cls.template_string = ("""
                {% load %}
                {{ side.text }}
                {% if extra_content %}
                 """ + cls.extra_content_text + """
                {% endif %}
                """)
        cls.create_objects()

    def test_rendered_front_text_front_back(self):
        """
        Front-back card/front should only render front text and no extra content.
        """
        self.assertIn(self.card_description["_front"]["text"],
                      self.front_back_card.front)
        self.assertNotIn(self.extra_content_text,
                         self.front_back_card.front)

    def test_rendered_back_text_front_back(self):
        """
        Front-back card/back should render front text with extra content.
        """
        self.assertIn(self.card_description["_back"]["text"],
                      self.front_back_card.back)
        self.assertIn(self.extra_content_text,
                      self.front_back_card.back)

    def test_rendered_front_text_back_front(self):
        """
        Back-front card/front should render front text and no extra content.
        """
        self.assertIn(self.card_description["_back"]["text"],
                      self.back_front_card.front)
        self.assertNotIn(self.extra_content_text,
                         self.back_front_card.front)

    def test_rendered_back_text_back_front(self):
        """
        Back-front card/back should render back text with extra content.
        """
        self.assertIn(self.card_description["_front"]["text"],
                      self.back_front_card.back)
        self.assertIn(self.extra_content_text, self.back_front_card.back)


class ExtraContent(TestData):
    @classmethod
    def setUpTestData(cls):
        cls._setUpTestData()
        cls.card_description = {**cls.card_description,
            'extra_content': {
                'phonetics': {
                    'key': 'phonetics key',
                    # not implemented yet, but
                    # valid values should be 'IPA' or 'ASCII' (Techland)
                    'format': 'ASCII',
                    'value': 'I'  # actual phonetic string
                },
                'example_sentences': [
                    'example sentence 1',
                    'example sentence 2'
                ]
            },
        }
        included_template_body = """
        {% load phonetics_converter %}
        <p id="phonetics-key">
           {{ extra_content.phonetics.key }}
        </p>
        {% if extra_content.example_sentences %}
          
          <p id="phonetics-value">
            {{ extra_content.phonetics.value|convert_ascii_phonetics|safe }}
          </p>
          <div id="example-sentences">
           {% for sentence in extra_content.example_sentences %}
            <p>{{ sentence }}</p>
          {% endfor %}
          </div>
        {% endif %}
        """
        included_template = CardTemplate.objects.create(
            title="included template",
            description="included template",
            body=included_template_body)
        cls.template_string = ("""
                {{ side.text }}
                {% if extra_content %}
                  {% include "included template" %}
                {% endif %}
                """)
        cls.create_objects()

    def test_phonetics_key(self):
        phonetics_key = self.card_description['extra_content'] \
            ['phonetics']['key']
        self.assertIn(phonetics_key, self.front_back_card.back)

    def test_phonetics(self):
        expected_phonetics = ('<span class="phonetic-entity"'
                              ' title="ɪ - i - as in pit, hill or y -'
                              ' as in happy">ɪ</span>')
        self.assertIn(expected_phonetics, self.front_back_card.back)

    def test_example_sentences(self):
        self.assertIn("<p>example sentence 1</p>", self.front_back_card.back)
        self.assertIn("<p>example sentence 2</p>", self.front_back_card.back)