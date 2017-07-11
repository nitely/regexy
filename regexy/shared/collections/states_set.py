# -*- coding: utf-8 -*-


__all__ = ['StatesSet']


class StatesSet:

    STATE, CAPTURED = range(2)

    def __init__(self):
        self._list = []
        self._set = set()

    def __len__(self):
        return len(self._list)

    def __bool__(self):
        return bool(self._list)

    def __iter__(self):
        yield from self._list

    def __contains__(self, item):
        return item in self._set

    def extend(self, items):
        items = tuple(
            item
            for item in items
            if item[self.STATE] not in self._set)
        self._list.extend(items)
        self._set.update(
            item[self.STATE]
            for item in items)

    def clear(self):
        self._list.clear()
        self._set.clear()
