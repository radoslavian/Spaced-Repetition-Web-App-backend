from django.template import Context, Template

from card_types.card_managers import FrontBackBackFront


class DoubleSidedFormatted(FrontBackBackFront):
    default_template_string = "<h3>{{ side.text|safe }}</h3>"

    def _update_text_fields(self, card, back, front):
        card.front = self._render_side(front)
        card.back = self._render_side(back)

    def _get_formatting_template_string(self):
        formatting_template_string_db = super()._get_formatting_template_string(
            self.card_note.card_description)
        formatting_template_string = self.card_note.card_description.get(
            "formatting_template_string")
        template_string = (formatting_template_string_db
                           or formatting_template_string
                           or self.default_template_string)
        return template_string

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
