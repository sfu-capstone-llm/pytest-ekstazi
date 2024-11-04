import json
import sys
from dataclasses import asdict, dataclass
from hashlib import md5
from types import FrameType
from typing import Dict, List

import pytest


def pytest_addoption(parser):
    group = parser.getgroup("ekstazi")
    group.addoption(
        "--ekstazi",
        action="store_true",
        help='Turn on regression test selection when specified',
    )


@pytest.fixture
def bar(request):
    return request.config.option.dest_foo


@dataclass
class TestDependency:
    src: str
    hash: str


deps: Dict[str, List[TestDependency]] = {}
parent = ""


def handler(frame: FrameType, event: str, _):
    if event != "call":
        return

    global parent

    filename = frame.f_code.co_filename
    key = parent if parent != filename else filename

    dirs = filename.split("/")
    excluded_dir = {".tox", ".venv", ".local"}

    if not dirs[-1].endswith(".py"):
        return

    for dir in dirs:
        if dir in excluded_dir:
            return

    if key not in deps:
        deps[key] = []

    with open(filename, "r") as file:
        hash = md5(file.read().encode())
        hashstr = hash.hexdigest()
        deps[key].append(TestDependency(filename, hashstr))


def pytest_runtest_call(item: pytest.Item):
    global parent
    ekstazi = item.config.getoption("--ekstazi")
    parent = item.fspath.strpath
    sys.settrace(handler)


def pytest_runtest_teardown(item: pytest.Item):
    sys.settrace(None)


def pytest_sessionfinish(session, exitstatus):
    with open("deps.json", "w") as file:
        json_deps = {k: [asdict(dep) for dep in v] for k, v in deps.items()}
        json.dump(json_deps, fp=file, indent=4)
