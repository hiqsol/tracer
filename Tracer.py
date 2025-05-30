#!/usr/bin/env python3

import re
import json
from CT import CT
from Plan import Plan
from Trace import Trace
from Parser import Parser

# In general tracing works in several steps:
# - log -> events -> Trace objects -> Processing/Filtering -> Chrome Trace objects -> JSON file
# - such multistep process is needed to allow for filtering and processing on the level of Trace objects.
#
# 1. Parser reads the given log file and creates a list of events
# 2. Tracer processes the events and creates a list of Trace objects
# 3. Tracer can apply process (e.g. filter) list of Trace objects
# 4. Tracer creates a list of Chrome Trace objects from the Trace objects and exports them to a JSON file
#
# Event is simple dictionary with the keys like: ltip, time, task, args, pres, etc.
# Trace is a class that represents a single task with its start and finish time, agent, and other attributes
# CT class provides methods to convert Trace objects to Chrome Trace format

class Tracer:
    def __init__(self, events: list[dict]):
        self._tasks = {}
        self._actions = {}
        self._del_tasks = {}
        self._options = {}
        self.parser = Parser('')
        self.session = {}
        self._methods = {
            Parser.DECOMPOSED:      self._prepare_Decomposed,
            Parser.REPLACE_PLAN:    self._prepare_ReplacePlan,
            Parser.NEW_TASK:        self._prepare_NewTask,
            Parser.TASK_COMPLETED:  self._prepare_TaskCompleted,
            Parser.PLAN_CHANGED:    self._prepare_PlanChanged,
            Parser.TASK_RECEIVED:   self._prepare_TaskReceived,
            Parser.STATUS_CHANGED:  self._prepare_StatusChanged,
            Parser.START_SESSION:   self._prepare_StartSession,
        }
        self._events = events
        self._traces = self.prepare(events)

    def prepare(self, events) -> list[Trace]:
        res = []
        finish = ''
        for event in events:
            if isinstance(event, Trace):
                res.append(event)
                continue
            ltip = event.get('ltip')
            if 'time' in event:
                finish = event['time']
            data = self._prepare_event(ltip, event)
            if not data:
                continue
            if isinstance(data, list):
                res.extend(data)
            else:
                res.append(data)
        self.session['finish'] = finish
        for _, data in self._tasks.items():
            data['finish'] = finish
            res.append(Trace(data))
        return res

    def _prepare_event(self, ltip, data: dict):
        task = data.get('task', '')
        method = self._methods.get(ltip, None)
        if method:
            return method(task, data)
        return []

    def _prepare_Decomposed(self, task: str, data: dict):
        if task in self._tasks:
            self._tasks[task]['reset_time'] = data['time']
    def _prepare_ReplacePlan(self, _: str, data: dict):
        for _, task_data in self._tasks.items():
            if 'reset_time' not in task_data:
                task_data['reset_time'] = data['time']
    def _prepare_NewTask(self, task: str, data: dict):
        if task not in self._tasks:
            self._tasks[task] = data
        self._tasks[task].pop('reset_time', None)
    def _prepare_TaskCompleted(self, task: str, data: dict):
        if task not in self._tasks:
            return {}
        start_data = self._tasks[task]
        start_data['finish'] = data['time']
        del self._tasks[task]
        return Trace(start_data)
    def _prepare_PlanChanged(self, _: str, __: dict):
        res = []
        for task, task_data in self._tasks.copy().items():
            if 'reset_time' in task_data:
                self._del_tasks[task] = task_data
                del self._tasks[task]
                task_data['finish'] = task_data['reset_time']
                res.append(Trace(task_data))
        return res
    def _prepare_TaskReceived(self, task: str, data: dict):
        self._actions[task] = data
        return []
    def _prepare_StatusChanged(self, task: str, data: dict):
        if task not in self._actions:
            raise ValueError(f"Task {task} not found in actions")
        if not self.has_task(task):
            raise ValueError(f"Task {task} not found in tasks: {self._tasks.keys()}")
        action = self._actions[task]
        task_data = self.get_task(task).copy()
        task_data['task'] = 'A:' + task
        task_data['optype'] = Trace.ACTION
        task_data['start'] = action['time']
        task_data['status'] = data['status']
        task_data['finish'] = data['time']
        del self._actions[task]
        return Trace(task_data)
    def _prepare_StartSession(self, _: str, data: dict):
        data['start'] = data['time']
        self.session = data
        return []

    @property
    def traces(self) -> list[Trace]:
        return self._traces

    def set_option(self, key: str, value) -> None:
        self._options[key] = value

    def is_option(self, key: str) -> bool:
        return self._options.get(key, False)

    def export(self, filename: str) -> None:
        Tracer.export_traces(self._traces, f'{filename}.json')
        Tracer.export_actions(self._traces, f'{filename}-actions.json')

    @staticmethod
    def export_actions(traces: list[Trace], output_path: str) -> None:
        res = []
        for trace in traces:
            if trace.get('optype') == Trace.ACTION:
                res.append(trace)
        Tracer.export_traces(res, output_path)

    @staticmethod
    def export_traces(traces: list[Trace], output_path: str) -> None:
        trs = []
        for trace in traces:
            type = trace.get('type')
            if not type in ['SOLVE_MAPF', 'CHECK_SELF_CONTROL_REQS', 'CHECK_ROBOT_BATTERIES', 'INCREMENT_THROUGHPUT']:
                trs.append(trace)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(CT.build_file(trs), f, indent=2)
        print(f"Trace exported to {output_path}")

    def has_task(self, task: str) -> bool:
        return task in self._tasks or task in self._del_tasks
    def get_task(self, task: str) -> dict:
        if task in self._tasks:
            return self._tasks[task]
        if task in self._del_tasks:
            return self._del_tasks[task]
        return {}

    def render_current_plan(self):
        plan = Plan(self)
        plan.add_tasks(self._tasks)
        return plan.render()

