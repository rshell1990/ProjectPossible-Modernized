
import enum
from typing import Any

type NodeState = Any
type NodeLocation = tuple[str, int]
type Position = tuple[int | float, int | float]


class RenpyTestException(RuntimeError):
    pass


class RenpyTestAssertionError(AssertionError):
    pass


class RenpyTestScreenshotError(RenpyTestException):
    pass


class RenpyTestTimeoutError(TimeoutError):
    pass


class HookType(enum.Enum):
    SETUP = "setup"
    BEFORE_TESTSUITE = "before_testsuite"
    BEFORE_TESTCASE = "before_testcase"
    AFTER_TESTCASE = "after_testcase"
    AFTER_TESTSUITE = "after_testsuite"
    TEARDOWN = "teardown"
