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

## 编写你自己的序列化逻辑

默认情况下，我们会使用 `pickle` 来序列化和反序列化类，如果上述的序列化逻辑无法满足你的需求，你可以编写自己的序列化逻辑。

```python
simple_http_server_redis_session.http_session_redis_impl import ObjectSerializer

class MyObjectSerializer(ObjectSerializer):

    def object_to_bytes(self, obj: Any) -> bytes:
        bys = ...
        return bys

    def bytes_to_objects(self, value: bytes) -> Any:
        obj = ...
        return obj
```

