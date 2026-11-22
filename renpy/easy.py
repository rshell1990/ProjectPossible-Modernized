
# Functions that make the user's life easier.

from __future__ import division, absolute_import, with_statement, print_function, unicode_literals
from renpy.compat import *


import renpy.display
import renpy.display.core
import renpy.display.image
import renpy.display.predict
import renpy.color
import renpy.config
import renpy.exports
import renpy.loader
import renpy.store  # type: ignore[import-not-found]
import renpy.substitutions
import renpy.easy
import renpy.styledata
import renpy.styledata.stylesets  # type: ignore[import-not-found]
import contextlib
import time

Color = renpy.color.Color
color = renpy.color.Color


def lookup_displayable_prefix(d):
    """
    Given `d`, a string given a displayable, returns the displayale it
    corresponds to or None if it it does not correspond to one.
    """

    prefix, colon, arg = d.partition(":")

    if not colon:
        return None

    fn = renpy.config.displayable_prefix.get(prefix, None)
    if fn is None:
        return None

    return displayable(fn(arg))


def displayable_or_none(d, scope=None, dynamic=True):

    if isinstance(d, renpy.display.core.Displayable):
        return d

    if d is None:
        return d

    if isinstance(d, basestring):
        if not d:
            raise Exception("An empty string cannot be used as a displayable.")
        elif ("[" in d) and renpy.config.dynamic_images and dynamic:
            return renpy.display.image.DynamicImage(d, scope=scope)

        rv = lookup_displayable_prefix(d)

        if rv is not None:
            return rv
        elif d[0] == '#':
            return renpy.store.Solid(d)
        elif "." in d:
            return renpy.store.Image(d)
        else:
            return renpy.store.ImageReference(tuple(d.split()))

    if isinstance(d, Color):
        return renpy.store.Solid(d)

    if isinstance(d, list):
        return renpy.display.image.DynamicImage(d, scope=scope)

    # We assume the user knows what he's doing in this case.
    if hasattr(d, '_duplicate'):
        return d

    if d is True or d is False:
        return d

    raise Exception("Not a displayable: %r" % (d,))


def displayable(d, scope=None):
    """
    :doc: udd_utility
    :name: renpy.displayable

    This takes `d`, which may be a displayable object or a string. If it's
    a string, it converts that string into a displayable using the usual
    rules.
    """

    if isinstance(d, renpy.display.core.Displayable):
        return d

    if isinstance(d, basestring):
        if not d:
            raise Exception("An empty string cannot be used as a displayable.")
        elif ("[" in d) and renpy.config.dynamic_images:
            return renpy.display.image.DynamicImage(d, scope=scope)

        rv = lookup_displayable_prefix(d)

        if rv is not None:
            return rv
        elif d[0] == '#':
            return renpy.store.Solid(d)
        elif "." in d:
            return renpy.store.Image(d)
        else:
            return renpy.store.ImageReference(tuple(d.split()))

    if isinstance(d, Color):
        return renpy.store.Solid(d)

    if isinstance(d, list):
        return renpy.display.image.DynamicImage(d, scope=scope)

    # We assume the user knows what he's doing in this case.
    if hasattr(d, '_duplicate'):
        return d

    if d is True or d is False:
        return d

    raise Exception("Not a displayable: %r" % (d,))


def dynamic_image(d, scope=None, prefix=None, search=None):
    """
    Substitutes a scope into `d`, then returns a displayable.

    If `prefix` is given, and a prefix has been given a prefix search is
    performed until a file is found. (Only a file can be used in this case.)
    """

    if not isinstance(d, list):
        d = [ d ]

    def find(name):

        if renpy.exports.image_exists(name):
            return True

        if renpy.loader.loadable(name):
            return True

        if lookup_displayable_prefix(name):
            return True

        if (len(d) == 1) and (renpy.config.missing_image_callback is not None):
            if renpy.config.missing_image_callback(name):
                return True

    for i in d:

        if not isinstance(i, basestring):
            continue

        if (prefix is not None) and ("[prefix_" in i):

            if scope:
                scope = dict(scope)
            else:
                scope = { }

            for p in renpy.styledata.stylesets.prefix_search[prefix]:  # @UndefinedVariable
                scope["prefix_"] = p

                rv = renpy.substitutions.substitute(i, scope=scope, force=True, translate=False)[0]

                if find(rv):
                    return displayable_or_none(rv)

                if search is not None:
                    search.append(rv)

        else:

            rv = renpy.substitutions.substitute(i, scope=scope, force=True, translate=False)[0]

            if find(rv):
                return displayable_or_none(rv)

            if search is not None:
                search.append(rv)

    else:

        rv = d[-1]

        if find(rv):
            return displayable_or_none(rv, dynamic=False)

        return None


def predict(d):
    d = renpy.easy.displayable_or_none(d)

    if d is not None:
        renpy.display.predict.displayable(d)


@contextlib.contextmanager
def timed(name):
    start = time.time()
    yield
    print("{0}: {1:.2f} ms".format(name, (time.time() - start) * 1000.0))


def split_properties(properties, *prefixes):
    """
    :doc: other

    Splits up `properties` into multiple dictionaries, one per `prefix`. This
    function checks each key in properties against each prefix, in turn.
    When a prefix matches, the prefix is stripped from the key, and the
    resulting key is mapped to the value in the corresponding dictionary.

    If no prefix matches, an exception is thrown. (The empty string, "",
    can be used as the last prefix to create a catch-all dictionary.)

    For example, this splits properties beginning with text from
    those that do not::

        text_properties, button_properties = renpy.split_properties(properties, "text_", "")
    """

    rv = [ ]

    for _i in prefixes:
        rv.append({})

    if not properties:
        return rv

    prefix_d = list(zip(prefixes, rv))

    for k, v in properties.items():
        for prefix, d in prefix_d:
            if k.startswith(prefix):
                d[k[len(prefix):]] = v
                break
        else:
            raise Exception("Property {} begins with an unknown prefix.".format(k))

    return rv
