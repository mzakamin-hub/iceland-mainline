# 05 - Porting the work to other distributions (Debian in detail; Arch and postmarketOS-style in brief)

State: 14 Oct 2026 (kernel queue q89g, `iceland-device` 0.28-8, `iceland-firmware` 11.A.38-3, Fedora 44 installed on the
owner's tablet on 13 Oct). **Nothing in this document has been tested on the tablet with a distribution other than
Fedora 44.** The project's target is Fedora (the owner's decision of 28 Sep). This is a map of what you would have to
redo, built from what the Fedora work needed and why.

Sources (public repositories):
- `iceland-linux`: `configs/distro-neutral.config`, `packaging/fedora/`, `scripts/`;
- `iceland-mainline`: `packaging/iceland-device/` (README, spec, `files/`), `packaging/sensors/` (README, specs),
  `docs/PLAN.md` (Phase 7), `docs/guide/04-BUILD-YOUR-OWN.md`;
- `iceland-u-boot`: `patches/0002-iceland/` (the install build, patches 0004-0010).

## 1. What is distribution-neutral and what is not

| Piece | Neutral? | Notes |
|---|---|---|
| Kernel source (`iceland-linux` queue) and `distro-neutral.config` | **yes** | its header says so: one kernel for Fedora, Debian / Ubuntu, Arch, postmarketOS. Boot-critical drivers built in, firmware users as modules |
| U-Boot (`iceland-u-boot`) and the boot chain ABL -> U-Boot -> EFI | **yes** | any EFI loader (GRUB, systemd-boot) can follow U-Boot |
| Firmware from your tablet | **yes** | the same files under the same names for every distribution (`iceland-firmware` carries the generic part) |
| UCM profile, AudioReach topology | **yes** | standard ALSA UCM2 paths |
| udev rules, hwdb entry, systemd units and drop-ins, logind / sleep / journald drop-ins | **mostly** | standard systemd paths; Debian has them in the same places (usrmerge) |
| Battery guard, thermal policy, refresh-rate, Wi-Fi country, camera-focus scripts | **mostly** | Python 3 and shell, sysfs-based. Their dependencies are listed below |
| `kernel-iceland.spec`, `kernel-install` plug-ins, dnf / dnf5 configuration, the release pin, protected packages, grubby, BLS entries, the snapshot / trial-boot units built on libdnf5 actions | **no, Fedora-specific** | rewrite per distribution (sections 2, 5) |
| SELinux as the default LSM | **Fedora's choice** | Debian and Ubuntu use AppArmor: see section 2.3 |

**Mesa is the hard requirement.**
- The Adreno 840 (gen8) needs **Mesa 26.0 or newer**: freedreno OpenGL and turnip Vulkan. Fedora 44 was chosen
  partly because it ships Mesa 26.x (`phase4/README.md`); the project's Fedora 44 image runs Mesa 26.2.4.
- `docs/PLAN.md` Phase 7 therefore rules out Debian stable and Ubuntu LTS: their Mesa is too old.
- Use **Debian testing / unstable**, or a backport of Mesa >= 26.0. Check with `apt policy mesa-vulkan-drivers
  libgl1-mesa-dri`.

## 2. The kernel package

### 2.1 What the Fedora package does (for comparison)

`packaging/fedora/kernel-iceland.spec` (in `iceland-linux`):
- Repackages a `scripts/build.sh` output as an installonly package: `/usr/lib/modules/<ver>/` with `vmlinuz`, the
  modules, `config`, `System.map`, `dtb/qcom/kaanapali-oneplus-iceland.dtb` and `BUILD_INFO`.
- `%posttrans` runs `kernel-install add`, which runs dracut and writes the BLS entry.
- The plug-in `90-iceland-dtb.install` copies the device tree to `<ESP>/dtb/qcom/kaanapali-oneplus-iceland.dtb`.
  That is where U-Boot's EFI boot manager loads `fdtfile` and applies ABL's memory map before it starts shim / GRUB.
- The rpm version maps `7.3.0-rc7-iceland-NNNNN-gHASH` to `7.3.0~rc7.iceland.NNNNN.gHASH` (q89g: `00426`,
  `g520e85da9244`).

### 2.2 Debian: `linux-image` from the same tree

```sh
cd iceland-linux && scripts/prepare.sh ./src && scripts/build.sh ./src ./out     # config as in 04, section 3
make -C src O="$PWD/out" ARCH=arm64 LLVM=1 -j"$(nproc)" bindeb-pkg               # untested here
# -> ../linux-image-7.3.0-rc7-iceland-..._arm64.deb (+ linux-headers, linux-libc-dev)
```

