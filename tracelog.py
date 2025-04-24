#!/usr/bin/env python3

import sys

from TraceLog import TraceLog

def main():
    if len(sys.argv) < 2:
        print("Usage: tracelog.py <log_file> [output_file]")
        sys.exit(1)

    log_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None

    trace = TraceLog(log_file)
    trace.render_as_tasks()

    if output_file:
        trace.export_chrome_trace(output_file)
    else:
        trace.dump()

if __name__ == '__main__':
    main()

