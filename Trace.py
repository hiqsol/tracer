#!/usr/bin/env python3

import re
import datetime

class Trace:
    ACTION = 'A'
    TASK = 'T'
    OPERATOR = 'O'
    PRE = 'P'

    def __init__(self, data: dict):
        self._data = self.prepare(data)

    @property
    def task(self) -> str:
        return self.get('task')

    def get_all(self) -> dict:
        return self._data
    def has(self, key: str) -> bool:
        return key in self._data and self._data[key]
    def get(self, key: str) -> str:
        if key not in self._data:
            raise KeyError(f"Key '{key}' not found in Trace data: {self._data}")
        return self._data.get(key, '')
    def get_dict(self, key: str) -> dict:
        if key not in self._data:
            raise KeyError(f"Key '{key}' not found in Trace data: {self._data}")
        return self._data.get(key, {})
    def get_ms(self, key: str) -> int:
        return Trace.time2ms(self.get(key))

    def prepare(self, data: dict) -> dict:
        data['agent'] = Trace.data2agent(data)
        if 'agentID' in data:
            del data['agentID']
        if 'agentID' in data['args']:
            del data['args']['agentID']
        if 'start' not in data:
            if 'time' not in data:
                raise ValueError(f"Start time not found in Trace data: {data}")
            data['start'] = data['time']
        if 'finish' not in data:
            raise ValueError(f"Finish time not found in Trace data: {data}")
        task = data.get('task', '')
        name = task
        type = Trace.task2type(task)
        if type == 'DISP_MSG':
            type = data['args']['kind']
            name = f'{type}-{task}'
        data['name'] = name
        data['type'] = type
        return data

    @staticmethod
    def task2type(task: str) -> str:
        ms = re.search(r'(\w+)\.(\w+)\.([\w\+]+)', task)
        if ms:
            return ms.group(1)
        return task
    @staticmethod
    def data2agent(data: dict) -> str:
        if 'agent' in data:
            return data['agent']
        if 'agentID' in data:
            return data['agentID']
        if 'args' in data:
            return Trace.data2agent(data['args'])
        return ''
    @staticmethod
    def time2ms(time: str) -> int:
        tstr = time.replace('Z', '+00:00')
        return int(datetime.datetime.fromisoformat(tstr).timestamp() * 1000000)
