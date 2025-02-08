"""
Tests for CardSide (itself tested through inheriting classes).
"""
from unittest import TestCase

from cards.management.fr_importer.modules.card_answer import Answer
from cards.management.fr_importer.modules.card_question import Question


class SoundExtractionTestCase(TestCase):
    """
    Sound paths and file names extraction tests.
    """

    @classmethod
    def setUpClass(cls):
        cls.question_sound_file_rel_path = \
            "snds/Make_sentences_about_Ann_when_she_was_six.mp3"
        cls.question = ("<b>Definition</b>\n"
                        "Example"
                        f"<snd>{cls.question_sound_file_rel_path}</snd>")
        cls.question_sound_filename = \
            "Make_sentences_about_Ann_when_she_was_six.mp3"

        cls.answer = ("jocular ['d7Ckjul2(r)]\n"
                      "He, he, he! You will pardon me for being jocular."
                      "<snd>snds/he_joined_with_the_best_grace.mp3</snd>")
        cls.answer_sound_file_rel_path = \
            "snds/he_joined_with_the_best_grace.mp3"
        cls.answer_sound_filename = "he_joined_with_the_best_grace.mp3"

        # for testing question/answer with no snd tags
        cls.text_no_snd_tag = """bearing false witness
He accused his neighbour of bearing false witness against him."""

    def test_path_extraction_Question(self):
        """
        Should return path to the sound file embedded in an item's question.
        """
        item_question = Question(self.question)
        self.assertEqual(self.question_sound_file_rel_path,
                         item_question.sound_file_path)

    def test_path_extraction_Answer(self):
        """
        Should return path to the sound file embedded in an item's answer.
        """
        item_answer = Answer(self.answer)
        self.assertEqual(self.answer_sound_file_rel_path,
                         item_answer.sound_file_path)

    def test_path_extraction_Question_no_snd_tag(self):
        """
        Should return None if there is no <snd> tag in an item's question.
        """
        item_question = Question(self.text_no_snd_tag)
        self.assertEqual(None, item_question.sound_file_path)

    def test_path_extraction_Answer_no_snd_tag(self):
        """
        Should return None if there is no <snd> tag in an item's answer.
        """
        item_answer = Answer(self.text_no_snd_tag)
        self.assertEqual(None, item_answer.sound_file_path)

    def test_filename_extraction_Question(self):
        item_question = Question(self.question)
        self.assertEqual(self.question_sound_filename,
                         item_question.sound_file_name)

    def test_filename_extraction_Answer(self):
        item_answer = Answer(self.answer)
        self.assertEqual(self.answer_sound_filename,
                         item_answer.sound_file_name)

    def test_filename_extraction_Question_no_tag(self):
        item_question = Question(self.text_no_snd_tag)
        self.assertEqual(None, item_question.sound_file_name)

    def test_filename_extraction_Answer_no_tag(self):
        item_answer = Answer(self.text_no_snd_tag)
        self.assertEqual(None, item_answer.sound_file_name)


class ImageExtractionTestCase(TestCase):
    """
    Image paths and file names extraction tests.
    """

    @classmethod
    def setUpClass(cls):
        cls.question = (
            "<b>Consuming or eager to consume great amounts of food;"
            " ravenous.</b>\nHe was fond of inviting them to tea; and, "
            "though vowing they never got a look in with him at the cakes and"
            " muffins, for it was the fashion to believe that his corpulence "
            "pointed to [...] appetite, and his [...] appetite to tapeworms,"
            " they accepted his invitations with real pleasure."
            "<img>../obrazy/sucker-Blutegelmeyer.jpg</img><snd>snds"
            "/english_examples_0622.mp3</snd>"
        )
        cls.question_rel_image_path = "../obrazy/sucker-Blutegelmeyer.jpg"
        cls.question_image_filename = "sucker-Blutegelmeyer.jpg"
        cls.question_no_image = "złożyć listy uwierzytelniające"

        cls.answer = (
            "It takes two to make a quarrel.\nJill: Why are you"
            " always so quarrelsome?\nJane: Hey, it's not just my fault. It"
            " takes two to make a quarrel."
            "<img>../obrazy/quarrel.png</img>"
            "<snd>snds/english_examples_3788.mp3</snd>"
        )
        cls.answer_rel_image_path = "../obrazy/quarrel.png"
        cls.answer_image_filename = "quarrel.png"
        cls.answer_no_image = (
            "mill cannot grind with water that is past\nIf you want to go "
            "abroad, do it now, while you're young and have the money."
            " The mill cannot grind with water that is past."
            "<snd>snds/english_examples_2856.mp3</snd>"
        )

    def test_Question_file_path(self):
        question = Question(self.question)
        self.assertEqual(self.question_rel_image_path,
                         question.image_file_path)

    def test_Answer_file_path(self):
        answer = Answer(self.answer)
        self.assertEqual(self.answer_rel_image_path,
                         answer.image_file_path)

    def test_Question_file_path_no_image_tag(self):
        """
        Should return None if there is no image in an item's question.
        """
        question = Question(self.question_no_image)
        self.assertEqual(None, question.image_file_path)

    def test_Answer_file_path_no_image_tag(self):
        """
        Should return None if there is no image in an item's answer.
        """
        answer = Answer(self.answer_no_image)
        self.assertEqual(None, answer.image_file_path)

    def test_Question_image_filename(self):
        item_question = Question(self.question)
        self.assertEqual(self.question_image_filename,
                         item_question.image_file_name)

    def test_Question_image_filename_no_image_tag(self):
        item_question = Question(self.question_no_image)
        self.assertEqual(None, item_question.image_file_name)

    def test_Answer_image_filename(self):
        item_answer = Answer(self.answer)
        self.assertEqual(self.answer_image_filename,
                         item_answer.image_file_name)

    def test_Answer_image_filename_no_image_tag(self):
        item_answer = Answer(self.answer_no_image)
        self.assertEqual(None, item_answer.image_file_name)
