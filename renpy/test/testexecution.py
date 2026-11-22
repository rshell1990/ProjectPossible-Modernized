
from __future__ import division, absolute_import, with_statement, print_function, unicode_literals
from renpy.compat import *

from typing import Any

import renpy.display
import renpy.display.behavior
import renpy.display.core
import renpy.exports
import renpy.arguments
import renpy.test
import renpy.test.testast
import renpy.test.testmouse
import pygame_sdl2 # type: ignore[import-not-found]

# A map from the name of a testcase to the testcase.
testcases = { }

# The root node.
node = None

# The location of the currently execution TL node.
node_loc = None

# The state of the root node.
state = None

# The previous state and location in the game script.
old_state = None
old_loc = None

# The last time the state changed.
last_state_change = 0

# The time the root node started executing.
start_time = None

# An action to run before executing another command.
action = None

# The set of labels that have been reached since the last time execute
# has been called.
labels = set()


def take_name(name):
    """
    Takes the name of a statement that is about to run.
    """

    if node is None:
        return

    if isinstance(name, basestring):
        labels.add(name)


class TestJump(Exception):
    """
    An exception that is raised in order to jump to `node`.
    """

    def __init__(self, node):
        self.node = node


def lookup(name, from_node):
    """
    Tries to look up the name with `target`. If found, returns it, otherwise
    raises an exception.
    """

    if name in testcases:
        return testcases[name]

    raise Exception("Testcase {} not found at {}:{}.".format(name, from_node.filename, from_node.linenumber))


def execute_node(now, node, state, start):
    """
    Performs one execution cycle of a node.
    """

    while True:

        try:
            if state is None:
                state = node.start()
                start = now

            if state is None:
                break

            state = node.execute(state, now - start)

            break

        except TestJump as e:
            node = e.node
            state = None

    if state is None:
        node = None

    return node, state, start


def execute():
    """
    Called periodically by the test code to generate events, if desired.
    """

    global node
    global state
    global start_time
    global action
    global old_state
    global old_loc
    global last_state_change

    _test = renpy.test.testast._test

    if node is None:
        return

    interface = renpy.display.interface # type: Any
    if interface.suppress_underlay and (not _test.force):
        return

    if _test.maximum_framerate:
        renpy.exports.maximum_framerate(10.0)
    else:
        renpy.exports.maximum_framerate(None)

    # Make sure there are no test events in the event queue.
    for e in pygame_sdl2.event.copy_event_queue():  # @UndefinedVariable
        if getattr(e, "test", False):
            return

    if action:
        old_action = action
        action = None
        renpy.display.behavior.run(old_action)

    now = renpy.display.core.get_time()

    node, state, start_time = execute_node(now, node, state, start_time)

    labels.clear()

    if node is None:
        renpy.test.testmouse.reset()
        return

    loc = renpy.exports.get_filename_line()

    if (old_state != state) or (old_loc != loc):
        last_state_change = now

    old_state = state
    old_loc = loc

    if (now - last_state_change) > _test.timeout:
        location = node_loc if node_loc is not None else (node.filename, node.linenumber)
        raise Exception("Testcase stuck at {}:{}.".format(location[0], location[1]))


def test_command():
    """
    The dialogue command. This updates dialogue.txt, a file giving all the dialogue
    in the game.
    """

    ap = renpy.arguments.ArgumentParser(description="Runs a testcase.")
    ap.add_argument("testcase", help="The name of a testcase to run.", nargs='?', default="default")

    args = ap.parse_args()

    if args.testcase not in testcases:
        raise Exception("Testcase {} was not found.".format(args.testcase))

    global node
    node = testcases[args.testcase]

    return True


renpy.arguments.register_command("test", test_command)
