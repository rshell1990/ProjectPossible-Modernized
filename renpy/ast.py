from __future__ import division, absolute_import, with_statement, print_function, unicode_literals
from renpy.compat import *  # noqa: F401,F403

import random
from typing import Any, Callable, Dict, List, Optional, Tuple, cast

import renpy.ast
import renpy.atl
import renpy.config
import renpy.display
import renpy.display.layout
import renpy.display.matrix  # type: ignore[reportMissingImports]
import renpy.display.motion
import renpy.display.predict
import renpy.easy
import renpy.game
import renpy.gl2
import renpy.gl2.gl2mesh2  # type: ignore[reportMissingImports]
import renpy.gl2.gl2mesh3  # type: ignore[reportMissingImports]
import renpy.object
import renpy.pyanalysis
import renpy.python
import renpy.store  # type: ignore[reportMissingImports]


def compiling(loc: Any) -> None:
    file, number = loc  # @ReservedAssignment
    renpy.game.exception_info = "Compiling ATL code at %s:%d" % (file, number)


def executing(loc: Any) -> None:
    file, number = loc  # @ReservedAssignment
    renpy.game.exception_info = "Executing ATL code at %s:%d" % (file, number)


# A map from the name of a time warp function to the function itself.
warpers: Dict[str, Callable[[float], float]] = {}


def atl_warper(f: Callable[[float], float]) -> Callable[[float], float]:
    name = f.__name__
    warpers[name] = f
    return f


# The pause warper is used internally when no other warper is specified.
@atl_warper
def pause(t: float) -> float:
    if t < 1.0:
        return 0.0
    return 1.0


@atl_warper
def instant(t: float) -> float:
    return 1.0


position = renpy.object.Sentinel("position")


def any_object(x: Any) -> Any:
    return x


def bool_or_none(x: Any) -> Optional[bool]:
    if x is None:
        return None
    return bool(x)


def float_or_none(x: Any) -> Optional[float]:
    if x is None:
        return None
    return float(x)


def matrix(x: Any) -> Any:
    if x is None:
        return None
    if callable(x):
        return x
    return renpy.display.matrix.Matrix(x)


def mesh(x: Any) -> Any:
    if isinstance(x, (renpy.gl2.gl2mesh2.Mesh2, renpy.gl2.gl2mesh3.Mesh3, tuple)):
        return x
    return bool(x)


# A dictionary giving property names and the corresponding default
# values. This is massively added to by renpy.display.transform.
PROPERTIES: Dict[str, Callable[[Any], Any]] = {}


def correct_type(v: Any, b: Any, ty: Any) -> Any:
    """
    Corrects the type of v to match ty. b is used to inform the match.
    """
    if ty is position:
        if v is None:
            return None
        return type(b)(v)
    return ty(v)


def interpolate(t: float, a: Any, b: Any, prop_type: Any) -> Any:  # @ReservedAssignment
    """
    Linearly interpolate the arguments.
    """
    # Deal with booleans, nones, etc.
    if b is None or isinstance(b, (bool, basestring, renpy.display.matrix.Matrix)):  # noqa: F405
        return b if t >= 1.0 else a

    # Recurse into tuples.
    if isinstance(b, tuple):
        if a is None:
            a = [None] * len(b)

        type_tuple = prop_type if isinstance(prop_type, tuple) else (prop_type,) * len(b)
        return tuple(interpolate(t, i, j, ty) for i, j, ty in zip(a, b, type_tuple))

    # If something is callable, call it and return the result.
    if callable(b):
        a_origin = getattr(a, "origin", None)
        rv = b(a_origin, t)
        if rv is not None:
            setattr(rv, "origin", b)
        return rv

    # Interpolate everything else.
    if a is None:
        a = 0

    return correct_type(a + t * (b - a), b, prop_type)


# Interpolate the value of a spline. This code is based on Aenakume's code,
# from 00splines.rpy.
def interpolate_spline(t: float, spline: Any) -> Any:
    if isinstance(spline[-1], tuple):
        return tuple(interpolate_spline(t, i) for i in zip(*spline))

    if spline[0] is None:
        return spline[-1]

    if len(spline) == 2:
        t_p = 1.0 - t
        rv = t_p * spline[0] + t * spline[-1]

    elif len(spline) == 3:
        t_pp = (1.0 - t) ** 2
        t_p = 2 * t * (1.0 - t)
        t2 = t ** 2
        rv = t_pp * spline[0] + t_p * spline[1] + t2 * spline[2]

    elif len(spline) == 4:
        t_ppp = (1.0 - t) ** 3
        t_pp = 3 * t * (1.0 - t) ** 2
        t_p = 3 * t ** 2 * (1.0 - t)
        t3 = t ** 3
        rv = t_ppp * spline[0] + t_pp * spline[1] + t_p * spline[2] + t3 * spline[3]

    else:
        if t <= 0.0 or t >= 1.0:
            rv = spline[0 if t <= 0.0 else -1]
        else:
            # Catmull-Rom (re-adjust the control points)
            spline_pts = (
                [spline[1], spline[0]]
                + list(spline[2:-2])
                + [spline[-1], spline[-2]]
            )

            inner_spline_count = float(len(spline_pts) - 3)
            sector = int(t // (1.0 / inner_spline_count) + 1)
            t = (t % (1.0 / inner_spline_count)) * inner_spline_count
            rv = get_catmull_rom_value(t, *spline_pts[sector - 1:sector + 3])

    return correct_type(rv, spline[-1], position)


def get_catmull_rom_value(t: float, p_1: Any, p0: Any, p1: Any, p2: Any) -> Any:
    """
    Very basic Catmull-Rom calculation with no alpha or handling
    of multi-dimensional points
    """
    t = float(max(0.0, min(1.0, t)))
    return type(p0)(
        (
            t * ((2 - t) * t - 1) * p_1
            + (t * t * (3 * t - 5) + 2) * p0
            + t * ((4 - 3 * t) * t + 1) * p1
            + (t - 1) * t * t * p2
        )
        / 2
    )


# A list of atl transforms that may need to be compiled.
compile_queue: List[Any] = []


def compile_all() -> None:
    """
    Called after the init phase is finished and transforms are compiled,
    to compile all transforms.
    """
    global compile_queue

    for i in compile_queue:
        atl = getattr(i, "atl", None)
        if atl is not None and getattr(atl, "constant", None) == GLOBAL_CONST:
            i.compile()

    compile_queue = []


# This is the context used when compiling an ATL statement. It stores the
# scopes that are used to evaluate the various expressions in the statement,
# and has a method to do the evaluation and return a result.
class Context(object):

    def __init__(self, context: Any) -> None:
        self.context: Dict[str, Any] = context if context is not None else {}

    def eval(self, expr: Optional[str]) -> Any:  # @ReservedAssignment
        if expr is None:
            return None
        escaped = renpy.python.escape_unicode(expr)
        return eval(escaped, renpy.store.__dict__, self.context)  # @UndefinedVariable

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Context):
            return False
        return self.context == other.context

    def __ne__(self, other: object) -> bool:
        return not (self == other)


