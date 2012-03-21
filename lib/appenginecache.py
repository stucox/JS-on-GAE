# Custom cache backend uses AppEngine's memcached

# todo: investigate `compare and set` and loadtest appropriately, see:
# http://code.google.com/appengine/docs/python/memcache/overview.html

from django.core.cache.backends.base import BaseCache, InvalidCacheBackendError
from django.utils.encoding import smart_str
from google.appengine.api import memcache


class CacheClass(BaseCache):

    def __init__(self, server, params):
        super(CacheClass, self).__init__(params)


    def add(self, key, value, timeout=0):
        if isinstance(value, unicode):
            value = value.encode('utf-8')
        return memcache.add(key=smart_str(key), value=value, time=timeout)



    def get(self, key, default=None):
        val = memcache.get(key=smart_str(key))
        if val is None:
            return default
        return val


    def set(self, key, value, timeout=0):
        memcache.set(key=smart_str(key), value=value, time=timeout)



    def delete(self, key):
        memcache.delete(key=smart_str(key))


    def get_many(self, keys):
        return memcache.get_multi(keys=map(smart_str, keys))



    def set_many(self, data, timeout=0):
        safe_data = {}
        for key, value in data.items():
            if isinstance(value, unicode):
                value = value.encode('utf-8')
            safe_data[smart_str(key)] = value
        memcache.set_multi(mapping=safe_data, time=timeout)


    def delete_many(self, keys):
        memcache.delete_multi(keys=map(smart_str, keys))


    def clear(self):
        memcache.flush_all()

