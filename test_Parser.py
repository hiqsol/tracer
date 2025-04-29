#!/usr/bin/env python3

import unittest

from Parser import Parser

class TestTraceLog(unittest.TestCase):
    def test_example(self):
        trace = Parser('example.txt')
        self.assertEqual(trace.unparsed, 0)
        trace.dump()

if __name__ == '__main__':
    unittest.main()
