
init -1900 python:
    config.audio_directory = 'audio'

    def _scan_audio_directory():

        import os

        if not config.audio_directory:
            return

        prefix = config.audio_directory.rstrip('/') + '/'

        for fn in renpy.list_files():
            if not fn.startswith(prefix):
                continue

            basename = os.path.basename(fn)
            base, ext = os.path.splitext(basename)

            if not ext.lower() in [ ".wav", ".mp2", ".mp3", ".ogg", ".opus" ]:
                continue

            base = base.lower()
            audio.__dict__.setdefault(base, fn)

init python:
    _scan_audio_directory()
