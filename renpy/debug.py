
# This file contains debugging code that isn't enabled in normal Ren'Py
# operation.

from __future__ import division, absolute_import, with_statement, print_function, unicode_literals
from renpy.compat import *

import renpy
import threading
import datetime
import traceback
import os
import builtins
import io

if PY2:
    real_open = io.open
else:
    real_open = builtins.open

report = True


def replacement_open(*args, **kwargs):

    global report

    rv = real_open(*args, **kwargs)

    if not renpy.game.contexts:
        return rv

    if renpy.game.context().init_phase:
        return rv

    if threading.current_thread().name != "MainThread":
        return rv

    if not report:
        return rv

    if os.environ["RENPY_DEBUG_MAIN_THREAD_OPEN"] == "stack":
        report = False
        print()
        traceback.print_stack()
        report = True

    print(datetime.datetime.now().strftime("%H:%M:%S"), "In main thread: open" + repr(args))
    return rv


def init_main_thread_open():
    if not "RENPY_DEBUG_MAIN_THREAD_OPEN" in os.environ:
        return

    builtins.open = replacement_open
