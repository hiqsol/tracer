#!/usr/bin/env python3

import unittest

from Plan import Plan
from Parser import Parser
from Tracer import Tracer

class TestPlan(unittest.TestCase):
    def setUp(self):
        self.tracer = Tracer([])

    def no_test_render_simple_plan(self):
        tasks = {
            'TASK1': {'task': 'TASK1', 'optype': 'T'},
            'TASK2': {'task': 'TASK2', 'optype': 'T'},
            'OPER3': {'task': 'OPER3', 'optype': 'O', 'parent': 'TASK1'},
            'TASK4': {'task': 'TASK4', 'optype': 'T', 'parent': 'TASK2'},
            'TASK5': {'task': 'TASK5', 'optype': 'T', 'parent': 'TASK4'},
        }
        expected_output = '''5 tasks
[T] TASK1
  [O] OPER3
[T] TASK2
  [T] TASK4
    [T] TASK5
'''
        plan = Plan(self.tracer)
        plan.add_tasks(tasks)
        self.assertEqual(plan.render(), expected_output)

    def test_render_parsed_plan(self):
        parser = Parser('plan.log')
        tracer = Tracer(parser.events)
        plan = tracer.render_current_plan()
        expected_output = '''3 tasks
[T] DISP_MSG.3p.c(msgID=870000000082857, kind=ProductFromBinToWSTableMove, status=Created) Pre: `PLAN_AFTER(task=DISP_MSG.3p.b)`, `STATE_READY()`
  [O] MARK_GROUP_ACTIVE.3p.3N(f019549d-b121-49cb-9a23-e88deddcfc63 true) Pre: `IF_VALID(task=DISP_MSG.3p.c)`, `CAN_PERFORM_DM()`
  [T] WAIT_FOR_DM_DONE.3p.3O(msgID=870000000082857) Pre: `RUN_AFTER(task=MARK_GROUP_ACTIVE.3p.3N)`, `DONE_RECEIVED()`, `IS_MESSAGE_GROUP_ACTIVE(fmID=870000000082857, groupID=f019549d-b121-49cb-9a23-e88deddcfc63)`
'''
        self.assertEqual(plan, expected_output)

if __name__ == '__main__':
    unittest.main()