# This is intended to be subclassed by ATLTransform. It takes care of
# managing ATL execution, which allows ATLTransform itself to not care
# much about the contents of this file.
class ATLTransformBase(renpy.object.Object):

    # Compatibility with older saves.
    parameters: Any = renpy.ast.ParameterInfo([], [], None, None)
    parent_transform: Optional[Any] = None
    atl_st_offset: Optional[float] = 0.0

    # The block, as first compiled for prediction.
    predict_block: Any = None

    child: Any = None
    st: float = 0.0
    at: float = 0.0
    st_offset: float = 0.0
    at_offset: float = 0.0

    nosave = ["parent_transform"]

    def __init__(self, atl: Any, context: Any, parameters: Any) -> None:
        if parameters is None:
            parameters = ATLTransformBase.parameters

        self.parameters = parameters
        self.atl = atl
        self.context = Context(context)
        self.block: Any = None
        self.predict_block = None
        self.properties: Optional[List[Tuple[str, Any]]] = None
        self.atl_state: Any = None
        self.done: bool = False
        self.transform_event: Optional[str] = None
        self.last_transform_event: Optional[str] = None
        self.last_child_transform_event: Optional[str] = None
        self.raw_child: Any = None
        self.parent_transform = None

        if renpy.config.atl_start_on_show:
            self.atl_st_offset = None
        else:
            self.atl_st_offset = 0.0

        game_ctx = renpy.game.context()
        if game_ctx is not None and getattr(game_ctx, "init_phase", False):
            compile_queue.append(self)

    def _handles_event(self, event: str) -> bool:
        if (event == "replaced") and (self.atl_state is None):
            return True

        if (self.block is not None) and self.block._handles_event(event):
            return True

        if self.child is None:
            return False

        return bool(self.child._handles_event(event))

    def get_block(self) -> Any:
        """
        Returns the compiled block to use.
        """
        if self.block:
            return self.block
        if self.predict_block and renpy.display.predict.predicting:
            return self.predict_block
        return None

    def take_execution_state(self, t: Any) -> None:
        """
        Updates self to begin executing from the same point as t. This
        requires that t.atl is self.atl.
        """
        parent_take_state = getattr(super(ATLTransformBase, self), "take_execution_state", None)
        if callable(parent_take_state):
            parent_take_state(t)

        self.atl_st_offset = None
        self.atl_state = None

        if self is t:
            return
        if not isinstance(t, ATLTransformBase):
            return
        if t.atl is not self.atl:
            return

        # Important to do it this way, so we use __eq__. The exception handling
        # optimistically assumes that uncomparable objects are the same.
        try:
            if not (t.context == self.context):
                return
        except Exception:
            pass

        self.done = t.done
        self.block = t.block
        self.atl_state = t.atl_state
        self.transform_event = t.transform_event
        self.last_transform_event = t.last_transform_event
        self.last_child_transform_event = t.last_child_transform_event

        self.st = t.st
        self.at = t.at
        self.st_offset = t.st_offset
        self.at_offset = t.at_offset
        self.atl_st_offset = t.atl_st_offset

        if self.child is renpy.display.motion.null:
            t_child = getattr(t, "child", None)
            if t_child is not None and getattr(t_child, "_duplicatable", False):
                self.child = t_child._duplicate(None)
            else:
                self.child = t_child

            self.raw_child = getattr(t, "raw_child", None)

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        _args = kwargs.pop("_args", None)
        context: Dict[str, Any] = self.context.context.copy()

        for k, v in self.parameters.parameters:
            if v is not None:
                context[k] = renpy.python.py_eval(v)

        positional: List[str] = list(self.parameters.positional)
        args_list: List[Any] = list(args)
        child: Any = None

        if not positional and args_list:
            child = args_list.pop(0)

        while positional and args_list:
            name = positional.pop(0)
            value = args_list.pop(0)

            if name in kwargs:
                raise Exception("Parameter %r is used as both a positional and keyword argument to a transition." % name)

            context[name] = value

        if args_list:
            raise Exception("Too many arguments passed to ATL transform.")

        for k, v in kwargs.items():
            if k in positional:
                positional.remove(k)
                context[k] = v
            elif k in context:
                context[k] = v
            elif k == "child":
                child = v
            else:
                raise Exception("Parameter %r is not known by ATL Transform." % k)

        if child is None:
            child = self.child

        parameters = renpy.ast.ParameterInfo({}, positional, None, None)

        rv: Any = renpy.display.motion.ATLTransform(
            atl=self.atl,
            child=child,
            style=getattr(self, "style_arg", None),
            context=context,
            parameters=parameters,
            _args=_args,
        )

        rv.parent_transform = self
        take_state_fn = getattr(rv, "take_state", None)
        if callable(take_state_fn):
            take_state_fn(self)

        return rv

    def compile(self) -> Any:  # @ReservedAssignment
        """
        Compiles the ATL code into a block. As necessary, updates the
        properties.
        """
        constant = (self.atl.constant == GLOBAL_CONST)

        if not constant:
            for p in self.parameters.positional:
                if p not in self.context.context:
                    raise Exception(
                        "Cannot compile ATL Transform at %s:%d, as it's missing positional parameter %s."
                        % (self.atl.loc[0], self.atl.loc[1], p)
                    )

        parent = self.parent_transform
        if constant and parent is not None:
            parent_block = getattr(parent, "block", None)
            if parent_block is not None:
                self.block = parent_block
                self.properties = getattr(parent, "properties", None)
                self.parent_transform = None
                return self.block

        old_exception_info = renpy.game.exception_info
        block = self.atl.compile(self.context)

        if block is not None and all(
            isinstance(statement, Interpolation) and statement.duration == 0
            for statement in block.statements
        ):
            props: List[Tuple[str, Any]] = []
            for interp in block.statements:
                if isinstance(interp, Interpolation):
                    props.extend(interp.properties)
            self.properties = props

        if not constant and renpy.display.predict.predicting:
            self.predict_block = block
        else:
            self.block = block
            self.predict_block = None

        renpy.game.exception_info = old_exception_info

        parent = self.parent_transform
        if constant and parent is not None:
            parent.block = self.block
            parent.properties = self.properties
            self.parent_transform = None

        return block

    def execute(self, trans: Any, st: float, at: float) -> Optional[float]:
        if self.done:
            return None

        block = self.get_block()
        if block is None:
            block = self.compile()

        events: List[Optional[str]] = []

        if trans is not None:
            if getattr(trans, "hide_request", False):
                self.transform_event = "hide"

            if getattr(trans, "replaced_request", False):
                self.transform_event = "replaced"

        if renpy.config.atl_multiple_events:
            if self.transform_event != self.last_transform_event:
                events.append(self.transform_event)
                self.last_transform_event = self.transform_event

        child = self.child
        if child is not None:
            child_event = getattr(child, "transform_event", None)
            if child_event != self.last_child_transform_event:
                self.last_child_transform_event = child_event

                if child_event is not None:
                    self.transform_event = child_event

        if self.transform_event != self.last_transform_event:
            events.append(self.transform_event)
            self.last_transform_event = self.transform_event

        if self.transform_event in renpy.config.repeat_transform_events:
            self.transform_event = None
            self.last_transform_event = None

        old_exception_info = renpy.game.exception_info

        if (self.atl_st_offset is None) or (st - self.atl_st_offset) < 0:
            self.atl_st_offset = st

        if getattr(self.atl, "animation", False):
            timebase = at
        else:
            offset = self.atl_st_offset if self.atl_st_offset is not None else 0.0
            timebase = st - offset

        pause_val: Optional[float] = None
        if block is not None:
            _action, arg, pause_val = block.execute(trans, timebase, self.atl_state, events)
        else:
            _action, arg = "done", None

        renpy.game.exception_info = old_exception_info

        if _action == "continue" and not renpy.display.predict.predicting:
            self.atl_state = arg
        else:
            self.done = True

        return pause_val

    def predict_one(self) -> None:
        self.atl.predict(self.context)

    def visit(self) -> List[Any]:
        block = self.get_block()

        if block is None:
            block = self.compile()

        children = getattr(self, "children", None) or []
        block_visits = block.visit() if block is not None else []
        return list(children) + list(block_visits)


