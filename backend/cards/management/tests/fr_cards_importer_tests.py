from io import StringIO

from django.test import TestCase
from django.core.management import call_command

from cards.management.modules.phonetics_converter import PhoneticsConverter, \
    Token


class CLIImportingMemorizedCardsTestCase(TestCase):
    """
    Importing cards and their user review-data.
    """
    command = "import_fr_memorized_cards"

    def setUp(self):
        self.command_output = StringIO()

    def get_stripped_command_output(self):
        return self.command_output.getvalue().rstrip()

    def test_calling_from_cli(self):
        """
        An import command is available at all.
        """
        expected_command_output = "no input file specified"
        call_command(self.command, stdout=self.command_output)

        self.assertEqual(self.get_stripped_command_output(),
                         expected_command_output)

    def test_file_not_found(self):
        """
        An attempt to import data from a non-existent file.
        """
        expected_command_output = ("the /fake/directory/file.xml file was"
                                   " not found")
        filename = "/fake/directory/file.xml"
        opts = {"inputfile": filename}

        call_command(self.command, stdout=self.command_output, **opts)

        self.assertEqual(self.get_stripped_command_output(),
                         expected_command_output)


class ConvertPhoneticsTestCase(TestCase):
    def test_single_char_token(self):
        lexeme = "a"
        expected_token_representation = "SINGLE_CHAR a"
        received_token_representation = str(Token(lexeme))

        self.assertEqual(expected_token_representation,
                         received_token_representation)

    def test_multichar_token(self):
        lexeme = "(2)"
        expected_token_representation = "MULTI_CHAR (2)"
        received_token_representation = str(Token(lexeme))

        self.assertEqual(expected_token_representation,
                         received_token_representation)

    def test_token_for_unrecognized_lexeme(self):
        lexeme = "璃"
        expected_representation = ["UNRECOGNIZED 璃"]
        converter = PhoneticsConverter(lexeme)
        received_token_representation = [
            str(_token) for _token in converter.scan_tokens()]

        self.assertEqual(expected_representation,
                         received_token_representation)

    # def test_single_character_conversion(self):
    #     converter = PhoneticsConverter("2")
    #     converted_phonetics = converter.get_converted()
    #     expected_phonetics = ('<span class=phonetics '
    #                           'title="ə - as in another">ə</span>')
    #
    #     self.assertEqual(converted_phonetics, expected_phonetics)

    def test_scan_singlechar_token(self):
        lexeme = "r"
        converter = PhoneticsConverter(lexeme)
        tokens = [str(_token) for _token in converter.scan_tokens()]
        expected_tokens = [str(Token(lexeme))]

        self.assertEqual(tokens, expected_tokens)

    def test_scan_multichar_token(self):
        lexeme = "a2(r)"
        converter = PhoneticsConverter(lexeme)
        tokens = [str(_token) for _token in converter.scan_tokens()]
        expected_tokens = [str(Token(lexeme))]

        self.assertEqual(tokens, expected_tokens)

    def test_longest_available_lexeme(self):
        converter = PhoneticsConverter("fake_phonetics")
        longest_lexeme = 5
        self.assertEqual(converter.longest_lexeme, longest_lexeme)

    def test_shortest_longest_lexeme(self):
        """
        Should recognize the longest lexeme surrounded by single characters.
        """
        lexeme = "ra2(r)r"
        converter = PhoneticsConverter(lexeme)
        tokens = [str(token) for token in converter.scan_tokens()]
        expected_tokens = [str(Token(token))
                           for token in ["r", "a2(r)", "r"]]

        self.assertEqual(tokens, expected_tokens)
