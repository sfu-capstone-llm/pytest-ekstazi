import json
import pickle
import sys
from dataclasses import asdict, dataclass
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


deps: Dict[str, List[TestDependency]] = {}


def handler(frame: FrameType, event: str, _):
    if event == "call":
        filename = frame.f_code.co_filename

        dirs = filename.split("/")
        excluded_dir = {".tox", ".venv", ".local"}

        if not dirs[-1].endswith(".py"):
            return

        for dir in dirs:
            if dir in excluded_dir:
                return

        if filename not in deps:
            deps[filename] = []

        # with open("test.txt", "a") as file:
        #     file.write(f"src: {filename}\n")

        # assert filename == False

        with open(filename, "r") as file:
            hash = md5(file.read().encode())
            hashstr = hash.hexdigest()
            deps[filename].append(TestDependency(filename, hashstr))

        # with open("test.txt", "a") as file:
        #     file.write(f"src: {filename} hash: {hashstr}\n"

        out_file = open("test.txt", "w")
        json.dump(deps, out_file)


def pytest_runtest_call(item: pytest.Item):
    sys.settrace(handler)


def pytest_runtest_teardown(item: pytest.Item):
    sys.settrace(None)


def pytest_sessionfinish(session, exitstatus):
    with open("deps.pkl", "wb") as file:
        json_deps = {
            k: [asdict(dep) for dep in v] for k, v in deps.items()
        }  # Convert to dict
        # json.dump(json_deps, json_file, indent=4)
        pickle.dump(json_deps, file)
