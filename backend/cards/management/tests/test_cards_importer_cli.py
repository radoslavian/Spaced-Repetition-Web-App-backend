from io import StringIO

from django.test import TestCase
from django.core.management import call_command

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
