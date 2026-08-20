"""Small bounded LRU cache (thread-unsafe, GUI-thread only).

Used for the in-memory image cache and the timeline thumbnail cache so a
session browsing many frames does not keep every decoded image around.
"""

from __future__ import annotations

from collections import OrderedDict
from typing import Generic, TypeVar

K = TypeVar("K")
V = TypeVar("V")


class LRUCache(Generic[K, V]):
    """Bounded dict evicting the least-recently-used key on insert."""

    def __init__(self, maxsize: int):
        self._maxsize = max(1, int(maxsize))
        self._data: OrderedDict[K, V] = OrderedDict()

    def get(self, key: K, default=None) -> V:
        if key not in self._data:
            return default
        self._data.move_to_end(key)
        return self._data[key]

    def __getitem__(self, key: K) -> V:
        self._data.move_to_end(key)
        return self._data[key]

    def __setitem__(self, key: K, value: V) -> None:
        self._data[key] = value
        self._data.move_to_end(key)
        if len(self._data) > self._maxsize:
            self._data.popitem(last=False)

    def __contains__(self, key: K) -> bool:
        return key in self._data

    def __len__(self) -> int:
        return len(self._data)

    def clear(self) -> None:
        self._data.clear()
