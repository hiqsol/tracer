#!/usr/bin/env python3

class DBSaver:
    def __init__(self, db, tracer):
        self.db = db
        self.tracer = tracer
        self.site_id = None
        self.session_id = None

    def save(self):
        self.save_site()
        self.save_session()
        self.save_traces()

    def save_site(self):
        site = self.tracer.session['site']
        self.site_id = self.find_site_id(site)
        if not self.site_id:
            self.db.insert([{"name": site}], "site", ["name"], ["name"])
        self.site_id = self.find_site_id(site)

    def find_site_id(self, site):
        res = self.db.select(f"SELECT id FROM site WHERE name='{site}'")
        if not res:
            return None
        return res[0][0]

    def find_session_id(self, site_id=None, start=None):
        res = self.db.select(f"SELECT id FROM session WHERE site_id={site_id} AND start='{start}'")
        if not res:
            return None
        return res[0][0]

    def save_session(self):
        start = self.tracer.session['start']
        data = {
            'site_id': self.site_id,
            'start': start,
            'finish': self.tracer.session['finish'],
            'type': self.tracer.session['type'],
        }
        self.session_id = self.find_session_id(self.site_id, start)
        if not self.session_id:
            self.db.insert([data], 'session', data.keys(), ['site_id', 'start'])
        self.session_id = self.find_session_id(self.site_id, start)

    def save_traces(self):
        rows = []
        for trace in self.tracer.traces:
            rows.append({
                'session_id': self.session_id,
                'task': trace.task,
                'type': trace.get('type'),
                'optype': trace.get('optype'),
                'start': trace.get('start'),
                'finish': trace.get('finish'),
                'data': trace.data,
            })
        first = rows[0]
        self.db.upsert(rows, 'trace', first.keys(), ['session_id', 'task', 'start'])
