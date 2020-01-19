import functools
import socket

import bddrest
import pytest

from yhttp import Application


@pytest.fixture
def app():
    return Application()


@pytest.fixture
def story():
    def given_(app, *a, **kw):
        return bddrest.Given(app, None, *a, **kw)

    return given_


@pytest.fixture
def when():
    return functools.partial(bddrest.when, None)


@pytest.fixture
def freetcpport():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.bind((socket.gethostname(), 0))
        return s.getsockname()[1]
    finally:
        s.close()