- Debian's `bindeb-pkg` installs the device trees under `/usr/lib/linux-image-<version>/` (`qcom/...`). Nothing
  puts them on the ESP. Add a hook that does what `90-iceland-dtb.install` does:
  - `/etc/kernel/postinst.d/zz-iceland-dtb` (and a matching `postrm.d` hook);
  - it copies the newest kernel's `qcom/kaanapali-oneplus-iceland.dtb` to `<ESP>/dtb/qcom/` (write to `.new`, then
    rename);
  - it keeps the previous one in `<ESP>/dtb.prev/`.
- `flash-kernel` is **not** needed: it serves boards whose U-Boot reads `boot.scr`. Our U-Boot uses its EFI boot
  manager.
- `/etc/kernel/postinst.d/initramfs-tools` and `zz-update-grub` run automatically. Make sure the DTB hook runs too;
  the `zz-` prefix orders it late.
- **Keep Debian's own kernels off:** they have no Pad 4 support. Do not install `linux-image-arm64`, and pin it
  away (`/etc/apt/preferences.d/` with `Pin-Priority: -1`). This is the equivalent of Fedora's dnf exclude.

### 2.3 Security module: AppArmor instead of SELinux

`distro-neutral.config` builds SELinux **and** AppArmor (`SECURITY_APPARMOR=y`). But its
`CONFIG_LSM="landlock,lockdown,yama,loadpin,safesetid,selinux,ipe,bpf"` starts SELinux and **not** AppArmor. On
Debian / Ubuntu either:
- boot with `lsm=landlock,lockdown,yama,apparmor,bpf` (in `GRUB_CMDLINE_LINUX`); or
- build with your own `CONFIG_LSM` that lists `apparmor` (and drop `DEFAULT_SECURITY_SELINUX`).

Without a policy SELinux only initialises and allows everything (the RAM tests showed that), so this does not break a
boot. AppArmor confinement, though, simply does not happen until you change it.

### 2.4 Firmware compression

The kernel reads plain, `.xz` and `.zst` firmware (`FW_LOADER_COMPRESS_XZ` / `_ZSTD`, added for Fedora's
xz-compressed firmware). Debian's firmware packages work either way.
- If your distribution's linux-firmware lacks the Kaanapali GPU files (`qcom/gen80200_sqe.fw`, `gen80200_gmu.bin`,
  `gen80200_aqe.fw`), take them from upstream linux-firmware.
- The generic Pad 4 files are in `iceland-firmware` (11.A.38-3, with sha256 per file); the unit-specific files come
  from your own tablet (`04-BUILD-YOUR-OWN.md` section 5). Put them under `/usr/lib/firmware/updates/` (searched
  first) or `/lib/firmware/`.

## 3. Initramfs: dracut (Fedora) vs initramfs-tools (Debian)

### 3.1 What our dracut module does

`iceland-device` 0.28-8, the dracut pieces in `files/` (`dracut-iceland-carrier`, `dracut-iceland-module-setup.sh`,
`dracut-iceland-rollback`, `dracut-iceland-rehearsal`, `90-iceland-dracut.conf`, `91-iceland-install-dracut.conf`):

1. **Read-only first.** Before anything opens a disk, every UFS block device except `userdata` (and the LUN that
   holds it) gets the kernel's read-only flag (BLKROSET). The same rule (`59-iceland-storage-ro.rules`) is
   installed for the running system. udisks then ignores those devices.
2. **The carrier.**
   - It finds the GPT partition named `fedora` (dual boot) or `userdata`.
   - It checks for a GPT header ("EFI PART") at byte 4096.
   - It attaches `losetup --partscan --direct-io=on` over it. Linux does not scan a partition table nested inside a
     partition, so the root (`loop0p3`) only appears this way. The installed system's root is a btrfs filesystem on
     this loop device.
   - udev then finds `root=UUID=...` as on any disk.
3. **The rehearsal** (optional, a development path): the same, with an NBD disk from the PC over the USB gadget
   instead of `userdata`.
4. **Rollback hooks:** boot a snapshot as the root.

### 3.2 Debian equivalent

