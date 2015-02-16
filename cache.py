#!/usr/bin/env python
# -*- coding: utf-8 -*-

import exceptions

class BaseCacheModule(object):
    def get(self, key):
        raise exceptions.NotImplementedError

    def set(self, key, value):
        raise exceptions.NotImplementedError

    def keys(self):
        raise exceptions.NotImplementedError

    def contains(self, key):
        raise exceptions.NotImplementedError

    def delete(self, key):
        raise exceptions.NotImplementedError

    def flush(self):
        raise exceptions.NotImplementedError

    def copy(self):
        raise exceptions.NotImplementedError


class CacheModule(BaseCacheModule):
    def __init__(self, *args, **kwargs):
        self._cache = {}

    def get(self, key):
        return self._cache.get(key)

    def set(self, key, value):
        self._cache[key] = value

    def keys(self):
        return self._cache.keys()

    def contains(self, key):
        return key in self._cache

    def delete(self, key):
        del self._cache[key]

    def flush(self):
        self._cache = {}

    def copy(self):
        return self._cache.copy()