# This is used in mark_constant to analyze expressions for constness.
_raw_is_constant_expr = renpy.pyanalysis.Analysis().is_constant_expr
GLOBAL_CONST: int = renpy.pyanalysis.GLOBAL_CONST


def is_constant_expr(expr: Optional[str]) -> int:
    if expr is None:
        return GLOBAL_CONST
    result = _raw_is_constant_expr(expr)
    return int(result) if result is not None else 0


def _min_const(current: int, candidate: Optional[int]) -> int:
    if candidate is None:
        return current
    return min(current, candidate)


# The base class for raw ATL statements.
class RawStatement(object):

    constant: Optional[int] = None

    def __init__(self, loc: Any) -> None:
        super(RawStatement, self).__init__()
        self.loc = loc

    def compile(self, ctx: Context) -> Any:  # @ReservedAssignment
        raise Exception("Compile not implemented.")

    def predict(self, ctx: Context) -> None:
        return

    def mark_constant(self) -> None:
        """
        Sets self.constant to true if all expressions used in this statement
        and its children are constant.
        """
        self.constant = 0


# The base class for compiled ATL Statements.
class Statement(renpy.object.Object):

    def __init__(self, loc: Any) -> None:
        super(Statement, self).__init__()
        self.loc = loc

    def execute(self, trans: Any, st: Any, state: Any, events: Any) -> Any:
        raise Exception("Not implemented.")

    def visit(self) -> List[Any]:
        return []

    def _handles_event(self, event: str) -> bool:
        return False


# This represents a Raw ATL block.
class RawBlock(RawStatement):

    animation: bool = False

    def __init__(self, loc: Any, statements: List[Any], animation: bool) -> None:
        super(RawBlock, self).__init__(loc)
        self.statements: List[Any] = statements
        self.animation = animation

    def compile(self, ctx: Context) -> Statement:  # @ReservedAssignment
        compiling(self.loc)
        compiled_stmts: List[Any] = [i.compile(ctx) for i in self.statements]
        return Block(self.loc, compiled_stmts)

    def predict(self, ctx: Context) -> None:
        for i in self.statements:
            i.predict(ctx)

    def mark_constant(self) -> None:
        constant: int = GLOBAL_CONST
        for i in self.statements:
            i.mark_constant()
            constant = _min_const(constant, i.constant)
        self.constant = constant


