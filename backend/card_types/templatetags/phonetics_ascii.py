from django import template

from cards.management.fr_importer.items_parser.\
    modules.phonetics_converter import convert_techland_phonetics


register = template.Library()


def convert_ascii_phonetics(arg):
    """
    Converts ASCII phonetics for English pronunciation into IPA.
    ASCII phonetics was used in the Techland (brand name) English dictionary.
    """
    return convert_techland_phonetics(arg)


register.filter("convert_ascii_phonetics", convert_ascii_phonetics)