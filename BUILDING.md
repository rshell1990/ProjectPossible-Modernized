# Building

The checked-in engine sources and launchers target Ren'Py 8.6.1. The binary
platform runtime in `lib/` and the game archive `game/archive.rpa` are excluded
from Git and must be supplied locally.

1. Extract the Ren'Py 8.6.1 SDK.
2. Copy the SDK's `lib/` directory to the project root, replacing any older
   runtime files.
3. Restore `game/archive.rpa` from the project's authorized build assets.
4. Open the project in the Ren'Py 8.6.1 Launcher and build distributions.

The SDK provides Windows x64, Linux x64, and universal macOS runtimes; it does
not include a 32-bit Windows runtime. Android packaging also requires the
Android toolchain configured in the Ren'Py Launcher.
