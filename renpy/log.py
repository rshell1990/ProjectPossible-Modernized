
# This module handles the logging of messages to a file.

from __future__ import division, absolute_import, with_statement, print_function, unicode_literals
import os.path
import traceback
import platform
import time
import tempfile
import sys
import io

import encodings.latin_1 # @UnusedImport

import renpy.config
import renpy.util

real_stdout = sys.stdout
real_stderr = sys.stderr

# The file events are logged to.
log_file = None


class LogFile(object):
    """
    This manages one of our logfiles.
    """

    def __init__(self, name, append=False, developer=False, flush=True):
        """
        `name`
            The name of the logfile, without the .txt extension.
        `append`
            If true, we will append to the logfile. If false, we will truncate
            it to an empty file the first time we write to it.
        `developer`
            If true, nothing happens if config.developer is not set to True.
        `flush`
            Determines if the file is flushed after each write.
        """

        self.name = name
        self.append = append
        self.developer = developer
        self.flush = flush
        self.file = None

        # File-like attributes.
        self.softspace = 0
        self.newlines = None

        # Should we emulate file's write method? We do so if this is True.
        self.raw_write = False

        if renpy.ios:
            self.file = real_stdout

    def open(self): # @ReservedAssignment

        if renpy.config.log_to_stdout:
            self.file = real_stdout
            return True

        if self.file:
            return True

        if self.file is False:
            return False

        if renpy.macapp:
            return False

        if self.developer and not renpy.config.developer:
            return False

        if not renpy.config.log_enable:
            return False

        try:
            base = os.environ.get("RENPY_LOG_BASE", renpy.config.logdir or renpy.config.basedir)

            if base is None:
                return False

            fn = os.path.join(base, self.name + ".txt")

            altfn = os.path.join(tempfile.gettempdir(), "renpy-" + self.name + ".txt")

            if self.append:
                mode = "a"
            else:
                mode = "w"

            try:
                self.file = io.open(fn, mode, encoding="utf-8")
                renpy.util.expose_file(fn)
            except:
                self.file = io.open(altfn, mode, encoding="utf-8")
                renpy.util.expose_file(altfn)

            if self.append:
                self.write('')
                self.write('=' * 78)
                self.write('')

            self.write("%s", time.ctime())
            try:
                self.write("%s", platform.platform())
            except:
                self.write("Unknown platform.")
            self.write("%s", renpy.version)
            self.write("%s %s", renpy.config.name, renpy.config.version)
            self.write("")

            return True

        except:
            self.file = False
            traceback.print_exc(file=real_stderr)
            return False

    def write(self, s, *args):
        """
        Formats `s` with args, and writes it to the logfile.
        """

        if self.open():

            if not self.raw_write:
                try:
                    s = s % args
                except:
                    s = repr((s,) + args)

                s += "\n"

            if isinstance(s, bytes):
                s = s.decode("latin-1")

            if self.file is not None and self.file is not False:
                getattr(self.file, "write")(s)

            if self.flush and self.file is not None and self.file is not False:
                getattr(self.file, "flush")()

    def exception(self):
        """
        Writes the exception to the logfile.
        """

        self.raw_write = True
        traceback.print_exc(None, self)
        self.raw_write = False


# A map from the log name to a log object.
log_cache = { }


def open(name, append=False, developer=False, flush=False): # @ReservedAssignment
    rv = log_cache.get(name, None)

    if rv is None:
        rv = LogFile(name, append=append, developer=developer, flush=flush)
        log_cache[name] = rv

    return rv

################################################################################
# Timed event log.


class TimeLog(list):
    """
    This represents a log that is limited to the last `duration` seconds.
    """

    def __init__(self, duration):
        self.duration = duration

    def append(self, v):
        now = time.time()

        list.append(self, (now, v))
        self.prune(now)

    def prune(self, now=None):

        if now is None:
            now = time.time()

        while self[0][0] < (now - self.duration):
            self.pop(0)

################################################################################
# Stdout / Stderr Redirection


class StdioRedirector(object):

    real_file = real_stdout

    def get_callbacks(self):
        return [ ]

    def __init__(self):
        self.buffer = ''
        self.log = open("log", developer=False, append=False, flush=True)

    def write(self, s):

        if not isinstance(s, str):
            s = str(s, "utf-8", "replace")

        if not renpy.config.log_to_stdout:
            self.real_file.write(s)
            self.real_file.flush()

        if renpy.ios:
            return

        s = self.buffer + s

        lines = s.split("\n")

        try:
            callbacks = self.get_callbacks()
        except:
            callbacks = [ ]

        for l in lines[:-1]:
            self.log.write("%s", l)

            for i in callbacks:
                try:
                    i(l)
                except:
                    pass

        self.buffer = lines[-1]

    def writelines(self, lines):
        for i in lines:
            self.write(i)

    def flush(self):
        self.real_file.flush()
        pass

    def close(self):
        pass


if not "RENPY_NO_REDIRECT_STDIO" in os.environ:

    class StdoutRedirector(StdioRedirector):
        real_file = real_stdout

        def get_callbacks(self):
            return renpy.config.stdout_callbacks

    sys.stdout = sys_stdout = StdoutRedirector()

    class StderrRedirector(StdioRedirector):
        real_file = real_stderr

        def get_callbacks(self):
            return renpy.config.stderr_callbacks

    sys.stderr = sys_stderr = StderrRedirector()

else:

    sys_stdout = sys.stdout
    sys_stderr = sys.stderr


def post_init():
    sys.stdout = sys_stdout
    sys.stderr = sys_stderr
