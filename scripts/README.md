# Scripts

Scripts used in dataset preparation during *dubRE* research (require Python 3.10 or newer).

## `pdb.py`
Demangles and transforms pre-parsed PDB information from a JSON file into `pdb` SQLite table.
 
To produce a JSON file from PDB use this fork of [willglynn/pdb](https://github.com/michal-kapala/pdb/tree/ground-truth).

Usage:
```
python pdb.py --dbpath="<database path>" --json="<JSON file path>"
```

## `tokenize.py`
Creates `tokens` SQLite table off `strings` table; to create `strings` use [`string_export.py`](https://github.com/michal-kapala/dubRE/tree/master/plugins) IDA plugin.

Usage:
```
python tokenize.py --dbpath="<database path>"
```

## `mergedb.py`

Merges all binary databases specified in a JSON configuration file into one.

See example [merge_db_config.json](/merge_db_config.json) for details.

Usage (with example config):
```
python mergedb.py --config="<dubRE root dir>/mergedb_example.json"
```

# Modules

Packages implemented for internal use:
- `demangler` - simple demangler for MSVC-originating function names found in [PDB format](https://github.com/microsoft/microsoft-pdb) (based on [wikiversity.org](https://en.wikiversity.org/wiki/Visual_C++_name_mangling))
- `tokens` - parsers for structuring name-like tokens from raw text
- `utils` - miscellaneous utilities

# Tests

Basic unit tests for internal modules - file naming convention is `test_<package name>.py`.
