# iceland-coexist

Kernel-install support for a Fedora 44 that lives in a **subdirectory of a shared `/boot`** on the OnePlus Pad 4, and
the `iceland-oneshot` tool for one-shot boot entries. The reference tablet uses this layout: one ext4 boot file system
(mounted at `/bootfs`) holds GRUB's `grub2/`, the shared `loader/entries/` and Fedora's own files in `fedora44/`, which
`/etc/fstab` bind-mounts at `/boot`; the EFI system partition stays read-only. Systems installed from the generic image
(one `/boot` of their own) do not need this package. `build-rpm.sh OUT` builds `iceland-coexist-*.noarch.rpm`
(rpmbuild, on Fedora 44). Current version: **1.0-6**.

| File | Installed as | Why |
|---|---|---|
| `60-iceland-coexist.install` | `/usr/lib/kernel/install.d/` | writes a kernel's files into `fedora44/` (kernel, initramfs, the device tree of `DTB_VARIANT`) and its BLS entry `fedora-<kver>-f44.conf` into the shared `loader/entries/`; never changes the default boot entry; removes them again at `kernel-install remove`. Since 1.0-6 a new kernel without its own `DTB_VARIANT` tree gets the default kernel's tree when the two kernels' own trees are byte-identical (else its own tree, with a warning) |
| `45-iceland-vmlinuz-first.install` | `/usr/lib/kernel/install.d/` | (1.0-3) puts `/boot/vmlinuz-<kver>` in place before dracut runs, so dracut never targets the read-only EFI partition for a new kernel |
| `coexist.conf` | `/etc/iceland/coexist.conf` | `DTB_VARIANT` (the device-tree variant of Fedora's entries, `standard` = the kernel's own tree) and `SUBDIR` (Fedora's subdirectory) |
| `install.conf` | `/etc/kernel/install.conf` | `layout=other`: no BLS type-1 directory layout, the plugin above writes the files |
| `02-iceland-coexist.conf` | `/etc/dracut.conf.d/` | a generic (not host-only) initramfs |
| `52-iceland-coexist-hold.repo` | `/usr/share/dnf5/repos.override.d/` | keeps Fedora's Mesa, gst-plugins-good, libcamera, GRUB and shim from replacing the tablet's builds |
| masks (`/dev/null` links) | `/etc/kernel/install.d/` | Fedora's own boot-entry, device-tree, GRUB, UKI and tuned plugins and iceland-device's `96-iceland-trial` / `90-iceland-dtb`: this layout writes its entries itself |
| `iceland-oneshot` | `/usr/bin/` | (1.0-4) one-shot boot entries: `iceland-oneshot-NAME.conf` = a copy of the default entry with added or dropped options (`--args` / `--drop`, marker `iceland.oneshot=NAME`); GRUB cannot write `grubenv` on this tablet, so Linux clears the one-shot: in the initramfs before udev starts and, as a fallback, on every boot. `initramfs --side` / `--promote` / `--undo` builds the running kernel's initramfs with the module and boot-tests it as a one-shot first. Since 1.0-6 it also finds the boot file system on `/dev/mapper/iceland-*` (iceland-device 0.28-32's device-mapper option) |
| `dracut-oneshot-module-setup.sh`, `iceland-oneshot-clear.service`, `03-iceland-oneshot.conf` | `/usr/lib/dracut/modules.d/91iceland-oneshot/`, `/etc/dracut.conf.d/` | the initramfs part of `iceland-oneshot` (acts only with `iceland.oneshot=` on the command line) |
| `iceland-oneshot-consume.service` | `/usr/lib/systemd/system/` (enabled in `sysinit.target`) | the fallback that clears a one-shot entry from the running system |

Requires `iceland-device >= 0.28-30`, `kernel-install`, dracut, `grub2-editenv`, util-linux and diffutils.
