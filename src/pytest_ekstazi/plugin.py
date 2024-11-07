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
    
json_deps = {}
deps: Dict[str, List[TestDependency]] = collections.defaultdict(list)
newDeps: Dict[str, List[TestDependency]] = collections.defaultdict(list)
parent = ""

def should_run_file(filename: str) -> bool:
    dirs = filename.split("/")
    excluded_dirs = {".tox", ".venv", ".local"}

    if not dirs[-1].endswith(".py"):
        return False

    if any(dir in excluded_dirs for dir in dirs):
        return False
    
    return True


def run_all_handler(frame: FrameType, event: str, _):
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
        deps[key].append(TestDependency(filename, hashstr))

def rerun_handler(frame: FrameType, event: str, _):
    if event != "call":
        return

    filename = frame.f_code.co_filename
    if not should_run_file(filename):
        return

    global parent, json_deps
    key = parent if parent != filename else filename
        
    for key, value in json_deps.items():
        for src, hash in enumerate(value):
            deps[key].append(TestDependency(src, hash))
            
    with open(filename, "r") as file:
        hash = md5(file.read().encode())
        hashstr = hash.hexdigest()
        for key in json_deps:
            for dep in json_deps[key]:
                if dep['src'] == filename and dep['hash'] == hashstr:
                    return
        newDeps[key].append(TestDependency(filename, hashstr))

def pytest_runtest_call(item: pytest.Item):
    global parent, json_deps
    isRunAll = item.config.getoption("--runAll")
    if not isRunAll:
        with open("deps.json", "r") as file:
            json_deps = json.load(file)
            print("JSON DEPS", json_deps)
    
    logger.info(f"Running with isRunAll: {isRunAll}")
    parent = item.fspath.strpath
    trace_handler = run_all_handler if isRunAll else rerun_handler
    sys.settrace(trace_handler)


def pytest_runtest_teardown(item: pytest.Item):
    sys.settrace(None)


def pytest_sessionfinish(session, exitstatus):
    isRunAll = session.config.getoption("--runAll")
    if not isRunAll:
        print("NEW DEPS", newDeps)
    
    notUpdate = session.config.getoption("--noUpdate")
    if notUpdate:
        return
    with open("deps.json", "w") as file:
        json_deps = {k: [asdict(dep) for dep in v] for k, v in deps.items()}
        json.dump(json_deps, fp=file, indent=4)
