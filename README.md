# dubRE
Classification-driven function name extraction plugin for IDA Pro.

## Directories

See subfolder READMEs for details on plugin and script usage:
- `plugins` - IDA plugin utilities for IDB information export
- `scripts` - standalone scripts for data transformation; contains dependency modules

## Datasets

The research on dubRE was performed on 15 binaries which are pending publication in raw and processed form. The repository list of applications used throughout the research is available [here](https://github.com/stars/michal-kapala/lists/dubre-sources).

To extend the dataset with new binaries see [*Dataset preparation*](https://github.com/michal-kapala/dubRE/wiki/Dataset-preparation).

## Wikis

Conceptual notes and remarks made during implementation of *dubRE* are available as [wikis](https://github.com/michal-kapala/dubRE/wiki).

## Dependencies

| Dependency | Version |
|---|---|
| IDA Pro | 7.0 |
| Python (plugins) | 2.7 |
| Python (scripts) | >= 3.10 |
| [Sark](https://github.com/tmr232/Sark) | IDA-6.x |
