from django.template import Context, Template

from card_types.card_managers import FrontBackBackFront
from cards.models import CardTemplate


class DoubleSidedFormatted(FrontBackBackFront):
    default_template_string = "<h3>{{ side.text|safe }}</h3>"

    def _update_text_fields(self, card, back, front):
        card.front = self._render_side(front)
        card.back = self._render_side(back)

    def _get_formatting_template_string(self):
        formatting_template_string_db = self._get_db_formatting_template()
        formatting_template_string = self.card_note.card_description.get(
            "formatting_template_string")
        template_string = (formatting_template_string_db
                           or formatting_template_string
                           or self.default_template_string)
        return template_string

    def _get_db_formatting_template(self):
        db_template_title = self.card_note.card_description.get(
            "formatting_template_db")
        template_body = CardTemplate.objects.get(
            title__exact=db_template_title).body if db_template_title else None
        return template_body

    def _render_side(self, side):
        context_data = {
            "side": side
        }
        rendered_side = self._render_with_context(context_data)
        return rendered_side

    def _render_with_context(self, context_data):
        template_string = self._get_formatting_template_string()
        context = Context(context_data)
        template = Template(template_string=template_string)
        return template.render(context)
