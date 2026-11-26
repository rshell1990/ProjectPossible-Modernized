
# This used to hack pygame to support resolution-scaling. Now it just kinda
# sits here, to provide compatibility with what it used to be.

from __future__ import division, absolute_import, with_statement, print_function, unicode_literals
from renpy.compat import PY2, basestring, bchr, bord, chr, open, pystr, range, round, str, tobytes, unicode  # *


import renpy
import renpy.pygame as pygame
import renpy.display.pgrender as pgrender

import _renpy

##############################################################################
# The scaling API that's used if we don't enable scaling.

# Gets the real pygame surface.


def real(s):
    return s


# Scales the number, n.


def scale(n):
    return n


def real_bilinear(src, size):
    rv = pgrender.surface_unscaled(size, src)
    renpy.display.module.bilinear_scale(src, rv)
    return rv


# Does pygame.transform.scale.


def real_transform_scale(surf, size):
    return pgrender.transform_scale_unscaled(surf, size)


# Loads an image, without scaling it.


def image_load_unscaled(f, hint, convert=True):
    rv = pgrender.load_image_unscaled(f, hint)
    return rv


# Saves an image without rescaling.


def image_save_unscaled(surf, filename):
    pygame.image.save(surf, filename)  # pygame does the filename encoding.


# Scales down a surface.


def surface_scale(full):
    return full


real_renpy_pixellate = _renpy.pixellate
real_renpy_transform = _renpy.transform


def real_smoothscale(src, size, dest=None):
    """
    This scales src up or down to size. This uses both the pixellate
    and the transform operations to handle the scaling.
    """

    width, height = size
    srcwidth, srcheight = src.get_size()
    iwidth, iheight = srcwidth, srcheight

    if dest is None:
        dest = pgrender.surface_unscaled(size, src)

    if width == 0 or height == 0:
        return dest

    xshrink = 1
    yshrink = 1

    while iwidth >= width * 2:
        xshrink *= 2
        iwidth //= 2

    while iheight >= height * 2:
        yshrink *= 2
        iheight //= 2

    if iwidth != srcwidth or iheight != srcheight:
        inter = pgrender.surface_unscaled((iwidth, iheight), src)
        real_renpy_pixellate(src, inter, xshrink, yshrink, 1, 1)
        src = inter

    real_renpy_transform(
        src,
        dest,
        0,
        0,
        1.0 * iwidth / width,
        0,
        0,
        1.0 * iheight / height,
        precise=1,
    )

    return dest


smoothscale = real_smoothscale
