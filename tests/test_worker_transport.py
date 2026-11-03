"""Catch installed Celery/Redis incompatibilities before a worker is deployed."""

from types import SimpleNamespace

import redis
from kombu.transport.redis import Channel


def test_worker_transport_can_construct_its_redis_client_without_connecting():
    client_type = Channel._get_client(SimpleNamespace(global_keyprefix=""))
    client = client_type(host="127.0.0.1", port=1, db=0)
    assert isinstance(client, redis.Redis)
    assert client.connection_pool.connection_kwargs["port"] == 1
    client.close()
