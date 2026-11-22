
from __future__ import division, absolute_import, with_statement, print_function, unicode_literals
from renpy.compat import *

from typing import Any

import pygame_sdl2 as pygame # type: ignore[import-not-found]

# The overridden positioning of the mouse.
mouse_pos = None # type: Any

# The mouse buttons.
mouse_buttons = [ 0, 0, 0 ]


def get_mouse_pos(x, y):
    """
    Called to get the overridden mouse position.
    """

    if mouse_pos is None:
        return x, y

    return mouse_pos


def post(event_type, **kwargs):
    pygame.event.post(pygame.event.Event(event_type, test=True, **kwargs))


def move_mouse(x, y):
    """
    Moves the mouse to x, y.
    """

    global mouse_pos

    pos = (x, y)

    if mouse_pos != pos:
        if mouse_pos:
            rel = (pos[0] - mouse_pos[0], pos[1] - mouse_pos[1])
        else:
            rel = (0, 0)

        post(pygame.MOUSEMOTION, pos=pos, rel=rel, buttons=tuple(mouse_buttons))

    mouse_pos = pos


def press_mouse(button):
    """
    Presses mouse button `button`.
    """

    post(pygame.MOUSEBUTTONDOWN, pos=mouse_pos, button=button)

    if button < 3:
        mouse_buttons[button - 1] = 1


def release_mouse(button):
    """
    Releases mouse button `button`.
    """
    post(pygame.MOUSEBUTTONUP, pos=mouse_pos, button=button)

    if button < 3:
        mouse_buttons[button - 1] = 0


def click_mouse(button, x, y):
    """
    Clicks the mouse at x, y
    """

    move_mouse(x, y)
    press_mouse(button)
    release_mouse(button)


def reset():
    """
    Resets mouse handling once the test has ended.
    """

    global mouse_pos
    mouse_pos = None
