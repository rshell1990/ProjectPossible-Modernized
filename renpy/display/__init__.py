
from __future__ import division, absolute_import, with_statement, print_function, unicode_literals
from renpy.compat import *

import renpy
renpy.update_path()

import renpy.log

# The draw object through which all drawing is routed. This object
# contains all of the distinction between the software and GL
# renderers.
draw = None

# The interface object.
interface = None

# Should we disable imagedissolve-type transitions?
less_imagedissolve = False

# Are we on a touchscreen?
touch = False

# The pygame.display.Info object, which we want to survive a reload.
info = None


def get_info():
    global info

    if info is None:
        import pygame_sdl2 as pygame  # type: ignore[import-not-found]
        pygame.display.init()
        info = pygame.display.Info()

    return info


# Logs we use.
log = renpy.log.open("log", developer=False, append=False)
ic_log = renpy.log.open("image_cache", developer=True, append=False)
to_log = renpy.log.open("text_overflow", developer=True, append=True)