| dracut piece | initramfs-tools equivalent |
|---|---|
| module-setup.sh `install()` | a hook in `/etc/initramfs-tools/hooks/iceland`: `copy_exec /usr/sbin/losetup` (busybox's `losetup` has no `--partscan` / `--direct-io`), `copy_exec /usr/sbin/blockdev`, the udev rule into `/usr/lib/udev/rules.d/` of the image |
| the carrier service before `initrd-root-device.target` | a `local-top` script in `/etc/initramfs-tools/scripts/local-top/iceland`: set the read-only flags, find `/dev/disk/by-partlabel/userdata` (or `fedora`), check the GPT signature, `losetup -P --direct-io=on`, `udevadm settle`. `local-top` runs before the root is mounted |
| `91-iceland-install-dracut.conf` (what goes in) | `/etc/initramfs-tools/modules` + `MODULES=` in `initramfs.conf` |

**What must not be in the initramfs** (boot-log finding P1-a, not published):
- A driver that needs firmware probes before the root is mounted, and remoteproc does not retry. `qcom_q6v5_pas` (ADSP
  / CDSP) from the initramfs logged "Direct firmware load ... failed with error -2" and stayed down.
- Either keep `qcom_q6v5_pas` and other firmware users out (`MODULES=dep`, or a short `MODULES=list`; there is no omit
  list in initramfs-tools), or copy their firmware in with a hook. The image is then private.
- The installed Fedora system has its SoCCP, ADSP and CDSP firmware in the initramfs (the charger co-processor, USB-C
  and pmic_glink come up before the network disk), while Wi-Fi, Bluetooth and video load from the root. Follow that
  split if your image needs the same bring-up order.

**Kernel command line**:
- **No** `clk_ignore_unused pd_ignore_unused regulator_ignore_unused` on the installed system (the install
  workflow's decision of 3 Oct, finding F24). The rehearsal boots ran without them, with the display driver bound and
  Linux switching off unused clocks, power domains and regulators. The device package's `iceland-cmdline` removes them
  from every boot entry and `/etc/kernel/cmdline`. Keep the lesson: never boot a display configuration that has not
  been seen working - an unmanaged panel once lost power.
- `lsm=...` (section 2.3).

## 4. The disk image: 4 KiB sectors

Every UFS LUN has **4096-byte logical blocks** (`02-HARDWARE.md` section 5). A Debian image made for 512-byte disks
does not boot through U-Boot's blkmap. When you build the image file on a PC (all untested here; the Fedora
builder does the equivalent, and its tools are not in the public repositories):
- Attach the file with `losetup --sector-size 4096 -P`.
- Make a GPT on it in 4 KiB units: `sfdisk` / `sgdisk` on the 4 KiB loop device. Use the standard types: ESP,
  Linux root (arm64), optionally an extended boot partition.
- `mkfs.vfat -F 32 -S 4096` for the ESP; ext4 and btrfs with 4096-byte blocks / sector size.
- Size it to `userdata` exactly if you want the root to grow into the whole partition (systemd-repart works on GPT
  only).
- The written form is an Android sparse image (`img2simg`). Writing it is the install (owner's / your decision);
  read `07-INSTALL-REVIEW.md` first.
- U-Boot's install environment knows only the partition names `fedora` (a separate dual-boot partition) and
  `userdata`. A Debian disk in its own partition must be named `fedora`, or change `fedora_blkmap` in the U-Boot
  environment.

## 5. The device package, piece by piece, mapped to Debian

From `packaging/iceland-device/README.md` and the spec (version 0.28-8). The file names are in `packaging/iceland-device/files/`:

| Piece (installed path on Fedora) | Purpose | On Debian |
|---|---|---|
| `81-iceland-ssc.rules` (udev) | sensor hub: enable accel / proximity, mount matrix, start hexagonrpcd and iio-sensor-proxy when `/dev/fastrpc-adsp` appears | same file in `/usr/lib/udev/rules.d/` |
| `71-iceland-dma-heap.rules` | CMA dma-heaps root-only, so libcamera's soft ISP takes the system heap. The final kernel does not offer CMA as dma-heaps at all (F2), so the rule has nothing left to restrict | keep it for a kernel that still has `CONFIG_DMABUF_HEAPS_CMA` |
| `59-iceland-storage-ro.rules` + `iceland-storage-ro` | every other UFS partition read-only | same; also into the initramfs (section 3) |
| `61-iceland-battery.hwdb` | `CHARGE_LIMIT=80,85` for UPower's "Preserve Battery Health" | same (`/usr/lib/udev/hwdb.d/`, then `systemd-hwdb update`); needs a UPower with charge-threshold support (what GNOME's "Preserve Battery Health" uses) |
| UCM: `/usr/share/alsa/ucm2/Qualcomm/kaanapali/OnePlus-Pad4/*.conf` + `conf.d/kaanapali/oneplus-OnePlusPad4.conf` link | speakers, microphones, the speaker level cap | same paths (alsa-ucm-conf layout) |
| `/usr/lib/firmware/qcom/kaanapali/OnePlus-Pad4-tplg.bin` | the AudioReach topology, built from `audio/topology/OnePlus-Pad4.m4` with `m4` + `alsatplg` over upstream audioreach-topology 993a17d | build the same way (`alsatplg` comes with alsa-utils or a separate topology-tools package, depending on the distribution) |
| `sleep-iceland.conf`, `logind-iceland.conf`, `journald-iceland.conf` (systemd drop-ins) | s2idle only; the cover suspends on battery and locks on a charger; journal cap | same |
| `upower-iceland.conf` drop-in | UPower after udev's first scan (it reads the thresholds once) | same |
| `iceland-battery-guard` + service + `battery-guard.conf` | stock charging limits as a second layer, the charge limit, awake on a charger, the thermal charge cap, the charger input cut at a hot USB-C connector | same; Python 3 (+ PyGObject for D-Bus) |
| `iceland-thermal` + service + `thermal.conf` | stock's skin-temperature gears (only lowers limits) | same; the private model file stays private |
| `iceland-refresh` + `refresh.conf` | 60 Hz on battery, 120 Hz on mains | same (uses the compositor's D-Bus; GNOME-specific) |
| `iceland-power-profiles`, `tuned/iceland-*` profiles | GNOME's three power modes mapped to stock's CPU ranges, through **tuned-ppd** | Debian ships tuned; use tuned with tuned-ppd if available, else power-profiles-daemon's defaults (stock's per-mode caps are lost) |
| `iceland-bdaddr` + service | the tablet's Bluetooth address from `/etc/iceland/bdaddr` (written at install, never shipped) | same |
| `iceland-wifi-country` + service | Wi-Fi regulatory country from `/etc/iceland/wifi-country` | same (needs `iw`) |
| `60-iceland-wifi-powersave.conf` (NetworkManager) | Wi-Fi power saving | same |
| `hexagonrpcd-adsp-sensorspd-iceland.conf`, `iio-sensor-proxy-iceland.conf`, `iceland-ssc-wait`, `iceland-ssc-resume.service` | sensor service order, readiness wait, restart after a suspend | same, once the sensor packages exist (section 6) |
| `sc1320cs.yaml`, `sc820cs.yaml` (`/usr/share/libcamera/ipa/simple/`) | the cameras' black level for the soft ISP | same path |
| `51-iceland-camera.conf` (WirePlumber) | hides the raw CAMSS video nodes | same, but **WirePlumber 0.5.17 stalls with it** (0 camera sources); require >= 0.5.18 or leave the rule out |
| `iceland-camera-focus` + service | lens at stock's start position while the rear camera streams | same |
| `machine-info` | GNOME's About shows "OnePlus Pad 4" | `/etc/machine-info` |
| `iceland-npu` / `iceland-npu-off.service` | was: stop the CDSP on battery. **Do not use the stop**: it costs CX collapse until reboot (area-combo-66 / -67, not published); the CDSP keeps running | keep the CDSP running |
| fwupd guard (`iceland-fwupd-guard`, `DisabledPlugins=` in `/etc/fwupd/fwupd.conf`) | fwupd cannot write boot code, EFI variables or the UFS device firmware | same file and setting on Debian. **Important:** fwupd lists the UFS storage as updatable by default |
| `iceland-cmdline` (grubby) | removes the three `*_ignore_unused` arguments from every boot entry and `/etc/kernel/cmdline` (F24) | Debian: keep them out of `GRUB_CMDLINE_LINUX` in `/etc/default/grub` (+ `update-grub`) |
| `80-iceland-kernel.conf`, `50-iceland-fedora-hold.repo`, `51-iceland-fedora-44-pin.repo`, `49-iceland-no-system-upgrade.rules`, `iceland-protected.conf` | no distribution kernels, rescue initramfs, akmods / dkms, boot loaders; GRUB, shim and firmware held; release pinned; our packages protected | `/etc/apt/preferences.d/` pins (`Pin-Priority: -1` for `linux-image-*` except ours; holds via `apt-mark hold grub-efi-arm64 shim-signed firmware-*`). The polkit rule names PackageKit, which Debian's GNOME Software uses; Debian release upgrades are not offered by GNOME Software anyway |
| `iceland-repo-sync`, `iceland-local.repo` | a local dnf repository filled from the PC | a local apt repository (`file:` source with `reprepro` / `aptly`), or `dpkg -i` |
| snapshot (libdnf5 actions, `iceland-snapshot.actions`) + trial boot (`96-iceland-trial.install`, `iceland-trial`, GRUB `next_entry`) + `iceland-grub-setup` | btrfs snapshot before every transaction, a boot-once trial of new kernels | no direct equivalent: snapper + grub-btrfs for snapshots; GRUB's `grub-reboot` for a boot-once trial, with your own confirm service |
| `kernel-install` plug-ins (`90-iceland-dtb.install`) | device tree to the ESP | the `postinst.d` hook of section 2.2 |
| `iceland-slot-mark` (qbootctl) | marks the installed slot good at boot (0.28-8 fix for the installed loop-root layout) | an equivalent is needed only if your boot chain has ABL's slot counters (see `GLOSSARY.md`, "A/B slots") |

## 6. The sensor stack (hexagonrpc, libssc, iio-sensor-proxy)

All physical sensors sit behind the ADSP's sensor hub. Linux reaches them through FastRPC and QMI. Three user-space
programs are needed (`packaging/sensors/README.md`):

| Program | Upstream pin | Needed change |
|---|---|---|
| `hexagonrpc` | github.com/linux-msm/hexagonrpc `598b591` (v0.5.0 + 19) | patch 0001 (serves `/odm/etc/sensor`), systemd units, user `fastrpc`, udev rule `60-hexagonrpc.rules` for the device nodes |
| `libssc` | codeberg.org/DylanVanAssche/libssc `54dd13e` (v0.4.4 + 8) | none (built without its test / mocking subdirectories) |
| `iio-sensor-proxy` | gitlab.freedesktop.org/hadess/iio-sensor-proxy **3.9** | build with `-Dssc-support=enabled`, plus patch 0001 (poll sensors claimed during discovery) and patch 0002 (a work-around for mutter 50 never claiming the accelerometer after a boot in touch mode; drop it once mutter is fixed) |

On Debian:
- Build them with meson (dependencies as in the README: glib2, libqmi, protobuf-c, gobject-introspection, libgudev,
  polkit, systemd).
- `libssc` goes before `iio-sensor-proxy`.
- Keep the distribution's older iio-sensor-proxy from replacing yours: pin it.
- hexagonrpcd needs the tablet's own DSP file tree at `/usr/share/qcom/kaanapali/OnePlus/iceland` (unit-specific; see
  `02-HARDWARE.md` section 7 and `04-BUILD-YOUR-OWN.md` section 5).
