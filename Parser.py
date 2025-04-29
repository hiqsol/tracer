#!/usr/bin/env python3

import re
import json
from typing import Dict, List

class Parser:
    APPEND_PLAN = 'AppendPlan'
    REPLACE_PLAN = 'ReplacePlan'
    DECOMPOSED = 'Decomposed'
    NEW_TASK = 'NewTask'
    PLAN_CHANGED = 'PlanChanged'
    PERFORM_TASK = 'PerformTask'
    STATUS_CHANGED = 'StatusChanged'
    TASK_RECEIVED = 'TaskReceived'
    TASK_COMPLETED = 'TaskCompleted'

    @property
    def events(self) -> List[Dict]: return self._events
    @property
    def unparsed(self) -> int: return self._unparsed

    def __init__(self, path: str):
        self._path = path
        self._events = []
        self._state = ''
        self._parent_task = ''
        self._count = 0
        self._unparsed = 0
        self._task_exp = r'(\w+\.\w+\.[\w\+]+)'
        self._parsers = {
            self.DECOMPOSED:        [self._parse_Decomposed],
            self.APPEND_PLAN:       [self._parse_AppendPlan],
            self.REPLACE_PLAN:      [self._parse_ReplacePlan],
            self.NEW_TASK:          [self._parse_NewTask],
            self.PERFORM_TASK:      [self._parse_PerformTask],
            self.STATUS_CHANGED:    [self._parse_StatusChanged],
            self.TASK_RECEIVED:     [self._parse_TaskReceived],
            self.TASK_COMPLETED:    [
                self._parse_TaskCompleted,
                self._parse_TaskCompletedWithAgent,
                self._parse_TaskCompletedWithMessage,
            ],
        }
        self.read_file(path)

    def read_file(self, path: str) -> None:
        try:
            with open(path, 'r', encoding='utf-8') as f:
                prev = {}
                for line in f:
                    try:
                        data = json.loads(line)
                        res = self.parse_data(data)
                        if res:
                            self._events.append(res)
                        ltip = res.get('ltip', '')
                        if prev and prev['ltip'] == self.NEW_TASK and ltip != self.NEW_TASK:
                            self._events.append({
                                'ltip': self.PLAN_CHANGED,
                                'time': prev['time'],
                            })
                        prev = res

                    except json.JSONDecodeError:
                        print(f"Invalid JSON: {line}")
                        continue
        except FileNotFoundError:
            print(f"Can't read {path}")

    def parse_data(self, data: Dict) -> Dict:
        if not self._validate_log_entry(data):
            return {}
        for ltip, parsers in self._parsers.items():
            for parser in parsers:
                res = parser(data)
                if res:
                    res['ltip'] = ltip
                    return res
        # print(f"Cannot parse message: {data['message']}")
        self._unparsed += 1
        return {}

    def _validate_log_entry(self, data: Dict) -> bool:
        return all(key in data for key in ['scope', 'message', 'time'])

    def _parse_AppendPlan(self, data: Dict) -> Dict:
        ms = re.search(r'^APPEND PLAN', data['message'])
        if not ms:
            return {}
        self._state = self.APPEND_PLAN
        self._parent_task = ''
        return {
            'time': data['time'],
            'scope': data['scope'],
            'tick': data.get('tick', 0)
        }

    def _parse_ReplacePlan(self, data: Dict) -> Dict:
        ms = re.search(r'^REPLACE PLAN', data['message'])
        if not ms:
            return {}
        self._parent_task = ''
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

        self._parent_task = ms.group(1)
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
            'optype': ms.group(2),
            'parent': self._parent_task,
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

    def dump(self) -> None:
        for item in self._events:
            ltip = item.get('ltip')
            del item['ltip']
            print(f'{ltip:>20}: {item}')

