import unittest

from src.wuhan_pilot.utils import normalize_name, parse_numeric


class UtilsTest(unittest.TestCase):
    def test_parse_numeric(self):
        self.assertEqual(parse_numeric("暂无"), None)
        self.assertEqual(parse_numeric("1.80元/平米/月"), 1.80)
        self.assertEqual(parse_numeric("35.0%"), 35.0)

    def test_normalize_name(self):
        self.assertEqual(normalize_name(" 武汉 江山 "), "武汉江山")


if __name__ == "__main__":
    unittest.main()

