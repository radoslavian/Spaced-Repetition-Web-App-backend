from django.core.exceptions import ObjectDoesNotExist
from django.template import Template, TemplateDoesNotExist
from django.template.loaders.base import Loader
from cards.models import CardTemplate


class CardTemplateLoader(Loader):
    def get_template(self, template_name, dirs=None, skip=[]):
        source, origin = self.load_template_source(template_name)
        template = Template(source, origin.title)
        return template

    @staticmethod
    def load_template_source(template_name, template_dirs=None):
        try:
            origin = CardTemplate.objects.get(title__exact=template_name)
        except ObjectDoesNotExist:
            raise TemplateDoesNotExist(f"The template {template_name} "
                                       "was not found")
        source = origin.body
        return source, origin