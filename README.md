iracing-audio-cue
=================

This program plays sounds when events happens in the iRacing simulator using the telemetry channel as event source.

Supported events (can be enabled/disabled individually):

- spotter left-right warnings
- faster class cars reaching behind us

Configuration happens via the `config.ini` file in the program directory; sounds can be replaced in the sounds directory if needed.

compile
-------

Install via `pip` the following packages: `pyirsdk`, `pyinstaller`, `pywin32`, `pystray`.

Compile with:

`pyinstaller --onefile --hidden-import pystray._win32 --hidden-import win32api --hidden-import -w pywintypes main.py`
