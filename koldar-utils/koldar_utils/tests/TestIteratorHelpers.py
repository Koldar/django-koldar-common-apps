import unittest

from koldar_utils.functions import iterator_helpers


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


    def test_03(self):
        r = 100
        p = 100
        dot = 3.14 * r

        result={}
        for x_f in range(0, p):
            real_x_f = int(x_f)
            if x_f > p/2:
                x_f = int(x_f - p/2)

            x_g = int((360 * x_f) / p)
            x_r = int((x_g * 2 * dot) / 360)

            parenthesis = int( (dot - x_r))
            parenthesis_2 = int(x_r * parenthesis)
            num = int(r*16*x_r*(dot-x_r))
            den = int(5*dot**2 - 4*x_r * (dot -x_r))

            if real_x_f != x_f:
                num = -1 * num

            sinx = int(num/den)

            result[real_x_f] = dict(x_f=x_f, x_g=x_g, parenthesis=parenthesis, parenthesis_2=parenthesis_2, num=num, den=den, sinx=sinx)

        for k in sorted(result.keys()):
            print(f"x real = {k}, " + ", ".join(map(lambda x: f"{x[0]} = {x[1]}", result[k].items())))
