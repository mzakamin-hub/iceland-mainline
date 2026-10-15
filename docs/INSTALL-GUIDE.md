# OnePlus Pad 4: installing Fedora 44 GNOME on the tablet

This guide describes the install of Fedora 44 Workstation (GNOME) on the OnePlus Pad 4 (`iceland`, OPD2514): what the
install consists of, what you need, the steps, and what works afterwards. The reasons behind each rule (the partition
choice, verified boot, the slot counter, the update policy) are in [INSTALL-PLAN.md](INSTALL-PLAN.md); the boot chain is
explained in [guide/03-BOOT-AND-PARTITIONS.md](guide/03-BOOT-AND-PARTITIONS.md), and the risks with their safeguards in
[guide/07-INSTALL-REVIEW.md](guide/07-INSTALL-REVIEW.md).

> **Read this first.**
> - The procedure has been carried out on one tablet. It started from LineageOS 24.0 on slot b (slot a without an
>   Android system), with stock 11.A.38 firmware on both slots. A different starting state (stock OxygenOS, slot a
>   active, another firmware release) has not been tried.
> - The project does not publish a ready-to-write disk image, nor the tool that built it: an install image contains
>   files that belong to one tablet (its sensor calibration registry and its Bluetooth address). Section 2 lists what the
>   image must contain. The kernel, U-Boot and all packages are published and can be built (see
>   [guide/04-BUILD-YOUR-OWN.md](guide/04-BUILD-YOUR-OWN.md)).
> - The install writes two partitions. Both writes are yours to make, after your own checks. Nothing in the project's
>   repositories writes to a device.
> - "Not verified" below means exactly that: the step is part of the design, but nobody has run it.

## 1. What the install consists of

| Partition | What is written | Size | How it is undone |
|---|---|---|---|
| `userdata` | the whole Fedora disk (EFI partition, `/boot`, btrfs root) as an Android sparse image; its unpacked size equals the partition | 237,159,641,088 bytes (`0x3737D0F000`) on the tablet it was done on; read yours with `fastboot getvar partition-size:userdata` | the return to stock (section 8) erases it; or write the image again |
| `boot_b` (the boot partition of the active slot) | the U-Boot **install build** from [iceland-u-boot](https://github.com/mzakamin-hub/iceland-u-boot), with an AVB hash footer made for your tablet's current `boot_b` | 100,663,296 bytes (`0x6000000`) | write back the copy of `boot_b` you saved before (section 4, step 4) |

Nothing else is ever written: not the boot firmware (`xbl*`, `abl*`, `tz*`, `hyp*`, ...), not the radio and DSP
firmware, not the per-device data (`persist`, `cdt`, `ddr`, ...), not the security state (`devinfo`, `keystore`,
`frp`, ...), not Android's `super`, `vbmeta*`, `vendor_boot*`, `init_boot*`, `dtbo*` or `recovery*`, and no partition
table. As long as these stay untouched the tablet's own boot loader (ABL) keeps working, and its fastboot can put
everything back.

How the installed tablet starts:

1. ABL starts `boot_b`. The tablet is unlocked, so ABL shows its orange warning and continues.
2. U-Boot shows a boot menu for 5 s (Fedora by default, or the boot loader's fastboot; Volume Down moves, Power
   selects). It maps `userdata` as a disk with 4096-byte blocks and starts Fedora's shim and GRUB from it through EFI.
3. GRUB starts `kernel-iceland` with the Pad 4 device tree. The initramfs makes every other internal partition read-only
   and puts a partitioned loop device over `userdata`; the root is btrfs on it. SELinux is enforcing.
4. At the first start the root grows to the whole of `userdata`, and GNOME's first-boot setup asks for your user
   account.

## 2. What you need

**The tablet**

- A OnePlus Pad 4 with an **unlocked** boot loader (unlocking is described in
  [guide/04-BUILD-YOUR-OWN.md](guide/04-BUILD-YOUR-OWN.md), section 1.3; it erases the tablet).
- Stock firmware 11.A.38 on both slots. Never flash or boot firmware older than 11.A.38 (anti-rollback).
- Battery above 60 %.
- About 13 GB of data are written. Everything on Android's data partition is lost with the first write.

**The PC**

- Android platform tools (`adb`, `fastboot`), the USB port and cable you have already used with this tablet, the PC on
  mains power and not going to sleep.
- About 30 GB free for the backup, the stock images and the install files.

**The install files**

- **The disk image** (`fedora-iceland.sparse.img`). It is built from the official `Fedora-Workstation-Disk-44` aarch64
  raw image (checksum- and signature-checked; `phase4/fetch-fedora.sh` downloads it) and must have:
  - a GPT in 4096-byte units with the standard partition types, and the EFI partition rebuilt as FAT32 with
    4096-byte sectors (U-Boot refuses the original 512-byte FAT16 layout: "FAT sector size mismatch"; Linux would
    read the original DOS table in 4 KiB units); `/boot` (ext4) and the btrfs root copied unchanged;
  - `kernel-iceland`, `iceland-device`, `iceland-firmware`, the sensor packages (`hexagonrpc`, `libssc`,
    `iio-sensor-proxy`) and Fedora's `qbootctl`, shim and GRUB;
  - the tablet's own unit-specific files in `/usr/lib/firmware/updates`, extracted read-only from its partitions (the
    sensor calibration registry and the Bluetooth address; see [guide/04-BUILD-YOUR-OWN.md](guide/04-BUILD-YOUR-OWN.md)
    section 5);
  - no preset user, no password, no SSH keys, no Wi-Fi networks, an empty machine-id, root locked;
  - an unpacked size that equals your `userdata` exactly.
