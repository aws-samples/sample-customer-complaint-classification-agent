# Python Execution Guidelines

When executing Python commands in this project, always use `python3` instead of `python`.

## Examples

- Run tests: `python3 -m pytest tests/`
- Run a script: `python3 script.py`
- Install packages: `python3 -m pip install -r requirements.txt`
- Run module: `python3 -m module_name`

This ensures compatibility on systems where `python` may not be available or may point to Python 2.

# Python Formatting Guidelines

When formatting Python code in this project, and after completing tests, remove all comments aside from docstrings which explain functions, classes, etc.

This helps to remove the "bloat" within the project that comes along with comments existing everywhere. Someone who knows how to read Python should be able to determine what is happening in each section and file.
