
# This file was responsible for joystick support in Ren'Py, which has
# been removed, save for a few compatibility functions.

from __future__ import division, absolute_import, with_statement, print_function, unicode_literals
from renpy.compat import PY2, basestring, bchr, bord, chr, open, pystr, range, round, str, tobytes, unicode  # *


import renpy
import renpy.pygame as pygame


# Do we have a joystick enabled?
enabled = False


class JoyBehavior(renpy.display.layout.Null):
    """
    This is a behavior intended for joystick calibration. If a joystick
    event occurs, this returns it as a string.
    """


joysticks = {}


def count():
    return pygame.joystick.get_count()


def get(n):
    if n in joysticks:
        return joysticks[n]

    try:
        joysticks[n] = pygame.joystick.Joystick(n)
        return joysticks[n]
    except Exception:
        return None
