
screen _translation_info():
    layer config.interface_layer
    zorder 1500
    style_prefix ""

    default show_copy = False

    python:
        identifier = renpy.get_translation_identifier()
        copy = None

        if identifier:
            copy = (SetScreenVariable("show_copy", True),
                    Function(renpy.pygame.scrap.put,
                             renpy.pygame.scrap.SCRAP_TEXT,
                             identifier.encode("utf8")))


        tl = renpy.get_translation_info()
        filename, line = renpy.get_filename_line()

    # The filename and line to show.

    drag:
        draggable True
        focus_mask None
        xpos 0
        ypos 0

        frame:
            style "empty"
            background "#0004"
            xpadding 5
            ypadding 5
            xminimum 200

            has vbox

            null height gui._scale(7)

            textbutton _("Translation identifier: [identifier]"):
                action copy
                padding (0, 0)
                text_color "#fff"
                text_hover_color "#bdf"

                text_size gui._scale(14)

            null height gui._scale(7)

            hbox:

                textbutton "[filename]:[line]":
                    padding (0, 0)
                    text_color "#fff"
                    text_hover_color "#bdf"
                    text_size gui._scale(14)

                    action EditFile(filename, line)

                if tl and preferences.language:
                    textbutton _(" translates [tl.filename]:[tl.linenumber]"):
                        padding (0, 0)
                        text_color "#fff"
                        text_hover_color "#bdf"
                        text_size gui._scale(14)

                        action EditFile(tl.filename, tl.linenumber)

            if tl and preferences.language and tl.source:
                null height gui._scale(7)

                for s in tl.source:
                    text "    [s]":
                        size gui._scale(14)
                        color "#fff"

            if show_copy:
                text _("\n{color=#fff}Copied to clipboard.{/color}"):
                    size gui._scale(14)

                timer 2.0 action SetScreenVariable("show_copy", False)
