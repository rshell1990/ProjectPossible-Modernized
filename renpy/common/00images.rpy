init -1900 python:

    # Compat for < 8.5
    config.images_directory = None

    config.late_images_scan = False

    config.image_extensions =  [ ".jpg", ".jpeg", ".png", ".webp", ".avif", ".svg" ]

    def _scan_images_directory():

        import os

        directories = config.image_directories

        if config.images_directory and config.images_directory not in directories:
            directories = directories + [ config.images_directory ]

        for prefix in directories:

            prefix = prefix.strip('/') + '/'

            non_oversampled_images = [ ]

            oversampled_images = [ ]

            for fn in renpy.list_files():
                if not fn.startswith(prefix):
                    continue

                basename = os.path.basename(fn)
                base, ext = os.path.splitext(basename)

                if not ext.lower() in config.image_extensions:
                    continue

                base = base.lower()
                base, _, oversampled = base.partition("@")

                if oversampled:
                    oversampled_images.append((base, fn))
                else:
                    non_oversampled_images.append((base, fn))

            for base, fn in non_oversampled_images:
                if renpy.has_image(base, exact=True):
                    continue

                renpy.image(base, fn)

            for base, fn in oversampled_images:
                if renpy.has_image(base, exact=True):
                    continue

                renpy.image(base, fn)

init python:

    if not config.late_images_scan:
        _scan_images_directory()

init 1900 python:

    if config.late_images_scan:
        _scan_images_directory()
