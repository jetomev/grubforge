# Backups and undo

Every save makes a backup of your settings first; the last 10 are kept. Each one also keeps a copy of your boot-order file.

## Undo a change

1. Open **Backups** (press **5**).
2. Pick the backup from before the change. The right side shows what restoring it would change, setting by setting.
3. **Restore this backup…** (or **R**). The window starts on **Cancel**; move to **Restore** to confirm.
4. Rebuild with **F9**.

Today's settings are backed up before a restore, so a restore can be undone too.

## Good to know

- **Back up now** (**N**) makes one whenever you like.
- A restore puts back the **settings**. The boot order is changed on the Boot menu screen; the saved copy beside each backup is there for recovery.
- Backups live in `/var/lib/grubforge/backups`.
