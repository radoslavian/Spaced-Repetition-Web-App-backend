import unittest


class HtmlFormattedMemorizedCardMapping(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # attribute of the <fullrecall ...></fullrecall> tag
        cls.time_of_start = 1186655166

        # attributes of an <item ...></item> tag
        cls.card_review_details = {
            "id": 1236435838,
            "tmtrpt": 6574,
            "stmtrpt": 6574,
            "livl": 1274,
            "rllivl": 1764,
            "ivl": 583,
            "rp": 6,
            "gr": 4
        }
