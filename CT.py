#!/usr/bin/env python3

import re
import json
import datetime
from typing import Dict, List, Any, Optional
from Parser import Parser

# Chrome Trace object
class CT:
    @staticmethod
    def B(data: Dict) -> Dict: return CT.build(data, {'ph': 'B'})
    @staticmethod
    def E(data: Dict) -> Dict: return CT.build(data, {'ph': 'E'})

    @staticmethod
    def build(data: Dict, data2: Dict) -> Dict:
        if 'task' not in data:
            raise ValueError(f"Task not found in data: {data}")
        data.update(data2)
        if 'pid' not in data:
            data['pid'] = 0
        if 'time' in data:
            data['ts'] = CT.time2ts(data['time'])
        # data['name'] = CT.task2tt(data.get('task', ''))
        data['name'] = data['task']
        data['args'] = CT.data2args(data)
        res = {}
        for key in ['name', 'cat', 'ph', 'ts', 'pid', 'tid', 'args']:
            if key in data and data[key]:
                res[key] = data[key]
        return res

    @staticmethod
    def time2ts(time: str) -> int:
        tstr = time.replace('Z', '+00:00')
        return int(datetime.datetime.fromisoformat(tstr).timestamp() * 1000000)
    @staticmethod
    def task2tt(task: str) -> str:
        ms = re.search(r'(\w+)\.(\w+)\.([\w\+]+)', task)
        if ms:
            return ms.group(1)
        return task
    @staticmethod
    def data2args(data: Dict) -> Dict:
        args = {}
        for key in ['agent', 'status', 'message']:
            if key in data:
                args[key] = data[key]
        return args


class CTRenderer:
    def __init__(self, events: List[Dict]):
        self._events = events
        self._tasks = {}
        self._currs = []

    def export(self, output_path: Optional[str] = None) -> None:
        """Export trace data in Chrome Trace JSON format"""
        traces = self.process(self._events)
        trace_data = self.build_chrome_trace(traces)
        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(trace_data, f, indent=2)
            print(f"Trace exported to {output_path}")
        else:
            print(json.dumps(trace_data, indent=2))

    def build_chrome_trace(self, events: List[Dict]) -> Dict[str, Any]:
        return {
            'traceEvents': events,
            'displayTimeUnit': 'ms',
        }

    def process(self, events):
        res = []
        last = ''
        for event in events:
            task = event.get('task', '')
            if task:
                tt = CT.task2tt(task)
                if tt in ['SOLVE_MAPF', 'CHECK_SELF_CONTROL_REQS', 'CHECK_ROBOT_BATTERIES', 'INCREMENT_THROUGHPUT']:
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
            data['name'] = task
            res.append(CT.B(data))
            data['time'] = last
            res.append(CT.E(data))
        return res

    def process_task(self, ltip, data: Dict):
        task = data.get('task', '')
        # if ltip == Parser.DECOMPOSED:
        #     self._tasks[task]['reset_plan'] = data['time']
        if ltip == Parser.REPLACE_PLAN:
            # print(f"ReplacePlan: {data}\ntasks: {self._tasks.keys()}")
            for task, task_data in self._tasks.items():
                task_data['reset_time'] = data['time']
        if ltip == Parser.NEW_TASK:
            if task not in self._tasks:
                self._tasks[task] = data
            self._tasks[task].pop('reset_time', None)
        elif ltip == Parser.TASK_COMPLETED:
            if task not in self._tasks:
                return {}
            else:
                start_data = self._tasks[task]
                del self._tasks[task]
                return [CT.B(start_data), CT.E(data)]
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
            res += ' ' * 2 * depth + f'[{task["optype"]}] {task["task"]}\n'
            res += self.render_plan_tree(tree, task['task'], depth + 1)
        return res

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

