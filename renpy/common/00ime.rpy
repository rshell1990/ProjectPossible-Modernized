
# The in-game IME candidate list. This is shown by Ren'Py while an input
# method is offering candidates, as the platform's candidate window may be
# hidden when the game is fullscreen.

init -1500:

    style _ime_candidates_frame is default:
        background "#000000e0"
        padding (6, 4)

    style _ime_candidates_box is default:
        spacing 8

    style _ime_candidates_item_frame is default:
        background None
        padding (4, 2)

    style _ime_candidates_selected_item_frame is _ime_candidates_item_frame:
        background "#ffffffe0"

    style _ime_candidates_text is default:
        color "#ffffff"
        outlines [ ]
        xalign 0.0
        xmaximum None
        font (gui.system_font or "_WenQuanYiMicroHei.woff2")

    style _ime_candidates_selected_text is _ime_candidates_text:
        color "#000000"

    screen _ime_candidates():
        layer config.interface_layer
        zorder 1100

        $ _ime = renpy.display.ime.get_candidates()

        if _ime is not None:

            _ime_candidates_placer:

                frame:
                    style "_ime_candidates_frame"

                    hbox:
                        style "_ime_candidates_box"
                        box_layout ("horizontal" if _ime.horizontal else "vertical")

                        for _i, _c in enumerate(_ime.candidates):
                            frame:
                                style ("_ime_candidates_selected_item_frame" if _i == _ime.selected else "_ime_candidates_item_frame")

                                # The candidate includes the number used to select it.
                                text _c.replace("{", "{{"):
                                    style ("_ime_candidates_selected_text" if _i == _ime.selected else "_ime_candidates_text")
                                    substitute False
