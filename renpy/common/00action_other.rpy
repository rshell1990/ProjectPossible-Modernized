# Modernized custom/extended Ren'Py Actions, Tooltips, and Notify screen (Ren'Py 7 / 8+)
# Note: Most of these Action classes and `screen notify` are built into Ren'Py.
# Keep custom names or only load overrides intentionally to avoid shadowing built-ins.

define config.enter_replay_transition = None
define config.exit_replay_transition = None

init -1500 python:

    @renpy.pure
    class InvertSelected(Action, DictEquality):
        """Inverts the selection state of `action` while delegating other methods."""

        def __init__(self, action):
            self.action = action
            self.alt = getattr(action, "alt", None)

        def __call__(self):
            return self.action()

        def get_selected(self):
            return not self.action.get_selected()

        def get_sensitive(self):
            return self.action.get_sensitive()

        def periodic(self, st):
            return self.action.periodic(st)

        def predict(self):
            self.action.predict()


    @renpy.pure
    def If(expression, true=None, false=None):
        """Returns `true` if `expression` is truthy, otherwise `false`."""
        return true if expression else false


    @renpy.pure
    class SelectedIf(Action, DictEquality):
        """Uses `expression` (or an `Action`) to determine a button's selected state."""

        def __init__(self, expression):
            self.expression = expression

            if isinstance(expression, Action):
                for attr in ("get_selected", "get_sensitive", "get_tooltip", "periodic", "unhovered"):
                    if hasattr(expression, attr):
                        setattr(self, attr, getattr(expression, attr))

        def __call__(self):
            if isinstance(self.expression, Action):
                return self.expression()
            return None

        def get_selected(self):
            return self.expression


    @renpy.pure
    class SensitiveIf(Action, DictEquality):
        """Uses `expression` (or an `Action`) to determine a button's sensitive state."""

        def __init__(self, expression):
            self.expression = expression

            if isinstance(expression, Action):
                for attr in ("get_selected", "get_sensitive", "get_tooltip", "periodic", "unhovered"):
                    if hasattr(expression, attr):
                        setattr(self, attr, getattr(expression, attr))

        def __call__(self):
            if isinstance(self.expression, Action):
                return self.expression()
            return None

        def get_sensitive(self):
            return self.expression


    @renpy.pure
    class Screenshot(Action, DictEquality):
        """Takes a screenshot."""

        def __call__(self):
            _screenshot()


    @renpy.pure
    class HideInterface(Action, DictEquality):
        """Hides the interface until the player clicks."""

        def __call__(self):
            renpy.call_in_new_context("_hide_windows")


    @renpy.pure
    class OpenURL(Action, DictEquality):
        """Opens `url` in a web browser."""

        def __init__(self, url):
            self.url = url

        def __call__(self):
            try:
                import webbrowser
                webbrowser.open_new(self.url)
            except Exception:
                pass


    class With(Action, DictEquality):
        """Applies `transition` and restarts the interaction."""

        def __init__(self, transition):
            self.transition = transition

        def __call__(self):
            renpy.transition(self.transition)
            renpy.restart_interaction()


    @renpy.pure
    class Notify(Action, DictEquality):
        """Displays `message` via `renpy.notify`."""

        def __init__(self, message):
            self.message = message

        def predict(self):
            renpy.predict_screen("notify")

        def __call__(self):
            renpy.notify(self.message)


    @renpy.pure
    class Rollback(Action, DictEquality):
        """Performs a rollback when possible."""

        def __init__(self, *args, **kwargs):
            self.args = args
            kwargs.setdefault("force", "menu")
            self.kwargs = kwargs

        def __call__(self):
            renpy.rollback(*self.args, **self.kwargs)

        def get_sensitive(self):
            return renpy.can_rollback()


    class RollbackToIdentifier(Action, DictEquality):
        """Rolls back to a given checkpoint identifier when available."""

        def __init__(self, identifier):
            self.identifier = identifier

        def __call__(self):
            checkpoints = renpy.get_identifier_checkpoints(self.identifier)
            if checkpoints is not None:
                renpy.rollback(checkpoints=checkpoints, force="menu")

        def get_sensitive(self):
            return renpy.get_identifier_checkpoints(self.identifier) is not None


    @renpy.pure
    class RestartStatement(Action, DictEquality):
        """Rolls back to before the current statement and re-runs it."""

        def __call__(self):
            renpy.rollback(force=True, checkpoints=0, defer=True)


    @renpy.pure
    class RollForward(Action, DictEquality):
        """Performs a rollforward when possible."""

        def __call__(self):
            return renpy.exports.roll_forward_core()

        def get_sensitive(self):
            return renpy.roll_forward_info() is not None


    def GetTooltip(screen=None):
        """Returns the tooltip of the currently focused displayable, or None."""
        return renpy.display.focus.get_tooltip(screen)


    @renpy.pure
    class Language(Action, DictEquality):
        """Switches the active translation language."""

        alt = _("Language [text]")

        def __init__(self, language):
            self.language = language

        def __call__(self):
            renpy.change_language(self.language)

        def get_selected(self):
            return _preferences.language == self.language

        def get_sensitive(self):
            if self.language is None:
                return True
            return self.language in renpy.known_languages()


    @renpy.pure
    class Replay(Action, DictEquality):
        """Starts `label` as a replay with optional `scope` and `locked` override."""

        def __init__(self, label, scope=None, locked=None):
            self.label = label
            self.scope = {} if scope is None else dict(scope)
            self.locked = locked

        def __call__(self):
            if not self.get_sensitive():
                return

            if config.enter_replay_transition:
                renpy.transition(config.enter_replay_transition)

            renpy.call_replay(self.label, self.scope)

            if config.exit_replay_transition:
                renpy.transition(config.exit_replay_transition)

        def get_sensitive(self):
            if self.locked is not None:
                return not self.locked
            return renpy.seen_label(self.label)


    @renpy.pure
    class EndReplay(Action, DictEquality):
        """Ends the current replay, optionally prompting via the `yesno` screen."""

        def __init__(self, confirm=True):
            self.confirm = confirm

        def __call__(self):
            if not self.get_sensitive():
                return

            if self.confirm:
                renpy.show_screen(
                    "yesno",
                    message=layout.END_REPLAY,
                    yes_action=[Hide("yesno"), EndReplay(False)],
                    no_action=Hide("yesno"),
                )
                renpy.restart_interaction()
            else:
                renpy.end_replay()

        def get_sensitive(self):
            return _in_replay


    @renpy.pure
    class MouseMove(Action, DictEquality):
        """Moves the mouse pointer to `(x, y)` over `duration` seconds."""

        def __init__(self, x, y, duration=0):
            self.x = x
            self.y = y
            self.duration = duration

        def __call__(self):
            if _preferences.mouse_move:
                renpy.set_mouse_pos(self.x, self.y, self.duration)


    @renpy.pure
    class QueueEvent(Action, DictEquality):
        """Queues an input event via `renpy.queue_event`."""

        def __init__(self, event, up=False):
            self.event = event
            self.up = up

        def __call__(self):
            renpy.queue_event(self.event, up=self.up)


    class Function(Action, DictEquality):
        """Calls `callable` with `args` and `kwargs`, optionally restarting interaction."""

        update_screens = True

        def __init__(self, callable, *args, **kwargs):
            self.callable = callable
            self.args = args
            self.update_screens = kwargs.pop("_update_screens", True)
            self.kwargs = kwargs

        def __call__(self):
            rv = self.callable(*self.args, **self.kwargs)
            if self.update_screens:
                renpy.restart_interaction()
            return rv


    @renpy.pure
    class Confirm(Action, DictEquality):
        """Prompts via `yesno(message, yes_action, no_action)` before running `yes`."""

        def __init__(self, prompt, yes, no=None, confirm_selected=False):
            self.prompt = prompt
            self.yes = yes
            self.no = no
            self.confirm_selected = confirm_selected

        def __call__(self):
            if self.get_selected() and not self.confirm_selected:
                return renpy.run(self.yes)

            yes_list = [Hide("yesno"), self.yes] if self.yes is not None else [Hide("yesno")]
            no_list = [Hide("yesno"), self.no] if self.no is not None else [Hide("yesno")]

            renpy.show_screen(
                "yesno",
                message=self.prompt,
                yes_action=yes_list,
                no_action=no_list,
            )
            renpy.restart_interaction()

        def get_sensitive(self):
            if self.yes is None:
                return False
            return renpy.is_sensitive(self.yes)

        def get_selected(self):
            return renpy.is_selected(self.yes)

        def get_tooltip(self):
            return renpy.display.behavior.get_tooltip(self.yes)


    @renpy.pure
    class Scroll(Action, DictEquality):
        """Scrolls a `bar`, `viewport`, or `vpgrid` by widget `id`."""

        def __init__(self, id, direction, amount="step"):
            self.id = id
            self.direction = direction
            self.amount = amount

        def __call__(self):
            widget = renpy.get_widget(None, self.id)
            if widget is None:
                raise Exception("There is no displayable with the id {}.".format(self.id))

            if self.direction == "increase":
                delta = 1
                adjustment = widget.adjustment
            elif self.direction == "decrease":
                delta = -1
                adjustment = widget.adjustment
            elif self.direction == "horizontal increase":
                delta = 1
                adjustment = widget.xadjustment
            elif self.direction == "horizontal decrease":
                delta = -1
                adjustment = widget.xadjustment
            elif self.direction == "vertical increase":
                delta = 1
                adjustment = widget.yadjustment
            elif self.direction == "vertical decrease":
                delta = -1
                adjustment = widget.yadjustment
            else:
                raise Exception("Unknown scroll direction: {}".format(self.direction))

            if self.amount == "step":
                adjustment.change(adjustment.value + delta * adjustment.step)
            elif self.amount == "page":
                adjustment.change(adjustment.value + delta * adjustment.page)
            else:
                adjustment.change(adjustment.value + delta * self.amount)


init -1500:

    transform _notify_transform:
        xalign 0.02
        yalign 0.015

        on show:
            alpha 0.0
            linear 0.25 alpha 1.0
        on hide:
            linear 0.5 alpha 0.0

    screen notify:
        zorder 100

        text "[message!tq]" at _notify_transform

        timer 3.25 action Hide("notify")