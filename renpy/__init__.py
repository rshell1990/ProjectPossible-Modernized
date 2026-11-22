# This file ensures that renpy packages will be imported in the right
# order.

from __future__ import division, absolute_import, with_statement, print_function, unicode_literals

# All imports should go below renpy.compat.


def update_path():
    """
    Update the __path__ of package, to import binary modules from a libexec
    directory.
    """
    import os.path
    import sys

    name = sys._getframe(1).f_globals["__name__"]
    package = sys.modules[name]
    pkg_parts = name.split(".")

    try:
        import _renpy  # type: ignore[reportMissingImports]
        renpy_file = getattr(_renpy, "__file__", None)
        if renpy_file is not None:  # .so/.dll
            libexec = os.path.dirname(renpy_file)
            package.__path__.append(os.path.join(libexec, *pkg_parts))

        # Also find encodings, to deal with the way py2exe lays things out.
        import encodings
        libexec = os.path.dirname(encodings.__path__[0])
        package.__path__.append(os.path.join(libexec, *pkg_parts))
    except ImportError:
        return


from renpy.compat import *  # noqa: F401,F403
update_path()

import copy
import os
import platform
import site
import sys
import types

import renpy.compat.pickle as pickle

################################################################################
# Version information
################################################################################

try:
    from renpy.vc_version import vc_version, official, nightly
except ImportError:
    vc_version = 0
    official = False
    nightly = False

official = official and getattr(site, "renpy_build_official", False)

if PY2:  # noqa: F405
    version_tuple = (7, 4, 11, vc_version)
    version_name = "Lucky Beckoning Cat"
else:
    version_tuple = (8, 0, 0, vc_version)
    version_name = "Heck Freezes Over"

version_only = ".".join(str(i) for i in version_tuple)

if not official:
    version_only += "u"
elif nightly:
    version_only += "n"

version = "Ren'Py " + version_only

script_version = 5003000
savegame_suffix = "-LT1.save"
bytecode_version = 1

################################################################################
# Platform Information
################################################################################

windows = False
macintosh = False
linux = False
android = False
ios = False
emscripten = False

experimental = "RENPY_EXPERIMENTAL" in os.environ


def get_windows_version():
    """
    When called on Windows, returns the Windows version as `(major, minor)`.
    """
    import ctypes

    class OSVERSIONINFOEXW(ctypes.Structure):
        _fields_ = [
            ("dwOSVersionInfoSize", ctypes.c_ulong),
            ("dwMajorVersion", ctypes.c_ulong),
            ("dwMinorVersion", ctypes.c_ulong),
            ("dwBuildNumber", ctypes.c_ulong),
            ("dwPlatformId", ctypes.c_ulong),
            ("szCSDVersion", ctypes.c_wchar * 128),
            ("wServicePackMajor", ctypes.c_ushort),
            ("wServicePackMinor", ctypes.c_ushort),
            ("wSuiteMask", ctypes.c_ushort),
            ("wProductType", ctypes.c_byte),
            ("wReserved", ctypes.c_byte),
        ]

    try:
        os_version = OSVERSIONINFOEXW()
        os_version.dwOSVersionInfoSize = ctypes.sizeof(os_version)
        retcode = ctypes.windll.Ntdll.RtlGetVersion(ctypes.byref(os_version))

        if retcode != 0:
            return (10, 0)

        return (os_version.dwMajorVersion, os_version.dwMinorVersion)
    except Exception:
        return (10, 0)


if platform.win32_ver()[0]:
    windows = get_windows_version()
elif os.environ.get("RENPY_PLATFORM", "").startswith("ios"):
    ios = True
elif platform.mac_ver()[0]:
    macintosh = True
elif "ANDROID_PRIVATE" in os.environ:
    android = True
elif sys.platform == "emscripten" or "RENPY_EMSCRIPTEN" in os.environ:
    emscripten = True
else:
    linux = True

mobile = android or ios or emscripten
macapp = False

################################################################################
# Backup Data for Reload
################################################################################

safe_mode_checked = False
autoreload = False
session = {}

backup_blacklist = {
    "renpy",
    "renpy.compat",
    "renpy.compat.dictviews",
    "renpy.object",
    "renpy.log",
    "renpy.bootstrap",
    "renpy.debug",
    "renpy.display",
    "renpy.display.pgrender",
    "renpy.display.scale",
    "renpy.display.presplash",
    "renpy.display.test",
    "renpy.six",
    "renpy.text.ftfont",
    "renpy.test",
    "renpy.test.testast",
    "renpy.test.testexecution",
    "renpy.test.testkey",
    "renpy.test.testmouse",
    "renpy.test.testparser",
    "renpy.gl2",
    "renpy.gl",
    "renpycoverage",
}

