
python early in icon:

    from store import Image, Color, Text, Transform, TintMatrix

    # The path to the icons.
    path = [ '', 'icons/' ]

    class Icon(renpy.Displayable):

        def __init__(self, name, style="icon", **properties):
            super(Icon, self).__init__(style=style, **properties)

            self.name = name

        def find_image(self, prefix):

            for p in path:
                fn = p + prefix + self.name + ".png"
                if renpy.loadable(fn):
                    return fn

            for p in path:
                fn = p + self.name + ".png"

                if renpy.loadable(fn):
                    c = self.style.color

                    if c is not None:
                        c = Color(self.style.color)
                        tint = tuple(component / 255.0 for component in c)
                        return Transform(fn, matrixcolor=TintMatrix(tint))
                    else:
                        c = Image(fn)

            return Text('icon {}'.format(self.name))

        def render(self, width, height, st, at):
            d = self.find_image(self.style.prefix)
            cr = renpy.render(d, width, height, st, at)
            cw, ch = cr.get_size()

            scale = min(1.0 * width / cw, 1.0 * height / ch)

            rv = renpy.Render(cw * scale, ch * scale)
            rv.zoom(scale, scale)
            rv.blit(cr, (0, 0))

            return rv

        STATES = [
            "insensitive_",
            "idle_",
            "hover_",
            "selected_idle_",
            "selected_hover_",
            ]

        def visit(self):
            return [ self.find_image(p) for p in Icon.STATES ]

    # Register the icon with screen language.
    renpy.register_sl_displayable("icon", Icon, 0, "icon") \
        .add_positional("name") \
        .add_style_property("color")
