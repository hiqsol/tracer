#!/usr/bin/env python3

from Tracer import Tracer

class FindChildren:
    def __init__(self, tracer):
        self.tracer = tracer
        self.tasks = {}

    def start(self, task_name):
        self.tasks = {task_name: 1}
        while True:
            count = len(self.tasks)
            self.find_all_tasks()
            if count == len(self.tasks):
                break

    def find_all_tasks(self):
        for trace in self.tracer.traces:
            data = trace.get_all()
            if self.check_mentions_tasks(data):
                self.tasks[trace.task] = 1

    def check_mentions_tasks(self, data: dict):
        for value in data.values():
            if isinstance(value, dict):
                res = self.check_mentions_tasks(value)
                if res:
                    return True
            else:
                if value in self.tasks:
                    return True
        return False

    def export(self, filename: str):
        traces = []
        for trace in self.tracer.traces:
            if trace.task in self.tasks:
                traces.append(trace)
        Tracer.export_traces(traces, f'{filename}.json')

class FindRelated(FindChildren):
    def __init__(self, tracer):
        super().__init__(tracer)
        self.tasks = {}
        self.relation = {}

    def find_all_tasks(self):
        super().find_all_tasks()
        self.add_related_tasks()

    def add_related_tasks(self):
        for task in self.tasks.copy():
            self.add_mentioned_tasks(self.tracer.get_task(task))

    def add_mentioned_tasks(self, task: dict):
        for key, value in task.items():
            if isinstance(value, dict):
                self.add_mentioned_tasks(value)
            else:
                if key in ['task']:
                    self.tasks[value] = 1
