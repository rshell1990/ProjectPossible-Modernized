
from renpy import pygame

# The overridden positioning of the mouse.
mouse_pos: tuple[int, int] | None = None

# The mouse buttons.
mouse_buttons = [0, 0, 0]


def get_mouse_pos(x: int = 0, y: int = 0) -> tuple[int, int]:
    """
    Called to get the overridden mouse position.
    """

    if mouse_pos is None:
        return x, y

    return mouse_pos


def post(event_type: int, **kwargs) -> None:
    pygame.event.post(pygame.event.Event(event_type, test=True, **kwargs))  # type: ignore


def move_mouse(x: int, y: int) -> None:
    """
    Moves the mouse to x, y.
    """

    global mouse_pos

    pos = (x, y)

    if mouse_pos != pos:
        if mouse_pos:
            rel = (pos[0] - mouse_pos[0], pos[1] - mouse_pos[1])
        else:
            rel = (0, 0)

        post(pygame.MOUSEMOTION, pos=pos, rel=rel, buttons=tuple(mouse_buttons))  # type: ignore

    mouse_pos = pos


def press_mouse(button: int) -> None:
    """
    Presses mouse button `button`.
    """

    post(pygame.MOUSEBUTTONDOWN, pos=mouse_pos, button=button)  # type: ignore

    if button < 3:
        mouse_buttons[button - 1] = 1


def release_mouse(button: int) -> None:
    """
    Releases mouse button `button`.
    """
    post(pygame.MOUSEBUTTONUP, pos=mouse_pos, button=button)  # type: ignore

    if button < 3:
        mouse_buttons[button - 1] = 0


def click_mouse(button: int, x: int, y: int) -> None:
    """
    Clicks the mouse at x, y
    """

    move_mouse(x, y)
    press_mouse(button)
    release_mouse(button)


def scroll_mouse(amount: int, x: int, y: int) -> None:
    """
    Scrolls the mouse wheel at x, y
    """

    move_mouse(x, y)

    btn = 4 if amount > 0 else 5
    for i in range(abs(amount)):
        post(pygame.MOUSEBUTTONDOWN, pos=mouse_pos, button=btn)  # type: ignore
        post(pygame.MOUSEBUTTONUP, pos=mouse_pos, button=btn)  # type: ignore


def reset() -> None:
    """
    Resets mouse handling once the test has ended.
    """

    global mouse_pos
    mouse_pos = None
