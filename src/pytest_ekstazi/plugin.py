import pickle
from dataclasses import dataclass
from hashlib import md5
from types import FrameType
from typing import Dict, List

import pytest


def pytest_addoption(parser):
    group = parser.getgroup("ekstazi")
    group.addoption(
        "--foo",
        action="store",
        dest="dest_foo",
        default="2024",
        help='Set the value for the fixture "bar".',
    )

    parser.addini("HELLO", "Dummy pytest.ini setting")


@pytest.fixture
def bar(request):
    return request.config.option.dest_foo


@dataclass
class TestDependency:
    src: str
    hash: str


deps: Dict[str, List[TestDependency]] = {"test": [TestDependency("a", "b")]}


def handler(frame: FrameType, event: str, _):
    if event == "call":
        filename = frame.f_code.co_filename

        if filename not in deps[filename]:
            deps[filename] = []

        with open(filename) as file:
            hash = md5(file.read().encode())
            hashstr = hash.digest().decode()
            deps[filename].append(TestDependency(filename, hashstr))


def pytest_runtest_setup(item: pytest.Item):
    print(f"\n[plugin] Setting up before test: {item.name}")


def pytest_runtest_teardown(item: pytest.Item):
    print(f"\n[plugin] Tearing down after test: {item.name}")


def pytest_sessionfinish(session, exitstatus):
    with open("deps.pkl", "wb") as file:
        pickle.dump(deps, file)
