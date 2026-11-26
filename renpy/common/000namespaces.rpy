python early hide:

    class _ObjectNamespace(object):
        pure = True
        allow_child_namespaces = False
        repeat_at_default_time = False

        def __init__(self, nso, name):
            self.nso = nso
            self.name = name

        def set(self, name, value):
            setattr(self.nso, name, value)

        def set_default(self, name, value):
            raise Exception("The default statement can not be used with the {} namespace.".format(self.name))

        def get(self, name):
            return getattr(self.nso, name)

    class _PersistentNamespace(object):
        pure = False
        allow_child_namespaces = False
        repeat_at_default_time = True

        def set(self, name, value):
            if getattr(persistent, name) is None:
                setattr(persistent, name, value)

        def set_default(self, name, value):
            if getattr(persistent, name) is None:
                setattr(persistent, name, value)

        def get(self, name):
            if config.developer:
                raise Exception("Using define with the persistent namespace is obsolete - use `default.persistent = ...` instead. Updating persistent variables with define is not supported.")

            return getattr(persistent, name)

    class _ErrorNamespace(object):
        pure = False
        allow_child_namespaces = False
        repeat_at_default_time = False

        def __init__(self, name):
            self.name = name

        def set(self, name, value):
            raise Exception("The define statement can not be used with the {} namespace.".format(self.name))

        def set_default(self, name, value):
            raise Exception("The default statement can not be used with the {} namespace.".format(self.name))

        def get(self, name):
            raise Exception("The default and define statements can not be used with the {} namespace.".format(self.name))

    class _PreferencesNamespace(object):
        pure = False
        allow_child_namespaces = False
        repeat_at_default_time = True

        def set(self, name, value):
            raise Exception("The define statement can not be used with the preferences namespace.")

        def set_default(self, name, value):

            undefined = object()

            if not isinstance(persistent._preference_default, dict):
                persistent._preference_default = { }

            old_default = persistent._preference_default.get(name, undefined)

            if old_default != value:
                setattr(_preferences, name, value)
                persistent._preference_default[name] = value

            default_field = "default_" + name

            # This ensures we don't conflict with the old way of doing
            # things.
            try:
                has_default_field = hasattr(config, default_field)
            except Exception:
                has_default_field = False

            if has_default_field:
                setattr(config, default_field, value)

        def get(self, name):
            raise Exception("The define statement can not be used with the preferences namespace.")

    class _VolumeNamespace(object):
        pure = False
        allow_child_namespaces = False
        repeat_at_default_time = True

        def set(self, name, value):
            raise Exception("The define statement can not be used with the preferences namespace.")

        def set_default(self, name, value):

            undefined = object()

            if not isinstance(persistent._preference_default, dict):
                persistent._preference_default = { }

            if not "volume" in persistent._preference_default:
                persistent._preference_default["volume"] = { }

            old_default = persistent._preference_default["volume"].get(name, undefined)

            if old_default != value:
                _preferences.set_volume(name, _vol(value))
                persistent._preference_default["volume"][name] = value

            default_field = "default_" + name + "_volume"

            # This ensures we don't conflict with the old way of doing
            # things.
            try:
                has_default_field = hasattr(config, default_field)
            except Exception:
                has_default_field = False

            if has_default_field:
                setattr(config, default_field, value)

        def get(self, name):
            raise Exception("The define statement can not be used with the preferences namespace.")

    # Variables in GUI that have been set using default.
    gui._defaults = set()

    class _GuiNamespace(object):
        pure = True
        allow_child_namespaces = True
        repeat_at_default_time = False

        def set(self, name, value):
            setattr(gui, name, value)

        def set_default(self, name, value):
            setattr(gui, name, value)
            renpy.mark_changed("gui", name)
            gui._defaults.add(name)

        def get(self, name):
            return getattr(gui, name)

    config.special_namespaces["store.config"] = _ObjectNamespace(config, "config")
    config.special_namespaces["store.persistent"] = _PersistentNamespace()
    config.special_namespaces["store.preferences"] =  _PreferencesNamespace()
    config.special_namespaces["store.preferences.volume"] =  _VolumeNamespace()
    config.special_namespaces["store.gui"] = _GuiNamespace()
    config.special_namespaces["store.renpy"] = _ErrorNamespace("renpy")
