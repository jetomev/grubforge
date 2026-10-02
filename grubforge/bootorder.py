"""Your boot order: a draft of the menu you can change before saving (v2.0.0).

The menu is read from grub.cfg. Entries made by the scripts grubForge manages
(this system's kernels, other systems found by os-prober, UEFI firmware) and
entries you added are **movable**: saving writes them, in your order, to
/etc/grub.d/40_custom and turns those scripts off. Entries made by any other
tool (btrfs snapshots, Debian's memtest script…) are **fixed**: they stay where
their tool puts them and are never copied into your order, so saving cannot
duplicate them (#20, Javier's ruling 2026-10-02).

Where a fixed entry lands relative to your order follows GRUB's own rule:
scripts run in name order, so a script numbered below 40 comes before your
entries, one above 40 after them.
"""

from __future__ import annotations

import copy
import re
from dataclasses import dataclass, field

from .boot_entries_manager import MANAGED_SCRIPTS, BootEntry, render_custom_order


def script_number(source: str) -> int:
    m = re.match(r"(\d+)_", source or "")
    return int(m.group(1)) if m else 99


def is_movable(e: BootEntry) -> bool:
    return e.source in MANAGED_SCRIPTS or e.source == "40_custom"


@dataclass
class Item:
    """One entry in the draft, with what you did to it."""
    entry: BootEntry
    original_index: int | None     # None = added by you
    original_title: str = ""
    removed: bool = False

    @property
    def movable(self) -> bool:
        return is_movable(self.entry)

    @property
    def stale_copy(self) -> bool:
        """A fixed entry stuck inside your saved order: the old #20 duplicate.
        The next save drops it; its tool keeps making the live one."""
        return self.entry.in_custom_order and not self.movable

    @property
    def renamed(self) -> bool:
        return self.original_index is not None and self.entry.title != self.original_title


@dataclass
class BootDraft:
    original: list[BootEntry] = field(default_factory=list)
    items: list[Item] = field(default_factory=list)

    @classmethod
    def from_entries(cls, entries: list[BootEntry]) -> "BootDraft":
        d = cls(original=[copy.deepcopy(e) for e in entries])
        d.items = [Item(copy.deepcopy(e), i, e.title) for i, e in enumerate(entries)]
        d._settle_fixed()
        return d

    # ── what is shown ────────────────────────────────────────────────────────
    def _settle_fixed(self) -> None:
        """Fixed entries sit where GRUB will put them: before or after yours."""
        before = [it for it in self.items if not it.movable and script_number(it.entry.source) < 40]
        after = [it for it in self.items if not it.movable and script_number(it.entry.source) >= 40]
        mine = [it for it in self.items if it.movable]
        self.items = before + mine + after

    def visible(self) -> list[Item]:
        return [it for it in self.items if not it.removed]

    @property
    def stale_copies(self) -> list[Item]:
        return [it for it in self.items if it.stale_copy]

    # ── changing ─────────────────────────────────────────────────────────────
    def move(self, item: Item, step: int) -> bool:
        """Move a movable entry among the movable ones. False when it can't."""
        mine = [it for it in self.items if it.movable and not it.removed]
        if item not in mine:
            return False
        i = mine.index(item)
        j = i + step
        if not 0 <= j < len(mine):
            return False
        # slide it, not swap it: the entries in between keep their order
        slots = [self.items.index(x) for x in mine]
        mine.insert(j, mine.pop(i))
        for slot, it in zip(slots, mine):
            self.items[slot] = it
        return True

    def rename(self, item: Item, title: str) -> None:
        from .boot_entries_manager import rename_entry
        item.entry = rename_entry(item.entry, title)

    def add(self, entry: BootEntry) -> Item:
        it = Item(entry, None, entry.title)
        last_mine = max((i for i, x in enumerate(self.items) if x.movable), default=-1)
        self.items.insert(last_mine + 1, it)
        return it

    def remove(self, item: Item) -> None:
        if item.original_index is None:
            self.items.remove(item)
        else:
            item.removed = True

    # ── comparing ────────────────────────────────────────────────────────────
    def _order(self) -> list[int | None]:
        return [it.original_index for it in self.items if it.movable and not it.removed]

    def _original_order(self) -> list[int]:
        d = BootDraft.from_entries(self.original)
        return [it.original_index for it in d.items if it.movable]

    @property
    def changed(self) -> bool:
        return (self._order() != self._original_order()
                or any(it.renamed or it.removed or it.original_index is None or it.stale_copy
                       for it in self.items))

    def changes(self) -> list[tuple[str, str, str]]:
        """(entry, old, new) for the review, in plain words."""
        out: list[tuple[str, str, str]] = []
        orig = self._original_order()
        now = self._order()
        def nth(n: int) -> str:
            return f"{n}{'tsnrhtdd'[(n // 10 % 10 != 1) * (n % 10 < 4) * n % 10::4]}"
        for it in self.items:
            if it.stale_copy:
                out.append((f"{it.entry.title} (old copy)", "in your saved order", "dropped"))
                continue
            if not it.movable:
                continue
            if it.original_index is None and not it.removed:
                out.append((it.entry.title, "not in the menu", "added"))
                continue
            if it.removed:
                out.append((it.original_title, "in the menu", "removed"))
                continue
            if it.renamed:
                out.append((it.original_title, "name", f'"{it.entry.title}"'))
            if it.original_index in orig and it.original_index in now:
                a, b = orig.index(it.original_index), now.index(it.original_index)
                if a != b:
                    out.append((it.entry.title, nth(a + 1), nth(b + 1)))
        return out

    # ── saving ───────────────────────────────────────────────────────────────
    def custom_40(self) -> str:
        """The text of 40_custom: your movable entries only, in your order (#20)."""
        return render_custom_order([it.entry for it in self.items if it.movable and not it.removed])

    def scripts_to_turn_off(self) -> list[str]:
        """The managed scripts whose entries are now in your order."""
        used = {it.entry.source for it in self.items if it.movable and it.original_index is not None}
        return [s for s in MANAGED_SCRIPTS if s in used]
