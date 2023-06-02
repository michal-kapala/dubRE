# Plugins

Data extraction plugins for IDA Pro.

## `string_export.py`

Exports unique raw strings from IDA into SQLite `strings` table.

IDA hotkey: `Shift+S`

# Installation

To install a plugin either drop it in `IDA Pro/plugins` directory or use [Sark's plugin loader](https://sark.readthedocs.io/en/latest/plugins/installation.html) to load it from a remote folder.

# Dependencies

Please note that non-plugin scripts use Python 3 syntax.

| Dependency | Version |
|---|---|
| IDA Pro | 7.0 |
| Python | 2.7 |
| [Sark](https://github.com/tmr232/Sark) | IDA-6.x |
