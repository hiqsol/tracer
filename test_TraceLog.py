#!/usr/bin/env python3

import unittest

from TraceLog import TraceLog

class TestTraceLog(unittest.TestCase):
    def test_example(self):
        trace = TraceLog('example.txt')
        self.assertEqual(trace.unparsed, 0)

if __name__ == '__main__':
    unittest.main()
