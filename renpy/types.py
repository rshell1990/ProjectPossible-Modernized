
# This file contains the various types that Ren'Py uses.
# This file should be import order agnostic, so it can be used
# by other modules, so it should not directly reference any
# Ren'Py modules (type statement and string forward references are okay).
# In general, you should prefer to define type information in other files,
# and use this module only if that would create a circular import, or
# the type is very generic and importing it from a lot of places would
# be inconvenient.

import renpy

type Displayable = renpy.display.displayable.Displayable

type DisplayableLike = Displayable | str | list[str] | renpy.color.Color
"""
This describes anything that Ren'Py considers to be a displayable.

Apart from Displayable itself, this could be one of:
- Path to a file, relative to one of searchpath routes.
- #-prefixed string of a color.
- Name of a defined image.
- Ren'Py interpolation string referencing one of above.
- List of any of the above.
- renpy.color.Color object.
"""

type Position = int | float | renpy.display.position.absolute | renpy.display.position.position
"""
This describes a position, which can be one of:
- An integer - treated as pixels from the top left corner of the area.
- A float - treated as a percentage position from the top left corner of the
  area.
- An absolute position - treated as pixels from the top left corner of the
  area, where fractional part is a subpixel offset.
- A position instance - special type that combines absolute and relative positions.
"""
