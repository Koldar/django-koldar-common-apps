import unittest

from django_koldar_utils.functions import iterator_helpers


class TestIteratoHelpers(unittest.TestCase):

    def test_01(self):
        self.assertEqual(list(iterator_helpers.to_shifting_pairs([0, 1, 2, 3, 4, 5])), [(0,1), (1, 2), (2, 3), (3, 4), (4, 5)])
        self.assertEqual(list(iterator_helpers.to_shifting_pairs([0, 1])), [(0, 1)])
        self.assertEqual(list(iterator_helpers.to_shifting_pairs([0])), [(0, None)])

        self.assertEqual(list(iterator_helpers.to_shifting_pairs([0], pad_last=False)), [(0, )])
        self.assertEqual(list(iterator_helpers.to_shifting_pairs([0], include_temp_at_end=False)), [])

    def test_02(self):
        self.assertEqual(list(iterator_helpers.to_pairs([0, 1, 2, 3, 4, 5])), [(0, 1), (2, 3), (4, 5)])
        self.assertEqual(list(iterator_helpers.to_pairs([0, 1])), [(0, 1)])
        self.assertEqual(list(iterator_helpers.to_pairs([0])), [(0, None)])

        self.assertEqual(list(iterator_helpers.to_pairs([0], pad_last=False)), [(0,)])
        self.assertEqual(list(iterator_helpers.to_pairs([0], include_temp_at_end=False)), [])
