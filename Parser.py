#!/usr/bin/env python3

import re
import json

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
    def events(self) -> list[dict]: return self._events
    @property
    def unparsed(self) -> int: return self._unparsed

    def __init__(self, path: str):
        self._path = path
        self._events = []
        self._state = ''
        self._parent_task = ''
        self._count = 0
        self._unparsed = 0
        self._task_exp = r'(?P<task>\w+\.\w+\.[\w\+]+)'
        self._orgn_exp = r'(?P<orgn>\w+\.\w+\.[\w\+]+)'
        self._args_exp = r'(\((?P<args>[^\)]+)\))?'
        self._pres_exp = r' Pre: (?P<pres>.*)'
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
                self._parse_TaskMarkedAsCompleted,
            ],
        }
        if path:
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

    def parse_data(self, data: dict) -> dict:
        if not self._validate_log_entry(data):
            return {}
        for ltip, parsers in self._parsers.items():
            for parser in parsers:
                res = parser(data)
                if res:
                    res['ltip'] = ltip
                    res['message'] = data['message']
                    return res
        # print(f"Cannot parse message: {data['message']}")
        self._unparsed += 1
        return {}

    def _validate_log_entry(self, data: dict) -> bool:
        return all(key in data for key in ['scope', 'message', 'time'])

    def _parse_AppendPlan(self, data: dict) -> dict:
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

    def _parse_ReplacePlan(self, data: dict) -> dict:
        ms = re.search(r'^REPLACE PLAN', data['message'])
        if not ms:
            return {}
        self._parent_task = ''
        return {
            'time': data['time'],
            'scope': data['scope'],
            'tick': data.get('tick', 0)
        }

    def _parse_Decomposed(self, data: dict) -> dict:
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

    def _parse_NewTask(self, data: dict) -> dict:
        # 0. [T] DISP_MSG.3p.3(msgID=870000000082842, kind=AOApplicationSummary, status=Created) Pre: `STATE_READY`"}
        ms = re.search(rf'^(\d+)\. \[(T|O)\] {self._task_exp}{self._args_exp}{self._pres_exp}', data['message'])
        if not ms:
            # 4. [T] WRAP.3p.Nm(orgn=DISP_MSG.3p.Gg(msgID=870000000082915, kind=BinFromWSChannelToBinStorageMove, status=Created)) Pre: `PLAN_AFTER(task=DRL.3p.NM)`
            ms = re.search(rf'^(\d+)\. \[(T|O)\] {self._task_exp}\(orgn={self._orgn_exp}{self._args_exp}\){self._pres_exp}', data['message'])
            if not ms:
                return {}

        return {
            'task': ms.group('task'),
            'optype': ms.group(2),
            'parent': self._parent_task,
            'origin': ms.groupdict().get('orgn', ''),
            'args': self.parse_args(ms.group('args')),
            'pres': self.parse_pres(ms.group('pres')),
            'no': ms.group(1),
            'time': data['time'],
            'scope': data['scope'],
            'tick': data.get('tick', 0)
        }

    def parse_args(self, input: str) -> dict:
        if not input:
            return {}
        res = {}

        # e=[0.01500, 0.02500]
        ms = re.search(r'^(.*)e=\[([\d\.]*), ([\d\.]+)\](.*)$', input)
        if ms:
            input = ms.group(1) + 'e=[' + ms.group(2) + ',' + ms.group(3) + ']' + ms.group(4)

        args = input.split(', ')
        if len(args) == 1:
            args = input.split(' ')
            for i in range(len(args)):
                res[f'arg{i}'] = args[i]
            return res


        for arg in args:
            try:
                key, value = arg.split('=', 1)
            except ValueError:
                raise Exception(f"Invalid argument format: {arg}\ninput: {input}")
            res[key.strip()] = value.strip()
        return res

    def parse_pres(self, input: str) -> dict:
        # Pre: `RUN_AFTER(task=MARK_GROUP_ACTIVE.3p.1d)`, `IS_MESSAGE_GROUP_ACTIVE(fmID=870000000082862, groupID=47d113d4-c79b-42f7-8e24-17ffde564356)`
        if not input:
            return {}

        res = {}
        pres = input.strip('`').split('`, `')
        for i in range(len(pres)):
            res[f'pre{i}'] = pres[i]
        return res


    def _parse_PerformTask(self, data: dict) -> dict:
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

    def _parse_StatusChanged(self, data: dict) -> dict:
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

    def _parse_TaskReceived(self, data: dict) -> dict:
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

    def _parse_TaskCompleted(self, data: dict) -> dict:
        # Task SELF.R.9(RS2) completed. There are 4 task(s) left in the plan
        ms = re.search(rf'Task {self._task_exp}{self._args_exp} completed\. There are', data['message'])
        if not ms:
            return {}
        return {
            'task': ms.group(1),
            'args': self.parse_args(ms.group('args')),
            'time': data['time'],
            'scope': data['scope'],
            'tick': data.get('tick', 0)
        }

    def _parse_TaskMarkedAsCompleted(self, data: dict) -> dict:
        # Task MOVE_BIN_TO_STORAGE.3p.sA is marked as completed because SEND_FM_MSG.3p.sH is already completed"}
        ms = re.search(rf'Task {self._task_exp} is marked as completed', data['message'])
        if not ms:
            return {}
        return {
            'task': ms.group(1),
            'time': data['time'],
            'scope': data['scope'],
            'tick': data.get('tick', 0)
        }

    def dump(self) -> None:
        for item in self._events:
            ltip = item.get('ltip')
            del item['ltip']
            print(f'{ltip:>20}: {item}')

