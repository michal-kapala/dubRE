# Scripts

Scripts used in dataset preparation during *dubRE* research (require Python 3.10 or newer).

## `autolabel_paths.py`

Automatically labels `paths` records based on token inclusion in `pdb` function names. Obtained results still need manual review and corrections.

Usage:
```
python autolabel_paths.py --dbpath=<database path>
```

## `mergedb.py`

Merges all binary databases specified in a JSON configuration file into one.

See example [mergedb_example.json](/mergedb_example.json) for details.

Usage (with example config):
```
python mergedb.py --config="<dubRE root dir>/mergedb_example.json"
```

## `pdb.py`
Demangles and transforms pre-parsed PDB information from a JSON file into `pdb` SQLite table.
 
To produce a JSON file from PDB use this fork of [willglynn/pdb](https://github.com/michal-kapala/pdb/tree/ground-truth).

Usage:
```
python pdb.py --dbpath="<database path>" --json="<JSON file path>"
```

## `tokenize_one.py`
Creates unlabelled `tokens` off a single string; to create `strings` use [`string_export.py`](https://github.com/michal-kapala/dubRE/tree/master/plugins) IDA plugin.

Usage:
```
python tokenize_one.py --dbpath="<database path>" --offset=<string offset>
```

## `tokenize.py`
Creates `tokens` SQLite table off `strings` table; to create `strings` use [`string_export.py`](https://github.com/michal-kapala/dubRE/tree/master/plugins) IDA plugin.

Usage:
```
python tokenize.py --dbpath="<database path>"
```

## `tpaths_add_missing_pos.py`
Adds missing token paths from `paths` positives to `token_paths_positive` to be labelled and merged into `token_paths` (use [`tpaths_merge_pos.py`](#tpaths_merge_pospy)).

Usage:
```
python tpaths_add_missing_pos.py --dbpath="<database path>"
```

## `tpaths_add_one_missing.py`
Adds missing `tokens` and `token_paths` of a single unlabelled string referenced by a path. Only for unexpected deletions/extraction plugin failures.

Usage:
```
python tpaths_add_one_missing.py --dbpath="<database path>" --pathid=<path id>
```

## `tpaths_label_neg.py`
Adds missing labels of negative `token_paths` based on `paths` labels.

Usage:
```
python tpaths_label_neg.py --dbpath="<database path>"
```

## `tpaths_merge_pos.py`

Copies positive labels from `token_paths_positive` helper table into `token_paths` table and deletes `token_paths_positive`.

Usage:
```
python tpaths_merge_pos.py --dbpath=<database path>
```

## `tpaths_neg.py`

Adds and autolabels negative `token_paths` based on `paths` labels.

Usage:
```
python tpaths_neg.py --dbpath="<database path>"
```

## `tpaths_pos.py`

Creates and populates `token_paths_positive` table with **positive** function-string paths. Manual labelling of function-token paths should be performed on this table and copied back to `token_paths` with [`tpaths_merge_pos.py`](#tpaths_merge_pospy).

Usage:
```
python tpaths_pos.py --dbpath=<database path>
```

## `tpaths.py`

Creates and populates `token_paths` table from `paths` and `tokens` positives.

Usage:
```
python tpaths.py --dbpath="<database path>"
```

# Modules

Packages implemented for internal use:
- `demangler` - simple demangler for MSVC-originating function names found in [PDB format](https://github.com/microsoft/microsoft-pdb) (based on [wikiversity.org](https://en.wikiversity.org/wiki/Visual_C++_name_mangling))
- `tokens` - parsers for structuring name-like tokens from raw text
- `utils` - miscellaneous utilities

# Tests

Basic unit tests for internal modules - file naming convention is `test_<package name>.py`.

## `test_tokens.py`

Unit tests for `tokens` module.

Usage:
```
python -m unittest test_tokens.py
```