# A compiled ATL block.
class Block(Statement):

    def __init__(self, loc: Any, statements: List[Any]) -> None:
        super(Block, self).__init__(loc)
        self.statements: List[Any] = statements
        self.times: List[Tuple[Any, int]] = []

        for i, s in enumerate(statements):
            if isinstance(s, Time):
                self.times.append((s.time, i + 1))

        self.times.sort()

    def _handles_event(self, event: str) -> bool:
        for i in self.statements:
            if i._handles_event(event):
                return True
        return False

    def execute(self, trans: Any, st: Any, state: Any, events: Any) -> Tuple[str, Any, Any]:
        executing(self.loc)

        if state is not None:
            index, start, loop_start, repeats, times, child_state = state
        else:
            index, start, loop_start, repeats, times, child_state = 0, 0, 0, 0, self.times[:], None

        action: str = "continue"
        arg: Any = None
        pause_val: Any = None

        while action == "continue":
            if times:
                time_val, tindex = times[0]
                target = min(time_val, st)
                max_pause: Any = time_val - target
            else:
                target = st
                max_pause = 15

            while True:
                if index >= len(self.statements):
                    return "next", target - start, None

                stmt = self.statements[index]
                action, arg, pause_val = stmt.execute(trans, target - start, child_state, events)

                if action == "continue":
                    if pause_val is None:
                        pause_val = max_pause

                    action, arg, pause_val = (
                        "continue",
                        (index, start, loop_start, repeats, times, arg),
                        min(max_pause, pause_val),
                    )
                    break

                if action == "event":
                    return action, arg, pause_val

                if action == "next":
                    index += 1
                    start = target - arg
                    child_state = None

                elif action == "repeat":
                    count, repeat_arg = arg
                    loop_end = target - repeat_arg
                    duration = loop_end - loop_start

                    if (state is None) and (duration <= 0):
                        raise Exception("ATL appears to be in an infinite loop.")

                    if duration:
                        new_repeats = int((target - loop_start) / duration)
                    else:
                        new_repeats = 0

                    if count is not None:
                        if repeats + new_repeats >= count:
                            new_repeats = count - repeats
                            loop_start += new_repeats * duration
                            return "next", target - loop_start, None

                    repeats += new_repeats
                    loop_start = loop_start + new_repeats * duration
                    start = loop_start
                    index = 0
                    child_state = None

            if times:
                time_val, tindex = times[0]
                if time_val <= target:
                    times.pop(0)
                    index = tindex
                    start = time_val
                    child_state = None
                    continue

            return action, arg, pause_val

    def visit(self) -> List[Any]:
        return [j for i in self.statements for j in i.visit()]


class RawMultipurpose(RawStatement):

    warp_function: Optional[str] = None

    def __init__(self, loc: Any) -> None:
        super(RawMultipurpose, self).__init__(loc)

        self.warper: Optional[str] = None
        self.duration: Optional[str] = None
        self.properties: List[Tuple[str, Any]] = []
        self.expressions: List[Tuple[Any, Any]] = []
        self.splines: List[Tuple[str, List[Any]]] = []
        self.revolution: Optional[str] = None
        self.circles: Optional[str] = "0"

    def add_warper(self, name: Optional[str], duration: Optional[str], warp_function: Optional[str]) -> None:
        self.warper = name
        self.duration = duration
        self.warp_function = warp_function

    def add_property(self, name: str, exprs: Any) -> None:
        self.properties.append((name, exprs))

    def add_expression(self, expr: Any, with_clause: Any) -> None:
        self.expressions.append((expr, with_clause))

    def add_revolution(self, revolution: Optional[str]) -> None:
        self.revolution = revolution

    def add_circles(self, circles: Optional[str]) -> None:
        self.circles = circles

    def add_spline(self, name: str, exprs: List[Any]) -> None:
        self.splines.append((name, exprs))

    def compile(self, ctx: Context) -> Any:  # @ReservedAssignment
        compiling(self.loc)

        if (
            self.warper is None
            and self.warp_function is None
            and not self.properties
            and not self.splines
            and len(self.expressions) == 1
        ):
            expr, withexpr = self.expressions[0]

            child = ctx.eval(expr)
            transition = ctx.eval(withexpr) if withexpr else None

            if isinstance(child, (int, float)):
                return Interpolation(self.loc, "pause", child, [], None, 0, [])

            child_disp = renpy.easy.displayable(child) if child is not None else None

            if isinstance(child_disp, ATLTransformBase):
                child_disp.compile()
                return child_disp.get_block()

            return Child(self.loc, child_disp, transition)

        compiling(self.loc)

        if self.warp_function:
            warper: Any = ctx.eval(self.warp_function)
        else:
            warper = self.warper or "instant"
            if warper not in warpers:
                raise Exception("ATL Warper %s is unknown at runtime." % warper)

        compiled_props: List[Tuple[str, Any]] = []
        for name, expr in self.properties:
            if name not in PROPERTIES:
                raise Exception("ATL Property %s is unknown at runtime." % name)
            value = ctx.eval(expr)
            compiled_props.append((name, value))

        compiled_splines: List[Tuple[str, List[Any]]] = []
        for name, exprs in self.splines:
            if name not in PROPERTIES:
                raise Exception("ATL Property %s is unknown at runtime." % name)
            values = [ctx.eval(i) for i in exprs]
            compiled_splines.append((name, values))

        for expr, _with in self.expressions:
            try:
                value = ctx.eval(expr)
            except Exception:
                raise Exception("Could not evaluate expression %r when compiling ATL." % expr)

            if not isinstance(value, ATLTransformBase):
                raise Exception(
                    "Expression %r is not an ATL transform, and so cannot be included in an ATL interpolation." % expr
                )

            value.compile()

            if value.properties is None:
                raise Exception("ATL transform %r is too complicated to be included in interpolation." % expr)

            compiled_props.extend(value.properties)

        duration: Any = ctx.eval(self.duration) if self.duration is not None else 0
        circles: Any = ctx.eval(self.circles) if self.circles is not None else 0

        return Interpolation(self.loc, warper, duration, compiled_props, self.revolution, circles, compiled_splines)

    def mark_constant(self) -> None:
        constant: int = GLOBAL_CONST

        constant = _min_const(constant, is_constant_expr(self.warp_function))
        constant = _min_const(constant, is_constant_expr(self.duration))
        constant = _min_const(constant, is_constant_expr(self.circles))

        for _name, expr in self.properties:
            constant = _min_const(constant, is_constant_expr(expr))

        for _name, exprs in self.splines:
            for expr in exprs:
                constant = _min_const(constant, is_constant_expr(expr))

        for expr, withexpr in self.expressions:
            constant = _min_const(constant, is_constant_expr(expr))
            constant = _min_const(constant, is_constant_expr(withexpr))

        self.constant = constant

    def predict(self, ctx: Context) -> None:
        for i, _j in self.expressions:
            try:
                evaluated = ctx.eval(i)
            except Exception:
                continue

            if isinstance(evaluated, ATLTransformBase):
                evaluated.atl.predict(ctx)
                return

            try:
                if evaluated is not None:
                    renpy.easy.predict(evaluated)
            except Exception:
                continue


