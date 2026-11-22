
from __future__ import division, absolute_import, with_statement, print_function, unicode_literals
from renpy.compat import *


# Allow pickling NoneType.
if PY2:
    import __builtin__  # type: ignore[import-not-found]
    setattr(__builtin__, "NoneType", type(None))
else:
    import builtins
    setattr(builtins, "NoneType", type(None))


class Object(object):
    """
    Our own base class. Contains methods to simplify serialization.
    """

    __version__ = 0

    nosave = [ ]
    after_upgrade = None

    def __getstate__(self):
        rv = vars(self).copy()

        for f in self.nosave:
            if f in rv:
                del rv[f]

        rv["__version__"] = self.__version__

        return rv

    # None, to prevent this from being called when unnecessary.
    after_setstate = None

    def __setstate__(self, new_dict):
        new_dict = new_dict.copy()
        version = new_dict.pop("__version__", 0)

        self.__dict__.update(new_dict)

        if version != self.__version__ and callable(self.after_upgrade):
            self.after_upgrade(version)  # E1101

        if self.after_setstate:
            self.after_setstate()  # E1102

# We don't handle slots with this mechanism, since the call to vars should
# throw an error.


sentinels = { }


class Sentinel(object):
    """
    This is used to represent a sentinel object. There will be exactly one
    sentinel object with a name existing in the system at any time.
    """

    def __new__(cls, name):
        rv = sentinels.get(name, None)

        if rv is None:
            rv = object.__new__(cls)
            sentinels[name] = rv

        return rv

    def __init__(self, name):
        self.name = name

    def __reduce__(self):
        return (Sentinel, (self.name, ))
