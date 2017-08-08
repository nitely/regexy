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
- [x] Shorthands: `\w`, `\d`, `\s`, `\W`, `\D`, `\S`
- [x] Sets `[...]` (+ ranges and shorthands)
- [x] Repetition ranges `{n, m}`
- [x] non-capturing groups
- [x] Greedy and non-greedy match
- [x] `^` and `$` symbols
- [x] `\b` word boundary
- [x] Match any (dot)
- [x] Sets complement
- [x] Lookahead assertion `(?=...)` and `(?!...)` (limited to a single char)
- [x] Assertions `\A`, `\z`, `\B`
- [x] Named capturing groups
- [x] `search`
- [x] `full_match`
- [ ] Flags
- [ ] User friendly compiling errors
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
# Match<('aab', ('a', 'a'))>

regexy.match(regexy.compile(r'a'), 'b')
# None

regexy.match(regexy.compile(r'a'), 'a')
# Match<()>
```

Streams are supported (i.e: network and files)

> Note: Capturing may take as much RAM as all of
> the data in worst case when the full regex is captured

```python
import io
import regexy


def stream_gen():
    stream = io.BytesIO(b'Im a stream')
    stream_wrapper = io.TextIOWrapper(stream, encoding='utf-8', write_through=True)

    while True:
        chars = stream_wrapper.read(5)

        if not chars:
            break

        yield from chars

regexy.match(regexy.compile(r'(\w+| +)*'), stream_gen())
# (('Im', ' ', 'a', ' ', 'stream'),)
```

Here is a (undocumented) way to print the generated
NFA for debugging purposes:

```python
import regexy

str(regexy.compile(r'a*').state)
# ('*', [('a', [('*', [...])]), ('EOF', [])])
# The [...] thing means it's recursive
```


# Docs

[Read The Docs](http://regexy.readthedocs.io)


## Tests

```
$ make test
```


## License

MIT