- On the Pad 4 it still runs as root, because the hub writes below its registry directory.

## 7. Cameras: libcamera with the GPU soft ISP

Results of the GPU soft-ISP measurement (area-combo-77, -84, -88, -91; the logs are not published):
- **libcamera 0.7.1 already contains the GPU soft ISP and uses it by default.** It takes 2.3 ms instead of about
  21 ms of CPU per 1080p frame at 30 fps, with the same pictures and power within 0.2 W. Select it with
  `LIBCAMERA_SOFTISP_MODE` or `/etc/libcamera/configuration.yaml`.
- Fedora 44 now ships libcamera **0.7.1-2**. An earlier local 0.7.1 build added three upstream fixes (framing anchored
  top-left with garbage columns at the right edge; no CPU fallback when EGL fails; an EGL context leak of about 19.8 MB
  of GPU memory per camera start). That local build is no longer used. **Whether Fedora's 0.7.1-2 carries all three
  fixes is unverified: check them on your distribution's libcamera.** Fedora's 0.7.2 with some of these was withdrawn
  from Fedora 44 for a flicker regression.
- PipeWire's libcamera plug-in (`pipewire-libcamera` on Debian) and xdg-desktop-portal give browsers and GNOME
  Camera (Snapshot) their camera.
- **The DMA-heap rule** (`71-iceland-dma-heap.rules`) is required only on a kernel that offers CMA as a dma-heap (the
  final kernel does not, F2); there the stream fails on the 32 MiB CMA heap ("Format negotiation failed").
