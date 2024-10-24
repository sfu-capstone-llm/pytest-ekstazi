
from multiple_files.a import func_a
from pytest import Pytester

def test_foo():
    func_a()
    print("WOO")


def test_bar_fixture(pytester: Pytester):
    """Make sure that pytest accepts our fixture."""

    # create a temporary pytest test module
    pytester.makepyfile(
        """
        def test_sth(bar):
            assert bar == "europython2015"
    """
    )

    # run pytest with the following cmd args
    result = pytester.runpytest("--foo=europython2015", "-v")

    # fnmatch_lines does an assertion internally
    result.stdout.fnmatch_lines(
        [
            "*::test_sth PASSED*",
        ]
    )

    # make sure that we get a '0' exit code for the testsuite
    assert result.ret == 0


def test_help_message(pytester: Pytester):
    result = pytester.runpytest(
        "--help",
    )
    # fnmatch_lines does an assertion internally
    result.stdout.fnmatch_lines(
        [
            "ekstazi:",
            '*--foo=DEST_FOO*Set the value for the fixture "bar".',
        ]
    )


def test_hello_ini_setting(pytester: Pytester):
    pytester.makeini(
        """
        [pytest]
        HELLO = world
    """
    )

    pytester.makepyfile(
        """
        import pytest

        @pytest.fixture
        def hello(request):
            return request.config.getini('HELLO')

        def test_hello_world(hello):
            assert hello == 'world'
    """
    )

    result = pytester.runpytest("-v")

    # fnmatch_lines does an assertion internally
    result.stdout.fnmatch_lines(
        [
            "*::test_hello_world PASSED*",
        ]
    )

    # make sure that we get a '0' exit code for the testsuite
    assert result.ret == 0