type_blacklist = (
    types.ModuleType,
)

name_blacklist = {
    "renpy.loadsave.autosave_not_running",
    "renpy.python.unicode_re",
    "renpy.python.string_re",
    "renpy.python.store_dicts",
    "renpy.python.store_modules",
    "renpy.text.text.VERT_FORWARD",
    "renpy.text.text.VERT_REVERSE",
    "renpy.savelocation.scan_thread_condition",
    "renpy.savelocation.disk_lock",
    "renpy.character.TAG_RE",
    "renpy.display.im.cache",
    "renpy.display.render.blit_lock",
    "renpy.display.render.IDENTITY",
    "renpy.loader.auto_lock",
    "renpy.display.screen.cprof",
    "renpy.audio.audio.lock",
    "renpy.audio.audio.periodic_condition",
    "renpy.webloader.queue_lock",
    "renpy.persistent.save_MP_instances",
    "renpy.exports.sdl_dll",
}


class Backup(object):
    """
    Represents a backup of fields in Python modules comprising Ren'Py,
    captured shortly after initial import.
    """

    def __init__(self):
        self.variables = {}
        self.objects = {}
        self.names = {}

        if mobile:
            return

        for m in sys.modules.values():
            if m is None:
                continue

            self.backup_module(m)

        self.objects_pickle = pickle.dumps(self.objects, pickle.HIGHEST_PROTOCOL)
        self.objects = None

    def backup_module(self, mod):
        """
        Makes a backup of `mod`, which must be a Python module.
        """
        try:
            name = mod.__name__
        except Exception:
            return

        if not name.startswith("renpy"):
            return

        if name in backup_blacklist:
            return

        if name.startswith("renpy.styledata"):
            return

        self.names[mod] = set(vars(mod).keys())

        for k, v in vars(mod).items():
            if k.startswith("__") and k.endswith("__"):
                continue

            if isinstance(v, type_blacklist):
                continue

            if name + "." + k in name_blacklist:
                continue

            idv = id(v)
            self.variables[mod, k] = idv

            if self.objects is not None:
                self.objects[idv] = v

            try:
                pickle.dumps(v, pickle.HIGHEST_PROTOCOL)
            except Exception:
                print("Cannot pickle", name + "." + k, "=", repr(v))
                print("Reduce Ex is:", repr(v.__reduce_ex__(pickle.HIGHEST_PROTOCOL)))

    def restore(self):
        """
        Restores modules to a state similar to when the backup was created.
        """
        if not self.names:
            return

        for mod, names in self.names.items():
            modvars = vars(mod)
            for name in set(modvars.keys()) - names:
                del modvars[name]

        objects = pickle.loads(self.objects_pickle)

        for k, v in self.variables.items():
            mod, field = k
            setattr(mod, field, objects[v])


backup = None

################################################################################
# Import
################################################################################


def plog(depth, event, *args):
    """
    Empty version of renpy.plog that is replaced by the real implementation
    in import_all.
    """
    return


