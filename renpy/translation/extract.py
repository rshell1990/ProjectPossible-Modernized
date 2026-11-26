
from __future__ import division, absolute_import, with_statement, print_function, unicode_literals
from renpy.compat import PY2, basestring, bchr, bord, chr, open, pystr, range, round, str, tobytes, unicode  # *


import renpy
import json


def extract_strings_core(language, destination, merge=False, force=False):
    if (not force) and (language not in renpy.game.script.translator.strings):
        raise Exception("Language %r does not have any translations." % language)

    st = renpy.game.script.translator.strings[language]

    result = {}

    if merge:
        with open(destination, "r") as f:
            result.update(json.load(f, encoding="utf-8"))

    for k, v in st.translations.items():
        if v and v != k:
            result[k] = v

    with open(destination, "w") as f:
        json.dump(result, f, ensure_ascii=True)


def extract_strings():
    """
    The extract strings command.
    """

    ap = renpy.arguments.ArgumentParser(description="Extracts translated strings.")
    ap.add_argument("language", help="The language to extract translated strings from.")
    ap.add_argument("destination", help="The json file to store the translated strings into.")
    ap.add_argument(
        "--merge",
        help="If given, the current contents of the file are preserved, and new contents are merged into the file.",
        action="store_true",
    )
    ap.add_argument(
        "--force", help="If given, no exceptions are thrown if the language does not exist.", action="store_true"
    )

    args = ap.parse_args()

    language = args.language

    if language == "None":
        language = None

    extract_strings_core(language, args.destination, args.merge, args.force)

    return False


renpy.arguments.register_command("extract_strings", extract_strings)
