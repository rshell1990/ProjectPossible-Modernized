
from __future__ import division, absolute_import, with_statement, print_function, unicode_literals
from renpy.compat import *
from typing import Any

import renpy
import renpy.arguments
import renpy.config
import renpy.game as game
game: Any
import renpy.scriptedit
from renpy.translation import quote_unicode
import json


def merge_strings():
    """
    The merge strings command.
    """

    ap = renpy.arguments.ArgumentParser(description="Merges translated strings with the game script.")
    ap.add_argument("language", help="The language to merge translated strings to.")
    ap.add_argument("source", help="The json file to take translated strings from.")
    ap.add_argument("--reverse", action="store_true", help="Reverses the languages in the json file.")
    ap.add_argument("--replace", action="store_true", help="Replaces non-trivial translations.")

    args = ap.parse_args()

    language = args.language

    if language == 'None':
        language = None

    if language not in game.script.translator.strings:  # @UndefinedVariable
        raise Exception("Language %r does not have any translations." % language)

    with open(args.source, "r", encoding="utf-8") as f:
        data = json.loads(f.read())

    if args.reverse:
        new_data = { }

        for k, v in data.items():
            new_data[v] = k

        data = new_data

    st = game.script.translator.strings[language]  # @UndefinedVariable

    renpy.config.clear_lines = False

    for k, v in st.translations.items():

        trivial = (not v) or (k == v)

        if (not trivial) and (not args.replace):
            continue

        if k not in data:
            continue

        if k not in st.translation_loc:
            continue

        new = data[k]
        quoted = quote_unicode(new)
        code = u'new "{}"'.format(quoted)

        filename, linenumber = st.translation_loc[k]
        renpy.scriptedit.insert_line_before(code, filename, linenumber)
        renpy.scriptedit.remove_line(filename, linenumber + 1)

    return False


renpy.arguments.register_command("merge_strings", merge_strings)
