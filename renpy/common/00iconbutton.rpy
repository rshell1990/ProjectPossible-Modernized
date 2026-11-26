python early:
    renpy.register_sl_statement("iconbutton", 1, 0) \
        .add_property("caption") \
        .add_property_group("window") \
        .add_property_group("button") \
        .add_property_group("text", "text_") \
        .add_property_group("position", "text_") \
        .add_property_group("position", "icon_") \
        .add_prefix_style_property("icon_", "color")

screen iconbutton(icon, caption=None, **properties):
    $ icon_properties, text_properties, button_properties = renpy.split_properties(properties, "icon_", "text_", "")

    button:
        style "iconbutton"
        properties button_properties

        if caption:
            text caption style "iconbutton_text" properties text_properties

        icon icon style "iconbutton_icon" properties icon_properties
