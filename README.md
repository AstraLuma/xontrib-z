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
pip install git+https://github.com/astronouth7303/xontrib-z
```

## Configuration

To automatically load z startup, put
```console
xontrib load z
```

in your `.xonshrc`
The location of the data file is determined by setting an environment variable `_Z_DATA` 
(default `~/.z` if not set).
