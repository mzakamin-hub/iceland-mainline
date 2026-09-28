# OnePlus Pad 4 (`iceland`, SM8850P) — mainline Linux plan v3

Version 3, 2026-09-28. Replaces v2 (kept with all discovery notes in [RESEARCH.md](RESEARCH.md)).
Changes from v2: built on what has been **verified on the tablet**, a faster order of work, and a realistic
distro scope (one kernel source packaged per distro, tiered distro support, upstreaming early).

## Goal

A mainline kernel + U-Boot for the OnePlus Pad 4 that boots current arm64 distros through EFI:
**pmOS first**, then **Fedora** and **Arch Linux ARM**, then best-effort Debian testing / Kali / latest Ubuntu.
Long-term the real "any distro" path is **upstream**: once the Pad 4 support is in mainline Linux and U-Boot,
distributions' own kernels boot it and our packaging disappears.

## What is verified (on the tablet or by build)

| Item | State | Evidence |
|---|---|---|
| ABL accepts RAM boot (`fastboot boot`) of a header v4 image | ✅ | U-Boot test 1 |
| U-Boot runs when packed as header v4, kernel = gzip(u-boot.bin) | ✅ | diag run 3 test A |
| ABL framebuffer 0xfc800000, 3392x2400 | ✅ | diag run 3 test B (white) |
| U-Boot console on panel, U-Boot USB fastboot enumerates | ✅ (Windows driver to bind) | diag run 3 test C |
| U-Boot reads UFS / partitions, U-Boot log over USB | ⏳ | diag run 4 |
| Kernel: Linux 7.3-rc4 + infiniti (138) + Pad 4 series (20) builds, 0 warnings, Pad 4 drivers present | ✅ build | `iceland-linux`, `7.3.0-rc4-iceland-00158` |
| Device facts: ABL memory map (20 segments, 11.5 GiB), 68 reserved regions, I2C/SPI map, live + stock DTs, firmware inventory | ✅ | `docs/device-facts/` |
| Firmware manifest: 21 files, stock sources + sha256 | ✅ | `firmware/manifest.tsv` |

## Architecture (unchanged, now partly proven)

```
ABL (stock, untouched) → U-Boot (RAM boot now; boot_a later) → EFI → systemd-boot/GRUB → our kernel + DTB → distro
```
- **U-Boot** (`iceland-u-boot`): infiniti-mainline U-Boot + Pad 4 board. Can't write storage during bring-up.
- **Kernel** (`iceland-linux`): one source + one config (`distro-neutral.config`), both SELinux and AppArmor
  built in; `lsm=` chosen per distro in its boot entry. Boot-critical drivers built in; BT/ath12k as modules.
- **Firmware**: extracted from the user's own tablet (never committed), one tree for all distros.
- **Device files** (UCM, udev, sensor/sleep units): one FHS tree under `/usr/lib`, all distros.
- **Per distro**: only a kernel package wrapper, an initramfs hook, a boot entry template.

## Faster order of work

