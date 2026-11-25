init 100 python:
    import builtins

    class _LegacyFile:
        def __new__(cls, name=None, mode="r", buffering=-1):
            if name is None:
                return object.__new__(cls)

            if "U" in mode:
                mode = mode.replace("U", "") or "r"
                if "b" not in mode:
                    mode += "b"

            return open(name, mode, buffering)

    # Python 2 pickles resolve "file" as a type when using NEWOBJ.
    builtins.file = _LegacyFile

    # Keep Ren'Py's button and focus bindings while disabling hide_windows.
    config.keymap = config.default_keymap.copy()
    config.keymap["hide_windows"] = []
