#!/usr/bin/env python3

import re
import json
import datetime
from typing import List, Optional
from Parser import Parser

# Chrome Trace object
class CT:
    short_names = False

    @staticmethod
    def B(data: dict) -> dict: return CT.build(data, {'ph': 'B'})
    @staticmethod
    def E(data: dict) -> dict: return CT.build(data, {'ph': 'E'})

    @staticmethod
    def build(data1: dict, data2: dict) -> dict:
        if 'task' not in data1:
            raise ValueError(f"Task not found in data: {data1}")
        data = data1.copy()
        data.update(data2)

        if 'time' in data:
            data['ts'] = CT.time2ts(data['time'])
        if data['ph'] == 'B':
            data['start'] = data['time']
        if data['ph'] == 'E':
            data['finish'] = data['time']
        data['task'] = data.get('task', '')
        data['type'] = CT.task2type(data['task'])
        data['name'] = CT.data2name(data)
        data['agent'] = CT.data2agent(data)
        data['pid'] = CT.data2pid(data)
        data['args'] = CT.data2args(data)
        res = {}
        for key in ['name', 'cat', 'ph', 'ts', 'pid', 'tid', 'args']:
            if key in data and data[key]:
                res[key] = data[key]
        return res

    @staticmethod
    def data2name(data: dict) -> str:
        if data['type'] == 'DISP_MSG':
            if CT.short_names:
                return data['args']['kind']
            return f'{data["args"]["kind"]}-{data["task"]}'
        if CT.short_names:
            return data['type']
        return data['task']

    @staticmethod
    def data2pid(data: dict) -> int:
        agent = CT.data2agent(data)
        ms = re.search(r'(\d+)$', agent)
        if ms:
            return int(ms.group(1))
        return 0
    @staticmethod
    def data2agent(data: dict) -> str:
        if 'agent' in data:
            return data['agent']
        if 'agentID' in data:
            return data['agentID']
        if 'args' in data:
            return CT.data2agent(data['args'])
        return ''

    @staticmethod
    def time2ts(time: str) -> int:
        tstr = time.replace('Z', '+00:00')
        return int(datetime.datetime.fromisoformat(tstr).timestamp() * 1000000)
    @staticmethod
    def task2type(task: str) -> str:
        ms = re.search(r'(\w+)\.(\w+)\.([\w\+]+)', task)
        if ms:
            return ms.group(1)
        return task
    @staticmethod
    def data2args(data: dict) -> dict:
        args = data.get('args', {}).copy()
        for key in ['task', 'parent', 'origin', 'agent', 'status', 'pres', 'scope', 'start', 'finish']:
            if key in data and data[key]:
                args[key] = data[key]
        if 'agentID' in args:
            del args['agentID']
        return args