The main speed-ups against v2:
1. **Boot Linux from RAM through U-Boot** (`fastboot boot` of kernel+DTB+initramfs into U-Boot's fastboot) — no
   userdata wipe, no flashing, a new kernel is tested in ~1 minute. Android stays usable until Linux is good.
2. **One distro until the hardware works**: pmOS only (best bring-up tooling: debug initramfs, USB networking,
   device-package flow; the OnePlus 15 already has a pmOS package to copy). Other distros only in phase 7.
3. **Reuse before writing**: every subsystem is checked first against infiniti-mainline (same SoC), map220v
   (same device), the Lenovo Y700 notes (same SoC tablet) and upstream — the troikoss "missing layer" rule.
4. **Upstream as we go**, not at the end: each driver/DT change that works on the tablet goes to a
   `upstream/` queue, coordinated with map220v and infiniti-mainline (only after the user says so).
5. **Cut scope that doesn't help the goal**: Mu-Silicium fallback dropped (U-Boot works); direct-ABL Linux boot
   kept only as a diagnostic; Debian stable / Ubuntu LTS not supported (Mesa too old for Adreno 840).

## Phases

Tablet rule for every phase: the user runs every tablet command; the agent's test scripts only use allowlisted,
non-writing commands until a phase explicitly says otherwise and the user agrees.

### Phase 1 — U-Boot bring-up (in progress)
- [x] RAM boot accepted, U-Boot runs, framebuffer, USB fastboot enumerates
- [ ] Run 4: bind Windows driver, UFS partition tables, `getvar all`, U-Boot log (`oem console`)
- [ ] Enable U-Boot `fastboot boot` of an Android boot image (Linux kernel + DTB + initramfs) → Phase 2
- Exit: U-Boot's fastboot usable from Windows; UFS partitions listed.

### Phase 2 — First Linux shell, from RAM (next)
- Initramfs: pmOS debug initramfs (or a small busybox one) with USB **NCM** networking + telnet/SSH.
- Boot: `fastboot boot linux.img` into U-Boot (no writes). U-Boot passes the DT with ABL's memory map.
- Cmdline: `clk_ignore_unused pd_ignore_unused console=tty0`; display on simpledrm first; remoteprocs one at a
  time (SM8750 precedent: ADSP start killed simplefb).
- Diagnostic fallback only: ABL direct boot with the memory map baked in (`docs/device-facts/memory-map.txt`).
- Exit: shell over USB, `dmesg` saved, `/proc/device-tree/model` = "OnePlus Pad 4".

### Phase 3 — Core hardware (RAM boot, Android still installed)
Order by value: CPU/thermal **with cooling maps before any load** (Y700: 100 °C in 2 s) → UFS read-only mounts →
native display (NT36536, dual DSI; test item: DSI1 vs DSI0 sync) + KTZ8869 backlight → touch → Wi-Fi (firmware
from manifest) → battery/charging (check `charger_pd` / Oplus charger firmware) → lid (TLMM 98) → Bluetooth
(real BD address from persist). Firmware extractor (`firmware/`) written and run once by the user here.
- Exit: usable touch desktop over RAM boot, Wi-Fi, battery %, safe thermals.

### Phase 4 — pmOS install (first write to the tablet; needs the user's explicit OK)
- Before: file-level copy of `/data/vendor` TEE files + persist (script from Phase 1 captures), full backup exists.
- `boot_a` ← U-Boot (rollback: stock boot_a, proven 2-minute loop); `userdata` ← pmOS disk image (erases Android).
- pmOS device package `device-oneplus-iceland` derived from `device-oneplus-infiniti` (read from Nura/pmaports).
- Exit: pmOS boots from UFS, kernel updates via packages without reflashing.

### Phase 5 — Remaining hardware (on pmOS)
GPU (Adreno 840, firmware in initramfs, Mesa ≥ 26) → audio (6× TFA9865, AudioReach topology, UCM; volume capped
until speaker protection) → suspend/resume → sensors (hexagonrpcd + libssc; `get_in_bufs2` patch) → video (iris)
→ USB-C DP → cameras (CAMSS from infiniti; sensors at 0x20/0x6c on i2c9) → pen.

### Phase 6 — Upstreaming (runs alongside 3–5)
Pad 4 DTS, KTZ8869, NT36536 panel desc (already in the upstream driver), touch driver cleanup, TFA9865, U-Boot
board. Coordinate with map220v and infiniti-mainline. Publishing/contact only when the user asks.

### Phase 7 — More distros
Per distro: kernel package wrapper (rpm / PKGBUILD / deb), initramfs hook (dracut / mkinitcpio /
initramfs-tools), systemd-boot or GRUB entry with `devicetree` and `lsm=`, distro kernel held back.
- Tier 1 (tested every release): pmOS edge, Fedora current, Arch Linux ARM.
- Tier 2 (best effort): Debian testing, Kali, latest non-LTS Ubuntu.
- Not supported: Debian stable, Ubuntu LTS (Mesa/hexagonrpcd too old) unless backports appear.
- Installer: identity/size checks, writes only boot_a + userdata, typed confirmation, rollback bundle.
- Exit: the same kernel build passes `tools/hwcheck.sh` on all Tier 1 distros.

## Hard stops (ask the user)
Any write to the tablet (first one is Phase 4) · slot switching · slot b before it has 11.A.38 firmware ·
firmware not from this tablet's 11.A.38 · publishing or contacting maintainers.

## Where things live
Private GitHub repos (all work in the cloud; nothing on the user's PC except tablet test runs):
`iceland-mainline` (plan, facts, tests, firmware manifest, tools) · `iceland-linux` (kernel patch queue,
config, CI) · `iceland-u-boot` (U-Boot patch queue, test scripts). Test history: `docs/tests/README.md`.
