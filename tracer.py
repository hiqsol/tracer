#!/usr/bin/env python3

import sys

from Parser import Parser
from Tracer import Tracer, CT
from Filter import FindChildren, FindRelated
from PG import PG
from DBSaver import DBSaver

def main():
    if len(sys.argv) < 2:
        print("Usage: parser.py <log_file> [filename]")
        sys.exit(1)

    log_file = sys.argv[1]
    filename = sys.argv[2] if len(sys.argv) > 2 else 'trace'

    parser = Parser(log_file)

    # events = []
    # no = 0
    # for event in parser.events:
    #     events.append(event)
    #     if event['ltip'] == parser.PLAN_CHANGED:
    #         no += 1
    #         if no % 10 == 0 and no < 150:
    #             name = f'{filename}-{no:05d}.json'
    #             ctr = Tracer(events)
    #             ctr.export(name)
    #             print(f'Plan changed No. {no}: {ctr.render_current_plan()}')

    ctr = Tracer(parser.events)
    ctr.export(f'{filename}')

    db = PG({})
    dbt = DBSaver(db, ctr)
    dbt.save()

    fbt = FindChildren(ctr)
    fbt.start('DISP_MSG.3p.cv')
    fbt.export(f'{filename}-children')

    rel = FindRelated(ctr)
    rel.start('DISP_MSG.3p.cv')
    rel.export(f'{filename}-related')

    CT.short_names = True
    ctr.export(f'{filename}-short')

if __name__ == '__main__':
    main()

