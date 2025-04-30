#!/usr/bin/env python3

import unittest

from Parser import Parser

class TestTraceLog(unittest.TestCase):
    def test_example(self):
        trace = Parser('example.txt')
        self.assertEqual(trace.unparsed, 0)
        # trace.dump()

    def test_parse_pres(self):
        trace = Parser('')
        exs = {
            '`IF_VALID(task=CARRY_BIN.3p.4n)`, `CAN_LEASE_NODE(tenant=RS8, node=51.24.4-WS-4-N-10000001530-1f0)`': {
                'pre0': 'IF_VALID(task=CARRY_BIN.3p.4n)',
                'pre1': 'CAN_LEASE_NODE(tenant=RS8, node=51.24.4-WS-4-N-10000001530-1f0)',
            },
            '`RUN_AFTER(task=MARK_GROUP_ACTIVE.3p.1d)`, `IS_MESSAGE_GROUP_ACTIVE(fmID=870000000082862, groupID=47d113d4-c79b-42f7-8e24-17ffde564356)`': {
                'pre0': 'RUN_AFTER(task=MARK_GROUP_ACTIVE.3p.1d)',
                'pre1': 'IS_MESSAGE_GROUP_ACTIVE(fmID=870000000082862, groupID=47d113d4-c79b-42f7-8e24-17ffde564356)',
            },
        }
        for input, exp in exs.items():
            pres = trace.parse_pres(input)
            self.assertEqual(pres, exp)

if __name__ == '__main__':
    unittest.main()
