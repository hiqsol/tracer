# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands
- Run program: `./tracelog.py a.log`
- Run linting: `pylint tracelog.py`
- Run tests: `./test_TraceLog.py`

## Code Style Guidelines
- Imports: Standard library first, then third-party, then local modules
- Formatting: 4-space indentation, 80-character line limit, no trailing whitespace
- Types: Use type hints for function parameters and return values
- Naming: `snake_case` for variables/functions, CamelCase for classes
- Error handling: Use try/except blocks with specific exceptions
- Documentation: Docstrings for modules, classes, and functions
- File handling: Always use context managers (with statement) and explicit encoding
- JSON handling: Use try/except for parsing to handle malformed data
