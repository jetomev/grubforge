"""Settings controls made of several parts (v2.0.0).

* ``KernelOptions`` — a checklist of known options, each with a plain
  explanation, plus one field for anything else. Posts ``KernelOptions.Changed``
  with the whole option string, or a problem in words.
* ``ColourPair`` — text colour on background colour, from GRUB's 16 named
  colours, with a sample of how it reads. Posts ``ColourPair.Changed``.
"""

from __future__ import annotations

from rich.markup import escape
from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.message import Message
from textual.widgets import Input, Select, SelectionList, Static

from ..settings_spec import (
    GRUB_COLOURS, KNOWN_KERNEL_OPTIONS, join_kernel, kernel_other_problem, split_kernel,
)

# GRUB colour name → a terminal colour to draw the sample with
SAMPLE = {
    "black": "#000000", "blue": "#0000aa", "green": "#00aa00", "cyan": "#00aaaa", "red": "#aa0000",
    "magenta": "#aa00aa", "brown": "#aa5500", "light-gray": "#aaaaaa", "dark-gray": "#555555",
    "light-blue": "#5555ff", "light-green": "#55ff55", "light-cyan": "#55ffff", "light-red": "#ff5555",
    "light-magenta": "#ff55ff", "yellow": "#ffff55", "white": "#ffffff",
}


class KernelOptions(Vertical):
    DEFAULT_CLASSES = "gf-kernel"

    class Changed(Message):
        def __init__(self, sender: "KernelOptions", value: str, problem: str) -> None:
            super().__init__()
            self.kernel = sender
            self.value = value
            self.problem = problem

        @property
        def control(self) -> "KernelOptions":
            return self.kernel

    def __init__(self, raw: str | None, **kw) -> None:
        super().__init__(**kw)
        self._on, self._other = split_kernel(raw)

    def compose(self) -> ComposeResult:
        sl = SelectionList(*((f"{k:<21} [$forge-muted]{desc}[/]", k, k in self._on) for k, desc in KNOWN_KERNEL_OPTIONS),
                           classes="gf-kernel-known")
        sl.FORGE_HINTS = [("↑↓", "pick"), ("Space", "tick / untick"), ("Tab", "next")]
        yield sl
        with Horizontal(classes="gf-kernel-other-line"):
            yield Static("Other options", classes="gf-kernel-other-label")
            inp = Input(self._other, placeholder="separate with spaces", classes="gf-kernel-other")
            inp.FORGE_HINTS = [("type", "options, separated by spaces"), ("Tab", "next")]
            yield inp
        problem = Static("", classes="gf-kernel-problem")
        problem.display = False
        yield problem

    def value(self) -> tuple[str, str]:
        on = list(self.query_one(SelectionList).selected)
        other = self.query_one(".gf-kernel-other", Input).value
        return join_kernel(on, other), kernel_other_problem(other)

    def set_raw(self, raw: str | None) -> None:
        on, other = split_kernel(raw)
        sl = self.query_one(SelectionList)
        with sl.prevent(SelectionList.SelectedChanged):
            sl.deselect_all()
            for k in on:
                sl.select(k)
        inp = self.query_one(".gf-kernel-other", Input)
        with inp.prevent(Input.Changed):
            inp.value = other

    def _announce(self) -> None:
        value, problem = self.value()
        box = self.query_one(".gf-kernel-problem", Static)
        box.update(f"[$forge-danger]Other options {escape(problem)}[/]" if problem else "")
        box.display = bool(problem)
        self.post_message(self.Changed(self, value, problem))

    @on(SelectionList.SelectedChanged)
    def _ticked(self, e: SelectionList.SelectedChanged) -> None:
        e.stop()
        self._announce()

    @on(Input.Changed, ".gf-kernel-other")
    def _typed(self, e: Input.Changed) -> None:
        e.stop()
        self._announce()


def default_colours(key: str) -> str:
    """GRUB's own colours when the setting is absent."""
    return "black/light-gray" if key.endswith("HIGHLIGHT") else "light-gray/black"


def split_colours(raw: str | None, default: str = "light-gray/black") -> tuple[str, str]:
    for cand in (raw, default):
        if cand and "/" in cand:
            fg, bg = cand.split("/", 1)
            if fg in GRUB_COLOURS and bg in GRUB_COLOURS:
                return fg, bg
    return "light-gray", "black"


class ColourPair(Horizontal):
    DEFAULT_CLASSES = "gf-colours"

    class Changed(Message):
        def __init__(self, sender: "ColourPair", value: str) -> None:
            super().__init__()
            self.pair = sender
            self.value = value

        @property
        def control(self) -> "ColourPair":
            return self.pair

    def __init__(self, raw: str | None, default: str = "light-gray/black", **kw) -> None:
        super().__init__(**kw)
        self._default = default
        self._fg, self._bg = split_colours(raw, default)
        self._ready = False

    def compose(self) -> ComposeResult:
        opts = [(c, c) for c in GRUB_COLOURS]
        fg = Select(opts, value=self._fg, allow_blank=False, classes="gf-colour-fg")
        bg = Select(opts, value=self._bg, allow_blank=False, classes="gf-colour-bg")
        for s in (fg, bg):
            s.FORGE_HINTS = [("Enter", "open list"), ("type", "jump"), ("Tab", "next")]
        yield fg
        yield Static("on", classes="gf-colour-on")
        yield bg
        yield Static("", classes="gf-colour-sample")

    def on_mount(self) -> None:
        self._sample()
        # the lists report their starting value once they settle; that is not
        # a choice anyone made
        self.call_after_refresh(lambda: setattr(self, "_ready", True))

    def _sample(self) -> None:
        fg = self.query_one(".gf-colour-fg", Select).value
        bg = self.query_one(".gf-colour-bg", Select).value
        self.query_one(".gf-colour-sample", Static).update(
            f"[{SAMPLE.get(fg, '#aaaaaa')} on {SAMPLE.get(bg, '#000000')}] Sample [/]")

    def value(self) -> str:
        return f"{self.query_one('.gf-colour-fg', Select).value}/{self.query_one('.gf-colour-bg', Select).value}"

    def set_raw(self, raw: str | None) -> None:
        fg, bg = split_colours(raw, self._default)
        for cls, v in ((".gf-colour-fg", fg), (".gf-colour-bg", bg)):
            s = self.query_one(cls, Select)
            with s.prevent(Select.Changed):
                s.value = v
        self._sample()

    @on(Select.Changed)
    def _picked(self, e: Select.Changed) -> None:
        e.stop()
        self._sample()
        if self._ready:
            self.post_message(self.Changed(self, self.value()))
