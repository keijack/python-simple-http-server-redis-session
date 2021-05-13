# Redis Sesion Implementation for Python Simple Http Server

## What's this?

This is the redis session implementation for the project https://github.com/keijack/python-simple-http-server, use this extention to save you session data to redis.

## How to use?

```python
import simple_http_server
import simple_http_server.server as server
import os
from simple_http_server_redis_session.http_session_redis_impl import RedisSessionFactory

def main(*args):
    # host, port, db, username, password are all optional.
    simple_http_server.set_session_factory(RedisSessionFactory(host="10.0.2.16", port=6379, db=0, username="", password=""))
    server.scan("tests/ctrls", r'.*controllers.*')
    
    root = os.path.dirname(os.path.abspath(__file__))
    server.start(
        port=9090,
        resources={"/public/*": f"{root}/tests/static"})

```

## The Data Structure Saved to Redis

This module try to covert all the objects to json and save it to redis. However, it's quite hard to decide which properties should be saved or which should not. 

And after a consideration, I decided that only the properties which are `public` which without `_` prefix should be saved. 

```python

class MyData:

    # will be saved
    clz_a = "x"
    # won't be saved
    _clz_a = "y"

    def __init__(self):
        # will be saved
        self.a = "a"
        # won't be saved
        self._x = "x"
        # won't be saved
        self.__y = "y"

    # will be saved, but cannot be loaded back for there is no setter
    @property
    def x(self):
        return self._x

    # will be saved
    @property
    def y(self):
        return self.__y

    @y.setter
    def y(self, val):
        self.__y = val
```
...
## Write Your Own ObjectSerializer

If the defalut serialization logic could not satisfy you, you can write your own

```python
simple_http_server_redis_session.http_session_redis_impl import ObjectSerializer, ObjectDataWrapper

class MyObjectSerializer(ObjectSerializer):

    def object_to_bytes(self, obj: ObjectDataWrapper) -> bytes:
        bys = ...
        return bys

    def bytes_to_objects(self, value: bytes, module: str, clz: str) -> ObjectDataWrapper:
        """
        " value: the bytes stream comes from `object_to_bytes` method
        " module: the module of ObjectDataWrapper.data 
        " clz: the class of ObjectDataWrapper.data 
        """
        data = ...
        return ObjectDataWrapper(data)
```

