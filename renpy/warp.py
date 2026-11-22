
# This code implements the ability to "warp" to a given location in
# the Ren'Py source code, given the filename and line number of the
# location.

from __future__ import division, absolute_import, with_statement, print_function, unicode_literals
from renpy.compat import *

import renpy
import renpy.ast
import renpy.config
import renpy.exports
import renpy.game
import operator

warp_spec: object = None


def warp():
    """
    Given a filename and line number, this attempts to warp the user
    to that filename and line number.
    """

    global warp_spec

    spec = warp_spec
    warp_spec = None

    if spec is None:
        return None

    if not isinstance(spec, str):
        raise Exception("Invalid warp location.")

    spec = str(spec)

    if ':' not in spec:
        raise Exception('No : found in warp location.')

    filename, line = spec.split(':', 1)
    line = int(line)

    if not renpy.config.developer:
        raise Exception("Can't warp, developer mode disabled.")

    if not filename.startswith("game/"):
        filename = "game/" + filename

    script = getattr(renpy.game, "script", None)
    if script is None:
        return None

    # First, compute for each statement reachable from a scene statement,
    # one statement that reaches that statement.

    prev = { }

    seenset = set(script.namemap.values())

    # This is called to indicate that next can be executed following node.
    def add(node, next):  # @ReservedAssignment

        if next not in prev:
            prev[next] = node
            return

        # Try to figure out which node to use.

        old = prev[next]

        def prefer(fn):
            if fn(node, old):
                return node

            if fn(old, node):
                return old

            return None

        n = None
        n = n or prefer(lambda a, b : (a.filename == next.filename) and (b.filename != next.filename))
        n = n or prefer(lambda a, b : (a.linenumber <= next.linenumber) and (b.linenumber > next.linenumber))
        n = n or prefer(lambda a, b : (a.linenumber >= b.linenumber))
        n = n or node

        prev[next] = n

    for n in seenset:

        if isinstance(n, renpy.ast.Translate) and n.language:
            continue

        if isinstance(n, renpy.ast.Menu):
            for i in n.items:
                if i[2] is not None:
                    add(n, i[2][0])

        if isinstance(n, renpy.ast.Jump):
            if not n.expression and n.target in script.namemap:
                add(n, script.namemap[n.target])
                continue

        if isinstance(n, renpy.ast.While):
            add(n, n.block[0])

        if isinstance(n, renpy.ast.If):

            seen_true = False

            for condition, block in n.entries:
                add(n, block[0])

                if condition == "True":
                    seen_true = True

            if seen_true:
                continue

        if isinstance(n, renpy.ast.UserStatement):
            add(n, n.get_next())
        elif getattr(n, 'next', None) is not None:
            add(n, n.next)

    # Now, attempt to find a statement preceding the line that the
    # user wants to warp to.

    candidates = [ (n.linenumber, n)
                   for n in seenset
                   if n.filename == filename and n.linenumber <= line
                   ]

    # We didn't find any candidate statements, so give up the warp.
    if not candidates:
        raise Exception("Could not find a statement to warp to. ({})".format(spec))

    # Sort the list of candidates, so they're ordered by linenumber.
    candidates.sort(key=operator.itemgetter(0))

    # Pick the candidate immediately before (or on) the line.
    node = candidates[-1][1]

    # Now, determine a list of nodes to run while getting to this node.
    run = [ ]
    n = node

    while True:
        n = prev.pop(n, None)
        if n:
            run.append(n)
        else:
            break

    run.reverse()

    run = run[-renpy.config.warp_limit:]

    renpy.config.skipping = "fast"

    # Determine which statements we want to execute, and then run
    # only them.

    for n in run:

        if n.can_warp():

            # Execute, if possible.
            try:
                n.execute()
            except:
                pass

    # Now, return the name of the place where we will warp to. This
    # becomes the new starting point of the game.

    renpy.config.skipping = None
    renpy.game.after_rollback = True

    renpy.exports.block_rollback()

    renpy.game.context().goto_label(node.name)
    renpy.game.context().come_from(node.name, "_after_warp")
    raise renpy.game.RestartContext()