- **U-Boot, two forms of the same install build** (`scripts/build.sh` in iceland-u-boot): the plain image for the
  tethered RAM boot, and the same image with an AVB hash footer for `boot_b`. The footer must be made for your tablet's
  current `boot_b` (section 4, step 4): partition name `boot`, partition size 100,663,296 bytes, signed with the key
  that your `vbmeta_b` chains `boot` with, with your `boot_b`'s rollback index, and with its OS version and security patch
  level (ABL hands both to the secure world). The boot header values in `uboot.pin` must match your `boot_b` too.
  The project's footer tool is not published; `avbtool add_hash_footer` is the standard tool for this.
- Write down the SHA-256 of every file you will write, and check it again right before its write.

## 3. The rules for the whole procedure

1. Only `fastboot flash userdata ...` and `fastboot flash boot_b ...` are ever typed. Never `fastboot -w`, `flashall`,
   `update`, `set_active`, `erase`, `format` or `flashing lock`, and no third-party flashing tool.
2. Writes are made only in the tablet's own boot loader: `fastboot getvar product` must answer `canoe`. U-Boot's own
   fastboot (it answers `oneplus-iceland`) cannot write and is never used for a write.
3. If a screen, a message or a number differs from this guide: stop. Do not improvise and do not retry a write
   with other arguments. The boot loader is intact in every state this guide can produce (section 9).
4. Leaving U-Boot or a stuck screen: hold **Volume Down + Power** (about 15 s) until the boot loader's fastboot screen
   shows. Holding Power alone restarts the tablet, which counts as another boot of slot b (section 6).

## 4. Before the first write (read only)

**Step 1 - a full backup.** A read-only, checksummed copy of every partition except `userdata`. It holds the
calibration and identity of your tablet, which no download replaces. Reading partitions needs root on Android; the
project used a temporary system image (DSU) for this, without flashing anything. Keep a second copy on another disk and
never upload it.

**Step 2 - the stock images** of 11.A.38 with their checksums, for the way back (section 8).

**Step 3 - your own data.** Copy your files from Android, and Android's per-device runtime data (`/data/vendor`, with
`adb root`) for the record. The first write erases all of Android's data.

**Step 4 - save the current `boot_b`** from the running Android system (with `adb root`, read only). This file is the
undo of the second write, and the footer of section 2 is made from it. Take it from the system that runs today: an older
backup (for example one taken before a custom ROM was installed) has another header, key and rollback index. At the same
time check that `misc` does not hold `boot-recovery` or `boot-fastboot`, and that `vbmeta_b` chains `boot`.

**Step 5 - the slot flags and the rescue keys.** Switch the tablet off, hold **Volume Down + Power** until the boot
loader's fastboot screen shows, connect USB and read:

```
fastboot getvar product                # canoe
fastboot getvar unlocked               # yes
fastboot getvar current-slot           # b
fastboot getvar slot-successful:b
fastboot getvar slot-unbootable:b
fastboot getvar slot-retry-count:b
fastboot getvar partition-size:boot_b  # 0x6000000
fastboot getvar partition-size:userdata
fastboot reboot
```

These commands only read. Note the values. This key combination is the door that must work whatever is in `boot_b`.

**Step 6 (recommended) - a RAM boot of the install U-Boot.** `fastboot boot` of the plain install build loads it into
RAM only: on an Android tablet it maps the encrypted `userdata`, finds no Fedora and waits in its own fastboot
(`fastboot getvar product` answers `oneplus-iceland`). Return with Volume Down + Power or `fastboot reboot`. Nothing is
written, and the slot flags do not change.

Before the image was written, the project also booted the very same image from RAM through the installed chain, with the
disk served by the PC over USB, and ran its acceptance and update / rollback checks on it ([INSTALL-PLAN.md](INSTALL-PLAN.md)
section 4). That tooling is not published; if you build your own image, test it the same way before you write it.