class RawContainsExpr(RawStatement):

    def __init__(self, loc: Any, expr: Optional[str]) -> None:
        super(RawContainsExpr, self).__init__(loc)
        self.expression: Optional[str] = expr

    def compile(self, ctx: Context) -> Statement:  # @ReservedAssignment
        compiling(self.loc)
        child = ctx.eval(self.expression)
        return Child(self.loc, child, None)

    def mark_constant(self) -> None:
        self.constant = is_constant_expr(self.expression)


class RawChild(RawStatement):

    def __init__(self, loc: Any, child: Any) -> None:
        super(RawChild, self).__init__(loc)
        self.children: List[Any] = [child]

    def compile(self, ctx: Context) -> Statement:  # @ReservedAssignment
        children = [
            renpy.display.motion.ATLTransform(i, context=ctx.context)
            for i in self.children
        ]

        box = renpy.display.layout.MultiBox(layout="fixed")
        for i in children:
            box.add(i)

        return Child(self.loc, box, None)

    def mark_constant(self) -> None:
        constant: int = GLOBAL_CONST
        for i in self.children:
            i.mark_constant()
            constant = _min_const(constant, i.constant)
        self.constant = constant


class Child(Statement):

    def __init__(self, loc: Any, child: Any, transition: Any) -> None:
        super(Child, self).__init__(loc)
        self.child = child
        self.transition = transition

    def execute(self, trans: Any, st: Any, state: Any, events: Any) -> Tuple[str, Any, Any]:
        executing(self.loc)

        old_child = getattr(trans, "raw_child", None)
        child = self.child

        if child is not None and getattr(child, "_duplicatable", False):
            child = child._duplicate(getattr(trans, "_args", None))
            if hasattr(child, "_unique"):
                child._unique()

        if (old_child is not None) and (old_child is not renpy.display.motion.null) and (self.transition is not None):
            child = self.transition(old_widget=old_child, new_widget=child)
            if hasattr(child, "_unique"):
                child._unique()

        trans.set_child(child, duplicate=False)
        trans.raw_child = self.child

        return "next", st, None

    def visit(self) -> List[Any]:
        return [self.child] if self.child is not None else []


