import json
import sys
from dataclasses import asdict, dataclass
from hashlib import md5
from types import FrameType
from typing import Dict, List
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


deps: Dict[str, List[TestDependency]] = {}
parent = ""


def run_all_handler(frame: FrameType, event: str, _):
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

def rerun_handler(frame: FrameType, event: str, _):
    if event != "call":
        return
    # check all the hashes
    with open("deps.json", "r") as file:
        json_deps = json.load(file)
    
    print(json_deps)
    # if any of the hashes are different, rerun the test
    # if all the hashes are the same, don't rerun the test
    # if the file is not in the deps, rerun the test
    # if the file is in the deps, but the hash is different, rerun the test
    # if the file is in the deps, and the hash is the same, don't rerun the test
    # if the file is in the deps, but the file is not found, rerun the test
    

def pytest_runtest_call(item: pytest.Item):
    global parent
    isRunAll = item.config.getoption("--runAll")
    logger.info(f"Running with runAll: {isRunAll}")
    parent = item.fspath.strpath
    trace_handler = run_all_handler if isRunAll else rerun_handler
    sys.settrace(trace_handler)


def pytest_runtest_teardown(item: pytest.Item):
    sys.settrace(None)


def pytest_sessionfinish(session, exitstatus):
    notUpdate = session.config.getoption("--noUpdate")
    if notUpdate:
        return
    with open("deps.json", "w") as file:
        json_deps = {k: [asdict(dep) for dep in v] for k, v in deps.items()}
        json.dump(json_deps, fp=file, indent=4)
