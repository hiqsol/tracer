import json

try:
    import psycopg2
except ImportError:
    pass

class PG:
    def __init__(self, ops):
        self.conn = psycopg2.connect(
            host        = ops.get("host",       "localhost"),
            database    = ops.get("database",   "fractal"),
            user        = ops.get("user",       "sol"),
            password    = ops.get("password",   "operator"),
        )

    def select(self, query):
        cur = self.conn.cursor()
        cur.execute(query)
        rows = cur.fetchall()
        cur.close()
        return rows

    def insert(self, data, table, fields, unique=None):
        return self.upsert(data, table, fields, unique, mode='insert')

    def upsert(self, data, table, fields, unique=None, mode='upsert'):
        if not unique:
            unique = []
        cur = self.conn.cursor()
        for row in data:
            values = []
            uvs = [row[k] for k in unique]
            cur.execute(f"SELECT id FROM {table} WHERE {' AND '.join([f'{k}=%s' for k in unique])}", uvs)
            id = cur.fetchone()[0] if cur.rowcount else None
            if id and mode == 'insert':
                continue
            for k in fields:
                value = None
                if k in row:
                    value = row[k]
                    # del row[k]
                elif k in ['d', 'x']:
                    value = row
                if isinstance(value, dict) or isinstance(value, list):
                    value = json.dumps(value)
                values.append(value)
            ss = self.bindings(fields)
            if mode == 'insert' or (mode == 'upsert' and not id):
                cur.execute(f"INSERT INTO {table} ({','.join(fields)}) VALUES ({ss})", values)
            else:
                cur.execute(f"UPDATE {table} SET {','.join([f'{k}=%s' for k in fields])} WHERE id=%s", values + [id])
        self.conn.commit()
        cur.close()

    def bindings(self, fields):
        return ','.join(['%s' for _ in fields])

    def execute(self, query):
        cur = self.conn.cursor()
        cur.execute(query)
        self.conn.commit()
        cur.close()
