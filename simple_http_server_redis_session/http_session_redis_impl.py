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
import importlib
import time
import redis

import simple_http_server.bean_utils as bean_utils
from typing import Any, Tuple
from simple_http_server import Session, SessionFactory, DEFAULT_ENCODING
from simple_http_server.logger import get_logger


_logger = get_logger("redis_http_session")


class ObjectDataWrapper:

    def __init__(self, data: Any = None) -> None:
        self.data = data


class ObjectSerializer:

    def object_to_bytes(self, obj: ObjectDataWrapper) -> bytes:
        return bean_utils.bean_to_json(obj).encode(DEFAULT_ENCODING)

    def bytes_to_objects(self, value: bytes, module: str, clz: str) -> ObjectDataWrapper:
        mo = importlib.import_module(module)
        clz = getattr(mo, clz)
        obj_pro = bean_utils.ObjectProperties(ObjectDataWrapper(bean_utils.new_instance(clz)))
        val = value.decode(DEFAULT_ENCODING)
        json_val = json.loads(val)
        return obj_pro.fill(json_val)


def _get_redis_client(host="localhost", port=6379, db=0, username="", password="") -> redis.Redis:
    return redis.Redis(host=host, port=port, db=db, username=username, password=password)


def _get_session_hash_name(session_id: str) -> bytes:
    return f"__py_si_ht_se_{session_id}".encode(DEFAULT_ENCODING)


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
        v = val if isinstance(val, bytes) else str(val).encode(DEFAULT_ENCODING)
        self.__redis.hset(self.__redis_hash_name, key.encode(DEFAULT_ENCODING), v)

    def __get_(self, key: str) -> bytes:
        return self.__redis.hget(self.__redis_hash_name, key)

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
        return tuple([k[len(pre):].decode(DEFAULT_ENCODING) for k in keys if k.decode(DEFAULT_ENCODING).startswith(pre)])

    def get_attribute(self, name: str) -> Any:
        val_key = f"val_{name}"
        if not self.__redis.hexists(self.__redis_hash_name, val_key):
            return None
        val = self.__get_(val_key)
        mod = self.__get_(f"mod_{name}").decode(DEFAULT_ENCODING)
        clz = self.__get_(f"clz_{name}").decode(DEFAULT_ENCODING)
        _logger.debug(f"get from sever {name}:{mod}.{clz}:{val} to session: {self.__redis_hash_name}")
        obj_warpper = self.__obj_ser.bytes_to_objects(val, mod, clz)
        return obj_warpper.data

    def set_attribute(self, name: str, value: Any) -> None:
        val = self.__obj_ser.object_to_bytes(ObjectDataWrapper(value))
        val_type: type = type(value)
        _logger.debug(f"save {name}:{val_type}:{value} to session: {self.__redis_hash_name}")
        self.__set_(f"mod_{name}", val_type.__module__)
        self.__set_(f"clz_{name}", val_type.__name__)
        self.__set_(f"val_{name}", val)

    def invalidate(self) -> None:
        self.__redis.delete(self.__redis_hash_name)


class RedisSessionFactory(SessionFactory):

    def __init__(self, host="localhost", port=6379, db=0, username="", password="", obj_serializer: ObjectSerializer = ObjectSerializer()):
        self.__obj_ser: ObjectSerializer = obj_serializer
        self.__redis = _get_redis_client(host=host, port=port, db=db, username=username, password=password)

    def get_session(self, session_id: str, create: bool = False) -> Session:
        hash_name = _get_session_hash_name(session_id)
        if not self.__redis.exists(hash_name) and not create:
            return None
        else:
            return RedisSessionImpl(session_id, self.__obj_ser, self.__redis)
