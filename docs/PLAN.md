# OnePlus Pad 4 (`iceland`, SM8850P) — mainline Linux plan v4

Version 4, 2026-09-28 (evening). Replaces v3 (v3's history is in git; v2 and the discovery notes are in
[RESEARCH.md](RESEARCH.md)).

Changes from v3:
- **Target OS: Fedora 44 Workstation (GNOME), aarch64** (user's decision, 2026-09-28 20:38). pmOS is no longer first:
  pmaports has no OnePlus 15 package to derive from, and Fedora 44 already runs GNOME on the tablet in RAM.
- Phases 2 and 3 are done or nearly done; Phase 4 is rewritten as the Fedora install; the remaining hardware moves to
  Phase 5 in the PC's "B" order.

## Goal

**Fedora 44 Workstation with GNOME, installed on the Pad 4**, booted ABL → U-Boot → EFI → GRUB → our kernel + DTB,
with kernel updates through dnf and no reflashing.
- Other distros (Arch Linux ARM, pmOS, Debian testing, Kali, latest Ubuntu) become **later, optional** targets
  (Phase 7). They reuse the same kernel source and config (`distro-neutral.config` keeps SELinux and AppArmor both
  built in).
- Long-term, **upstream** remains the real "any distro" answer: once the Pad 4 is in mainline Linux and U-Boot,
  Fedora's own kernel boots it and our kernel package disappears.

## What is verified (all by RAM boot; nothing has been written to the tablet)

| Item | Evidence |
|---|---|
| U-Boot RAM-booted by ABL: display, USB fastboot, UFS read, EFI | diag runs 3–4 |
| Linux 7.3-rc4 + infiniti (138) + Pad 4 queue (0001–0035) | iceland-linux 6fcead4 |
| Native display: MSM DRM, dual DSI + DSC, **144 Hz** (stock timing), KTZ8869 backlight | pc-007, pc-023 |
| CPU thermal trips mirroring stock, tested under load; board and flash thermistors | pc-002/003, pc-021 |
| Touch firmware (SRAM download); the touch screen is a libinput device. The pen is ignored by libinput (resolution missing) | pc-008, pc-024 Y9 |
| Wi-Fi (WCN7860, ath12k) + scan; Bluetooth (hci_qca) | pc-009/010 |
| Battery and USB-C data over pmic-glink (SoCCP), units fixed; lid switch; rear flash LEDs | pc-011..019 |
| ADSP boots; the sound card registers (no playback yet) | pc-010, pc-017 |
| Firmware extractor on the tablet (modem_a/bluetooth_a/persist read-only; `super` not yet) | pc-023 |
| **Fedora 44 in RAM:** systemd as PID 1, dnf through the PC, the Adreno 840 renders (freedreno, Mesa 26.2.3), Wayland 120 Hz (glmark2 1836), **GNOME Shell 50 with gdm autologin** | pc-024 Y7–Y9 |
| The early resets were the kit's own `/dev/mem` sampler, not the kernel | pc-022 |

## Architecture

```
ABL (stock) → U-Boot (boot partition, or RAM-booted from the PC) → blkmap userdata → EFI boot manager
  → shim/GRUB on the Fedora ESP → BLS entry → our kernel (kernel-iceland rpm) + our DTB + dracut initramfs
  → Fedora 44 Workstation (btrfs root in userdata)
```
- **U-Boot** (`iceland-u-boot`): infiniti-mainline U-Boot + the Pad 4 board. It never writes storage (fastboot flash
  compiled out).
- **Kernel** (`iceland-linux`): one source + one config. Boot-critical drivers built in; BT/ath12k as modules.
- **Firmware:** extracted from the user's own tablet and OTA, never committed or uploaded.
- **Device files** (UCM, udev, units): one FHS tree under `/usr/lib`.

## Phases

Tablet rule for every phase: RAM boot and allowlisted commands only, until a step explicitly says otherwise and the
user agrees. The PC session runs kits unattended (KNOWLEDGE §2 rule 11), so kits must log their own state.

### Phase 1 — U-Boot bring-up ✅
### Phase 2 — First Linux shell from RAM ✅
### Phase 3 — Core hardware over RAM boot ✅ (except items that need a person: touch/pen/lid events, 5/6 GHz, OTG)

### Phase 4 — Fedora 44 Workstation (GNOME) install

**4a. RAM rehearsal (no writes; in progress on the PC).** This uses the proven `phase4/` workflow: Container Base
rootfs → dnf through `tools/relay/usb-proxy.py` → `rootfstar` hand-back → `ROOTFS_URL`, with systemd as PID 1 in
`ROOTFS_MODE=pid1` (never `switch`).
- Y10: boot `rootfs-gnome.tar.gz` and judge the GNOME session from the journal. The user gives a 30 s touch window.
- **Rehearse the real install in RAM too.** Loop-mount the official `Fedora-Workstation-Disk-44` raw image's
  partitions *in RAM on the tablet* (from the PC over `ROOTFS_URL`, or a trimmed copy). Install our kernel rpm,
  firmware and config into it with the same steps as 4c, and boot that tree in `pid1` mode. This proves the final
  image's userland on the tablet before anything is written.

**4b. Packages and configuration (built in the cloud or on the PC; reproducible, GPL-clean).**
1. **`kernel-iceland` rpm** (own spec, not `make binrpm-pkg`, so the name doesn't clash with Fedora's `kernel`):
   - `/usr/lib/modules/<kver>/{vmlinuz,dtb/qcom/kaanapali-oneplus-iceland.dtb,…}` + modules + System.map + config;
   - `%posttrans`: `kernel-install add` (dracut initramfs + BLS entry in XBOOTLDR);
   - a **kernel-install plugin** that copies the DTB to the ESP as `dtb/qcom/kaanapali-oneplus-iceland.dtb`, where
     U-Boot's EFI boot manager looks for `fdtfile`, and also writes a BLS `devicetree` line as a second path;
   - BUILD_INFO with the source commits; the source rpm is kept next to it (GPL).
2. **Fedora's own kernel must not take over:**
   - `/etc/sysconfig/kernel`: `DEFAULTKERNEL=kernel-iceland`, `UPDATEDEFAULT=no`;
   - dnf `excludepkgs=kernel kernel-core kernel-modules*` in the image (Fedora's kernel has no Pad 4 support).
   - This is revisited once the Pad 4 is upstream.
3. **Kernel command line (BLS options):**
   - `root=UUID=… rootflags=subvol=root`, the image's own;
   - `clk_ignore_unused pd_ignore_unused regulator_ignore_unused` until the drivers are complete;
   - `console=tty0`; no earlycon;
   - `lsm=` including `selinux`: Fedora runs SELinux enforcing, which our config supports.
4. **dracut** config (`/usr/lib/dracut/dracut.conf.d/iceland.conf`):
   - UFS, PHY, pinctrl and clocks are built in, so no hostonly surprises;
   - add the GPU firmware (`gen80200_*`, the zap) and the touch firmware to the initramfs, so the display and GPU
     come up early (troikoss lesson).
5. **Firmware** into `/usr/lib/firmware/updates/` (takes precedence over and doesn't conflict with Fedora's
   `linux-firmware`):
   - written by `fw-extract.sh` on the tablet from its own partitions;
   - the `super` contents (GPU zap, vpu, Wi-Fi odm BDF/regdb, touch, `tfa98xx.cnt`, pen) come from the PC's OTA until
     `super` is mapped;
   - the audio topology and the converted touch firmware come from the repo tools;
   - built on the device or PC as a local, never-uploaded `iceland-firmware` rpm, or just files.
6. **Device overlay rpm `iceland-device`** (GPL, in the repo):
   - UCM with **volume caps** (no speaker playback before TFA9865 protection);
   - `ath12k` loaded late (a modprobe `softdep` or a unit after USB);
   - BD address from wlan0's MAC (`btmgmt public-addr` unit);
   - libinput quirks until the pen reports resolution;
   - logind lid handling; sleep hooks in `/usr/lib/systemd/system-sleep/`;
   - journald size cap; `sleep.target` unmasked if Fedora masks it (Tab S6 trap).

**4c. Building the install image (on the PC; nothing on the tablet).** Start from the official
`Fedora-Workstation-Disk-44-*.aarch64.raw.xz` (checksum-verified by `phase4/fetch-fedora.sh`; DOS label: 500 MB ESP,
2 GB XBOOTLDR, btrfs root):
- install the three rpms above offline (`dnf --installroot`, or on the tablet during 4a);
- add the ESP `dtb/` file;
- `touch /.autorelabel` (SELinux labels after offline changes);
- convert it with `img2simg` into a **sparse** image.

**4d. Before any write (the user's explicit OK; in this order).**
1. Accept that flashing userdata **erases Android's data on both slots** (LineageOS on slot b uses the same userdata).
   Repartitioning is not an option (hard stop), so this is the only way to get disk space.
2. File-level copy of `/data/vendor` (TEE/TA files, needed later by QTEE/minkipc) and persist, read-only, from
   LineageOS with adb root. The raw userdata backup is FBE-encrypted and useless for this.
3. Confirm the existing 151-partition backup and the stock 11.A.38 package are on the PC.

**4e. The writes (each one approved separately; the user runs the commands).**
1. **userdata ← the sparse Fedora image, flashed with stock ABL `fastboot flash userdata`** (ABL supports sparse images;
   max-download 805 MB, so it goes in chunks automatically).
   - Our U-Boot keeps fastboot flash compiled out. No custom writer is needed, and nothing else on the UFS is touched.
   - Alternative if ABL refuses: `dd` from a RAM-booted Linux through a guarded installer (GPT name `userdata` only,
     size check, typed confirmation).
2. **Boot it tethered first:** `fastboot boot` U-Boot from the PC, then U-Boot → `bootefi bootmgr` → Fedora.
   - GNOME first-boot, dnf updates (with our kernel held), and a reboot loop.
3. **Only then choose where U-Boot lives** (the user's decision): the boot partition of the **current** slot (no slot
   switching), keeping the other slot's Android boot image for rollback. Rollback = flash back the saved boot image
   (the proven 2-minute loop).
- **Exit:** Fedora 44 GNOME boots from UFS without the PC; our kernel updates through dnf; rollback tested once.

### Phase 5 — Remaining hardware (on Fedora; test changes by RAM boot first, then as rpm updates)
In the PC's "B" order (KNOWLEDGE §13):
1. suspend/resume (s2idle + RTC wake);
2. Wi-Fi under NetworkManager, 5/6 GHz and regdomain;
3. BT address + pairing;
4. audio: speakers on Primary TDM, the TFA9865 protection, UCM, headset, mics;
5. touch/pen/lid events: nt36536 pen `input_abs_set_res`, lid closing;
6. USB host/OTG with PD, DisplayPort alt mode;
7. GPU extras: turnip when Mesa lands the a840, GPU cooling;
8. video (Iris), cameras (SC1320CS/SC820CS + CAMERA_ICP), sensors (SSC via hexagonrpcd), keyboard accessory;
9. `super` mapped for the extractor;
10. kernel loose ends (SoundWire port counts, pstore across PS_HOLD).

### Phase 6 — Upstreaming (runs alongside)
Pad 4 DTS, KTZ8869, the NT36536 panel desc (already in the upstream driver), touch driver cleanup, TFA9865, the
generic fixes found here, and the U-Boot board:
- the MDSS all-power-domains change (0026);
- the video-mode splash handling (0025);
- the pmic_glink early channel (0028);
- the kaanapali DPU clock factor (0035).

Coordinate with map220v and infiniti-mainline. Publishing or contact only when the user asks.

### Phase 7 — Other distros (optional, later)
Same kernel source and config. Per distro, only a kernel package wrapper (PKGBUILD/apk/deb), an initramfs hook, and
a loader entry with `devicetree` and `lsm=`.
- Arch Linux ARM and pmOS first (pmOS needs our own `device-oneplus-iceland`), then Debian testing, Kali and the
  latest non-LTS Ubuntu.
- Not supported: Debian stable and Ubuntu LTS (their Mesa is too old for the a840).

## Hard stops (ask the user)
Any write to the tablet (first: Phase 4e) · slot switching · repartitioning · firmware not from this tablet's 11.A.38
(exception: upstream linux-firmware files for the GPU) · publishing or contacting maintainers.

## Where things live
Private GitHub repos:
- `iceland-mainline`: plan, knowledge, facts, tests, firmware manifest, tools, `phase4/`, relay;
- `iceland-linux`: kernel patch queue, config, CI;
- `iceland-u-boot`: U-Boot patch queue, test scripts.

Shared memory of both sessions: [KNOWLEDGE.md](KNOWLEDGE.md). Test history: `docs/tests/README.md`. PC results:
`relay/results/`.
