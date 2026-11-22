
from cpython.object cimport PyObject
import types

# Import the Python internals. Here be dragons, but at least Python 2.7 isn't
# going to be changing.

cdef extern from "Python.h":
    ctypedef struct PyTypeObject
    cdef void PyType_Modified(PyTypeObject *)

    ctypedef struct PyCodeObject:
        int co_flags
        PyObject *co_filename

cdef extern from "frameobject.h":

    ctypedef struct PyFrameObject:
        PyFrameObject *f_back
        PyCodeObject *f_code

cdef extern from "Python.h":

    ctypedef struct PyThreadState:
        PyFrameObject *frame

    PyThreadState *PyThreadState_Get()

    enum:
        CO_FUTURE_DIVISION
        CO_FUTURE_WITH_STATEMENT


###############################################################################
# Add attributes to built in types.

cdef class MappingProxy:
    """
    This is something that Python's built-in mapping proxy can be converted
    to, in order to gain access to the internal dictionary so we can make
    changes to it.
    """

    cdef dict dict


def add_attribute(cls, name, value):
    """
    This adds an attribute to a Python built-in type.
    """

    cdef MappingProxy mp = <MappingProxy> <PyObject *> (cls.__dict__)
    mp.dict[name] = value

    PyType_Modified(<PyTypeObject *> cls)


################################################################################
# dict
#
# For the .items(), .keys(), and .values() methods, check to see if the calling
# code was compiled with "from __future__ import division", or the equivalent.
# If it was, then invoke Python 3 semantics for these methods, which means
# returning a view into a dict. Otherwise, go with Python 2.
#
# Why division? It's the most Python 3-specific of the flags, at least for
# Ren'Py purposes.

add_attribute(dict, "_items", dict.items)
add_attribute(dict, "_keys", dict.keys)
add_attribute(dict, "_values", dict.values)

cdef bint use_view():
    """
    Returns true if the methods should use view semantics, or false if
    they should use legacy/list semantics.
    """

    return ((PyThreadState_Get().frame.f_code.co_flags) & (CO_FUTURE_DIVISION | CO_FUTURE_WITH_STATEMENT)) == (CO_FUTURE_DIVISION | CO_FUTURE_WITH_STATEMENT)


def items(self):
    if use_view():
        return self.viewitems()
    else:
        return self._items()

def keys(self):
    if use_view():
        return self.viewkeys()
    else:
        return self._keys()

def values(self):
    if use_view():
        return self.viewvalues()
    else:
        return self._values()


add_attribute(dict, "items", types.MethodType(items, None, dict))
add_attribute(dict, "keys", types.MethodType(keys, None, dict))
add_attribute(dict, "values", types.MethodType(values, None, dict))

