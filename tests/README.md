# Test suite notes

EarthLive Wallpaper ships as a Windows application, but most of the
codebase is plain, OS-independent Python behind interfaces
(`domain/interfaces.py`), so the large majority of this suite runs on
any platform and is exercised in CI on `windows-latest`.

## Windows-only modules

A couple of modules touch Windows-only APIs directly:

- `infrastructure/system/autostart.py` (`AutostartManager`) — reads and
  writes the `HKEY_CURRENT_USER\...\Run` registry key via the stdlib
  `winreg` module.
- `infrastructure/wallpaper/windows_wallpaper_setter.py` — calls
  `ctypes.windll.user32.SystemParametersInfoW` to set the desktop
  wallpaper, and writes wallpaper style/tile registry values via
  `winreg`.

Because `winreg` and `ctypes.windll` don't exist outside Windows,
**importing** these modules (or anything that imports them, such as
`application.app_controller.AppController`) fails immediately on
Linux/macOS with `ModuleNotFoundError`. Test files that need to import
those modules guard themselves with a platform check so the rest of
the suite stays collectible on any OS:

```python
import sys
import pytest

if sys.platform != "win32":
    pytest.skip("... requires the Windows-only winreg module.", allow_module_level=True)
```

Such a file shows up as **skipped** (not failed) when running `pytest`
locally on Linux/macOS. It only actually executes for real on the
`windows-latest` CI runner, which is where the project's quality gate
lives.

## How each Windows-only module is covered

- **`UpdateWallpaperUseCase` and everything above it** (the business
  logic that decides *when* and *what* to download/assemble/apply) is
  tested with fake implementations of `TileDownloader`, `ImageAssembler`,
  `WallpaperSetter`, etc. (see `tests/application/test_update_wallpaper_use_case.py`).
  These fakes never touch the real registry or `ctypes`, so this layer
  is fully covered on any OS.
- **`AppController.delete_from_history`** is tested against a real,
  in-memory `StateRepository` fake, bypassing `AppController.__init__`
  entirely (see `tests/application/test_app_controller_delete.py`) so
  the test doesn't need to construct an `AutostartManager` at all.
- **`AutostartManager`** itself (the one place that actually calls
  `winreg.CreateKeyEx` / `SetValueEx` / `QueryValueEx` / `DeleteValue`)
  is exercised end-to-end by a real round-trip smoke test —
  `tests/infrastructure/test_autostart_smoke.py`. It calls the real
  `enable()` / `is_enabled()` / `disable()` methods against the actual
  `HKCU\...\Run` key, then cleans up after itself. This only runs on
  the `windows-latest` CI runner (each run gets a fresh, disposable VM,
  so there's no real user registry to disturb); on any other platform
  it's skipped the same way as above.

  If you run this specific test locally on a Windows machine, it will
  briefly create and then remove a real `EarthLive Wallpaper` entry
  under your own `HKCU\...\Run` key. That's expected and harmless (the
  test always calls `disable()` before finishing, whether it passes or
  fails), but worth knowing before you run it outside CI.
- **`windows_wallpaper_setter.py`** (the `ctypes.windll` call that
  actually repaints the desktop) has no automated test — there's no
  safe, side-effect-free way to assert "the desktop wallpaper changed"
  from a CI runner. This is the one Windows-only code path that relies
  on manual verification instead.
