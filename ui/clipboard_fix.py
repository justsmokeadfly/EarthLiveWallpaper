"""Workaround for a well-known Tk/Windows bug: Ctrl+C/V/X/A do nothing
when the OS keyboard layout is non-Latin (e.g. Russian).

Tk's default Entry bindings for copy/paste/cut/select-all are keyed to the
*keysym* produced by the key (e.g. "v"), not the physical key. On a
Cyrillic layout, holding Ctrl and pressing the key physically located at
"V" produces a different keysym (a Cyrillic letter), so Tk's built-in
"<Control-v>" binding never fires and paste silently does nothing - even
though the field itself is a perfectly ordinary, enabled text entry.

The fix is to bind by keycode (which identifies the physical key
regardless of layout) instead of keysym, and dispatch the corresponding
Tk virtual event ourselves.
"""

from __future__ import annotations

import tkinter as tk

_KEYCODE_TO_VIRTUAL_EVENT = {
    86: "<<Paste>>",  # V
    67: "<<Copy>>",  # C
    88: "<<Cut>>",  # X
    65: "<<SelectAll>>",  # A
}


def enable_clipboard_shortcuts(window: tk.Misc) -> None:
    """Make Ctrl+C/V/X/A work inside `window` regardless of keyboard layout.

    Bind this once per Toplevel/CTkToplevel (not per-Entry); Tk's bindtag
    propagation means a binding on the window fires for keypresses in any
    descendant widget, and it is automatically cleaned up when the window
    is destroyed.
    """

    def _on_control_keypress(event: tk.Event) -> None:
        virtual_event = _KEYCODE_TO_VIRTUAL_EVENT.get(event.keycode)
        if virtual_event is None:
            return
        widget = window.focus_get()
        if widget is None:
            return
        widget.event_generate(virtual_event)

    window.bind("<Control-KeyPress>", _on_control_keypress, add="+")