- **WirePlumber >= 0.5.18** if you use the rule that hides the raw CAMSS nodes.
- **The sensor driver** (SC1320CS / SC820CS) is in the kernel queue (in-tree in `iceland-linux`), so any
  distribution's kernel package built from the queue carries it. Its tuning files are in the `iceland-device` package.
  Without them there are no cameras, on any distribution.
- Autofocus does not exist in libcamera's simple pipeline yet. The focus helper holds the lens at stock's start
  position.

## 8. Video and browsers

- Iris hardware decoding is used by GStreamer's `v4l2*dec` elements (GNOME's player, GNOME Web inside its sandbox).
  H.264, HEVC, VP9 (including 10-bit) and AV1 decode in hardware on the Pad 4 and are bit-exact against the AOSP
  test vectors.
  - The BT.601 colour fix for the Iris decoder is in the kernel (queue patch 0292).
  - Streams labelled BT.601 with the 6/1/6 code points need GStreamer 1.28.9 (merge request 12699), not in the
    Fedora 44 build used so far (unverified for your distribution).
- Firefox decodes in software on Fedora: Fedora's `ffmpeg-free` has no V4L2-M2M H.264. Whether Debian's full FFmpeg
  plus Firefox uses the hardware decoder is **untested**.

## 9. Desktop choices

