

from __future__ import print_function

import importlib
import renpy
renpy.update_path()

def import_style_functions():
    import renpy.styledata.stylesets  # @UnresolvedImport  # type: ignore[import-not-found]

    import renpy.styledata.style_functions  # @UnresolvedImport  # type: ignore[import-not-found]
    import renpy.styledata.style_activate_functions  # @UnresolvedImport  # type: ignore[import-not-found]
    import renpy.styledata.style_hover_functions  # @UnresolvedImport  # type: ignore[import-not-found]
    import renpy.styledata.style_idle_functions  # @UnresolvedImport  # type: ignore[import-not-found]
    import renpy.styledata.style_insensitive_functions  # @UnresolvedImport  # type: ignore[import-not-found]

    import renpy.styledata.style_selected_functions  # @UnresolvedImport  # type: ignore[import-not-found]
    import renpy.styledata.style_selected_activate_functions  # @UnresolvedImport  # type: ignore[import-not-found]
    import renpy.styledata.style_selected_hover_functions  # @UnresolvedImport  # type: ignore[import-not-found]
    import renpy.styledata.style_selected_idle_functions  # @UnresolvedImport  # type: ignore[import-not-found]
    import renpy.styledata.style_selected_insensitive_functions  # @UnresolvedImport  # type: ignore[import-not-found]

    style_class = getattr(importlib.import_module("renpy.styledata.styleclass"), "Style")
    renpy_style = getattr(renpy, "style")
    setattr(renpy_style, "Style", style_class)