class CTRenderer:
    def __init__(self, events: List[dict]):
        self._events = events
        self._tasks = {}
        self._currs = []
        self._options = {}

    def set_option(self, key: str, value) -> None:
        self._options[key] = value

    def is_option(self, key: str) -> bool:
        return self._options.get(key, False)

    def filter_by_task(self, filter: str) -> list[dict]:
        traces = self.process(self._events)
        res = []
        for trace in traces:
            keep = False
            args = trace.get('args', {})
            message = args.get('message', '')
            parent = args.get('parent', '')
            origin = args.get('origin', '')
            if filter in message:
                keep = True
            if parent == filter:
                keep = True
            if origin == filter:
                keep = True
            if keep:
                res.append(trace)
        return res

    def export(self, output_path: Optional[str] = None) -> None:
        traces = self.process(self._events)
        self.export_traces(traces, output_path)

    def export_traces(self, traces: List[dict], output_path: Optional[str] = None) -> None:
        """Export trace data in Chrome Trace JSON format"""
        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(self.build_chrome_trace(traces), f, indent=2)
            print(f"Trace exported to {output_path}")
        else:
            print(json.dumps(traces, indent=2))

    def build_chrome_trace(self, events: List[dict]) -> dict:
        return {
            'traceEvents': events,
            'displayTimeUnit': 'ms',
        }

    def process(self, events) -> list[dict]:
        res = []
        last = ''
        for event in events:
            task = event.get('task', '')
            if task:
                type = CT.task2type(task)
                if type in ['SOLVE_MAPF', 'CHECK_SELF_CONTROL_REQS', 'CHECK_ROBOT_BATTERIES', 'INCREMENT_THROUGHPUT']:
                    continue
            ltip = event.get('ltip')
            if 'time' in event:
                last = event['time']
            data = self.process_task(ltip, event)
            if not data:
                continue
            if isinstance(data, list):
                res.extend(data)
            else:
                res.append(data)
        for task, data in self._tasks.items():
            res.append(CT.B(data))
            data['time'] = last
            res.append(CT.E(data))
        return res

    def process_task(self, ltip, data: dict):
        task = data.get('task', '')
        if ltip == Parser.DECOMPOSED:
            self._tasks[task]['reset_time'] = data['time']
        if ltip == Parser.REPLACE_PLAN:
            # print(f"ReplacePlan: {data}\ntasks: {self._tasks.keys()}")
            for task, task_data in self._tasks.items():
                if 'reset_time' not in task_data:
                    task_data['reset_time'] = data['time']
        if ltip == Parser.NEW_TASK:
            if task not in self._tasks:
                # print(f"NewTask: {task}: {data}")
                self._tasks[task] = data
            self._tasks[task].pop('reset_time', None)
        elif ltip == Parser.TASK_COMPLETED:
            if task not in self._tasks:
                return {}
            else:
                start_data = self._tasks[task]
                start_data['finish'] = data['time']
                del self._tasks[task]
                finish_data = start_data.copy()
                finish_data.update(data)
                return [CT.B(start_data), CT.E(finish_data)]
            # return CT.E(data)
        elif ltip == Parser.PLAN_CHANGED:
            res = []
            for task, task_data in self._tasks.copy().items():
                if 'reset_time' in task_data:
                    del self._tasks[task]
                    res.append(CT.B(task_data))
                    task_data['time'] = task_data['reset_time']
                    res.append(CT.E(task_data))
            # print(self.render_current_plan())
            return res
        return {}

    def render_current_plan(self):
        # print(f'tasks: {self._tasks}')
        tree = {}
        for task in self._tasks.values():
            parent = task.get('parent', '')
            if parent not in tree:
                tree[parent] = []
            tree[parent].append(task)
        return f'{len(self._tasks)} tasks\n' + self.render_plan_tree(tree)

    def render_plan_tree(self, tree, parent='', depth=0):
        res = ''
        for task in tree.get(parent, []):
            args = self.render_args(task.get('args', {}))
            pres = self.render_pres(task.get('pres', {}))
            res += ' ' * 2 * depth + f'[{task["optype"]}] {task["task"]}{args}{pres}\n'
            res += self.render_plan_tree(tree, task['task'], depth + 1)
        return res

    def render_args(self, args: dict) -> str:
        res = []
        for key in args:
            res.append(f'{key}={args[key]}')
        if not res:
            return ''
        return '(' + ', '.join(res) + ')'

    def render_pres(self, pres: dict) -> str:
        if not pres:
            return ''
        return ' Pre: ' + ', '.join(pres.values())

    def task2kebab(self, task: str) -> str:
        ms = re.search(r'(\w+)\.(\w+)\.([\w\+]+)', task)
        if ms:
            return '-'.join([ms.group(1), ms.group(2), ms.group(3)])
        return task

    def scope2cat(self, scope: str) -> str:
        """Convert scope to category for visualization"""
        return scope.strip('/').replace('/', '.')

    def agent2tid(self, agent: str) -> int:
        ms = re.search(r'(\d+)$', agent)
        return int(ms.group(1)) if ms else 0

