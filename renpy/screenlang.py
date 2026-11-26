
from __future__ import division, absolute_import, with_statement, print_function, unicode_literals
from renpy.compat import PY2, basestring, bchr, bord, chr, open, pystr, range, round, str, tobytes, unicode  # *

import renpy
import contextlib


class ScreenLangScreen(renpy.object.Object):
    """
    This represents a screen defined in the screen language.
    """

    __version__ = 1

    variant = "None"

    # Predict should be false for screens created before
    # prediction existed.
    predict = "False"

    parameters = None
    location = None

    def __init__(self):
        # The name of the screen.
        self.name = "<unknown>"

        # Should this screen be declared as modal?
        self.modal = "False"

        # The screen's zorder.
        self.zorder = "0"

        # The screen's tag.
        self.tag = None

        # The PyCode object containing the screen's code.
        self.code = None

        # The variant of screen we're defining.
        self.variant = "None"  # expr.

        # Should we predict this screen?
        self.predict = "None"  # expr.

        # The parameters this screen takes.
        self.parameters = None

        raise Exception("Creating a new ScreenLangScreen is no longer supported.")

    def after_upgrade(self, version):
        if version < 1:
            self.modal = "False"
            self.zorder = "0"

    def define(self, location):
        """
        Defines a screen.
        """

        renpy.display.screen.define_screen(
            self.name,
            self,
            modal=self.modal,
            zorder=self.zorder,
            tag=self.tag,
            variant=renpy.python.py_eval(self.variant),
            predict=renpy.python.py_eval(self.predict),
            parameters=self.parameters,
            location=self.location,
        )

    def __call__(self, *args, **kwargs):
        scope = kwargs["_scope"]

        if self.parameters:
            args = scope.get("_args", ())
            kwargs = scope.get("_kwargs", {})

            values = renpy.ast.apply_arguments(self.parameters, args, kwargs)
            scope.update(values)

        renpy.python.py_exec_bytecode(self.code.bytecode, locals=scope)  # type: ignore
