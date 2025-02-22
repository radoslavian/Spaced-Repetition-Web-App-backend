import unittest
from unittest import mock, skip

from cards.management.fr_importer.modules.items_importer import ItemsImporter
from cards.management.fr_importer.modules.user_review import UserReview


class MockOpen:
    builtin_open = open
    fake_data = '''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE fullrecall [
	<!ELEMENT fullrecall (category?)>
	<!ELEMENT category (item?)>
	<!ELEMENT item (q, a)>
	<!ELEMENT q (#PCDATA)>
	<!ELEMENT a (#PCDATA)>
	<!ATTLIST fullrecall core_version CDATA #IMPLIED
		time_of_start CDATA #REQUIRED>
	<!ATTLIST category name CDATA #REQUIRED
		qbgclr CDATA #IMPLIED
		abgclr CDATA #IMPLIED
		qfntclr CDATA #IMPLIED
		afntclr CDATA #IMPLIED
		qfont CDATA #IMPLIED
		afont CDATA #IMPLIED
		qimg CDATA #IMPLIED
		aimg CDATA #IMPLIED>
	<!ATTLIST item id ID #REQUIRED
		tmtrpt CDATA #REQUIRED
		stmtrpt CDATA #REQUIRED
		llivl CDATA #REQUIRED
		rlivl CDATA #REQUIRED
		ivl CDATA #REQUIRED
		rp CDATA #REQUIRED
		gr CDATA #REQUIRED
		sstick IDREF #IMPLIED
		hstick IDREF #IMPLIED>
]>
<fullrecall core_version="12" time_of_start="1186655166">
  <category name="category_1">
    <item id="1254521103" tmtrpt="6411" stmtrpt="6411" livl="268" rllivl="271" ivl="33" rp="12" gr="1">
      <q>question 1</q>
      <a><![CDATA[answer 1<img>../obrazy/chess_board.jpg</img><snd>snds/english_examples_0609.mp3</snd>]]></a>
    </item>
    <category name="category_2">
      <item id="1262379523" tmtrpt="7438" stmtrpt="7438" livl="879" rllivl="1545" ivl="1632" rp="9" gr="4">
<q>question 2</q>
<a><![CDATA[answer 2<snd>snds/english_examples_1959.mp3</snd>]]></a>
      </item>
      <category name="category 3">
        <item id="1234800390" tmtrpt="7440" stmtrpt="7440" livl="1099" rllivl="1646" ivl="1551" rp="14" gr="5">
          <q><![CDATA[question 3<img>../obrazy/lang/teller.png</img>]]></q>
          <a><![CDATA[answer 3<snd>snds/but_the_only_jobs.mp3</snd>]]></a>
        </item>
      </category>
    </category>
  </category>
</fullrecall>
    '''

    def open(self, *args, **kwargs):
        if args[0] == "/fake/path/elements.xml":
            return mock.mock_open(read_data=self.fake_data)(*args, **kwargs)
        return self.builtin_open(*args, **kwargs)


class ItemLoading(unittest.TestCase):
    @classmethod
    @mock.patch("builtins.open", MockOpen().open)
    def setUpClass(cls):
        cls.items_importer = ItemsImporter("/fake/path/elements.xml")

    def test_time_of_start(self):
        time_of_start = 1186655166
        self.assertEqual(time_of_start, self.items_importer.time_of_start)

    def test_number_of_cards(self):
        """
        Three items in the set.
        """
        number_of_items = 3
        received_number_of_items = len(list(self.items_importer))
        self.assertEqual(number_of_items, received_number_of_items)

    def test_question_different_cards(self):
        card_1, card_2, card_3 = list(self.items_importer)
        question_1 = "question 1"
        question_2 = "question 2"
        question_3 = "question 3"

        self.assertIn(question_1, card_1.question_output_text)
        self.assertIn(question_2, card_2.question_output_text)
        self.assertIn(question_3, card_3.question_output_text)

    def test_question_answer(self):
        """
        Should load data from <q></q> and <a></a>.
        """
        card = next(iter(self.items_importer))
        question = "question 1"
        answer = "answer 1"

        self.assertIn(question, card.question_output_text)
        self.assertIn(answer, card.answer_output_text)

    def test_review_details(self):
        card = next(iter(self.items_importer))
        card_dict = dict(card)
        review_details = dict(id="1254521103",
                               tmtrpt="6411",
                               stmtrpt="6411",
                               livl="268",
                               rllivl="271",
                               ivl="33",
                               rp="12",
                               gr="1")
        time_of_start = "1186655166"
        expected_output = UserReview(review_details, time_of_start)

        self.assertDictEqual(dict(expected_output),
                             card_dict["review_details"])
