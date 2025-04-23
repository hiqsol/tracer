# TraceLog

TraceLog is a Python library for parsing logs and converting them into source for profiling tools
like [Perfetto](https://perfetto.dev/) and [SpeedScope](https://speedscope.app/).
In practice it reads given log file and converts it to a Chrome Trace JSON format
compatible with many profiling tools.
The library contains many predefined parsers for log formats used in our projects.
All known line formats are presented in the [example.txt](./example.txt) file.
