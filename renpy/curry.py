

from __future__ import division, absolute_import, with_statement, print_function, unicode_literals
from renpy.compat import *


class Curry(object):
    """
    Stores a callable and some arguments. When called, calls the
    callable with the stored arguments and the additional arguments
    supplied to the call.
    """

    hash = None

    def __init__(self, callable, *args, **kwargs):  # @ReservedAssignment
        self.callable = callable
        self.args = args
        self.kwargs = kwargs
        self.__doc__ = getattr(self.callable, "__doc__", None)
        self.__name__ = getattr(self.callable, "__name__", None)

    def __call__(self, *args, **kwargs):

        merged_kwargs = dict(self.kwargs)
        merged_kwargs.update(kwargs)

        return self.callable(*(self.args + args), **merged_kwargs)

    def __repr__(self):
        return "<curry %s %r %r>" % (self.callable, self.args, self.kwargs)

    def __eq__(self, other):

        return (
            isinstance(other, Curry) and
            self.callable == other.callable and
            self.args == other.args and
            self.kwargs == other.kwargs)

    def __ne__(self, other):
        return not (self == other)

    def __hash__(self):

        if self.hash is None:
            self.hash = hash(self.callable) ^ hash(self.args)

            for i in self.kwargs.items():
                self.hash ^= hash(i)

        return self.hash


def curry(fn):
    """
    Takes a callable, and returns something that, when called, returns
    something that when called again, calls the function. So
    basically, the thing returned from here when called twice does the
    same thing as the function called once.
    """

    rv = Curry(Curry, fn)
    rv.__doc__ = getattr(fn, "__doc__", None)
    rv.__name__ = getattr(fn, "__name__", None)
    return rv


def partial(function, *args, **kwargs):
    """
    Stores the arguments and keyword arguments of function, and
    returns something that, when called, calls the function with
    a combination of the supplied arguments and the arguments of
    the second call.
    """

    return Curry(function, *args, **kwargs)
