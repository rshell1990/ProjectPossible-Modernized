
init -1900 python:
    config.images_directory = 'images'
    config.late_images_scan = False

    def _scan_images_directory():

        import os

        if not config.images_directory:
            return

        prefix = config.images_directory.rstrip('/') + '/'

        for fn in renpy.list_files():
            if not fn.startswith(prefix):
                continue

            basename = os.path.basename(fn)
            base, ext = os.path.splitext(basename)

            if not ext.lower() in [ ".jpg", ".jpeg", ".png", ".webp" ]:
                continue

            base = base.lower()

            if renpy.has_image(base, exact=True):
                continue

            renpy.image(base, fn)

init python:

    if not config.late_images_scan:
        _scan_images_directory()

init 1900 python:

    if config.late_images_scan:
        _scan_images_directory()
