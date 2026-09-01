"""
grubForge — Privilege

The one place grubForge asks for elevated rights.

grubForge runs as your user. When something needs to change under /etc or
/boot, this module calls the privileged helper, and polkit — not grubForge —
asks you to authenticate. grubForge never sees, holds, or forwards a password.

There is exactly one implementation of every privileged operation: the helper.
When grubForge already runs as root the helper is executed directly, and when
it does not, the same helper is executed through pkexec. Same code, same
checks, either way — so there is only one thing to audit.
"""

import asyncio
import os
import shutil
import subprocess
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

# ── Where things live ─────────────────────────────────────────────────────────

# pkexec will only run the exact path named in the polkit policy, so the
# installed location is the only one it can ever use.
INSTALLED_HELPER = Path("/usr/lib/grubforge/grubforge-helper")
POLICY_FILE      = Path("/usr/share/polkit-1/actions/org.kognogos.grubforge.policy")

# Running from a git checkout: helper/grubforge-helper next to the package.
SOURCE_HELPER = Path(__file__).resolve().parent.parent / "helper" / "grubforge-helper"

ACTION_ID = "org.kognogos.grubforge.manage"

HELPER_TIMEOUT = 300  # grub-mkconfig can be slow, and you have to type a password


# ── What we are able to do ────────────────────────────────────────────────────

class Privilege(Enum):
    """How — or whether — grubForge can make changes right now."""

    ROOT   = "root"      # already root; the helper runs directly, no prompt
    POLKIT = "polkit"    # normal user; polkit will ask you to authenticate
    NONE   = "none"      # cannot escalate; grubForge stays read-only


@dataclass
class Capability:
    """The current privilege level, and a sentence explaining it."""

    level:  Privilege
    reason: str

    @property
    def can_write(self) -> bool:
        return self.level is not Privilege.NONE

    @property
    def will_prompt(self) -> bool:
        return self.level is Privilege.POLKIT

    @property
    def prompt_note(self) -> str:
        """
        The heads-up shown in a confirmation dialog when a password is coming.

        Being asked for a password you were not expecting looks like something
        went wrong. Saying so in advance turns it into a normal step. Passed to
        ConfirmDialog as `note=`, which renders it in the title's yellow — it
        is a warning about what happens next, not part of the description.
        """
        return "You will be asked for your password." if self.will_prompt else ""


@dataclass
class HelperResult:
    """The outcome of one privileged operation."""

    ok:        bool
    output:    str = ""
    cancelled: bool = False   # you dismissed the password dialog

    @property
    def message(self) -> str:
        if self.cancelled:
            return "Cancelled — nothing was changed."
        return self.output.strip()


# ── Working out what we can do ────────────────────────────────────────────────

def detect() -> Capability:
    """
    Decide how grubForge can make changes, and be specific about why not.

    Called once at startup. The reason string is shown to the user, so it has
    to say what to do about it — not merely that something is wrong.
    """
    if os.geteuid() == 0:
        return Capability(Privilege.ROOT, "Running as root — changes apply directly.")

    if shutil.which("pkexec") is None:
        return Capability(
            Privilege.NONE,
            "polkit is not installed, so grubForge cannot ask for permission. "
            "Install polkit, or run grubForge with sudo.",
        )

    if not INSTALLED_HELPER.is_file():
        return Capability(
            Privilege.NONE,
            "grubForge's privileged helper is not installed, so permission cannot "
            "be requested. On Arch, install the package. On any other distribution, "
            "run  sudo sh install-helper.sh  from the checkout — it copies two files "
            "and nothing else. Or run grubForge with sudo.",
        )

    if not POLICY_FILE.is_file():
        return Capability(
            Privilege.NONE,
            "grubForge's polkit rule is not installed, so permission cannot be "
            "requested. Reinstall the package, or run  sudo sh install-helper.sh  "
            "from the checkout. Or run grubForge with sudo.",
        )

    return Capability(
        Privilege.POLKIT,
        "Changes are allowed — you will be asked for your password.",
    )


# ── Running the helper ────────────────────────────────────────────────────────

def _command(level: Privilege) -> list:
    """Build the argument list that gets us to the helper."""
    if level is Privilege.ROOT:
        # Prefer the checkout when there is one, so development tests the code
        # actually being edited rather than the last installed copy.
        helper = SOURCE_HELPER if SOURCE_HELPER.is_file() else INSTALLED_HELPER
        return [str(helper)]

    # --disable-internal-agent stops pkexec falling back to a text prompt on
    # the terminal. Textual owns the screen; a prompt printed underneath it
    # would corrupt the display and strand the user at an invisible question.
    # With no desktop authentication agent we would rather fail cleanly and
    # say so.
    return ["pkexec", "--disable-internal-agent", str(INSTALLED_HELPER)]


def run(
    verb:       str,
    argument:   str  = "",
    content:    str  = "",
    capability: Capability = None,
) -> HelperResult:
    """
    Perform one privileged operation. Blocking — prefer run_async() from the UI.

    `content` is piped to the helper on stdin for the verbs that write a file,
    so file contents never appear in a command line where other users could
    read them from the process list.
    """
    cap = capability or detect()

    if not cap.can_write:
        return HelperResult(ok=False, output=cap.reason)

    command = _command(cap.level) + [verb]
    if argument:
        command.append(argument)

    try:
        result = subprocess.run(
            command,
            input=content,
            capture_output=True,
            text=True,
            timeout=HELPER_TIMEOUT,
        )
    except FileNotFoundError:
        return HelperResult(ok=False, output="Could not start the privileged helper.")
    except subprocess.TimeoutExpired:
        return HelperResult(
            ok=False,
            output=f"The operation took longer than {HELPER_TIMEOUT} seconds and was stopped.",
        )

    # pkexec reports 126 when the password dialog is dismissed, and 127 when
    # authentication fails or the helper could not be started. Everything else
    # is the helper's own exit status.
    if cap.level is Privilege.POLKIT and result.returncode == 126:
        return HelperResult(ok=False, cancelled=True)

    if cap.level is Privilege.POLKIT and result.returncode == 127:
        # 127 covers both "you typed the wrong password" and "there was no
        # authentication agent to ask" — pkexec does not distinguish them, so
        # neither do we. Guessing would be worse than saying both.
        #
        # Left raw, this is where the user meets pkexec's "Not authorized. This
        # incident has been reported.", which sounds like a security event and
        # explains nothing. On a text console or over SSH it just means there is
        # no window to show a dialog in, and sudo is the answer.
        return HelperResult(
            ok=False,
            output=(
                "Permission was not granted, so nothing was changed.\n"
                "Either the password was not accepted, or this session has no "
                "authentication agent to ask — which is normal over SSH or on a "
                "text console. There, run grubForge with sudo instead."
            ),
        )

    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip()
        return HelperResult(ok=False, output=detail or "The operation failed.")

    return HelperResult(ok=True, output=result.stdout)


async def run_async(
    verb:       str,
    argument:   str  = "",
    content:    str  = "",
    capability: Capability = None,
) -> HelperResult:
    """
    run(), off the event loop.

    The UI must stay alive while the password dialog is up — you may take
    twenty seconds to type, and a frozen interface behind the dialog reads as
    a crash.
    """
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(
        None, lambda: run(verb, argument, content, capability)
    )
