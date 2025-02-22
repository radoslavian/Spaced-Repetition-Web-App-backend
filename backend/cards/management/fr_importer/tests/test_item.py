import unittest
import xml.etree.ElementTree as ET

from cards.management.fr_importer.modules.item import Item


class ItemTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.question = "question 1<img>../obrazy/lang/teller.png</img>"
        cls.answer = "answer 1<snd>snds/but_the_only_jobs.mp3</snd>"
        cls.review_details = dict(id="1234800390",
                                  tmtrpt="7440",
                                  stmtrpt="7440",
                                  livl="1099",
                                  rllivl="1646",
                                  ivl="1551",
                                  rp="14",
                                  gr="5")
        cls.review_details_string = " ".join(
            f'{str(k)}=\"{str(v)}\"'
            for k, v in cls.review_details.items())
        item = """<item {review_data_string}>
          <q><![CDATA[{question}]]></q>
          <a><![CDATA[{answer}]]></a>
        </item> 
        """.format(review_data_string=cls.review_details_string,
                   question=cls.question,
                   answer=cls.answer)
        item_parsed = ET.fromstring(item)
        cls.item = Item(item_parsed)

    def test_question_answer_text(self):
        """
        Should correctly extract question/answer.
        """
        self.assertEqual(self.item.question, self.question)
        self.assertEqual(self.item.answer, self.answer)

    def test_review_details(self):
        """
        Should correctly extract review details.
        """

        self.assertDictEqual(self.review_details,
                             self.item.review_details)

    def test_mapping(self):
        self.assertEqual(self.question, self.item["question"])
        self.assertEqual(self.answer, self.item["answer"])
        self.assertDictEqual(self.review_details, self.item["review_details"])
