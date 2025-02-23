from os import PathLike

from lxml import etree


xml_parser = etree.XMLParser(recover=True)

def from_string(input_text: str):
    return etree.fromstring(
        f"<root>{input_text}</root>", parser=xml_parser)

def parse(path: str|PathLike):
    return etree.parse(path, parser=xml_parser)
