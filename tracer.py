#!/usr/bin/env python3

import sys

from Parser import Parser
from CT import CTRenderer, CT

def main():
    if len(sys.argv) < 2:
        print("Usage: parser.py <log_file> [output_file]")
        sys.exit(1)

    log_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else 'trace'

    parser = Parser(log_file)
    events = []
    no = 0
    for event in parser.events:
        events.append(event)
        if event['ltip'] == parser.PLAN_CHANGED:
            no += 1
            if no % 10 == 0 and no < 150:
                name = f'{output_file}-{no:05d}.json'
                ctr = CTRenderer(events)
                ctr.export(name)
                print(f'Plan changed No. {no}: {ctr.render_current_plan()}')
    ctr = CTRenderer(events)
    ctr.export(f'{output_file}.json')

    filter = 'ALLOCATE_RESOURCE.3p.Gu'
    trs = ctr.filter_by_task(filter)
    ctr.export_traces(trs, f'{output_file}-filtered.json')

    CT.short_names = True
    ctr.export(f'{output_file}-short.json')

if __name__ == '__main__':
    main()

