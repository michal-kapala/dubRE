# Plugins

Data extraction plugins for IDA Pro.

Recommended data extraction order (ensures data integrity):
1. [`xref_export.py`](#xref_exportpy)
2. [`string_export.py`](#string_exportpy)
3. [`utf16_export.py`](#utf16_exportpy)
4. [`func_export.py`](#func_exportpy)
5. [`funcdata_export.py`](#funcdata_exportpy)

To run the plugins open the IDB file and use the assigned hotkeys or go to `Edit/Plugins`.

## `string_export.py`

Exports unique raw strings from IDA into SQLite `strings` table.

IDA hotkey: `Shift+S`

## `xref_export.py`

Exports unique cross reference paths from IDA into SQLite `paths` table.

IDA hotkey: `Shift+X`

## `func_export.py`

Exports function addresses into SQLite `funcs` table.

IDA hotkey: `Shift+F`

## `funcdata_export.py`

Exports function data into premade SQLite `funcs` table.

IDA hotkey: `Shift+D`

# Installation

To install a plugin either drop it in `IDA Pro/plugins` directory or use [Sark's plugin loader](https://sark.readthedocs.io/en/latest/plugins/installation.html) to load it from a remote folder.

# Dependencies

Please note that non-plugin scripts use Python 3 syntax.

| Dependency | Version |
|---|---|
| IDA Pro | 7.0 |
| Python | 2.7 |
| [Sark](https://github.com/tmr232/Sark) | IDA-6.x |
