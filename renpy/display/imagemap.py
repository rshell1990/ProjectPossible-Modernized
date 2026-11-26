
# This file handles imagemap caching.

from __future__ import division, absolute_import, with_statement, print_function, unicode_literals
from renpy.compat import PY2, basestring, bchr, bord, chr, open, pystr, range, round, str, tobytes, unicode  # *

import renpy
import renpy.pygame as pygame

from renpy.display.render import render


# A list of cache images we've already written.
cached = set()


class ImageMapCrop(renpy.display.displayable.Displayable):
    """
    This handles the cropping of uncached imagemap components.
    """

    def __init__(self, child, rect):
        super(ImageMapCrop, self).__init__()

        self.child = child
        self.rect = rect

        self._duplicatable = child._duplicatable

    def visit(self):
        return [self.child]

    def _duplicate(self, args):
        child = self.child._duplicate(args)

        if child is self.child:
            return self

        child._unique()

        rv = self._copy(args)
        rv.child = child
        rv._duplicatable = False
        return rv

    def _unique(self):
        self.child._unique()
        self._duplicatable = False

    def render(self, width, height, st, at):
        cr = render(self.child, renpy.config.screen_width, renpy.config.screen_height, st, at)
        return cr.subsurface(self.rect)


class ImageCacheCrop(renpy.display.displayable.Displayable):
    """
    This handles the cropping of an imagemap component.
    """

    def __init__(self, cache, index):
        super(ImageCacheCrop, self).__init__()

    def render(self, width, height, st, at):
        return renpy.display.render.Render(0, 0)


class ImageMapCache(renpy.object.Object):
    """
    This previously would cache an image map into a single image. That's not
    necessary anymore, so all this does is crop images.
    """

    def __init__(self, enable):
        enable = False
        self.enable = enable

    def crop(self, d, rect):
        return ImageMapCrop(d, rect)

    def finish(self):
        return
