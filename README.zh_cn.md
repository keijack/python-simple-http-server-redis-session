# Python Simple Http Server 的 Redis Session 实现

## 这是什么？

这是工程 https://gitee.com/keijack/python-simple-http-server 的分布式 session 的 redis 实现。

## 如何使用?

安装本工程之后，参考以下代码配置

```python
import simple_http_server
import simple_http_server.server as server
import os
from simple_http_server_redis_session.http_session_redis_impl import RedisSessionFactory

def main(*args):
    # host, port, db, username, password 均为可选。
    simple_http_server.set_session_factory(RedisSessionFactory(host="10.0.2.16", port=6379, db=0, username="", password=""))
    server.scan("tests/ctrls", r'.*controllers.*')
    
    root = os.path.dirname(os.path.abspath(__file__))
    server.start(
        port=9090,
        resources={"/public/*": f"{root}/tests/static"})

```

## 哪些内容会保存到 redis

本模块尝试将所有的类转换成 json 然后保存到 redis，取得的时候再从 redis 取出，保存到 redis 中的内容仅保存`公共`即无`_`开头的字段。参考以下例子：

```python

class MyData:

    # 会被保存
    clz_a = "x"
    # 不会被保存
    _clz_a = "y"

    def __init__(self):
        # 会被保存
        self.a = "a"
        # 不会被保存
        self._x = "x"
        # 不会被保存
        self.__y = "y"

    # 会被保存, 但由于无 setter，所以取得的时候不会加载。
    @property
    def x(self):
        return self._x

    # 会被保存
    @property
    def y(self):
        return self.__y

    @y.setter
    def y(self, val):
        self.__y = val
```

## 编写你自己的序列化逻辑

如果上述的序列化逻辑无法满足你的需求，你可以编写自己的序列化逻辑。

```python
simple_http_server_redis_session.http_session_redis_impl import ObjectSerializer, ObjectDataWrapper

class MyObjectSerializer(ObjectSerializer):

    def object_to_bytes(self, obj: ObjectDataWrapper) -> bytes:
        bys = ...
        return bys

    def bytes_to_objects(self, value: bytes, module: str, clz: str) -> ObjectDataWrapper:
        """
        " value: `object_to_bytes` 方法转成的字节流
        " module: ObjectDataWrapper.data 的模块
        " clz: ObjectDataWrapper.data 的类名
        """
        data = ...
        return ObjectDataWrapper(data)
```

