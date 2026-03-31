from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, TypeVar

from part4_oop.interfaces import Cache, HasCache, Policy, Storage

K = TypeVar("K")
V = TypeVar("V")


@dataclass
class DictStorage(Storage[K, V]):
    _data: dict[K, V] = field(default_factory=dict, init=False)

    def set(self, key: K, value: V) -> None:
        self._data[key] = value

    def get(self, key: K) -> V | None:
        return self._data.get(key)

    def exists(self, key: K) -> bool:
        return key in self._data

    def remove(self, key: K) -> None:
        if self.exists(key):
            del self._data[key]

    def clear(self) -> None:
        self._data.clear()


@dataclass
class FIFOPolicy(Policy[K]):
    capacity: int = 5
    _order: list[K] = field(default_factory=list, init=False)

    def register_access(self, key: K) -> None:
        if key not in self._order:
            self._order.append(key)

    def get_key_to_evict(self) -> K | None:
        if len(self._order) > self.capacity:
            return self._order[0]
        return None

    def remove_key(self, key: K) -> None:
        if key in self._order:
            self._order.remove(key)

    def clear(self) -> None:
        self._order.clear()

    @property
    def has_keys(self) -> bool:
        return len(self._order) > 0


@dataclass
class LRUPolicy(Policy[K]):
    capacity: int = 5
    _order: list[K] = field(default_factory=list, init=False)

    def register_access(self, key: K) -> None:
        if key in self._order:
            self._order.remove(key)
        self._order.append(key)

    def get_key_to_evict(self) -> K | None:
        if len(self._order) > self.capacity:
            return self._order[0]
        return None

    def remove_key(self, key: K) -> None:
        if key in self._order:
            self._order.remove(key)

    def clear(self) -> None:
        self._order.clear()

    @property
    def has_keys(self) -> bool:
        return len(self._order) > 0


@dataclass
class LFUPolicy(Policy[K]):
    previos: K | None = None
    capacity: int = 5
    _key_counter: dict[K, int] = field(default_factory=dict, init=False)
    _key_entry: dict[K, int] = field(default_factory=dict, init=False)
    cache_time: int = 0

    def register_access(self, key: K) -> None:
        self._key_counter[key] = self._key_counter.get(key, 0) + 1
        self.cache_time += 1
        if key not in self._key_entry:
            self.cache_time += 1
            self._key_entry[key] = self.cache_time
            self.previos = key

    def get_key_to_evict(self) -> K | None:
        if len(self._key_counter) > self.capacity:
            return self._search_min_key()

        return None

    def remove_key(self, key: K) -> None:
        self._key_counter.pop(key, None)
        self.cache_time += 1

    def clear(self) -> None:
        self._key_counter.clear()
        self.cache_time = 0

    @property
    def has_keys(self) -> bool:
        return len(self._key_counter) > 0

    def _search_min_key(self) -> K | None:
        candidates = [key for key in self._key_counter if key != self.previos]
        if not candidates:
            return None

        return min(candidates,
                    key=lambda k: (self._key_counter[k], self._key_entry[k]))


class MIPTCache(Cache[K, V]):
    def __init__(self, storage: Storage[K, V], policy: Policy[K]) -> None:
        self.storage = storage
        self.policy = policy

    def set(self, key: K, value: V) -> None:
        self.storage.set(key, value)
        self.policy.register_access(key)

        evict_key = self.policy.get_key_to_evict()
        if evict_key is not None:
            self.storage.remove(evict_key)
            self.policy.remove_key(evict_key)

    def get(self, key: K) -> V | None:
        value = self.storage.get(key)
        if value is not None:
            self.policy.register_access(key)
        return value

    def exists(self, key: K) -> bool:
        return self.storage.exists(key)

    def remove(self, key: K) -> None:
        self.storage.remove(key)
        self.policy.remove_key(key)

    def clear(self) -> None:
        self.storage.clear()
        self.policy.clear()


class CachedProperty[V]:
    def __init__(self, func: Callable[..., V]) -> None:
        self.func = func
        self.attr_name = func.__name__

    def __get__(self, instance: HasCache[Any, Any] | None, owner: type) -> V:
        if instance is None:
            return self  # type: ignore[return-value]

        result = instance.cache.get(self.attr_name)

        if result is None:
            result = self.func(instance)
            instance.cache.set(self.attr_name, result)

        return result