class Interpolation(Statement):

    def __init__(
        self,
        loc: Any,
        warper: Any,
        duration: Any,
        properties: List[Tuple[str, Any]],
        revolution: Optional[str],
        circles: Any,
        splines: List[Tuple[str, List[Any]]],
    ) -> None:
        super(Interpolation, self).__init__(loc)

        self.warper = warper
        self.duration = duration
        self.properties = properties
        self.splines = splines
        self.revolution = revolution
        self.circles = circles

    def execute(self, trans: Any, st: Any, state: Any, events: Any) -> Tuple[str, Any, Any]:
        executing(self.loc)

        warper_fn: Any = warpers.get(self.warper, self.warper)

        if getattr(trans.atl, "animation", False):
            st_or_at = trans.at
        else:
            st_or_at = trans.st

        if self.warper == "instant":
            first_frame = False
        elif state is not None:
            first_frame = False
        elif (self.duration == 0) and (not self.properties and not self.revolution and not self.splines):
            first_frame = True
        elif getattr(trans, "atl_state", None) is not None:
            first_frame = True
        elif st_or_at == 0:
            first_frame = True
        else:
            first_frame = False

        if self.duration:
            complete: float = float(min(1.0, st / self.duration))
        else:
            complete = 1.0

        if complete < 0.0:
            complete = 0.0
        elif complete > 1.0:
            complete = 1.0

        complete = float(warper_fn(complete)) if callable(warper_fn) else complete

        if state is None:
            newts = renpy.display.motion.TransformState()
            newts.take_state(trans.state)

            has_angle = False

            for k, v in self.properties:
                setattr(newts, k, v)
                if k == "angle":
                    newts.last_angle = v
                    has_angle = True

            linear: Dict[str, Tuple[Any, Any]] = trans.state.diff(newts)
            revolution: Optional[Tuple[Any, Any, Any, Any]] = None
            splines: List[Tuple[str, List[Any]]] = []

            revdir = self.revolution
            circles_val: Any = self.circles or 0

            xaround = getattr(newts, "xaround", None)
            if (revdir or (has_angle and renpy.config.automatic_polar_motion)) and (xaround is not None):
                for prop_name in [
                    "xpos",
                    "ypos",
                    "xanchor",
                    "yanchor",
                    "xaround",
                    "yaround",
                    "xanchoraround",
                    "yanchoraround",
                ]:
                    linear.pop(prop_name, None)

                if revdir is not None:
                    trans.state.xaround = xaround
                    trans.state.yaround = getattr(newts, "yaround", None)
                    trans.state.xanchoraround = getattr(newts, "xanchoraround", None)
                    trans.state.yanchoraround = getattr(newts, "yanchoraround", None)

                    startangle = getattr(trans.state, "angle", None)
                    endangle = getattr(newts, "angle", None)
                    startradius = getattr(trans.state, "radius", None)
                    endradius = getattr(newts, "radius", None)

                    if startangle is not None and endangle is not None:
                        if revdir == "clockwise":
                            if endangle < startangle:
                                startangle -= 360
                            startangle -= circles_val * 360

                        elif revdir == "counterclockwise":
                            if endangle > startangle:
                                startangle += 360
                            startangle += circles_val * 360

                    revolution = (startangle, endangle, startradius, endradius)

                else:
                    last_angle = getattr(trans.state, "last_angle", None)
                    if last_angle is None:
                        last_angle = getattr(trans.state, "angle", None)
                    new_last_angle = getattr(newts, "last_angle", None)
                    revolution = (
                        last_angle,
                        new_last_angle,
                        getattr(trans.state, "radius", None),
                        getattr(newts, "radius", None),
                    )

            for name, values in self.splines:
                splines.append((name, [getattr(trans.state, name, None)] + values))

            state = (linear, revolution, splines)

            for k, v in self.properties:
                if k not in linear:
                    setattr(trans.state, k, v)

        else:
            linear, revolution, splines = state

        for k, (old, new) in linear.items():
            value = interpolate(complete, old, new, PROPERTIES[k])
            setattr(trans.state, k, value)

        if revolution is not None:
            startangle, endangle, startradius, endradius = revolution
            angle = interpolate(complete, startangle, endangle, float)
            trans.state.last_angle = angle
            trans.state.angle = angle
            trans.state.radius = interpolate(complete, startradius, endradius, float)

        for name, values in splines:
            value = interpolate_spline(complete, values)
            setattr(trans.state, name, value)

        if (st >= self.duration) and ((not first_frame) or (not renpy.config.atl_one_frame)):
            return "next", st - self.duration, None

        if not self.properties and not self.revolution and not self.splines:
            return "continue", state, max(0, self.duration - st)

        return "continue", state, 0


class RawRepeat(RawStatement):

    def __init__(self, loc: Any, repeats: Optional[str]) -> None:
        super(RawRepeat, self).__init__(loc)
        self.repeats: Optional[str] = repeats

    def compile(self, ctx: Context) -> Statement:  # @ReservedAssignment
        compiling(self.loc)
        repeats = ctx.eval(self.repeats) if self.repeats is not None else None
        return Repeat(self.loc, repeats)

    def mark_constant(self) -> None:
        self.constant = is_constant_expr(self.repeats)


class Repeat(Statement):

    def __init__(self, loc: Any, repeats: Any) -> None:
        super(Repeat, self).__init__(loc)
        self.repeats = repeats

    def execute(self, trans: Any, st: Any, state: Any, events: Any) -> Tuple[str, Any, Any]:
        return "repeat", (self.repeats, st), 0


class RawParallel(RawStatement):

    def __init__(self, loc: Any, block: Any) -> None:
        super(RawParallel, self).__init__(loc)
        self.blocks: List[Any] = [block]

    def compile(self, ctx: Context) -> Statement:  # @ReservedAssignment
        return Parallel(self.loc, [i.compile(ctx) for i in self.blocks])

    def predict(self, ctx: Context) -> None:
        for i in self.blocks:
            i.predict(ctx)

    def mark_constant(self) -> None:
        constant: int = GLOBAL_CONST
        for i in self.blocks:
            i.mark_constant()
            constant = _min_const(constant, i.constant)
        self.constant = constant


class Parallel(Statement):

    def __init__(self, loc: Any, blocks: List[Any]) -> None:
        super(Parallel, self).__init__(loc)
        self.blocks: List[Any] = blocks

    def _handles_event(self, event: str) -> bool:
        for i in self.blocks:
            if i._handles_event(event):
                return True
        return False

    def execute(self, trans: Any, st: Any, state: Any, events: Any) -> Tuple[str, Any, Any]:
        executing(self.loc)

        if state is None:
            state = [(i, None) for i in self.blocks]

        left: List[Any] = []
        pauses: List[Any] = []
        newstate: List[Tuple[Any, Any]] = []

        for i, istate in state:
            action, arg, pause_val = i.execute(trans, st, istate, events)

            if pause_val is not None:
                pauses.append(pause_val)

            if action == "continue":
                newstate.append((i, arg))
            elif action == "next":
                left.append(arg)
            elif action == "event":
                return action, arg, pause_val

        if newstate:
            return "continue", newstate, min(pauses) if pauses else None
        return "next", min(left) if left else None, None

    def visit(self) -> List[Any]:
        return [j for i in self.blocks for j in i.visit()]


class RawChoice(RawStatement):

    def __init__(self, loc: Any, chance: Any, block: Any) -> None:
        super(RawChoice, self).__init__(loc)
        self.choices: List[Tuple[Any, Any]] = [(chance, block)]

    def compile(self, ctx: Context) -> Statement:  # @ReservedAssignment
        compiling(self.loc)
        return Choice(self.loc, [(ctx.eval(chance), block.compile(ctx)) for chance, block in self.choices])

    def predict(self, ctx: Context) -> None:
        for _i, j in self.choices:
            j.predict(ctx)

    def mark_constant(self) -> None:
        constant: int = GLOBAL_CONST
        for _chance, block in self.choices:
            block.mark_constant()
            constant = _min_const(constant, block.constant)
        self.constant = constant


