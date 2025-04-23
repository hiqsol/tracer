#!/usr/bin/env python3

import re
import json

class TraceLog:
    def __init__(self, path):
        self._path = path
        self._data = []
        self._count = 0
        self.read_file(path)

    def read_file(self, path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                while True:
                    line = f.readline()
                    if not line:
                        break
                    try:
                        data = json.loads(line)
                    except json.JSONDecodeError:
                        print(f"Invalid JSON: {line}")
                        continue
                    if self.process_data(data):
                        break
        except FileNotFoundError:
            print(f"Can't read {path}")

    def process_data(self, data):
        res = self.parse_data(data)
        if not res:
            return False
        self._data.append(res)
        self._count += 1
        return self._count >= 10

    def parse_data(self, data):
        if 'scope' not in data:
            return {}
        if 'message' not in data:
            return {}
        if 'time' not in data:
            return {}
        if data['scope'] != '/planner':
            return {}
        ms = re.search(r'^(\d+)\. \[(T|O)\] (\w+)', data['message'])
        if not ms:
            return {}

        res = {}
        res['no'] = ms.group(1)
        res['type'] = ms.group(2)
        res['name'] = ms.group(3)
        return res

    def get_data(self):
        return self._data

    def dump(self):
        for item in self._data:
            print(f'{item["no"]}: {item["type"]} {item["name"]}')

def main():
    trace = TraceLog('trace.log')
    trace.dump()

if __name__ == '__main__':
    main()
