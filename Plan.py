#!/usr/bin/env python3

import json

from Parser import Parser

class Plan:
    def __init__(self, tracer):
        self.parser = Parser('')
        self.tracer = tracer
        self.plan = {}
        self.tasks = {}
        self.tree = {}
        self.parents = {}

    def add_tasks(self, tasks: dict):
        for task in tasks.values():
            self.add_task(task)

    def add_task(self, task: dict):
        name = task['task']
        if name in self.tasks:
            return

        self.tasks[name] = task

        parent = task.get('parent', '')
        if parent not in self.tree:
            self.tree[parent] = []
            self.parents[parent] = 1
        if parent and parent not in self.tasks:
            parent_task = self.tracer.get_task(parent)
            if not parent_task:
                raise ValueError(f'Parent task {parent} not found for task {name}')
            self.add_task(parent_task)
        self.tree[parent].append(task)

    def render(self):
        return f'{len(self.tasks)} tasks\n' + self.render_subtree()

    def render_subtree(self, parent='', depth=0):
        res = ''
        for task in self.tree.get(parent, []):
            args = self.render_args(task.get('args', {}))
            pres = self.render_pres(task.get('pres', {}))
            res += ' ' * 2 * depth + f'[{task["optype"]}] {task["task"]}{args}{pres}\n'
            res += self.render_subtree(task['task'], depth + 1)
        return res

    def render_args(self, args: dict) -> str:
        if not args:
            return ''
        return '(' + self.parser.render_args(args) + ')'

    def render_pres(self, pres: dict) -> str:
        if not pres:
            return ''
        return ' Pre: ' + self.parser.render_pres(pres)

    def dump(self):
        print(f'tasks: {json.dumps(self.tasks, indent=2)}')
        print()
        print(f'tree: {json.dumps(self.tree, indent=2)}')
        print()
        print(f'parents: {json.dumps(self.parents, indent=2)}')
