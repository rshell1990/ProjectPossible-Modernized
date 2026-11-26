
from __future__ import division, absolute_import, with_statement, print_function, unicode_literals
from renpy.compat import PY2, basestring, bchr, bord, chr, open, pystr, range, round, str, tobytes, unicode  # *


import os
import renpy
import traceback
import subprocess


class Editor(object):
    """
    This class is intended to be subclassed by editor subclasses. It provides a
    number of editor related operations, which are called by Ren'Py (including
    the Ren'Py Launcher).

    Editor operations are grouped into transactions. An editor transaction
    starts with a call to the begin() method. Ren'Py will then call some number
    of command methods, each causing an operation to occur in the editor. Ren'Py
    will call end() at the end of the transaction.

    Although not required, it's reasonable than an implementation of this class
    will batch the files together and send them to the editor at once. It's also
    reasonable that an implementation will send the operations one at a time (and
    do little-to-nothing in begin() and end().

    Each operation takes a path to operate on. If the editor has a buffer
    corresponding to that path, that buffer is used. Otherwise, the editor
    is implicitly opened.

    We reserve the right to add new keyword arguments to methods of this class,
    so please ensure that subclasses accept and ignore unknown keyword
    arguments.
    """

    def begin(self, new_window=False, **kwargs):
        """
        Begins an editor transaction.

        `new_window`
            If True, a new editor window will be created and presented to the
            user. Otherwise, and existing editor window will be used.
        """

    def end(self, **kwargs):
        """
        Ends an editor transaction.
        """

    def open(self, filename, line=None, **kwargs):
        """
        Ensures `filename` is open in the editor. This may be called multiple
        times per transaction.

        `line`
            If not None, this should be a line number to open in the
            editor.

        The first open call in a transaction is somewhat special - that file
        should be given focus in a tabbed editor environment.
        """

    # This should be set to True if the editor supports projects.
    has_projects = False

    def open_project(self, directory):
        """
        Opens `directory` as a project in the editor.
        """


class SystemEditor(Editor):
    def open(self, filename, line=None, **kwargs):
        try:
            if renpy.windows:
                os.startfile(filename)  # type: ignore
            elif renpy.macintosh:
                subprocess.call(["open", filename])
            elif renpy.linux:
                subprocess.call(["xdg-open", filename])
        except Exception:
            traceback.print_exc()


# The editor that Ren'Py is using. It should be a subclass of the Editor
# class.
editor = None


def init():
    """
    Creates the editor object, based on the contents of the RENPY_EDIT_PY
    file.
    """

    global editor
    editor = SystemEditor()

    path = os.environ.get("RENPY_EDIT_PY", None)

    if path is None:
        return

    with open(path, "r") as f:
        source = f.read()

    code = compile(source, path, "exec")

    scope = {"__file__": path}
    exec(code, scope, scope)

    if "Editor" in scope:
        editor = scope["Editor"]()  # type: ignore
        return

    raise Exception("{0} did not define an Editor class.".format(path))


def launch_editor(filenames, line=1, transient=False):
    """
    Causes the editor to be launched.
    """

    # On mobile devices, we will never be able to launch the editor.
    if renpy.mobile:
        return True

    if editor is None:
        init()

    if editor is None:
        return False

    filenames = [renpy.lexer.unelide_filename(i) for i in filenames]
    filenames = [os.path.realpath(i) for i in filenames]

    try:
        editor.begin(new_window=transient)

        for i in filenames:
            editor.open(i, line)
            line = None  # The line number only applies to the first filename.

        editor.end()

        return True

    except Exception:
        traceback.print_exc()
        return False
