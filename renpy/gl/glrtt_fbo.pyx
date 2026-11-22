#@PydevCodeAnalysisIgnore
#cython: profile=False

from __future__ import print_function

from renpy.uguu.gl cimport *
from gldraw cimport *
from gldraw import Rtt

import renpy

# The framebuffer object we use.
cdef GLuint fbo

# The root framebuffer.
cdef GLint root_fbo

# The renderbuffer object we use.
cdef GLuint texture

class FboRtt(Rtt):
    """
    This class uses texture copying to implement Render-to-texture.
    """

    def init(self):

        glGetIntegerv(GL_FRAMEBUFFER_BINDING, &root_fbo);
        renpy.display.log.write("Root FBO is: %d", root_fbo)

        glGenFramebuffers(1, &fbo)
        glGenTextures(1, &texture)

        cdef int i

        glGetIntegerv(GL_MAX_TEXTURE_SIZE, &i)
        self.size_limit = min(i, 2048)
        renpy.display.log.write("FBO Maximum Texture Size: %d", self.size_limit)

        glBindTexture(GL_TEXTURE_2D, texture)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, self.size_limit, self.size_limit, 0, GL_RGBA, GL_UNSIGNED_BYTE, NULL)

        glBindFramebuffer(GL_FRAMEBUFFER, fbo)
        glFramebufferTexture2D(
            GL_FRAMEBUFFER,
            GL_COLOR_ATTACHMENT0,
            GL_TEXTURE_2D,
            texture,
            0)

        glBindFramebuffer(GL_FRAMEBUFFER, root_fbo)


    def deinit(self):
        """
        Called before changing the GL context.
        """

        glBindFramebuffer(GL_FRAMEBUFFER, root_fbo)
        glDeleteFramebuffers(1, &fbo)
        glDeleteTextures(1, &texture)

    def begin(self):
        """
        This function should be called when a Render-to-texture
        session begins. It's responsible for setting the GPU to
        RTT mode.
        """

    def render(self, Environ environ, texture, x, y, w, h, draw_func):
        """
        This function is called to trigger a rendering to a texture.
        `x`, `y`, `w`, and `h` specify the location and dimensions of
        the sub-image to render to the texture. `draw_func` is called
        to render the texture.
        """

        try:
            glBindFramebuffer(GL_FRAMEBUFFER, fbo)

            environ.viewport(0, 0, w, h)
            environ.ortho(x, x + w, y, y + h, -1, 1)

            draw_func(x, y, w, h)

            glBindTexture(GL_TEXTURE_2D, texture)
            glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, w, h, 0, GL_RGBA, GL_UNSIGNED_BYTE, NULL)
            glCopyTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, 0, 0, w, h, 0)

        finally:
            glBindFramebuffer(GL_FRAMEBUFFER, root_fbo)


    def get_size_limit(self, dimension):
        return self.size_limit
