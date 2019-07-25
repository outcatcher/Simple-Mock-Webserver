"""Pytest entry point"""
import random
import string
import time
from threading import Thread

import pytest
import requests
from ocomone.session import BaseUrlSession
from wsgiserver import WSGIServer

from too_simple_server.api import SERVER
from too_simple_server.configuration import EntityStruct, write_configuration, load_configuration
from too_simple_server.database import Entity, create_entity, init_db


def _rand_str():
    return "".join(random.choice(string.ascii_letters) for _ in range(10))


@pytest.fixture
def random_data():
    return _rand_str()


def delete_entity(uuid):
    Entity.delete().where(Entity.uuid == uuid)


@pytest.fixture
def entity(random_data):
    uuid = create_entity(EntityStruct(random_data))
    yield uuid
    delete_entity(uuid)


@pytest.fixture(scope="session")
def session() -> BaseUrlSession:
    port = load_configuration().server_port
    init_db()
    Thread(target=WSGIServer(SERVER, port=port).start, daemon=True).start()
    session = BaseUrlSession(f"http://localhost:{port}")
    end_time = time.monotonic() + 10

    def _not_up():
        """Returns True if server is down"""
        try:
            return session.get("").status_code != 200
        except requests.ConnectionError:
            return True

    while _not_up():  # wait until server is up and running
        time.sleep(0.1)
        if time.monotonic() > end_time:
            raise RuntimeError
    yield session
    session.close()
