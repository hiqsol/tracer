#!/usr/bin/env python3

import unittest

from Parser import Parser

class TestParser(unittest.TestCase):
    args_exs = {
        'RS5': {
            'arg0': 'RS5',
        },
        'tenant=RS8, node=51.24.4-WS-4-N-10000001530-1f0': {
            'tenant': 'RS8',
            'node': '51.24.4-WS-4-N-10000001530-1f0',
        },
        'RS1 other': {
            'arg0': 'RS1',
            'arg1': 'other',
        },
    }

    def test_parse_args(self):
        trace = Parser('')
        for input, args in TestParser.args_exs.items():
            self.assertEqual(trace.parse_args(input), args)

    def test_render_args(self):
        trace = Parser('')
        for input, args in TestParser.args_exs.items():
            self.assertEqual(trace.render_args(args), input)

    pres_exs = {
        '`IF_VALID(task=CARRY_BIN.3p.4n)`, `CAN_LEASE_NODE(tenant=RS8, node=51.24.4-WS-4-N-10000001530-1f0)`': {
            '0.IF_VALID': {'task': 'CARRY_BIN.3p.4n'},
            '1.CAN_LEASE_NODE': {'tenant': 'RS8', 'node': '51.24.4-WS-4-N-10000001530-1f0'},
        },
        '`RUN_AFTER(task=MARK_GROUP_ACTIVE.3p.1d)`, `IS_MESSAGE_GROUP_ACTIVE(fmID=870000000082862, groupID=47d113d4-c79b-42f7-8e24-17ffde564356)`': {
            '0.RUN_AFTER': {'task': 'MARK_GROUP_ACTIVE.3p.1d'},
            '1.IS_MESSAGE_GROUP_ACTIVE': {'fmID': '870000000082862', 'groupID': '47d113d4-c79b-42f7-8e24-17ffde564356'},
        },
        '`RUN_AFTER(task=MARK_GROUP_ACTIVE.3p.1d)`, `IS_MESSAGE_GROUP_ACTIVE(fmID=870000000082862, groupID=47d113d4-c79b-42f7-8e24-17ffde564356)`, `AFTER_TASK_TICK()`, `NO_BIN`': {
            '0.RUN_AFTER': {'task': 'MARK_GROUP_ACTIVE.3p.1d'},
            '1.IS_MESSAGE_GROUP_ACTIVE': {'fmID': '870000000082862', 'groupID': '47d113d4-c79b-42f7-8e24-17ffde564356'},
            '2.AFTER_TASK_TICK': {},
            '3.NO_BIN': {},
        },
    }

    def test_parse_pres(self):
        trace = Parser('')
        for input, pres in TestParser.pres_exs.items():
            self.assertEqual(trace.parse_pres(input), pres)

    def test_render_pres(self):
        trace = Parser('')
        for input, pres in TestParser.pres_exs.items():
            self.assertEqual(trace.render_pres(pres), input)

    def test_example(self):
        trace = Parser('example.txt')
        self.assertEqual(trace.unparsed, 0)
        # trace.dump()

if __name__ == '__main__':
    unittest.main()
