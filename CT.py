#!/usr/bin/env python3

import re

from Trace import Trace

# Chrome Trace
class CT:
    short_names = False

    @staticmethod
    def build_file(traces: list[Trace]) -> dict:
        cts = []
        for trace in traces:
            cts.append(CT.X(trace))
        return {
            'traceEvents': cts,
            'displayTimeUnit': 'ms',
        }
    @staticmethod
    def B(trace: Trace) -> dict:
        return CT.build('B', trace)
    @staticmethod
    def E(trace: Trace) -> dict:
        return CT.build('E', trace)
    @staticmethod
    def X(trace: Trace) -> dict:
        data = CT.build('X', trace)
        data['dur'] = trace.get_ms('finish') - data['ts']
        return data

    @staticmethod
    def build(ph: str, trace: Trace) -> dict:
        data = {
            'name': CT.trace2name(trace),
            'cat':  CT.trace2cat(trace),
            'ph':   ph,
            'ts':   trace.get_ms('start'),
            'pid':  CT.trace2pid(trace),
            'tid':  CT.trace2tid(trace),
            'args': CT.trace2args(trace),
        }
        return {k: v for k, v in data.items() if v}

    @staticmethod
    def trace2cat(trace: Trace) -> str:
        return trace.get('type')
    @staticmethod
    def trace2name(trace: Trace) -> str:
        return trace.get('type') if CT.short_names else trace.get('name')

    @staticmethod
    def trace2pid(trace: Trace) -> int:
        if not trace.has('agent'):
            return 0
        ms = re.search(r'(\d+)$', trace.get('agent'))
        if ms:
            return int(ms.group(1))
        return 0
    @staticmethod
    def trace2tid(trace: Trace) -> int:
        return 0

    @staticmethod
    def trace2args(trace: Trace) -> dict:
        args = trace.get_dict('args').copy()
        args.update(trace.get_all())
        for key in ['agentID', 'args', 'cat', 'ltip', 'time', 'reset_time', 'message']:
            if key in args:
                del args[key]
        res = {}
        for key, value in args.items():
            if value:
                res[key] = value
        return res

