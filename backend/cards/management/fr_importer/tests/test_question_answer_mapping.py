import unittest

from cards.management.fr_importer.modules.html_formatted_answer import \
    HTMLFormattedAnswer
from cards.management.fr_importer.modules.html_formatted_question import \
    HTMLFormattedQuestion


class HTMLFormattedQuestionMapping(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.definition = "question"
        cls.example = "example sentence"
        cls.img_filename = "theatre.jpg"
        cls.snd_filename = "en_26_02_2023_0008.mp3"
        cls.img_filepath = f"../obrazy/{cls.img_filename}"
        cls.snd_filepath = f"snds/{cls.snd_filename}"
        cls.question_text = (f"{cls.definition}\n{cls.example}"
                             f"<img>{cls.img_filepath}</img>"
                             f"<snd>{cls.snd_filepath}</snd>")
        cls.question = HTMLFormattedQuestion(cls.question_text)
        cls.mapped_to_dict = dict(cls.question)

    def test_text_mapping(self):
        self.assertIn(self.definition, self.mapped_to_dict["output_text"])
        self.assertIn(self.example, self.mapped_to_dict["output_text"])

    def test_file_paths_mapping(self):
        self.assertEqual(self.mapped_to_dict["image_file_path"],
                         self.img_filepath)
        self.assertEqual(self.mapped_to_dict["sound_file_path"],
                         self.snd_filepath)

    def test_filenames_mapping(self):
        self.assertEqual(self.img_filename,
                         self.mapped_to_dict["image_file_name"])
        self.assertEqual(self.snd_filename,
                         self.mapped_to_dict["sound_file_name"])


class HTMLFormattedAnswerMapping(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.answer = "answer"
        cls.examples = ["sentence 1", "sentence 2"]
        cls.img_filename = "theatre.jpg"
        cls.snd_filename = "en_26_02_2023_0008.mp3"
        cls.img_filepath = f"../obrazy/{cls.img_filename}"
        cls.snd_filepath = f"snds/{cls.snd_filename}"
        joined_examples = '\n'.join(cls.examples)
        cls.question_text = (f"{cls.answer}\n{joined_examples}"
                             f"<img>{cls.img_filepath}</img>"
                             f"<snd>{cls.snd_filepath}</snd>")
        cls.question = HTMLFormattedAnswer(cls.question_text)
        cls.mapped_to_dict = dict(cls.question)

    def test_text_mapping(self):
        self.assertIn(self.answer, self.mapped_to_dict["output_text"])
        self.assertIn(self.examples[0], self.mapped_to_dict["output_text"])
        self.assertIn(self.examples[1], self.mapped_to_dict["output_text"])

    def test_file_paths_mapping(self):
        self.assertEqual(self.mapped_to_dict["image_file_path"],
                         self.img_filepath)
        self.assertEqual(self.mapped_to_dict["sound_file_path"],
                         self.snd_filepath)

    def test_filenames_mapping(self):
        self.assertEqual(self.img_filename,
                         self.mapped_to_dict["image_file_name"])
        self.assertEqual(self.snd_filename,
                         self.mapped_to_dict["sound_file_name"])