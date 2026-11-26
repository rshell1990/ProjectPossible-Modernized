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

    if "OutlineEvent" not in globals():
        class OutlineEvent(object):
            pass

    # Keep Ren'Py's button and focus bindings while disabling hide_windows.
    config.keymap = config.default_keymap.copy()
    config.keymap["hide_windows"] = []

    def _migrate_legacy_character_positions():
        if "Shego2" not in globals() and "characterclass" in globals():
            globals()["Shego2"] = characterclass(
                "Shego2",
                hint="Number not unlocked",
                mood="A nice version of Shego.. How adroable. ",
                desc=(
                    "A controlled version of Shego who is not quite as evil"
                ),
                baseEyes=1,
                baseMouth=5,
                baseArms="a",
            )

        for key, value in list(globals().items()):
            if key.startswith("xPos") and not key.endswith("Original"):
                globals().setdefault(key + "Original", value)

        changed = list(globals().get("changedGirllist", []))
        migrated = []

        for name in changed:
            short_name = str(name).lower()
            original_key = "xPos%sOriginal" % short_name
            position_key = "xPos%s" % short_name

            if original_key in globals():
                migrated.append(name)
            elif position_key in globals():
                migrated.append(name)

        globals()["changedGirllist"] = migrated

    config.after_load_callbacks.append(_migrate_legacy_character_positions)
