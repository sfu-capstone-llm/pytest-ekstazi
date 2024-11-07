import json
import sys
from dataclasses import asdict, dataclass
from hashlib import md5
from types import FrameType
from typing import Dict, List
import collections
import logging
logger = logging.getLogger(__name__)

import pytest


def pytest_addoption(parser):
    group = parser.getgroup("runAll")
    group.addoption(
        "--runAll",
        action="store_true",
        help='Turn on run all test selection when specified. Does not run regression test',
    )
    group = parser.getgroup("noUpdate")
    group.addoption(
        "--noUpdate",
        action="store_true",
        help='Does not update deps.json file',
    )

@pytest.fixture
def bar(request):
    return request.config.option.dest_foo


@dataclass
class TestDependency:
    src: str
    hash: str
    
deps: Dict[str, List[TestDependency]] = collections.defaultdict(list)
try:
    with open("deps.json", "r") as file:
        json_deps = json.load(file)
except FileNotFoundError:
    print("Error: 'deps.json' file not found.")
    json_deps = {}
    for key, value in json_deps.items():
        for dep in value:
            deps[key].append(TestDependency(dep.src, dep.hash))

parent = ""

def should_run_file(filename: str) -> bool:
    dirs = filename.split("/")
    excluded_dirs = {".tox", ".venv", ".local"}

    if not dirs[-1].endswith(".py"):
        return False

    if any(dir in excluded_dirs for dir in dirs):
        return False
    
    return True


def trace_handler(frame: FrameType, event: str, _):
    if event != "call":
        return

    filename = frame.f_code.co_filename
    if not should_run_file(filename):
        return

    global parent
    key = parent if parent != filename else filename

    with open(filename, "r") as file:
        hash = md5(file.read().encode())
        hashstr = hash.hexdigest()
        # if key in deps and deps[key].src == filename and deps[key].hash == hashstr:
        #     return
        deps[key].append(TestDependency(filename, hashstr))


def test_deps_changed(deps: List[TestDependency]):
    for dep in deps:
        print("opening dep.src", dep.src)
        with open(dep.src, "r") as file:
            new_hash = md5(file.read().encode()).hexdigest()
            if new_hash != dep.hash:
                return True
    
    return False


def pytest_runtest_call(item: pytest.Item):
    global parent, deps
    isRunAll = item.config.getoption("--runAll")
    if isRunAll:
        return

    parent = item.fspath.strpath

    # try:
    #     with open("deps.json", "r") as file:
    #         json_deps = json.load(file)
    # except FileNotFoundError:
    #     print("Error: 'deps.json' file not found.")
    #     json_deps = {}
    #     
    # for key, value in json_deps.items():
    #     for dep in value:
    #         deps[key].append(TestDependency(dep.src, dep.hash))

    if parent in json_deps:
        if not test_deps_changed(deps[parent]):
            pytest.skip()
        else:
            deps[parent].clear()
    
    logger.info(f"Running with isRunAll: {isRunAll}")
    sys.settrace(trace_handler)


def pytest_runtest_teardown(item: pytest.Item):
    sys.settrace(None)


def pytest_sessionfinish(session, exitstatus):
    isRunAll = session.config.getoption("--runAll")
    if isRunAll:
       return 
    
    with open("deps.json", "w") as file:
        json_deps = {k: [asdict(dep) for dep in v] for k, v in deps.items()}
        json.dump(json_deps, fp=file, indent=4)
