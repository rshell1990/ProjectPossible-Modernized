
import renpy
import os


def expose_file(fn):
    """
    Ensures that `fn` can be read and written by the user, on platforms where
    that may not be the default.
    """

    if renpy.android:

        try:
            os.chmod(fn, 0o660)
        except:
            pass


def expose_directory(dn):
    """
    Ensures that `fn` can be read and written by the user, on platforms where
    that may not be the default.
    """

    if renpy.android:

        try:
            os.chmod(dn, 0o770)
        except:
            pass
