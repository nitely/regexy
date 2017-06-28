# regexy

[![Build Status](https://img.shields.io/travis/nitely/regexy.svg?style=flat-square)](https://travis-ci.org/nitely/regexy)
[![Coverage Status](https://img.shields.io/coveralls/nitely/regexy.svg?style=flat-square)](https://coveralls.io/r/nitely/regexy)
[![pypi](https://img.shields.io/pypi/v/regexy.svg?style=flat-square)](https://pypi.python.org/pypi/regexy)
[![licence](https://img.shields.io/pypi/l/regexy.svg?style=flat-square)](https://raw.githubusercontent.com/nitely/regexy/master/LICENSE)


A Python library for parsing, compiling, and executing regular expressions.
All searches execute in linear time with respect to the size of the regular
expression and search text.

Mostly based on Thompson's NFA.

> Be aware!
> This is nothing more than an experiment for researching purposes.

## Status

- [x] Matcher
- [x] Basic operators: `*`, `?`, `+` and `|`
- [x] Capturing groups
- [x] Symbols escaping
- [ ] Shorthands: `\w` and `\d`
- [ ] Sets `[...]`
- [ ] Char ranges
- [ ] Repetition ranges `{n, m}`
- [ ] ... ?

## Compatibility

* Python +3.5


## Install

```
$ pip install regexy
```


## Usage

Notice `regexy` returns all capturing groups specified within a repeated sub-expression

```python
import regexy

regexy.match(regexy.compile(r'((a)*b)'), 'aab')
# ('aab', ('a', 'a')

regexy.match(regexy.compile(r'a'), 'b')
# None

regexy.match(regexy.compile(r'a'), 'a')
# ()
```


# Docs

[Read The Docs](http://regexy.readthedocs.io)


## Tests

```
$ make test
```


## License

MIT
