from unittest import TestCase

from cards.management.fr_importer.tests.common_card_side_tests import \
    CommonCardSideTests
from cards.management.fr_importer.modules.card_side import Answer


class GetAnswer(CommonCardSideTests, TestCase):
    """
    Main answer component is located in the first line of an answer side.
    """
    @classmethod
    def setUpClass(cls):
        cls.single_line_answer_no_media = ("<u>some</u> <b><i>answer</i></b> "
                                           "<strike>text</strike>")
        cls.sound_path = ("<snd>snds/he was about to kick the"
                          " ball when he.mp3</snd>")
        cls.image_path = "<img>../obrazy/pike01.jpg</img>"
        cls.single_line_answer_sound = (cls.single_line_answer_no_media
                                        + cls.sound_path)
        cls.single_line_answer_image = (cls.single_line_answer_no_media
                                        + cls.image_path)
        cls.single_line_answer_all_media = (cls.single_line_answer_no_media
                                            + cls.sound_path + cls.image_path)

        cls.answer_single_line_no_media = Answer(
            cls.single_line_answer_no_media)

    def test_answer_extraction(self):
        expected_output = "some <i>answer</i> <strike>text</strike>"
        self.assertEqual(self.answer_single_line_no_media.answer,
                         expected_output)

    def test_no_illegal_tags(self):
        """
        The (main) answer shouldn't contain bold <b></b> and underline <u></u>
        tags.
        """
        self.assert_no_illegal_formatting_tags(
            self.answer_single_line_no_media.answer)

    def test_allowed_tags(self):
        self.assert_allowed_tags(self.answer_single_line_no_media.answer)