def import_all():
    import renpy  # @UnresolvedImport

    import renpy.arguments  # @UnresolvedImport
    import renpy.config
    import renpy.log
    import renpy.display
    import renpy.debug

    # Should probably be early, as we will add it as a base to serialized things.
    import renpy.object

    import renpy.game
    import renpy.preferences
    import renpy.loader
    import renpy.pyanalysis

    import renpy.ast
    import renpy.atl
    import renpy.curry
    import renpy.color
    import renpy.easy
    import renpy.execution
    import renpy.loadsave
    import renpy.savelocation  # @UnresolvedImport
    import renpy.persistent
    import renpy.scriptedit
    import renpy.parser
    import renpy.performance
    import renpy.pydict  # type: ignore[reportMissingImports]
    import renpy.python
    import renpy.script
    import renpy.statements
    import renpy.util

    global plog
    plog = renpy.performance.log  # type: ignore[reportAssignmentType]

    import renpy.styledata  # @UnresolvedImport
    import renpy.style  # type: ignore[reportMissingImports]
    renpy.styledata.import_style_functions()

    sys.modules[pystr("renpy.styleclass")] = renpy.style  # noqa: F405

    import renpy.substitutions
    import renpy.translation
    import renpy.translation.scanstrings
    import renpy.translation.generation
    import renpy.translation.dialogue
    import renpy.translation.extract
    import renpy.translation.merge

    import renpy.display  # @UnresolvedImport @Reimport
    import renpy.display.presplash
    import renpy.display.pgrender
    import renpy.display.scale
    import renpy.display.module
    import renpy.display.render  # @UnresolvedImport # type: ignore[reportMissingImports]
    import renpy.display.core  # @UnresolvedImport

    import renpy.text
    import renpy.text.ftfont  # type: ignore[reportMissingImports]
    import renpy.text.font
    import renpy.text.textsupport  # type: ignore[reportMissingImports]
    import renpy.text.texwrap  # type: ignore[reportMissingImports]
    import renpy.text.text
    import renpy.text.extras

    sys.modules[pystr("renpy.display.text")] = renpy.text.text  # noqa: F405

    import renpy.gl
    import renpy.gl2

    import renpy.display.layout
    import renpy.display.viewport
    import renpy.display.transform
    import renpy.display.motion  # @UnresolvedImport
    import renpy.display.behavior  # @UnresolvedImport
    import renpy.display.transition  # @UnresolvedImport
    import renpy.display.movetransition  # @UnresolvedImport
    import renpy.display.im
    import renpy.display.imagelike
    import renpy.display.image  # @UnresolvedImport
    import renpy.display.video
    import renpy.display.focus
    import renpy.display.anim
    import renpy.display.particle
    import renpy.display.joystick
    import renpy.display.controller
    import renpy.display.minigame
    import renpy.display.screen
    import renpy.display.dragdrop
    import renpy.display.imagemap
    import renpy.display.predict
    import renpy.display.emulator
    import renpy.display.tts
    import renpy.display.gesture
    import renpy.display.model
    import renpy.display.error

    # For Windows, renpy.audio.audio must come after renpy.display.module.
    import renpy.audio
    import renpy.audio.audio
    import renpy.audio.music
    import renpy.audio.sound

    import renpy.ui
    import renpy.screenlang

    import renpy.sl2
    import renpy.sl2.slast
    import renpy.sl2.slparser
    import renpy.sl2.slproperties
    import renpy.sl2.sldisplayables

    import renpy.lint
    import renpy.warp
    import renpy.editor
    import renpy.memory

    import renpy.exports
    import renpy.character  # @UnresolvedImport

    import renpy.add_from
    import renpy.dump

    import renpy.gl2.gl2draw  # type: ignore[reportMissingImports]
    import renpy.gl2.gl2mesh  # type: ignore[reportMissingImports]
    import renpy.gl2.gl2model  # type: ignore[reportMissingImports]
    import renpy.gl2.gl2polygon  # type: ignore[reportMissingImports]
    import renpy.gl2.gl2shader  # type: ignore[reportMissingImports]
    import renpy.gl2.gl2texture  # type: ignore[reportMissingImports]
    import renpy.gl2.live2d

    import renpy.minstore  # @UnresolvedImport
    import renpy.defaultstore  # @UnresolvedImport

    import renpy.test
    import renpy.test.testmouse
    import renpy.test.testfocus
    import renpy.test.testkey
    import renpy.test.testast
    import renpy.test.testparser
    import renpy.test.testexecution

    import renpy.main

    global backup
    if not mobile:
        backup = Backup()

    post_import()


def post_import():
    """
    Called after import or reload to finish initialization of stores and modules.
    """
    import renpy  # @UnresolvedImport
    import renpy.defaultstore
    import renpy.exports
    import renpy.python
    import renpy.store  # type: ignore[reportMissingImports]

    renpy.python.create_store("store")

    renpy.store = sys.modules["store"]
    setattr(renpy.exports, "store", renpy.store)
    sys.modules["renpy.store"] = sys.modules["store"]

    import subprocess
    sys.modules[pystr("renpy.subprocess")] = subprocess  # noqa: F405

    for k, v in renpy.defaultstore.__dict__.items():
        if k not in vars(renpy.store):
            setattr(renpy.store, k, v)

    setattr(renpy.store, "eval", renpy.defaultstore.eval)

    for k, v in globals().items():
        if k not in vars(renpy.exports):
            setattr(renpy.exports, k, v)


def issubmodule(sub, module):
    return sub == module or sub.startswith(module + ".")


def reload_all():
    """
    Resets all modules to the state they were in right after import_all
    returned.
    """
    if mobile:
        raise Exception("Reloading is not supported on mobile platforms.")

    import renpy
    import renpy.audio
    import renpy.audio.audio