## 5. Write 1: the Fedora image into `userdata`

```
adb reboot bootloader
fastboot getvar product                    # canoe
fastboot getvar current-slot               # b
fastboot getvar partition-size:userdata    # must equal the image's unpacked size
fastboot flash userdata fedora-iceland.sparse.img
```

ABL's `max-download-size` is 805 MB, so the PC's fastboot sends the sparse image in pieces and reports each
("Sending sparse 'userdata' 1/N ... OKAY", "Writing 'userdata' ... OKAY"); expect several minutes. Do not touch
the cable. If it stops with an error or the cable drops, the boot loader is not
affected: stay in (or re-enter) fastboot and run the same command again.

**Proof, still tethered:**

```
fastboot boot u-boot-iceland-usb.img       # the plain install build; RAM only
```

U-Boot's text, GRUB's menu (3 s), then Fedora's first-boot setup: language, keyboard, Wi-Fi, privacy and **your user
account and password** (the image has none). Switch off and repeat the tethered boot until Fedora reaches the desktop
reliably.

Until write 2, a power-on without the PC still starts Android, which reports that its data is damaged and offers a
factory reset. **Never confirm the reset** (it would erase Fedora). Choose "Try again" or power off, and keep this stage
short: an Android boot that cannot use its data may leave a `boot-recovery` command in `misc` (section 9).

## 6. Write 2: U-Boot into `boot_b`

Only after Fedora started tethered. Switch the tablet off, hold **Volume Down + Power**, connect USB:

```
fastboot getvar product                    # canoe (the tablet's own boot loader)
fastboot getvar current-slot               # b
fastboot flash boot_b u-boot-iceland-footered.img
fastboot getvar slot-successful:b          # read the flags before the reboot
fastboot getvar slot-retry-count:b
fastboot reboot
```

The write takes a few seconds. **What the flash does to the slot:** flashing `boot_b` clears slot b's *successful*
flag and sets its retry count to the maximum. From then on every normal power-on of slot b uses one try until a running
system marks the slot successful; at zero ABL marks the slot unbootable. On the installed system the service
`iceland-slot-mark` runs Fedora's `qbootctl -m` once after a good boot. This works on the installed layout (the root
on a loop device over `userdata`) from `iceland-device` 0.28-8 on: use an image with 0.28-8 or newer. Entering
fastboot with the keys, and U-Boot's "Boot loader (fastboot)" entry, do not use a try.

**Proof:**

1. Unplug the PC. Switch the tablet off and on a few times: the boot menu appears, and Fedora reaches the desktop.
2. In Fedora: `journalctl -u iceland-slot-mark` shows the marking, and `qbootctl` lists slot b as active, successful and
   bootable.
3. Optionally read the flags in the boot loader again (Volume Down + Power, then the `getvar` lines of section 4 step 5):
   `current-slot` is `b`, `slot-unbootable:b` is `no`, `slot-successful:b` is `yes`.

If slot b is still not marked and the retry count goes down from boot to boot, stop booting the tablet and restore
`boot_b` from the saved copy:

```
fastboot flash boot_b boot_b-saved.img      # the file of section 4, step 4
```

Android then starts without its data; Fedora stays in `userdata` and can still be started tethered as in section 5.

A later U-Boot update is the same write with a newly footered build, made from the `boot_b` that is on the tablet at
that time.

## 7. After the install

- **What works:** the feature list, [FEATURES.md](FEATURES.md). In short: display at 3392 x 2400 with 30 to 144 Hz,
  touch, pen, auto-rotate, the GPU (OpenGL 4.6, Vulkan 1.4), hardware video decode and encode, the six speakers and the
  microphones, Wi-Fi 2.4 GHz, Bluetooth, battery reporting and charge limits, thermal control with stock's limits,
  suspend and resume, the sensors and both cameras.
- **First checks:** Wi-Fi, sound, rotation, one suspend and resume; Settings > About shows "OnePlus Pad 4"; Settings >
  Power > Battery Charging offers "Preserve Battery Health" (stops at 80 / 85 %; on by default).
- **Sound:** the defaults are "Speakers" (a protection chain: 150 Hz high-pass, compressor with +9 dB make-up, limiter
  at -1 dBFS) and "Internal microphones (voice processing)" (echo canceller, then a +14 dB limiter). The outputs named
  "... (raw, unprotected)" bypass the protection: do not use them for loud playback.
- **Brightness and heat:** when the tablet gets warm, the thermal service lowers the backlight to stock's level through
  the kernel; GNOME's slider keeps your value. The skin-temperature policy (stock's 60 / 61 / 70 C for CPU, GPU and
  charging) is active.
- **Display idle refresh:** the kernel has an idle refresh mode for this panel, but it is off (it measured 74.8 Hz
  instead of 60 Hz). Do not add `msm.dpu_idle_refresh_ms` to the command line.
