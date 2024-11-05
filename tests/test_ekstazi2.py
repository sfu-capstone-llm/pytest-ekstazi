from multiple_files.main import main
from pytest import Pytester


def test_foo():
    main()
    print("WOO")
