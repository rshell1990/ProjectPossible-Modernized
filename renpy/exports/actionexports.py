
from __future__ import division, absolute_import, with_statement, print_function, unicode_literals  # type: ignore
from renpy.compat import PY2, basestring, bchr, bord, chr, open, pystr, range, round, str, tobytes, unicode  # *

import renpy


def notify(message):
    """
    :doc: other

    Causes Ren'Py to display the `message` using the notify screen. By
    default, this will cause the message to be dissolved in, displayed
    for two seconds, and dissolved out again.

    This is useful for actions that otherwise wouldn't produce feedback,
    like screenshots or quicksaves.

    Only one notification is displayed at a time. If a second notification
    is displayed, the first notification is replaced.

    This function just calls :var:`config.notify`, allowing its implementation
    to be replaced by assigning a new function to that variable.
    """

    renpy.config.notify(message)


def display_notify(message):
    """
    :doc: other

    The default implementation of :func:`renpy.notify`.
    """

    renpy.exports.hide_screen("notify")
    renpy.exports.show_screen("notify", message=message)
    renpy.display.tts.notify_text = renpy.text.extras.filter_alt_text(message)

    renpy.exports.restart_interaction()


def confirm(message, **kwargs):
    """
    :doc: other

    This causes the a yes/no prompt screen with the given message
    to be displayed, and dismissed when the player hits yes or no.

    Returns True if the player hits yes, and False if the player hits no.

    `message`
        The message that will be displayed.

    `screen`
        If provided, this screen will be used instead of the default screen.

    Additional keyword arguments not beginning with _ are passed to the screen.

    See :func:`Confirm` for a similar Action.
    """
    Return = renpy.store.Return
    screen = kwargs.pop("screen", None)
    renpy.store.layout.yesno_screen(message, yes=Return(True), no=Return(False), _screen=screen, **kwargs)
    return renpy.ui.interact()
