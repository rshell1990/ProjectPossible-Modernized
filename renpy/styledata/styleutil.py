
# Utility functions used by the various property functions:

from __future__ import print_function

import renpy


def none_is_null(o):
    if o is None:
        return renpy.display.layout.Null()
    else:
        return renpy.easy.displayable(o)


def none_is_0(o):
    if o is None:
        return 0
    else:
        return o


def expand_focus_mask(v):
    if v is None:
        return v
    elif v is False:
        return v
    elif v is True:
        return v
    elif callable(v):
        return v
    else:
        return renpy.easy.displayable(v)


def expand_outlines(l):
    rv = []

    for i in l:
        if len(i) == 2:
            rv.append((i[0], renpy.color.Color(i[1]), 0, 0))
        else:
            rv.append((i[0], renpy.color.Color(i[1]), i[2], i[3]))

    return rv


# Names for anchors.
ANCHORS = dict(
    left=0.0,
    right=1.0,
    center=0.5,
    top=0.0,
    bottom=1.0,
)


def expand_anchor(v):
    """
    Turns an anchor into a number.
    """

    try:
        return ANCHORS.get(v, v)
    except Exception:
        # This fixes some bugs in very old Ren'Pys.

        for n in ANCHORS:
            o = getattr(renpy.store, n, None)
            if o is None:
                continue

            if v is o:
                return ANCHORS[n]

        raise