class Choice(Statement):

    def __init__(self, loc: Any, choices: List[Tuple[Any, Any]]) -> None:
        super(Choice, self).__init__(loc)
        self.choices: List[Tuple[Any, Any]] = choices

    def _handles_event(self, event: str) -> bool:
        for i in self.choices:
            if i[1]._handles_event(event):
                return True
        return False

    def execute(self, trans: Any, st: Any, state: Any, events: Any) -> Tuple[str, Any, Any]:
        executing(self.loc)

        if state is None:
            total: float = float(sum(chance for chance, _choice in self.choices))
            n = random.uniform(0.0, total)

            choice = self.choices[-1][1]
            for chance, candidate_choice in self.choices:
                if n < chance:
                    choice = candidate_choice
                    break
                n -= chance

            cstate = None
        else:
            choice, cstate = state

        action, arg, pause_val = choice.execute(trans, st, cstate, events)

        if action == "continue":
            return "continue", (choice, arg), pause_val
        return action, arg, None

    def visit(self) -> List[Any]:
        return [j for i in self.choices for j in i[1].visit()]


class RawTime(RawStatement):

    def __init__(self, loc: Any, time: Optional[str]) -> None:
        super(RawTime, self).__init__(loc)
        self.time: Optional[str] = time

    def compile(self, ctx: Context) -> Statement:  # @ReservedAssignment
        compiling(self.loc)
        return Time(self.loc, ctx.eval(self.time))

    def mark_constant(self) -> None:
        self.constant = is_constant_expr(self.time)


class Time(Statement):

    def __init__(self, loc: Any, time: Any) -> None:
        super(Time, self).__init__(loc)
        self.time = time

    def execute(self, trans: Any, st: Any, state: Any, events: Any) -> Tuple[str, Any, Any]:
        return "continue", None, None


class RawOn(RawStatement):

    def __init__(self, loc: Any, names: List[str], block: Any) -> None:
        super(RawOn, self).__init__(loc)
        self.handlers: Dict[str, Any] = {name: block for name in names}

    def compile(self, ctx: Context) -> Statement:  # @ReservedAssignment
        compiling(self.loc)
        handlers = {k: v.compile(ctx) for k, v in self.handlers.items()}
        return On(self.loc, handlers)

    def predict(self, ctx: Context) -> None:
        for i in self.handlers.values():
            i.predict(ctx)

    def mark_constant(self) -> None:
        constant: int = GLOBAL_CONST
        for block in self.handlers.values():
            block.mark_constant()
            constant = _min_const(constant, block.constant)
        self.constant = constant


class On(Statement):

    def __init__(self, loc: Any, handlers: Dict[str, Any]) -> None:
        super(On, self).__init__(loc)
        self.handlers: Dict[str, Any] = handlers

    def _handles_event(self, event: str) -> bool:
        return event in self.handlers

    def execute(self, trans: Any, st: Any, state: Any, events: Any) -> Tuple[str, Any, Any]:
        executing(self.loc)

        if state is None:
            name: Optional[str] = "start"
            start: Any = st
            cstate: Any = None
        else:
            name, start, cstate = state

        for event in events:
            ev: Optional[str] = event
            while ev:
                if ev in self.handlers:
                    break
                ev = ev.partition("_")[2] or None

            if not ev:
                continue

            lock_event = (
                (name == "hide" and getattr(trans, "hide_request", False))
                or (name == "replaced" and getattr(trans, "replaced_request", False))
            )

            if not lock_event:
                name = ev
                start = st
                cstate = None

        while True:
            if name is None or name not in self.handlers:
                return "continue", (name, start, cstate), None

            action, arg, pause_val = self.handlers[name].execute(trans, st - start, cstate, events)

            if action == "continue":
                if name == "hide" or name == "replaced":
                    trans.hide_response = False
                    trans.replaced_response = False

                return "continue", (name, start, arg), pause_val

            if action == "next":
                if name == "default" or name == "hide" or name == "replaced":
                    name = None
                else:
                    name = "default"

                start = st - arg
                cstate = None
                continue

            if action == "event":
                ev_name, ev_arg = arg
                if ev_name in self.handlers:
                    name = ev_name
                    start = max(st - ev_arg, st - 30)
                    cstate = None
                    continue

                return "event", (ev_name, ev_arg), None

    def visit(self) -> List[Any]:
        return [j for i in self.handlers.values() for j in i.visit()]


class RawEvent(RawStatement):

    def __init__(self, loc: Any, name: str) -> None:
        super(RawEvent, self).__init__(loc)
        self.name: str = name

    def compile(self, ctx: Context) -> Statement:  # @ReservedAssignment
        return Event(self.loc, self.name)

    def mark_constant(self) -> None:
        self.constant = GLOBAL_CONST


class Event(Statement):

    def __init__(self, loc: Any, name: str) -> None:
        super(Event, self).__init__(loc)
        self.name: str = name

    def execute(self, trans: Any, st: Any, state: Any, events: Any) -> Tuple[str, Any, Any]:
        return "event", (self.name, st), None


class RawFunction(RawStatement):

    def __init__(self, loc: Any, expr: Optional[str]) -> None:
        super(RawFunction, self).__init__(loc)
        self.expr: Optional[str] = expr

    def compile(self, ctx: Context) -> Statement:  # @ReservedAssignment
        compiling(self.loc)
        return Function(self.loc, ctx.eval(self.expr))

    def mark_constant(self) -> None:
        self.constant = is_constant_expr(self.expr)


