# -*- coding: utf-8 -*-
import setuptools
from simple_http_server_redis_session import version

with open("README.md", "r") as fh:
    long_description = fh.read()


setuptools.setup(
    name="simple_http_server_redis_session",
    version=version,
    author="Keijack",
    author_email="keijack.wu@gmail.com",
    description="A redis session implementation for python-simple-http-server",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/keijack/python-simple-http-server-redis-session",
    packages=["simple_http_server_redis_session"],
    install_requires=[
        "simple-http-server",
        "redis"
    ],
    classifiers=[
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
