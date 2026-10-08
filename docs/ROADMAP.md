# grubForge — full roadmap

*The README carries what's next and the two most recent releases; the whole list lives here, newest first. What each release changed, in detail: [CHANGELOG.md](CHANGELOG.md).*

## Next

- [ ] **Write settings into `/etc/default/grub.d`** on Debian and Ubuntu, so settings decided there can be changed from grubForge too (today they're shown, locked, with the file to edit) ([#34](https://github.com/jetomev/grubforge/issues/34))
- [ ] **Fedora-style entries**: rename and reorder entries kept as separate files ([#35](https://github.com/jetomev/grubforge/issues/35))
- [ ] **Configurable preferences**: backup retention, theme folder

## Done

- [x] **v2.2.0**: a key for every menu entry (Help is 6), "Boot Menu", a page of hypeForge Settings, buttons that show their key ([#38](https://github.com/jetomev/grubforge/issues/38), [#39](https://github.com/jetomev/grubforge/issues/39), [#40](https://github.com/jetomev/grubforge/issues/40))
- [x] **v2.1.0**: the password in grubForge's own box, and saving on a text console ([#36](https://github.com/jetomev/grubforge/issues/36))
- [x] **v2.0.0**: rebuilt on forgekit, every screen redesigned, every major distribution ([#21](https://github.com/jetomev/grubforge/issues/21), [#20](https://github.com/jetomev/grubforge/issues/20), [#19](https://github.com/jetomev/grubforge/issues/19), [#17](https://github.com/jetomev/grubforge/issues/17), [#22](https://github.com/jetomev/grubforge/issues/22), [#24](https://github.com/jetomev/grubforge/issues/24), [#25](https://github.com/jetomev/grubforge/issues/25), [#29–#33](https://github.com/jetomev/grubforge/issues?q=is%3Aissue+F-))
- [x] **v1.1.3**: reads where each boot entry comes from instead of guessing it ([#28](https://github.com/jetomev/grubforge/issues/28))
- [x] **v1.1.2**: the distribution's name read from the system itself, so Debian is no longer called Arch ([#27](https://github.com/jetomev/grubforge/issues/27))
- [x] **v1.1.1**: a boot menu readable only by root is read through the helper, instead of being reported missing
- [x] **v1.1.0**: no more `sudo`: grubForge runs as you, and only a small helper does the root work, through polkit
- [x] **v1.0.3**: a batch of fixes closing all 15 findings from the v1.0.1 retest
- [x] **v1.0.2**: works with Textual 8
- [x] **v1.0.1**: fixes from the first full test cycle
- [x] **v1.0.0**: first stable release, on the AUR
- [x] **v0.1.0 – v0.9.0**: the first versions (April 2026)
