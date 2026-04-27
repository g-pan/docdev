import unittest

class TestDataExtraction(unittest.TestCase):
    def setUp(self):
        with open('summary.html', 'r') as file:
            self.lines = file.readlines()

    def test_extract_headers(self):
        headers = [self.lines[i].strip() for i in range(2, 11)]  # Lines 3-11
        self.assertTrue(all(header for header in headers))

    def test_regression_suite_data(self):
        regression_data = [self.lines[i].strip() for i in range(15, 21)] + 
                          [self.lines[i].strip() for i in range(23, 29)] + 
                          [self.lines[i].strip() for i in range(31, 37)]  # Lines 16-21, 24-29, 32-37
        self.assertTrue(all(data for data in regression_data))

    def test_unit_tests(self):
        unit_tests = [self.lines[i].strip() for i in range(42, 48)]  # Lines 43-48
        self.assertTrue(all(test for test in unit_tests))

    def test_performance_suite(self):
        performance_data = [self.lines[i].strip() for i in range(54, 55)] + 
                           [self.lines[i].strip() for i in range(58, 59)] + 
                           [self.lines[i].strip() for i in range(63, 64)] + 
                           [self.lines[i].strip() for i in range(67, 68)]  # Lines 55, 59, 64, 68
        self.assertTrue(all(data for data in performance_data))

    def test_code_coverage(self):
        coverage_data = [self.lines[i].strip() for i in range(78, 79)] + 
                        [self.lines[i].strip() for i in range(82, 83)]  # Lines 79 and 83
        self.assertTrue(all(data for data in coverage_data))

if __name__ == '__main__':
    unittest.main()