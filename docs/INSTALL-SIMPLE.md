# Installing Fedora on the OnePlus Pad 4: the short version

This page is the short path. The full reference is
[`tools/installer/README-INSTALLER.md`](../tools/installer/README-INSTALLER.md): every check, every command, and what
to do when something differs. Read it once before you start.

> **Status:** the installer refuses to flash (`flash_allowed: false`) until the release image has passed a RAM-boot
> test on a tablet. Until then you can download and back up, but not install.

Installing erases all Android data on the tablet. The installer cannot back up Android's data because it is
encrypted. Copy your own files off the tablet first.

## What you need

- A OnePlus Pad 4 (model OPD2514) with the **boot loader already unlocked**. The installer never unlocks it.
- **LineageOS on slot b**, booted and working, with Developer options > **USB debugging** and **Rooted debugging** on.
  This is the setup the install was tested from.
- Battery above 60 %, a good USB cable, and the PC's own USB port.
- A Windows PC with PowerShell (5.1 or 7) and Google's
  [platform-tools](https://developer.android.com/tools/releases/platform-tools) (`adb.exe`, `fastboot.exe`), for
  example in `C:\platform-tools`.
- About 30 GB of free disk space on the PC.

## 1. Download

From the release page, download `Install-Pad4Linux.ps1`, `release-manifest.json` and `README-INSTALLER.md` into one
folder. The image parts are listed in the manifest. The installer downloads them itself, checks every SHA-256,
and joins the parts:

```powershell
.\Install-Pad4Linux.ps1 -Manifest .\release-manifest.json -Phase Preflight -Execute
.\Install-Pad4Linux.ps1 -Manifest .\release-manifest.json -Phase Download  -Execute
```

Without `-Execute` every phase is a dry run: it prints the commands and touches nothing.

## 2. Back up

With LineageOS running and the tablet connected:

```powershell
.\Install-Pad4Linux.ps1 -Manifest .\release-manifest.json -Phase Backup -Execute
```

This step only reads. It copies the boot partitions (including the `boot_b` undo file) to
`%USERPROFILE%\Pad4Linux\backups\` and checks each copy. It also saves your tablet's Bluetooth address in
`bdaddr.txt`. Run it on the day of the install, and keep the folder: it is private to your tablet, so never upload it.
Add `-FullBackup` to also copy every other partition except `userdata` (about 18 GB more). You need that copy if you
ever want to return to stock.

## 3. Install

Put the tablet in fastboot mode: switch it off, then hold **Volume Down + Power** and connect USB. Then run:

```powershell
.\Install-Pad4Linux.ps1 -Manifest .\release-manifest.json -Phase Flash -Execute
```

The installer writes exactly two partitions. Before each write it shows the partition, the file, its size and its
SHA-256, and waits for you to type the confirmation:

1. `userdata`: the Fedora image. Type `I understand my Android data is erased`, then `userdata`.
2. `boot_b`: the U-Boot boot loader. Type `boot_b`.

Between the two writes the tablet starts Fedora three times from the PC, in RAM only. If Android appears and offers a
factory reset, choose **Try again** or power off. Never choose the reset.

## 4. First boot

1. Fedora's setup wizard starts: language, keyboard, network, and your user account.
2. On the first boot the system grows to fill the whole `userdata` partition. This happens once and on its own.
3. Open a terminal and set the Bluetooth address that the installer printed (it is also in `bdaddr.txt` in your
   backup folder):

   ```sh
   sudo iceland-provision --bdaddr <address the installer printed>
   ```

4. Back on the PC, put the tablet in fastboot mode once more and check the boot slot:

   ```powershell
   .\Install-Pad4Linux.ps1 -Manifest .\release-manifest.json -Phase VerifySlot -Execute
   ```

## 5. Updates

- Fedora's updates come through **Software** or `sudo dnf upgrade`, as on any Fedora system.
- Run `iceland-update-check` to see which updates are held back for testing on this tablet first.
- New tablet kernels are published on the [iceland-linux releases](https://github.com/mzakamin-hub/iceland-linux/releases)
  page. Install one with `sudo dnf install ./kernel-iceland-<version>.aarch64.rpm`. The previous kernel stays in the
  boot menu as a fallback.

## 6. The way back

- **Undo the boot loader write:** in fastboot mode, run
  `.\Install-Pad4Linux.ps1 -Manifest .\release-manifest.json -Phase UndoBootB -Execute`.
  This puts your saved `boot_b` back, so LineageOS starts again, without its old data.
- **Return to stock:** not automated. It needs the `-FullBackup` copy from step 2 and the stock OxygenOS images. See
  section 8 of [`README-INSTALLER.md`](../tools/installer/README-INSTALLER.md).
- **If anything looks different from this page:** stop and write nothing more. To leave U-Boot, hold Volume Down +
  Power for about 15 s to reach the boot loader. Then check section 9 of
  [`README-INSTALLER.md`](../tools/installer/README-INSTALLER.md).
