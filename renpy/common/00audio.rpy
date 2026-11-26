init -1900 python:
    config.audio_directory = None

    config.late_audio_scan = True

    def _scan_audio_directory():

        directories = config.audio_directories

        if config.audio_directory and config.audio_directory not in directories:
            directories = directories + [ config.audio_directory ]

        import os

        for directory in directories:

            prefix = directory.strip('/') + '/'

            for fn in renpy.list_files():
                if not fn.startswith(prefix):
                    continue

                basename = os.path.basename(fn)
                base, ext = os.path.splitext(basename)

                if not ext.lower() in [ ".wav", ".mp2", ".mp3", ".ogg", ".opus", ".flac" ]:
                    continue

                base = base.lower()
                audio.__dict__.setdefault(base, fn)

init python:
    if not config.late_audio_scan:
        _scan_audio_directory()

init 1900 python:
    if config.late_audio_scan:
        _scan_audio_directory()
