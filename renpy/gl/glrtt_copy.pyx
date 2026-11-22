#@PydevCodeAnalysisIgnore
#cython: profile=False

from __future__ import print_function

from renpy.uguu.gl cimport *
from gldraw cimport *
from gldraw import Rtt

class CopyRtt(Rtt):
    """
    This class uses texture copying to implement Render-to-texture.
    """

    def init(self):
        return

    def deinit(self):
        return

    def render(self, Environ environ, texture, x, y, w, h, draw_func):
        """
        This function is called to trigger a rendering to a texture.
        `x`, `y`, `w`, and `h` specify the location and dimensions of
        the sub-image to render to the texture. `draw_func` is called
        to render the texture.
        """

        environ.viewport(0, 0, w, h)
        environ.ortho(x, x + w, y, y + h, -1, 1)

        draw_func(x, y, w, h)

        glBindTexture(GL_TEXTURE_2D, texture)

        glCopyTexSubImage2D(
            GL_TEXTURE_2D,
            0,
            0,
            0,
            0,
            0,
            w,
            h)

    def end(self):
        """
        This is called when a Render-to-texture session ends.
        """

    def get_size_limit(self, dimension):
        return dimension

