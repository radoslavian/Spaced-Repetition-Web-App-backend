from django.contrib.admin.templatetags.admin_list import items_for_result
from django.test import TestCase

from cards.management.modules.fr_card_side import CardSide, Question, \
    Answer


class SoundExtractionTestCase(TestCase):
    """
    Sound paths and file names extraction tests.
    """

    @classmethod
    def setUpTestData(cls):
        cls.question = ("<b>Make sentences about Ann when she was six.</b>\n"
                        "lots of friends ? [...]?<snd>snds/Make_sentences_"
                        "about_Ann_when_she_was_six.mp3</snd>")
        cls.question_sound_file_rel_path = \
            "snds/Make_sentences_about_Ann_when_she_was_six.mp3"
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

    def test_path_extraction_ItemQuestion(self):
        """
        Should return path to the sound file embedded in an item's question.
        """
        item_question = Question(self.question)
        self.assertEqual(self.question_sound_file_rel_path,
                         item_question.sound_file_path)

    def test_path_extraction_ItemAnswer(self):
        """
        Should return path to the sound file embedded in an item's answer.
        """
        item_answer = Answer(self.answer)
        self.assertEqual(self.answer_sound_file_rel_path,
                         item_answer.sound_file_path)

    def test_path_extraction_ItemQuestion_no_snd_tag(self):
        """
        Should return None if there is no <snd> tag in an item's question.
        """
        item_question = Question(self.text_no_snd_tag)
        self.assertEqual(None, item_question.sound_file_path)

    def test_path_extraction_ItemAnswer_no_snd_tag(self):
        """
        Should return None if there is no <snd> tag in an item's answer.
        """
        item_answer = Answer(self.text_no_snd_tag)
        self.assertEqual(None, item_answer.sound_file_path)

    def test_filename_extraction_ItemQuestion(self):
        item_question = Question(self.question)
        self.assertEqual(self.question_sound_filename,
                         item_question.sound_file_name)

    def test_filename_extraction_ItemAnswer(self):
        item_answer = Answer(self.answer)
        self.assertEqual(self.answer_sound_filename,
                         item_answer.sound_file_name)

    def test_filename_extraction_ItemQuestion_no_tag(self):
        item_question = Question(self.text_no_snd_tag)
        self.assertEqual(None, item_question.sound_file_name)

    def test_filename_extraction_ItemAnswer_no_tag(self):
        item_answer = Answer(self.text_no_snd_tag)
        self.assertEqual(None, item_answer.sound_file_name)


class ImageExtractionTestCase(TestCase):
    """
    Image paths and file names extraction tests.
    """

    @classmethod
    def setUpTestData(cls):
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

    def test_ItemQuestion_file_path(self):
        question = Question(self.question)
        self.assertEqual(self.question_rel_image_path,
                         question.image_file_path)

    def test_ItemAnswer_file_path(self):
        answer = Answer(self.answer)
        self.assertEqual(self.answer_rel_image_path,
                         answer.image_file_path)

    def test_ItemQuestion_file_path_no_image_tag(self):
        """
        Should return None if there is no image in an item's question.
        """
        question = Question(self.question_no_image)
        self.assertEqual(None, question.image_file_path)

    def test_ItemAnswer_file_path_no_image_tag(self):
        """
        Should return None if there is no image in an item's answer.
        """
        answer = Answer(self.answer_no_image)
        self.assertEqual(None, answer.image_file_path)

    def test_ItemQuestion_image_filename(self):
        item_question = Question(self.question)
        self.assertEqual(self.question_image_filename,
                         item_question.image_file_name)

    def test_ItemQuestion_image_filename_no_image_tag(self):
        item_question = Question(self.question_no_image)
        self.assertEqual(None, item_question.image_file_name)

    def test_ItemAnswer_image_filename(self):
        item_answer = Answer(self.answer)
        self.assertEqual(self.answer_image_filename,
                         item_answer.image_file_name)

    def test_ItemAnswer_image_filename_no_image_tag(self):
        item_answer = Answer(self.answer_no_image)
        self.assertEqual(None, item_answer.image_file_name)


class ItemQuestionDefinitionExampleTestCase(TestCase):
    """
    Tests definition and example from the ItemQuestion
    + takes the definition from:
     - a card with only the definition
     - a card with the definition and one sentence with an example
     - removes the bold and italic tags;
    """

    @classmethod
    def setUpTestData(cls):
        # if BS uses xml parsers, it will return empty string if there are
        # no tags around input text - this is why the following
        # has no <b></b> tags around definition
        # there are many items in FR that have no tags around question/
        # answer
        cls.basic_question = "basic question"
        cls.question_img_snd_tags = (
            "not aware of or careful about possible"
            " risks and dangers;<img>../obrazy/"
            "swimmer-mike-paget.jpg</img><snd>snds/not "
            "aware of or careful.mp3</snd>")
        cls.definition_no_img_snd_tag = ("not aware of or careful about "
                                         "possible risks and dangers;")
        cls.question_example = (
            "<b>not pertaining to or connected with any particular"
            " person or persons; having no personal reference or "
            "connection: said of things;</b>\n"
            "The jewels and other \nappointments of the harem are quite "
            "[...], belonging to the establishment and not to any of"
            " their successive wearers."
            "<img>../obrazy/wedding_077.jpg</img><snd>snds/english_"
            "examples_2806.mp3</snd>")
        cls.definition = ("not pertaining to or connected with any "
                          "particular person or persons; having"
                          " no personal reference or connection: "
                          "said of things;")
        cls.example = (
            "The jewels and other <br/>appointments of the harem "
            "are quite [...], belonging to the establishment"
            " and not to any of their "
            "successive wearers.")

    def test_basic_question(self):
        item_question = Question(self.basic_question)
        self.assertEqual(item_question.definition, self.basic_question)

    def test_splitting_img_snd_tags_from_definition(self):
        """
        Removes media tags from cards with definition only (no example).
        """
        item_question = Question(self.question_img_snd_tags)
        self.assertEqual(item_question.definition,
                         self.definition_no_img_snd_tag)

    def test_definition(self):
        item_question = Question(self.question_example)
        self.assertEqual(item_question.definition, self.definition)

    def test_example(self):
        item_question = Question(self.question_example)
        self.assertEqual(item_question.example, self.example)

    def test_empty_example(self):
        """
        Should return None when there's no example sentence.
        """
        item_question = Question(self.question_img_snd_tags)
        self.assertEqual("", item_question.example)
