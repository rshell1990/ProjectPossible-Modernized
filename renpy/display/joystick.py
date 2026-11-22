
# This file was responsible for joystick support in Ren'Py, which has
# been removed, save for a few compatibility functions.

from __future__ import division, absolute_import, with_statement, print_function, unicode_literals
from renpy.compat import *

import renpy.display
import pygame_sdl2

# Do we have a joystick enabled?
enabled = False


class JoyBehavior(renpy.display.layout.Null):
    """
    This is a behavior intended for joystick calibration. If a joystick
    event occurs, this returns it as a string.
    """

    pass


joysticks = { }


def count():
    return pygame_sdl2.joystick.get_count()


def get(n):

    if n in joysticks:
        return joysticks[n]

    try:
        joysticks[n] = pygame_sdl2.joystick.Joystick(n)
        return joysticks[n]
    except:
        return None
