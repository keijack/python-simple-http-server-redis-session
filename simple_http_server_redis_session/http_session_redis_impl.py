# -*- coding: utf-8 -*-

"""
Copyright (c) 2021 Keijack Wu

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""


import json
import uuid
import time
import redis
import pickle

from typing import Any, Tuple, Union
from simple_http_server import Session, SessionFactory, DEFAULT_ENCODING
from simple_http_server.logger import get_logger


_logger = get_logger("redis_http_session")


class ObjectSerializer:

    def object_to_bytes(self, obj: Any) -> bytes:
        return pickle.dumps(obj)

    def bytes_to_objects(self, value: bytes) -> Any:
        return pickle.loads(value)


def _get_redis_client(host="localhost", port=6379, db=0, username="", password="") -> redis.Redis:
    return redis.Redis(host=host, port=port, db=db, username=username, password=password)


def _get_session_hash_name(session_id: str) -> str:
    return f"__py_si_ht_se_{session_id}".encode(DEFAULT_ENCODING)


def _to_byte(val: Union[bytes, str]) -> bytes:
    if isinstance(val, bytes):
        return val
    elif isinstance(val, str):
        return val.encode(DEFAULT_ENCODING)
    else:
        return f"{val}".encode(DEFAULT_ENCODING)


class RedisSessionImpl(Session):

    def __init__(self, id: str, obj_serializer: ObjectSerializer, redis: redis.Redis):
        super().__init__()
        self.__id = id if id else uuid.uuid4().hex
        self.__redis_hash_name = _get_session_hash_name(self.__id)
        self.__obj_ser: ObjectSerializer = obj_serializer

        self.__clz_creation_time = time.time()
        self.__is_new = False

        self.__redis = redis
        self.__sync_redis()
        self.__set_expire()

    def __sync_redis(self) -> bool:
        if not self.__redis.exists(self.__redis_hash_name):
            self.__set_("creation_time", self.__clz_creation_time)
            self.__is_new = True

        self.__set_("last_accessed_time", self.__clz_creation_time)

    def __set_(self, key: str, val: Any):
        self.__redis.hset(self.__redis_hash_name, _to_byte(key), _to_byte(val))

    def __get_(self, key: str) -> bytes:
        return self.__redis.hget(self.__redis_hash_name, _to_byte(key))

    def __exists(self, key: str) -> bool:
        return self.__redis.hexists(self.__redis_hash_name, _to_byte(key))

    def __set_expire(self):
        self.__redis.expire(self.__redis_hash_name, self.max_inactive_interval)

    @property
    def id(self) -> str:
        return self.__id

    @property
    def creation_time(self) -> float:
        try:
            return float(self.__get_("creation_time"))
        except:
            return self.__clz_creation_time

    @property
    def last_accessed_time(self) -> float:
        try:
            return float(self.__get_("last_accessed_time"))
        except:
            return self.__clz_creation_time

    @property
    def is_new(self) -> bool:
        return self.__is_new

    @property
    def is_valid(self) -> bool:
        return self.__redis.exists(self.__redis_hash_name)

    @property
    def attribute_names(self) -> Tuple:
        keys = self.__redis.hkeys(self.__redis_hash_name)
        pre = "val_"
        return tuple([k.decode(DEFAULT_ENCODING)[len(pre):] for k in keys if k.decode(DEFAULT_ENCODING).startswith(pre)])

    def get_attribute(self, name: str) -> Any:
        val_key = f"val_{name}"
        if not self.__exists(val_key):
            return None
        val = self.__get_(val_key)
        _logger.debug(f"Get attribute {name} -> bytes -> {val}")
        return self.__obj_ser.bytes_to_objects(val)

    def set_attribute(self, name: str, value: Any) -> None:
        self.__set_(f"val_{name}", self.__obj_ser.object_to_bytes(value))

    def invalidate(self) -> None:
        self.__redis.delete(self.__redis_hash_name)


class RedisSessionFactory(SessionFactory):

    def __init__(self, host="localhost", port=6379, db=0, username="", password="", redis_client: redis.Redis = None, object_serializer: ObjectSerializer = None):
        self.__obj_ser = object_serializer or ObjectSerializer()
        self.__redis = redis_client or _get_redis_client(host=host, port=port, db=db, username=username, password=password)

    def get_session(self, session_id: str, create: bool = False) -> Session:
        hash_name = _get_session_hash_name(session_id)
        if not self.__redis.exists(hash_name) and not create:
            return None
        else:
            return RedisSessionImpl(session_id, self.__obj_ser, self.__redis)