- **Charging:** the tablet does not fast-charge (SuperVOOC is not supported); the stock temperature and current limits
  are enforced by the kernel and the battery guard.
- **Updates:** GNOME Software or `dnf upgrade`, as on any Fedora. Updates can only change files inside `userdata`. A
  read-only btrfs snapshot of the root is taken before every transaction, each with a "Roll back to ..." entry in GRUB's
  menu. Fedora's own kernels are never installed; `kernel-iceland` and the project's packages come from the tablet's
  local repository. A new kernel boots once as a trial and becomes the default after a confirmed boot. Fedora's
  repositories hold back only the sensor programs and `alsa-ucm` (`iceland-update-check` lists what is held); GRUB,
  shim, libcamera and Fedora's firmware packages update from Fedora. The release stays on Fedora 44 until 45 has been
  tested on the tablet.
- **Never from inside Fedora:** no partitioning tool on the internal storage, no `dd` to `/dev/sd*`, no firmware or
  boot-loader tool. The device package makes the other partitions read-only, so such a mistake fails instead of doing
  harm; do not remove that rule.
- **Rescue:** a RAM boot from the PC (`fastboot boot` of a Linux image) starts without using the storage; from there the
  installed root can be mounted, checked, rolled back to a snapshot or given another kernel. The project's RAM rescue
  images are not published.

## 8. Back to stock OxygenOS

| From | Do |
|---|---|
| Before any write | nothing: a reboot starts Android |
| After write 1, before write 2 | return to stock (below), or write the image again |
| Only undo write 2 | `fastboot flash boot_b boot_b-saved.img` (the copy of section 4, step 4; not an older backup) |
| Full return to stock | in the boot loader's fastboot: the stock boot set (`boot`, `init_boot`, `vendor_boot`, `dtbo`, `recovery`, `vbmeta`, `vbmeta_system`, `vbmeta_vendor`, `pvmfw`) on both slots and `super`, from the stock 11.A.38 images or your backup; erase `userdata` and `metadata` (`fastboot -w`); make slot a active. Never any firmware partition |
| Locked boot loader as from the factory (optional) | only when the tablet is verifiably exactly stock |

**Not verified:** the full return to stock was written as a script and dry-run, but never executed; a way back to
LineageOS after the install is not written down.

## 9. If something is not as described

| What you see | What it means | What to do |
|---|---|---|
| `fastboot flash userdata` fails or the cable drops | incomplete image in `userdata`; the boot loader is untouched | re-enter fastboot (Volume Down + Power) and run the same command again |
| After write 1, Android says its data may be corrupt | expected between write 1 and write 2 | "Try again" or power off; never "Factory data reset" |
| The tethered boot after write 1 does not reach Fedora | an image or chain problem | do not make write 2; RAM-boot a rescue image for a look, or return to stock |
| After write 2 the boot loader shows a verified-boot error (not its usual orange warning) and stops | ABL refused `boot_b`, most likely a missing or wrong AVB footer | Volume Down + Power; restore `boot_b` from the saved copy; no `set_active` |
| `getvar current-slot` reads `a` after write 2 | ABL marked slot b unbootable and switched | write nothing else; restore `boot_b`; ask before any `set_active` |
| The retry count of slot b goes down from boot to boot | nothing marks the slot successful | check `journalctl -u iceland-slot-mark`; if it is not marked, restore `boot_b` before the count reaches zero |
| U-Boot's text, then the screen stays on, no Fedora | U-Boot found no Fedora and waits in its fastboot (the install build never resets or powers off by itself) | hold Volume Down + Power for the boot loader; with the PC, `fastboot oem console` (read only) shows U-Boot's log |
| A `grub>` prompt or a GRUB error | GRUB found no configuration (damaged `/boot`) | Volume Down + Power; repair `/boot` from a RAM rescue boot |
| After write 2 the tablet shows LineageOS recovery ("Can't load Android system") | `misc` still holds a `boot-recovery` command from an Android boot between the writes | choose "Reboot system now" (it clears the command), never "Factory data reset" |
| A switched-off tablet on a charger starts U-Boot / Fedora | ABL starts the boot partition in charger mode | expected; charger starts do not use a try |
| Fastboot does not appear with Volume Down + Power | cable, driver, or the tablet is still on | hold Volume Down + Power about 15 s, try again, try the other end of the cable |
| Fedora does not start after an update | a Fedora-side problem | the previous kernel or a snapshot from GRUB's menu; else a RAM rescue boot |
| Anything not in this table | - | stop; write nothing further |

The rows for a verified-boot error, a slot switch to `a`, the LineageOS recovery screen and the charger start follow
from Qualcomm's open ABL source and the design; they have not been observed on the tablet.