- **Tested: GNOME 50 on Wayland** (Fedora 44 Workstation set, 33 of 33 default apps open, the on-screen keyboard
  appears on a tap, auto-rotate through iio-sensor-proxy, GNOME's power modes, the charge-limit switch).
- **Untested:** KDE Plasma (and Plasma Mobile), Phosh, others. What they need is the same kernel side (DRM / KMS,
  libinput for touch and pen, iio-sensor-proxy for rotation, UPower for the battery and charge limit) plus their own
  equivalents of the GNOME-specific parts (`iceland-refresh`, the power-profile mapping).
- The pen is a libinput tablet device (kernel queue patch 0036).
- Pogo keyboard cover: a kernel input device (queue patches 0094-0097), so it works on any desktop.

## 10. Arch Linux ARM (brief)

- Kernel: a `PKGBUILD` that runs `scripts/prepare.sh` + `scripts/build.sh`, or packages their output. It installs
  `/usr/lib/modules/<ver>/`, `vmlinuz` and the DTB, with a pacman hook that copies the DTB to `<ESP>/dtb/qcom/`.
- Initramfs: a mkinitcpio hook (`/etc/initcpio/install/iceland` + `/etc/initcpio/hooks/iceland`) doing what section
  3.1 lists. Keep firmware users out of the image.
- Boot: GRUB or systemd-boot on the ESP. EFI variables are not stored by U-Boot, so install with `--removable` /
  `--no-nvram` (GRUB) or rely on the default `\EFI\BOOT\BOOTAA64.EFI` path.
- Arch ARM's Mesa and libcamera are usually current. Check the three libcamera fixes of section 7 and WirePlumber
  >= 0.5.18.
- `lsm=` as for Debian if you use AppArmor.

## 11. postmarketOS-style setups (brief)

The owner ruled out postmarketOS for their tablet (28 Sep). For someone else:
- A `device-oneplus-iceland` package would carry the device files (section 5), a `linux-oneplus-iceland` package the
  queue, and a firmware package built **locally** from the user's own tablet for the unit-specific files. The generic
  files are in `iceland-firmware` and may be used in that package with their sha256 checked.
- pmOS's common Qualcomm flow flashes an Android boot image with the kernel into `boot`, and often a vbmeta with
  verification disabled.
  - Both conflict with this project's rules (never write `vbmeta`; see the AVB note in `03-BOOT-AND-PARTITIONS.md`
    section 3).
  - The direct ABL -> Linux path is also unproven here: ABL picks the device tree from `vendor_boot`, not from our
    image.
  - The U-Boot + EFI path (`deviceinfo` UEFI boot) matches this project's chain and is the safer basis.

## 12. Fedora-specific decisions you can drop or replace

| Fedora choice | Why it was made | On another distribution |
|---|---|---|
| SELinux enforcing | Fedora default | AppArmor via `lsm=` |
| dnf5 excludes, release pin, protected packages | keep boot code and kernels under the project's control | apt pinning and holds |
| btrfs snapshots + trial boot via libdnf5 actions + BLS / GRUB `next_entry` | restorable updates | snapper / grub-btrfs, `grub-reboot` |
| shim | Fedora's ESP layout | optional: U-Boot does not enforce Secure Boot; GRUB can be `\EFI\BOOT\BOOTAA64.EFI` directly |
| tuned + tuned-ppd profiles | GNOME's power modes with stock's ranges | tuned (if packaged) or power-profiles-daemon |
| `kernel-iceland` rpm | installonly, three kept | `linux-image` deb with your own version scheme |
