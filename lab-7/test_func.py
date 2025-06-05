import unittest
from triangle_func import get_triangle_type, IncorrectTriangleSides

def read_test_cases(file_path="D:/dsa-lab-24-1/lab-7/check.txt"):
    test_cases = []
    with open(file_path, "r") as f:
        for line in f:
            parts = line.strip().split(",")
            if len(parts) == 4:
                a, b, c, expected = parts
                test_cases.append((int(a), int(b), int(c), expected))
    return test_cases

class TestGetTriangleType(unittest.TestCase):
    def test_from_check_file(self):
        test_cases = read_test_cases()
        for a, b, c, expected in test_cases:
            with self.subTest(a=a, b=b, c=c, expected=expected):
                if expected == "IncorrectTriangleSides":
                    with self.assertRaises(IncorrectTriangleSides):
                        get_triangle_type(a, b, c)
                else:
                    self.assertEqual(get_triangle_type(a, b, c), expected)

if __name__ == "__main__":
    unittest.main()
