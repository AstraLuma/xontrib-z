# xontrib-z
Port of [z](https://github.com/rupa/z) to xonsh.

<hr>

## Installation
Just do a
```console
pip install xontrib-z
```

or you can clone the repo with pip
```console
pip install git+https://github.com/AstraLuma/xontrib-z
```

## Configuration

To automatically load z startup, put
```console
xontrib load z
```

in your `.xonshrc`

### Environment variables
The location of the data file is determined by setting the environment variable `_Z_DATA` 
(default `~/.z` if not set).

* Ignore case-sensitive matching by setting `_Z_CASE_SENSITIVE` to `False`.
* Exclude directories from consideration by adding them to `_Z_EXCLUDE_DIRS`.
* Ignore symlinks by setting `_Z_NO_RESOLVE_SYMLINKS` to `True`.