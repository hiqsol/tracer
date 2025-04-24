#!/usr/bin/env python3

import re
import json
import datetime
import sys
from typing import Dict, List, Any, Optional

# Chrome Trace object
class CT:
    @staticmethod
    def B(data: Dict) -> Dict: return CT.build(data, {'ph': 'B'})
    @staticmethod
    def E(data: Dict) -> Dict: return CT.build(data, {'ph': 'E'})

    @staticmethod
    def build(data: Dict, data2: Dict = {}) -> Dict:
        data.update(data2)
        if 'pid' not in data:
            data['pid'] = 0
        res = {}
        for key in ['name', 'cat', 'ph', 'ts', 'pid', 'tid', 'args']:
            if key in data:
                res[key] = data[key]
        return res

class TraceLog:
    def __init__(self, path: str):
        self._path = path
        self._data = []
        self._events = []
        self._count = 0
        self._unparsed = 0
        self._task_exp = r'(\w+\.\w+\.[\w\+]+)'
        self._tasks = {}
        self._parsers = {
            'Decomposed':       [self._parse_Decomposed],
            'AppendPlan':       [self._parse_AppendPlan],
            'ReplacePlan':      [self._parse_ReplacePlan],
            'NewTask':          [self._parse_NewTask],
            'PerformTask':      [self._parse_PerformTask],
            'StatusChanged':    [self._parse_StatusChanged],
            'TaskReceived':     [self._parse_TaskReceived],
            'TaskCompleted':    [
                self._parse_TaskCompleted,
                self._parse_TaskCompletedWithAgent,
                self._parse_TaskCompletedWithMessage,
            ],
        }
        self.read_file(path)

    def read_file(self, path: str) -> None:
        try:
            with open(path, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        data = json.loads(line)
                        res = self.parse_data(data)
                        if res:
                            self._data.append(res)
                    except json.JSONDecodeError:
                        print(f"Invalid JSON: {line}")
                        continue
        except FileNotFoundError:
            print(f"Can't read {path}")

    def parse_data(self, data: Dict) -> Dict:
        if not self._validate_log_entry(data):
            return {}
        for kind, parsers in self._parsers.items():
            for parser in parsers:
                res = parser(data)
                if res:
                    res['kind'] = kind
                    return res
        # print(f"Cannot parse message: {data['message']}")
        self._unparsed+=1
        return {}

    @property
    def unparsed(self) -> int: return self._unparsed

    def _validate_log_entry(self, data: Dict) -> bool:
        return all(key in data for key in ['scope', 'message', 'time'])

    def _parse_AppendPlan(self, data: Dict) -> Dict:
        ms = re.search(r'^APPEND PLAN', data['message'])
        if not ms:
            return {}
        return {
            'time': data['time'],
            'scope': data['scope'],
            'tick': data.get('tick', 0)
        }

    def _parse_ReplacePlan(self, data: Dict) -> Dict:
        ms = re.search(r'^REPLACE PLAN', data['message'])
        if not ms:
            return {}
        return {
            'time': data['time'],
            'scope': data['scope'],
            'tick': data.get('tick', 0)
        }

    def _parse_Decomposed(self, data: Dict) -> Dict:
        # DECOMPOSED CHECK_SELF_CONTROL_REQS.R.5
        ms = re.search(rf'^DECOMPOSED {self._task_exp}', data['message'])
        if not ms:
            return {}

        return {
            'task': ms.group(1),
            'time': data['time'],
            'scope': data['scope'],
            'tick': data.get('tick', 0)
        }

    def _parse_NewTask(self, data: Dict) -> Dict:
        # 0. [O] SELF.R.9(RS2) Pre:
        ms = re.search(rf'^(\d+)\. \[(T|O)\] {self._task_exp}', data['message'])
        if not ms:
            return {}

        return {
            'task': ms.group(3),
            'type': ms.group(2),
            'no': ms.group(1),
            'time': data['time'],
            'scope': data['scope'],
            'tick': data.get('tick', 0)
        }

    def _parse_PerformTask(self, data: Dict) -> Dict:
        # Order agent RS5 to perform task SELF.R.7
        ms = re.search(rf'^Order agent (\w+) to perform task {self._task_exp}', data['message'])
        if not ms:
            return {}
        return {
            'task': ms.group(2),
            'agent': ms.group(1),
            'time': data['time'],
            'scope': data['scope'],
            'tick': data.get('tick', 0)
        }

    def _parse_StatusChanged(self, data: Dict) -> Dict:
        # Task SELF.R.7 status changed to Completed: position improved
        ms = re.search(rf'Task {self._task_exp} status changed to (.*)', data['message'])
        if not ms:
            return {}
        return {
            'task': ms.group(1),
            'status': ms.group(2),
            'agent': data.get('agentId', ''),
            'time': data['time'],
            'scope': data['scope'],
            'tick': data.get('tick', 0)
        }

    def _parse_TaskReceived(self, data: Dict) -> Dict:
        # New task SELF.R.9 received by agent
        ms = re.search(rf'New task {self._task_exp} received by agent', data['message'])
        if not ms:
            return {}
        return {
            'task': ms.group(1),
            'agent': data.get('agentId', ''),
            'time': data['time'],
            'scope': data['scope'],
            'tick': data.get('tick', 0)
        }

    def _parse_TaskCompleted(self, data: Dict) -> Dict:
        # Task SELF.R.9(RS2) completed. There are 4 task(s) left in the plan
        ms = re.search(rf'Task {self._task_exp}\((\w+)\) completed\.', data['message'])
        if not ms:
            # Task SET_DESTINATION.R.+(agentID=RS12, node=51.23.6-1-WS-2-A-100D30-1f0, dirs=[90º 270º]) completed. There are 27 task(s) left in the plan
            ms = re.search(rf'Task {self._task_exp}\(agentID=(\w+).+\) completed\.', data['message'])
        if not ms:
            return {}
        return {
            'task': ms.group(1),
            'agent': ms.group(2),
            'time': data['time'],
            'scope': data['scope'],
            'tick': data.get('tick', 0)
        }

    def _parse_TaskCompletedWithAgent(self, data: Dict) -> Dict:
        # Task DRE.R._(agent=RS8, from=51.23.6-DC-2-A-100L110-0f0#5-0, to=51.23.6-1-ws-DC-2-A-100D1110-0f0#5-90, len=1) completed. There are 26 task(s) left in the plan"}
        ms = re.search(rf'Task {self._task_exp}\(agent=(\w+).+\) completed\.', data['message'])
        if not ms:
            return {}
        return {
            'task': ms.group(1),
            'agent': ms.group(2),
            'time': data['time'],
            'scope': data['scope'],
            'tick': data.get('tick', 0)
        }

    def _parse_TaskCompletedWithMessage(self, data: Dict) -> Dict:
        # Task SEND_FM_MSG.R.Z(message=890000000000001, status=Assigned, binID=tUnk) completed. There are 27 task(s) left in the plan"}
        ms = re.search(rf'Task {self._task_exp}\(message=(\w+),\s+status=(\w+),\s+binID=(\w+)\) completed\.', data['message'])
        if not ms:
            return {}
        return {
            'task': ms.group(1),
            'message': ms.group(2),
            'status': ms.group(3),
            'bin': ms.group(4),
            'time': data['time'],
            'scope': data['scope'],
            'tick': data.get('tick', 0)
        }

    def _process_events(self) -> None:
        # Map for tracking start times of tasks
        task_starts = {}

        for entry in self._data:
            if not entry:
                continue

            # Convert ISO time to microseconds
            try:
                timestamp = datetime.datetime.fromisoformat(entry['time'].replace('Z', '+00:00')).timestamp() * 1000000
            except (ValueError, KeyError):
                continue

            # Handle task start events
            if entry.get('status') == 'Received' or entry.get('status') == 'InProgress':
                task_id = f"{entry.get('name')}-{entry.get('agent', '')}"
                task_starts[task_id] = {
                    'ts': timestamp,
                    'name': entry.get('name', ''),
                    'agent': entry.get('agent', '')
                }

            # Handle task completion events
            elif entry.get('status') == 'Completed':
                task_id = f"{entry.get('name')}-{entry.get('agent', '')}"
                if task_id in task_starts:
                    start_data = task_starts[task_id]
                    # Create duration event
                    self._events.append({
                        'name': start_data['name'],
                        'cat': 'task',
                        'ph': 'X',  # Duration event
                        'ts': start_data['ts'],
                        'dur': timestamp - start_data['ts'],
                        'pid': 1,
                        'tid': hash(start_data['agent']) % 1000,  # Create a thread ID from agent name
                        'args': {
                            'agent': start_data['agent']
                        }
                    })
                    # Remove from starts map
                    del task_starts[task_id]

            # Add all entries as instant events
            self._events.append({
                'name': entry.get('name', ''),
                'cat': entry.get('scope', '').replace('/', '.')[1:],
                'ph': 'i',  # Instant event
                'ts': timestamp,
                'pid': 1,
                'tid': hash(entry.get('agent', entry.get('scope', ''))) % 1000,
                'args': {
                    'tick': entry.get('tick', 0),
                    'status': entry.get('status', ''),
                    'scope': entry.get('scope', '')
                }
            })

    def render_as_tasks(self):
        for data in self._data:
            kind = data.get('kind')
            res = self.data2task(kind, data)
            if not res:
                continue
            elif isinstance(res, list):
                self._events.extend(res)
            else:
                self._events.append(res)
        for task, data in self._tasks.items():
            data['name'] = task
            # data['cat'] = self.scope2cat(data.get('scope', ''))
            data['ts'] = self.time2ts(data.get('time', ''))
            self._events.append(CT.B(data))

    def data2task(self, kind, data: Dict):
        task = data.get('task', '')
        # task = self.task2tt(task)
        data['name'] = task
        # data['cat'] = self.scope2cat(data.get('scope', ''))
        data['ts'] = self.time2ts(data.get('time', ''))
        # if 'agent' in data:
            # data['tid'] = self.agent2tid(data.get('agent', ''))
        if kind == 'NewTask':
            if task not in self._tasks:
                self._tasks[task] = data
                return {}
        elif kind == 'TaskCompleted':
            if task not in self._tasks:
                return {}
            else:
                start_data = self._tasks[task]
                del self._tasks[task]
                return [CT.B(start_data), CT.E(data)]
            # return CT.E(data)
        return {}

    def task2kebab(self, task: str) -> str:
        ms = re.search(r'(\w+)\.(\w+)\.([\w\+]+)', task)
        if ms:
            return '-'.join([ms.group(1), ms.group(2), ms.group(3)])
        return task

    def task2tt(self, task: str) -> str:
        ms = re.search(r'(\w+)\.(\w+)\.([\w\+]+)', task)
        if ms:
            return ms.group(1)
        return task

    def scope2cat(self, scope: str) -> str:
        """Convert scope to category for visualization"""
        return scope.strip('/').replace('/', '.')

    def agent2tid(self, agent: str) -> int:
        ms = re.search(r'(\d+)$', agent)
        return int(ms.group(1)) if ms else 0

    def time2ts(self, time: str) -> int:
        tstr = time.replace('Z', '+00:00')
        return int(datetime.datetime.fromisoformat(tstr).timestamp() * 1000000)

    def chrome_trace(self, data: Dict) -> Dict:
        """Convert data to Chrome Trace format"""
        return {
            'name': data.get('name', ''),
            'cat': self.scope2cat(data.get('scope', '')),
            'ph': data.get('ph', ''),
            'ts': data.get('ts', 0),
            'pid': data.get('pid', 0),
            'tid': data.get('tid', 0),
            'args': data.get('args', {})
        }

    def get_data(self) -> List[Dict]:
        return self._data

    def get_chrome_trace(self, events: List[Dict]) -> Dict[str, Any]:
        return {
            'traceEvents': events,
            'displayTimeUnit': 'ms',
            'otherData': {
                'version': '1.0',
                'source': self._path
            }
        }

    def dump(self) -> None:
        for item in self._data:
            kind = item.get('kind')
            del item['kind']
            print(f'{kind:>20}: {item}')

    def export_chrome_trace(self, output_path: Optional[str] = None) -> None:
        """Export trace data in Chrome Trace JSON format"""
        trace_data = self.get_chrome_trace(self._events)
        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(trace_data, f, indent=2)
            print(f"Trace exported to {output_path}")
        else:
            print(json.dumps(trace_data, indent=2))