class Function(Statement):

    def __init__(self, loc: Any, function: Any) -> None:
        super(Function, self).__init__(loc)
        self.function = function

    def _handles_event(self, event: str) -> bool:
        return True

    def execute(self, trans: Any, st: Any, state: Any, events: Any) -> Tuple[str, Any, Any]:
        fr = self.function(trans, st, getattr(trans, "at", 0.0))
        if fr is not None:
            return "continue", None, fr
        return "next", 0, None


def parse_atl(l: Any) -> RawBlock:
    l.advance()
    block_loc = l.get_location()

    statements: List[Optional[RawStatement]] = []
    animation: bool = False

    while not l.eob:
        loc = l.get_location()

        if l.keyword("repeat"):
            repeats: Optional[str] = l.simple_expression()
            statements.append(RawRepeat(loc, repeats))

        elif l.keyword("block"):
            l.require(":")
            l.expect_eol()
            l.expect_block("block")

            block = parse_atl(l.subblock_lexer())
            statements.append(block)

        elif l.keyword("contains"):
            expr: Optional[str] = l.simple_expression()

            if expr:
                l.expect_noblock("contains expression")
                statements.append(RawContainsExpr(loc, expr))
            else:
                l.require(":")
                l.expect_eol()
                l.expect_block("contains")

                block = parse_atl(l.subblock_lexer())
                statements.append(RawChild(loc, block))

        elif l.keyword("parallel"):
            l.require(":")
            l.expect_eol()
            l.expect_block("parallel")

            block = parse_atl(l.subblock_lexer())
            statements.append(RawParallel(loc, block))

        elif l.keyword("choice"):
            chance_expr: Optional[str] = l.simple_expression()
            chance: str = chance_expr if chance_expr else "1.0"

            l.require(":")
            l.expect_eol()
            l.expect_block("choice")

            block = parse_atl(l.subblock_lexer())
            statements.append(RawChoice(loc, chance, block))

        elif l.keyword("on"):
            names: List[str] = [cast(str, l.require(l.word))]

            while l.match(","):
                name = l.word()
                if name is None:
                    break
                names.append(str(name))

            l.require(":")
            l.expect_eol()
            l.expect_block("on")

            block = parse_atl(l.subblock_lexer())
            statements.append(RawOn(loc, names, block))

        elif l.keyword("time"):
            time_expr: Optional[str] = l.require(l.simple_expression)
            l.expect_noblock("time")
            statements.append(RawTime(loc, time_expr))

        elif l.keyword("function"):
            expr = l.require(l.simple_expression)
            l.expect_noblock("function")
            statements.append(RawFunction(loc, expr))

        elif l.keyword("event"):
            ev_word = l.require(l.word)
            l.expect_noblock("event")
            statements.append(RawEvent(loc, str(ev_word)))

        elif l.keyword("pass"):
            l.expect_noblock("pass")
            statements.append(None)

        elif l.keyword("animation"):
            l.expect_noblock("animation")
            animation = True

        else:
            rm: Any = renpy.atl.RawMultipurpose(loc)
            last_expression = False
            this_expression = False

            cp = l.checkpoint()
            warper: Optional[str] = l.name()

            duration: Optional[str]
            warp_function: Optional[str]

            if warper in warpers:
                duration = l.simple_expression()
                warp_function = None
            elif warper == "warp":
                warper = None
                warp_function = l.simple_expression()
                duration = l.simple_expression()
            else:
                l.revert(cp)
                warper = None
                warp_function = None
                duration = "0"

            rm.add_warper(warper, duration, warp_function)

            while True:
                last_expression = this_expression
                this_expression = False

                if l.keyword("pass"):
                    continue

                if l.keyword("clockwise"):
                    rm.add_revolution("clockwise")
                    continue

                if l.keyword("counterclockwise"):
                    rm.add_revolution("counterclockwise")
                    continue

                if l.keyword("circles"):
                    circles_expr: Optional[str] = l.simple_expression()
                    rm.add_circles(circles_expr)
                    continue

                cp = l.checkpoint()
                prop: Optional[str] = l.name()

                if prop is not None and ((prop in PROPERTIES) or prop.startswith("u_")):
                    prop_expr: Optional[str] = l.simple_expression()
                    knots: List[Optional[str]] = []

                    while l.keyword("knot"):
                        knots.append(l.simple_expression())

                    if knots:
                        knots.append(prop_expr)
                        rm.add_spline(prop, knots)
                    else:
                        rm.add_property(prop, prop_expr)

                    continue

                l.revert(cp)
                stmt_expr: Optional[str] = l.simple_expression()

                if not stmt_expr:
                    break

                if last_expression:
                    l.error(
                        "ATL statement contains two expressions in a row; is one of them a misspelled property? If not, separate them with pass."
                    )

                this_expression = True

                with_expr: Optional[str]
                if l.keyword("with"):
                    with_expr = l.simple_expression()
                else:
                    with_expr = None

                rm.add_expression(stmt_expr, with_expr)

            l.expect_noblock("ATL")
            statements.append(rm)

        if l.eol():
            l.advance()
            continue

        l.require(",", "comma or end of line")

    merged: List[RawStatement] = []
    old: Optional[RawStatement] = None

    for item in statements:
        if item is None:
            old = None
            continue

        stmt: RawStatement = item

        if isinstance(old, RawParallel) and isinstance(stmt, RawParallel):
            old.blocks.extend(stmt.blocks)
            continue

        if isinstance(old, RawChoice) and isinstance(stmt, RawChoice):
            old.choices.extend(stmt.choices)
            continue

        if isinstance(old, RawChild) and isinstance(stmt, RawChild):
            old.children.extend(stmt.children)
            continue

        if isinstance(old, RawOn) and isinstance(stmt, RawOn):
            old.handlers.update(stmt.handlers)
            continue

        merged.append(stmt)
        old = stmt

    return RawBlock(block_loc, merged, animation)