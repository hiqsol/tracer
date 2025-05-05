# TraceLog

TraceLog is a Python library for parsing logs and converting them into source for profiling tools
like [Perfetto](https://perfetto.dev/) and [SpeedScope](https://speedscope.app/).
In practice it reads given log file and converts it to a Chrome Trace JSON format
compatible with many profiling tools.
The library contains predefined parsers for log formats used in our projects.
All known line formats are presented in the [example.txt](./example.txt) file.

# Usage

```sh
./tracer.py sim.log sim
```

This will parse the `sim.log` file and create several Chrome Trace JSON files file in the same directory.
- `sim.json`
- `sim-short.json`
- more later
