from django.template import Template, Context
from django.test import TestCase


class AsciiPhoneticsFilter(TestCase):
    """
    Case for a tag for converting ASCII phonetics into IPA format.
    The ASCII format was used in the Techland English dictionary.
    """
    @classmethod
    def setUpTestData(cls):
        cls.template_string = """
        {% load phonetics_ascii %}
        {{ "a2(r)"|convert_ascii_phonetics|safe }}
        """
        cls.render_template()

    @classmethod
    def render_template(cls):
        template = Template(template_string=cls.template_string)
        cls.rendered_template = template.render(Context({}))

    def test_phonetics_ascii_filter(self):
        expected_phonetics = (' <span class="phonetic-entity" title="aʊə '
                              '- our - as in sour">aʊə</span>')
        self.assertIn(expected_phonetics, self.rendered_template)

