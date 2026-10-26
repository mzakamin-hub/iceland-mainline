# iceland-mainline

Mainline Linux for the OnePlus Pad 4 (`iceland`, model OPD2514, Qualcomm SM8850P). The tablet runs **Fedora 44** on a
mainline kernel, with **GNOME** (the desktop the install sets up) or **KDE Plasma 6**. The tablet's own boot loader (ABL) stays in place. Our U-Boot, in the `boot_b` partition,
shows a short boot menu and starts Fedora from a disk image in `userdata`. The menu can also start **BlissROM**, an
Android custom ROM, on the same tablet (dual boot).

This repository is the hub: the install guides, the list of working features, the device package (`iceland-device`)
and the tools. The kernel, U-Boot, the firmware and the Android trees have their own repositories, listed in
[Repositories](#repositories).

> **The install erases Android's data and changes two partitions.** Read [Before you start](#before-you-start) and
> the backup part of [Manual install](#manual-install) first.

## Boot chain

```
power on
  |
ABL             the tablet's own boot loader (OnePlus, closed). The project never writes it.
  |             On an unlocked tablet it shows an orange warning and goes on.
  v
boot_b          U-Boot, the project's install build. Boot menu, 5 s timeout:
  |
  +-- Fedora (default)
  |     starts the `fedora` partition if there is one, else the disk image in `userdata`
  |     -> shim -> GRUB -> kernel-iceland + initramfs -> Fedora 44 on the btrfs root
  |
  +-- BlissROM (dual boot only: it is shown only when it is safe, see DUAL-BOOT.md)
  |     Android's kernel from `boot_a`, with the ramdisk and device tree that ABL prepared
  |
  +-- Boot loader (fastboot)
        back to ABL's fastboot, where the writes are made
```

Storage on the tablet's main storage unit (LUN 0) after the dual-boot split:

```
LUN 0  +-----------------------------+--------------------------------+-----------+
       | fedora (new)                | userdata (smaller)             | 1 MiB     |
       | Fedora disk image           | BlissROM's encrypted data      | unused,   |
       | (ESP, /boot, btrfs root)    |                                | kept free |
       +-----------------------------+--------------------------------+-----------+
```

Without the split, `userdata` holds the whole Fedora disk image and Android no longer starts. The split is part C of
the manual install. Before it, the menu shows Fedora and the boot loader only.

## What works

This is a summary of [docs/FEATURES.md](docs/FEATURES.md), which has the details and what was measured. Features that
are still being worked on are not listed. Anything that is not in the list is not claimed to work.

| Area | What works |
|---|---|
| Display and input | The panel at its native 3392 x 2400 over dual DSI with DSC; refresh 30 to 144 Hz; backlight with GNOME's slider and automatic brightness (on by default); touch; pen; lid; power and volume keys; auto-rotate in tablet mode; the keyboard cover on the pogo pins; smooth window moves under load. |
| Graphics | The Adreno 840 GPU: OpenGL 4.6 and OpenGL ES 3.2 (Mesa), Vulkan 1.4 through turnip. Hardware video decode (H.264, HEVC, VP9, AV1) and encode (H.264, HEVC). |
| Audio | The sound card from the audio DSP; all six speakers in stereo behind a speaker-protection filter, as loud as stock; both microphones, with echo cancellation on the default input; headsets on the USB-C port. |
| Connectivity | Wi-Fi on 2.4 GHz and 5 GHz (6 GHz is not tested yet); Bluetooth with pairing in GNOME; USB device mode and a USB network link; USB host mode (keyboards, mice, sticks, hubs); an external monitor over USB-C DisplayPort. |
| Power and charging | Charging with stock's limits per charger type; pen charging; battery level, health and time estimate in GNOME; the charge limit at 80 / 85 % ("Preserve Battery Health"); bypass charging; the battery safety guard at stock's limits; low-battery current limits. |
| Thermal | CPU, GPU and skin-temperature limits from stock's values. |
| Sleep | Suspend (s2idle) and resume; the power key, the alarm, the cover, the keyboard and the charger wake the tablet; Wi-Fi comes back after a wake. Overnight drain of about 0.35 % per hour, measured on one tablet. |
| Sensors and camera | Accelerometer, compass, light, proximity and gyroscope through the sensor hub; the 13 MP rear and 8 MP front cameras stream through libcamera; GNOME Camera works with both; the rear flash works as a torch. |
| Desktop | GNOME 50 with Fedora 44 Workstation's apps; KDE Plasma 6 on Wayland with auto-rotate, automatic brightness, the charge limit in its power settings, suspend and Discover. |
| Virtual machines | Protected VMs on the Gunyah hypervisor with crosvm and the Virtual Machines app ([iceland-gvm](https://github.com/mzakamin-hub/iceland-gvm), [iceland-vms](https://github.com/mzakamin-hub/iceland-vms)): Linux guests from cloud images with NAT networking (vhost-net), shared folders and a serial console; 3D in the guest (OpenGL through virgl, Vulkan through venus) with GPU-composited desktops in the VM window; touch input modes, fullscreen and a VNC display; an opt-in shared-memory mode (the tablet can read that VM's memory; 3D OpenGL and Vulkan work there); an option that sends desktop shortcuts such as Super and Alt+Tab to the VM; an opt-in native GPU context in which the VM's own Mesa draws directly on the Adreno 840; an optional QEMU-Gunyah backend with 3D OpenGL in QEMU's window or over VNC; Windows 11 ARM guests with Remote Desktop, ssh and a clean Shut Down from the app. ISO installs are not supported yet. |
| Android apps | DroidLoom: Android 17 in a container (binder is in the kernel since q90m), each app in its own window with Close and a left-edge swipe for Back, an AndroidVM menu folder ([iceland-droidloom](https://github.com/mzakamin-hub/iceland-droidloom)). |
| System and boot | Boot from U-Boot through EFI into Fedora 44; kernel updates with dnf (a new kernel boots once as a trial); Fedora marks the boot slot successful; the dual-boot menu (Fedora / BlissROM v20.1); Fedora 44 Workstation's GNOME apps. |

Known limits, from the guides: the tablet does not fast-charge (SuperVOOC is not supported). Without the dual boot,
Android does not start after the Fedora install. The display's idle refresh (30 Hz after 1 s on a static screen)
is set by iceland-device 0.28-32 (`IDLE_RR` in `/etc/iceland/boot.conf`); do not add the option by hand with older
packages ([INSTALL-GUIDE section 7](docs/INSTALL-GUIDE.md#7-after-the-install)). Not yet: SuperVOOC fast charging,
camera autofocus and the amplifiers' own DSP protection.

## Feature matrix

<!-- feature-matrix:start -->
<!-- Generated by docs/features/build.py from docs/features/readme-short.py; do not edit by hand. -->

**Kernel 7.3.0-next-20261020-iceland-00554 (q90w2) · Fedora 44 · KDE Plasma 6 / GNOME 50 · 110 working features**

Only working features are listed; the details are in [docs/FEATURES.md](docs/FEATURES.md).

### Boot & platform

<details><summary>Show the 32 working features</summary>

| Feature | Status | Details |
|---|---|---|
| U-Boot (install build and RAM boot) | ✅ Working | U-Boot starts Fedora through EFI, with a power-on boot menu on the keys. |
| U-Boot boot setting for single or dual boot | ✅ Working | Boots a separate Fedora partition when there is one, else the Fedora image in userdata. |
| Linux (7.4 base) | ✅ Working | Linux with the Pad 4 patches on the 7.4 base boots through U-Boot's EFI, Fedora's shim and GRUB. |
| Internal storage (UFS 4) | ✅ Working | UFS 4 storage at about 2.3 GB/s read; btrfs root with compression, and TRIM reaches the flash. |
| Hardware watchdog | ✅ Working | A hung system reboots by itself. |
| System cache (LLCC) and memory error counters | ✅ Working | The system cache works and memory error counters are reported. |
| Memory bandwidth monitors | ✅ Working | The memory bandwidth monitors work and follow the load. |
| Memory bus DVFS (DDR / LLCC memlat) | ✅ Working | Memory and system-cache clocks scale with the load. |
| GPI DMA engines | ✅ Working | The DMA engines for the I2C and SPI buses work. |
| Fuses (QFPROM) | ✅ Working | The fuses are read; the GPU picks its speed bin from them. |
| Hardware random number generator | ✅ Working | Two hardware random number sources feed the kernel's random pool. |
| CPU firmware after a cold start | ✅ Working | The CPU control firmware starts cleanly, also after the tablet has cooled down. |
| Wall clock (RTC offset in SDAM2) | ✅ Working | The clock is right at boot, also offline. |
| Fedora 44 from RAM / the PC's disk | ✅ Working | For testing, Fedora boots from RAM or from a PC's disk without writing to the tablet. |
| GNOME Shell 50 | ✅ Working | GNOME 50 on Fedora 44, with GNOME's first-boot setup on a new install. |
| KDE Plasma 6 desktop | ✅ Working | KDE Plasma 6 on Wayland with auto-rotate, automatic brightness, the charge limit and suspend. |
| Stable USB sessions | ✅ Working | Long sessions over the USB link to a PC stay stable, also during fast transfers. |
| Firmware extractor (tablet's own partitions, read-only) | ✅ Working | Copies the tablet's own firmware read-only from its partitions and checks it. |
| Firmware package (iceland-firmware) | ✅ Working | The generic stock firmware as an RPM, every file checksum-pinned; no unit-specific data. |
| Fedora installed on the tablet | ✅ Working | Fedora installs with two partition writes and then boots on its own. |
| Boot slot marked good from Fedora | ✅ Working | Fedora marks the boot slot good after a successful boot. |
| Dual boot BlissROM + Fedora | ✅ Working | A power-on menu starts Fedora or BlissROM (Android); Fedora is the default. |
| Virtual machines (Gunyah) | ✅ Working | Protected VMs on the Gunyah hypervisor with the Virtual Machines app: Linux guests with 3D graphics. |
| Windows 11 ARM guest VM | ✅ Working | Windows 11 ARM runs as a VM with Remote Desktop, ssh, x86 apps and a clean Shut Down from the app. |
| VM window touch input modes | ✅ Working | The VM window takes touch as a tablet, a touchpad or a touch screen, also fullscreen. |
| VM VNC display | ✅ Working | A running VM's screen can be served over VNC, with a viewer button in the app. |
| VM memory and disk speed (2 MiB lends, io_uring) | ✅ Working | VMs boot in about 11 s and their disks read at about 3.3 GB/s. |
| VM fast networking (vhost-net) | ✅ Working | Fast VM networking through vhost-net, several GB/s each way. |
| VM shared-memory mode (partial protection) | ✅ Working | Opt-in shared-memory VMs with 3D OpenGL and Vulkan; the tablet can then read that VM's memory. |
| VM QEMU-Gunyah backend (3D OpenGL) | ✅ Working | An optional QEMU backend runs VMs with 3D OpenGL in a window or over VNC. |
| VM keyboard shortcuts (Send shortcuts to the VM) | ✅ Working | Optionally Super, Alt+Tab, Escape and similar desktop shortcuts go to the VM. |
| VM native GPU context (msm) | ✅ Working | Opt-in: the VM's own Mesa draws directly on the GPU, about 50 % faster than virgl. |

</details>

### Display & input

| Feature | Status | Details |
|---|---|---|
| Native display 3392×2400, dual DSI + DSC | ✅ Working | The panel runs at its native 3392×2400 resolution, without flicker. |
| Refresh 30 / 60 / 90 / 120 / 144 Hz | ✅ Working | 30 to 144 Hz with live switching; a still screen drops to 30 Hz to save power. |
| Backlight | ✅ Working | Brightness slider and automatic brightness work, as on stock. |
| Display wake from sleep | ✅ Working | The picture comes back after every wake from sleep. |
| No pink / blocky glitches in GNOME | ✅ Working | No pink or blocky glitches on the desktop. |
| Smooth window moves under load | ✅ Working | Window moves stay smooth, also under load. |
| Touchscreen | ✅ Working | Works, also after the screen turns off and after sleep. |
| Pen | ✅ Working | The pen works. |
| Lid switch | ✅ Working | The cover turns the screen off and on; on battery a closed cover suspends. |
| Power and volume keys | ✅ Working | The power key wakes and suspends the tablet, as on stock; the volume keys work. |
| Pogo keyboard | ✅ Working | The keyboard cover works: keys, touchpad, lamps and backlight. |
| Auto-rotate | ✅ Working | The screen rotates in tablet mode and stays put while a keyboard is connected. |

### Graphics & compute

| Feature | Status | Details |
|---|---|---|
| Adreno 840 GPU, GLES 3.2 | ✅ Working | OpenGL 4.6 / OpenGL ES 3.2 on Mesa with GPU preemption, without GPU faults. |
| GNOME and Wayland drawn by the GPU | ✅ Working | The desktop is drawn by the GPU; video and shared buffers show correctly. |
| GPU correctness, WebGL, stress | ✅ Working | Passes the GL / Vulkan conformance suites almost fully; WebGL works; GPU hangs are recovered. |
| Vulkan | ✅ Working | Vulkan 1.4 through Mesa's turnip driver. |
| Hardware video decoding | ✅ Working | H.264, HEVC, VP9 and AV1 decode in hardware; VA-API for ffmpeg and hardware video in Chromium. |
| Hardware video encoding | ✅ Working | H.264 and HEVC encode in hardware; screen recording can use it. |
| NPU (Hexagon on the CDSP) | ✅ Working | The NPU's DSP runs, and its runtime library loads. |

### Audio

| Feature | Status | Details |
|---|---|---|
| DSP audio + sound card | ✅ Working | The sound card comes up at boot and stays present. |
| GNOME shows speakers and microphones | ✅ Working | Speakers and microphones appear in the desktop's sound settings. |
| Microphones (2) | ✅ Working | Both microphones work, with echo cancellation and noise suppression by default. |
| Echo cancellation and loopback sound test | ✅ Working | Echo cancellation on the microphone, with a limiter so the output does not clip. |
| All six speakers in stereo | ✅ Working | All six speakers play in stereo with balanced left and right. |
| Speaker level | ✅ Working | The speakers play as loud as on stock. |
| Speaker protection (PipeWire chain) | ✅ Working | A protective filter chain in front of the amplifiers prevents clipping. |
| GNOME volume bar and input slider | ✅ Working | The volume and input sliders follow the desktop's curve. |
| Headset over USB-C | ✅ Working | Headsets work on the USB-C port. |

### Connectivity

| Feature | Status | Details |
|---|---|---|
| Wi-Fi 2.4 GHz | ✅ Working | Connects and reconnects, with a stable Wi-Fi address. |
| Wi-Fi 5 / 6 GHz | ✅ Working | Connects on 5 GHz with downloads above 100 Mbit/s. |
| Bluetooth, own address | ✅ Working | Bluetooth comes up with the tablet's own address. |
| Bluetooth pairing in GNOME | ✅ Working | Pairing and scanning work from the desktop's settings. |
| USB device mode / USB network | ✅ Working | USB device mode and a USB network link to a PC work. |
| Fast USB transfers into the tablet | ✅ Working | Fast USB transfers into the tablet run stable. |
| CPU latency request follows the USB cable | ✅ Working | Without a USB cable the CPUs reach deep idle. |
| USB host / OTG and hubs | ✅ Working | Keyboards, mice, USB sticks and hubs work on the USB-C port. |
| DisplayPort over USB-C | ✅ Working | An external monitor works over USB-C DisplayPort. |

### Power & charging

| Feature | Status | Details |
|---|---|---|
| Battery level, voltage, current, temperature, health | ✅ Working | Battery level and health are shown correctly in the desktop. |
| Battery power reading (power_now) | ✅ Working | The battery power reading is right, so the time remaining is right. |
| Battery time estimate | ✅ Working | A steady time estimate; about 14-16 h of light use or video at half brightness. |
| Charging | ✅ Working | Charges with stock's limits for each charger type. |
| Battery safety guard (stock limits) | ✅ Working | Stock's battery temperature, voltage and current limits are enforced. |
| Charger input cut at a hot USB-C connector | ✅ Working | Charging stops if the USB-C connector gets hot. |
| Charge limit (80 / 85 %) | ✅ Working | 'Preserve Battery Health' stops charging at 80 or 85 %. |
| Bypass charging | ✅ Working | A toggle lets the charger power the tablet while the battery level holds. |
| Low-battery current limiting (BCL) | ✅ Working | Stock's low-battery limits on the CPUs and GPU. |
| Pen charging | ✅ Working | The pen charges on the tablet's magnetic side. |

### Thermal

| Feature | Status | Details |
|---|---|---|
| CPU frequencies and CPU limits (stock) | ✅ Working | CPU temperatures are held at stock's limits under load. |
| Board and flash thermistors | ✅ Working | Board and flash temperatures are read, as on stock. |
| Skin and XO zones | ✅ Working | Stock's skin and crystal temperature limits and shutdown points. |
| Skin temperature policy (stock gears) | ✅ Working | Stock's temperature steps cap CPU, GPU, brightness and charging. |
| USB-C connector temperature zones | ✅ Working | The USB-C connector temperatures are watched. |
| GPU cooling | ✅ Working | The GPU is limited as on stock when it gets hot. |
| NPU / CDSP cooling | ✅ Working | The NPU throttles and recovers as on stock. |

### Sleep & power saving

| Feature | Status | Details |
|---|---|---|
| Suspend (s2idle) | ✅ Working | Suspend and resume work; the tablet sleeps through the night. |
| Wi-Fi across sleep | ✅ Working | Wi-Fi is back about 2 s after a wake. |
| Long sleep | ✅ Working | Long sleeps work. |
| Wake by power key and alarm | ✅ Working | The power key and alarms wake the tablet. |
| Wake by lid, keyboard, charger | ✅ Working | Opening the cover, the keyboard and the charger wake the tablet. |
| 60 Hz on battery (the CDSP stays running) | ✅ Working | 60 Hz on battery and 120 Hz on a charger to save power. |
| CPU scaling and GNOME power modes | ✅ Working | Stock's CPU and GPU levels; the desktop's power modes switch profiles. |
| Deep sleep, overnight drain about 0.35 %/h | ✅ Working | Deep sleep drains about 0.35 % of the battery per hour. |
| Per-rail power telemetry (PMIC) | ✅ Working | Power use of 7 supply rails can be read. |

### Sensors & camera

| Feature | Status | Details |
|---|---|---|
| Rear flash LEDs | ✅ Working | Both flash LEDs work as a torch. |
| Accelerometer, compass, light / proximity | ✅ Working | Accelerometer, compass, light and proximity sensors work. |
| Gyroscope (sensor hub) | ✅ Working | The gyroscope works. |
| Cameras (13 MP rear, 8 MP front) | ✅ Working | The 13 MP rear and 8 MP front cameras stream with the right orientation. |
| Camera app on the installed image | ✅ Working | The desktop camera app works with both cameras. |

### Software & packaging

| Feature | Status | Details |
|---|---|---|
| Kernel package (kernel-iceland) | ✅ Working | Kernel updates install with dnf; a new kernel becomes the default after a good boot. |
| Device package (iceland-device) | ✅ Working | One package carries the tablet's settings: battery guard, thermal, sound, sensors, power saving. |
| Update policy and minimal package holds | ✅ Working | Fedora updates normally, with a snapshot and a rollback entry before each update. |
| Full GNOME app set | ✅ Working | Fedora's default desktop apps, the on-screen keyboard and Flathub. |
| Android apps (DroidLoom) | ✅ Working | Android apps run in their own windows through DroidLoom. |
| Stock-values audit | ✅ Working | Battery, charger, thermal, CPU and GPU limits are checked to never exceed stock. |
| GNOME About page (model, processor) | ✅ Working | The About page shows the right model and processor. |
| Automated test runs | ✅ Working | Changes are checked by automated test runs before they are released. |
| Upstream fixes for this chip's drivers | ✅ Working | The kernel carries the upstream fixes for this chip's drivers. |
| Hardware inventory (every block vs stock) | ✅ Working | Every hardware block is accounted for against stock. |

<!-- feature-matrix:end -->

## Before you start

**The starting state.** The install was carried out on one tablet. It started from LineageOS 24.0 on slot b (slot a
without an Android system), with stock 11.A.38 firmware on both slots. Rooted debugging and USB debugging were on.
A different starting state (stock OxygenOS, slot a active, another firmware release) has not been tried, so it is
untested. ([INSTALL-GUIDE.md](docs/INSTALL-GUIDE.md), "Read this first".)

**The tablet.**

- An **unlocked** boot loader. Unlocking erases the tablet; its steps are in [guide 04, section 1.3](docs/guide/04-BUILD-YOUR-OWN.md).
  The orange warning at boot is expected.
- Stock firmware **11.A.38 on both slots**. Never flash or boot an older firmware: it breaks anti-rollback.
- Battery above 60 % for every write.
- About 13 GB are written. Android's data is lost with the first write.

**The PC.** Android platform tools (`adb`, `fastboot`), the USB cable you have used with this tablet, mains power, and
no sleep during the install. About 30 GB free for the backup and the files.

**The install files.** No install image is published. The image must contain the items of
[INSTALL-GUIDE section 2](docs/INSTALL-GUIDE.md#2-what-you-need), among them files taken from the tablet itself (the
guide names the sensor calibration registry and the Bluetooth address). Its unpacked size must equal your `userdata`
exactly. The U-Boot file for `boot_b` needs an AVB footer made for your tablet's current `boot_b`. Check every file's
SHA-256 before you write it.

The Windows installer ([tools/installer](tools/installer/README-INSTALLER.md)) cannot install yet: it refuses both
writes until a generic install image exists. Its read-only backup part works.

**What is never written, and why.** The Fedora install (Parts A and B) writes two partitions only (`userdata` and
`boot_b`). The optional dual boot (Parts C and D) also changes LUN 0's partition table, writes slot b's Android boot
partitions, `boot_a` and `super`, and erases `userdata` and `metadata`, exactly as its steps list. Every group
below except "Android system" and "Partition table" is never written in any part:

| Group | Partitions (examples) | Why, in plain words |
|---|---|---|
| Boot firmware | `xbl*`, `abl*`, `tz*`, `hyp*`, `aop*`, `uefi*`, `soccp*`, `engineering_cdt*` and the others of the boot chain | They start fastboot. No public emergency loader exists for this tablet, so a broken chain cannot be repaired at home. |
| Radio and DSP firmware | `modem*`, `bluetooth*`, `dsp*` | Signed and version-locked. Fedora only reads them. |
| Per-device data | `persist`, `cdt`, `ddr`, `dinfo`, `ocdt` | Calibration and identity of one tablet. They exist nowhere but in its backup. |
| Security state | `devinfo`, `keystore`, `frp`, `secdata`, `uefivarstore` | One wrong byte can lock the boot loader or the secure world. |
| Android system | `super`, `vbmeta*`, `vendor_boot*`, `init_boot*`, `dtbo*`, `recovery*`, `boot_a`, `misc` | Fedora does not need them. Leaving them alone keeps the way back short. |
| Partition table | the GPT of every unit | The Fedora install does not repartition. Part C changes LUN 0's table for the dual boot. |
| UFS storage firmware | the storage chip's own firmware | A wrong update is the one software path to a dead tablet that does not go through a partition. |

**The rules of the procedure** ([INSTALL-GUIDE section 3](docs/INSTALL-GUIDE.md#3-the-rules-for-the-whole-procedure)):

1. The install types only `fastboot flash userdata ...` and `fastboot flash boot_b ...`. The guide's rule list says
   never `fastboot -w`, `flashall`, `update`, `set_active`, `erase`, `format` or `flashing lock`. Parts C and E show
   where other guide steps use `erase` or `-w`; read those notes before you type the commands.
2. Writes are made only in the tablet's own boot loader: `fastboot getvar product` must answer `canoe`.
3. If a screen, a message or a number differs from the guide, stop. Do not retry a write with other arguments.

## Manual install

The commands below are copied from the guides, and each part names its guide section. For the reasons behind a step,
read [INSTALL-PLAN.md](docs/INSTALL-PLAN.md). Battery above 60 % for every write.

- **Part A**: backups and reads only.
- **Part B**: Fedora and U-Boot, the two writes of the install (`userdata`, then `boot_b`).
- **Part C**: the dual-boot split (optional): Fedora's partition table, then LUN 0's table.
- **Part D**: BlissROM (optional): Android's partitions, `super`, `userdata` and `metadata`.
- **Part E**: using the tablet, updates and the way back.

### Part A - backups (read only)

1. **A full backup** of every partition except `userdata` ([INSTALL-GUIDE section 4, step 1](docs/INSTALL-GUIDE.md#4-before-the-first-write-read-only)).
   The guide gives no script. The project read each partition from `/dev/block/by-name/<name>` with `dd` and hashed
   both copies ([guide 04, section 1.4](docs/guide/04-BUILD-YOUR-OWN.md)). Keep two copies on two disks. Never upload them.
2. **The stock 11.A.38 images** with their checksums, for the way back (step 2).
3. **Your own files.** Copy them off the tablet. Android's `/data/vendor` can be copied with `adb root` (step 3).
4. **The current `boot_b`**, saved from the running Android system with `adb root`, read only. Keep it as
   `boot_b-saved.img`; the undo in Part B uses that name. Take it from the system that runs today, not from an older
   backup. Check that `misc` does not hold `boot-recovery` or `boot-fastboot` (step 4).
5. **The slot flags and the rescue keys.** Switch the tablet off, hold **Volume Down + Power** until the boot loader's
   fastboot screen shows, connect USB, and read (these commands only read; step 5):

```bash
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

**Dual boot only, after Part B:** the dual-boot backup, read only, on the installed Fedora. Copy the folder to the PC and
check it there ([DUAL-BOOT.md, Backups first](docs/DUAL-BOOT.md#backups-first)):

```bash
sudo bash tools/dualboot/dualboot-backup.sh    # default output /var/tmp/dualboot-backup-<date-time>
sha256sum -c SHA256SUMS                         # on the PC, in the copied folder
```

The dual-boot backup holds the tablet's partition GUIDs and tables. Keep it private.

### Part B - Fedora and U-Boot

The file names below are the guide's. The v7 release names the images `u-boot-iceland-v7.img` (plain) and
`u-boot-iceland-v7-footered.img`. Check each file's SHA-256 against the release's `SHA256SUMS` before a write.

1. **RAM test of U-Boot, before any write** (step 6). `fastboot boot` loads the image into RAM only. Nothing is written
   and the slot flags do not change. U-Boot finds no Fedora and waits in its own fastboot.

```bash
fastboot boot u-boot-iceland-usb.img       # the plain install build; RAM only
fastboot getvar product                    # now: oneplus-iceland (U-Boot)
```

   Return with **Volume Down + Power** or `fastboot reboot`.

2. **Write 1: the Fedora image into `userdata`** (section 5). ABL accepts a sparse image in pieces of up to 805 MB; the
   PC's fastboot reports each piece. Expect several minutes. Do not touch the cable.

```bash
adb reboot bootloader
fastboot getvar product                    # canoe
fastboot getvar current-slot               # b
fastboot getvar partition-size:userdata    # must equal the image's unpacked size
fastboot flash userdata fedora-iceland.sparse.img
```

   Until write 2, Android starts and says its data may be corrupt. **Never confirm the factory reset**. Choose
   "Try again" or power off.

3. **Proof, still tethered.** Run the plain build again (`fastboot boot u-boot-iceland-usb.img`). Fedora's first-boot
   setup starts: language, keyboard, Wi-Fi, privacy, and your user account. The image has none. Repeat the tethered
   boot until Fedora reaches the desktop reliably.

4. **Write 2: U-Boot into `boot_b`.** Only after Fedora started tethered. Switch the tablet off, hold
   **Volume Down + Power**, connect USB (install guide, section 6):

```bash
fastboot getvar product                    # canoe (the tablet's own boot loader)
fastboot getvar current-slot               # b
fastboot flash boot_b u-boot-iceland-footered.img
fastboot getvar slot-successful:b          # read the flags before the reboot
fastboot getvar slot-retry-count:b
fastboot reboot
```

   Flashing `boot_b` clears slot b's *successful* flag and sets its retry count to the maximum. Each normal power-on
   then uses one try until the running system marks the slot good (`iceland-slot-mark`, iceland-device 0.28-8 or newer).

5. **Proof.** Unplug the PC. Switch the tablet off and on a few times: the menu appears and Fedora reaches the
   desktop. In Fedora, `journalctl -u iceland-slot-mark` shows the marking, and `qbootctl` lists slot b as active,
   successful and bootable. Then read the flags again (Volume Down + Power, then the `getvar` lines of Part A, step 5):
   `current-slot` is `b`, `slot-unbootable:b` is `no` and `slot-successful:b` is `yes`.

   **Undo:** if the retry count falls from boot to boot and slot b is not marked, stop booting and restore the copy:

```bash
fastboot flash boot_b boot_b-saved.img      # the file of Part A, step 4
```

   Android then starts without its data. Fedora stays in `userdata` and can still be started tethered.

### Part C - dual boot: split LUN 0 (optional)

This part adds BlissROM's space and follows [DUAL-BOOT.md](docs/DUAL-BOOT.md), steps W0a to A. The scripts refuse to
run in the wrong state. Most steps have a check and an undo. Who runs what:

- **On the installed Fedora, as root:** W0a, W0b, W1, W2 and W2b.
- **In a Linux started from RAM** (`fastboot boot`, no partition of LUN 0 mounted): W3. The guide names its needs:
  `dd`, `cmp`, `sha256sum` and `blockdev`. No such image is published, and the guide gives no tested recipe for one.
- **In the boot loader's fastboot, from the PC:** W4, W5b, W5k, W5c, W6, M and A.

Compute the numbers from your own backup, not from the examples, with `tools/dualboot/gpt-plan.py` (it never writes to a
device). The scripts refuse a disk of another size. Change their constants (`F`, `NI`, `P3START` in `dualboot-w2.sh`,
the `--blocks` default in `w3-gpt.sh`) as the guide says.

| Step | Where | What | Undo |
|---|---|---|---|
| W0a | Fedora | Install iceland-device [0.28-25](https://github.com/mzakamin-hub/iceland-mainline/releases/tag/iceland-device-0.28-25) or newer. Check: the package's `--check` rows pass. | Install the previous package again with `sudo rpm -Uvh --oldpackage ...`. |
| W0b | Fedora | `sudo systemctl mask systemd-repart.service` (repart would grow Fedora's disk back over the new end). Check: `systemctl is-enabled systemd-repart` = `masked`. | `sudo systemctl unmask systemd-repart.service` |
| W1 | Fedora | `sudo btrfs filesystem resize 120g /`, then `sudo btrfs scrub start -B /`. Check: no errors. | `sudo btrfs filesystem resize max /` |
| W2 | Fedora | Fedora's own partition table for the smaller disk: `gpt-plan.py shrink HEAD TAIL <DISK_BLOCKS> <NEW_BLOCKS> plan/ --trust-primary`, then `sudo bash dualboot-w2.sh --dry-run`, then `sudo bash dualboot-w2.sh --write --confirm CODE` (the dry run prints CODE). Check: two reboots, Fedora starts normally, and `sfdisk -d` on the loop disk shows p3 ending at `NEW_BLOCKS - 6` (32,730,382 in the tested example). | `sudo bash dualboot-w2.sh --restore --confirm CODE` |
| W2b | Fedora | Only with iceland-device 0.28-24 (not needed with 0.28-25), right before W3: `sudo grub2-editenv - list`. If there is no `iceland_args` line, `sudo grub2-editenv - set iceland_args=iceland.carrier=fedora`; otherwise add ` iceland.carrier=fedora` to its value. Check: `grub2-editenv - list` shows it. | `sudo grub2-editenv - unset iceland_args` (or the old value). Without W3, Fedora waits for a `fedora` partition: at the GRUB menu press `e`, remove `$iceland_args` from the `linux` line for that start, then unset it. |
| W3 | Linux in RAM | LUN 0's table: `gpt-plan.py split HEAD TAIL <LUN0_BLOCKS> <USERDATA_START> plan/ --userdata-last <USERDATA_LAST>`, then `w3-gpt.sh --dry-run`, then `w3-gpt.sh --write --confirm CODE`. Check: `RESULT PASS`; then `fastboot getvar partition-size:userdata` and `partition-size:fedora` show the new sizes, and Fedora starts from the `fedora` partition. | `w3-gpt.sh --restore --confirm CODE`, from the same RAM system. |
| W5b | Boot loader fastboot | `fastboot flash vendor_boot_b vendor_boot.img`, then `init_boot_b`, `dtbo_b`, `vbmeta_system_b`, `vbmeta_vendor_b` and `vbmeta_b` with their images. Check: slot b's flags are unchanged; U-Boot and Fedora still start. | Flash the backup's `parts/<name>.img` back. |
| W5k | Boot loader fastboot | `fastboot flash boot_a boot.img` (BlissROM's kernel image only). Check: slot b stays current. | Flash the backup's `parts/boot_a.img` back. |
| W5c | PC, then boot loader fastboot | `mk-super.py SUPER_HEAD IMG_DIR super-bliss.img`, then `check-super.py super-bliss.img IMG_DIR` (last line `SUPER-CHECK: 0 failure(s)`), then `fastboot flash super super-bliss.img`. | Not needed for Fedora. |
| W4 | Boot loader fastboot | `fastboot erase userdata`, then `fastboot erase metadata`. Only after W3's sizes are confirmed. | None: this erases Android's data. |
| M | Boot loader fastboot | RAM test, writes nothing: `fastboot boot u-boot-iceland-v7.img`, then choose BlissROM. | - |
| W6 | Boot loader fastboot | `fastboot flash boot_b u-boot-iceland-v7-footered.img` (U-Boot updated in place). Check: the menu shows Fedora, BlissROM and the boot loader. | Flash the backup's `parts/boot_b.img` back. |
| A | Boot loader fastboot | After one start of each system: power on with Volume Down held, then `fastboot getvar current-slot` (`b`) and `fastboot getvar slot-successful:b` (`yes`). Reads only. | - |

> **Note on W4.** The install guide's rules forbid `erase`. This step uses it for Android's data, as the dual-boot
> guide says. Run it only after W3 and the sizes are checked.

**Example, not a target:** the tested tablet had 256 GB of storage. Its split gave `fedora` about 124.9 GiB and
`userdata` about 96.0 GiB, with 1 MiB kept unused at the end of LUN 0. Yours will differ.

### Part D - BlissROM (optional, after Part C)

Use BlissROM v20.1 for `iceland` (the OTA zip) and a `payload.bin` extractor. The tested images are listed in
[DUAL-BOOT.md](docs/DUAL-BOOT.md). Each one goes to a fixed place. The OTA's firmware images are not flashed.

| Image | Goes to |
|---|---|
| `boot.img` | `boot_a`, the kernel only. Never into `boot_b` (that would replace U-Boot) or `recovery_b`. |
| `vendor_boot.img`, `init_boot.img`, `dtbo.img`, `vbmeta.img`, `vbmeta_system.img`, `vbmeta_vendor.img` | the `_b` partitions of the same names (W5b). |
| `system.img`, `system_ext.img`, `product.img`, `odm.img`, `vendor.img`, `system_dlkm.img`, `vendor_dlkm.img` | the `super` image of slot b, built by `mk-super.py` and checked by `check-super.py` (W5c). |

Why not `boot_b` or `recovery_b`: ABL starts `recovery_b` only when it has no kernel, and then with `boot_b`'s kernel
(U-Boot), so a kernel in `recovery_b` cannot start Android. `boot_a`, on the unused slot a, holds the kernel instead.

Keep in mind ([DUAL-BOOT.md, Keep in mind](docs/DUAL-BOOT.md#keep-in-mind)):

- Turn off BlissROM's automatic updates, and install nothing from its updater. The updater switches to slot a, which
  skips U-Boot.
- Never flash a BlissROM image into `boot_b`. Never use Settings > "Erase all data" in BlissROM.
- Never `fastboot set_active a`. Let each start finish, so that slot b is marked good.

### Part E - using the tablet, updates, the way back

- **The menu.** It appears at power-on. Volume Up and Volume Down move the highlight, Power selects. Fedora starts after
  5 s if nothing is chosen. The install guide (section 1) names only Volume Down for moving; the dual-boot guide names
  both keys.
- **The boot loader's fastboot.** Hold **Volume Down + Power** (about 15 s) until its fastboot screen shows, or hold
  Volume Down at power-on, or choose "Boot loader (fastboot)" in the menu. Holding Power alone restarts the tablet, and
  that counts as another try of slot b.
- **From Fedora, `systemctl reboot bootloader` does not reach the boot loader.** It lands in Fedora. This is unsolved.
- **Updates.** Use GNOME Software or `dnf upgrade`, as on any Fedora. Updates can only change files inside the Fedora
  disk (in `userdata`, or in `fedora` after the split). A read-only snapshot is taken before each change, with a
  rollback entry in GRUB's menu. Kernels from this project come from the tablet's own repository; a new kernel boots
  once as a trial. Fedora holds back the sensor programs and `alsa-ucm` ([INSTALL-GUIDE section 7](docs/INSTALL-GUIDE.md#7-after-the-install)).
- **Never from inside Fedora:** no partitioning tool on the internal storage, no `dd` to `/dev/sd*`, no firmware or
  boot loader tool. The device package makes the other partitions read-only.
- **Going back.** [INSTALL-GUIDE section 8](docs/INSTALL-GUIDE.md#8-back-to-stock-oxygenos) gives the table. To undo only
  write 2, flash the saved `boot_b` back (Part B, step 5). The full return to stock is written as a script and
  dry-run, and was never executed. Its table says to erase `userdata` and `metadata` with `fastboot -w`, which the
  install's rule list forbids; read section 8 before you type it. A way back to LineageOS after the install is not written down.
- **If something differs.** Stop and write nothing more. [INSTALL-GUIDE section 9](docs/INSTALL-GUIDE.md#9-if-something-is-not-as-described)
  lists what each symptom means and what to do.

## Downloads

Everything below is a published release with a `SHA256SUMS` file. Check your downloads with `sha256sum -c SHA256SUMS`.

| What | Version | Release page | Files |
|---|---|---|---|
| Kernel (`kernel-iceland`, Fedora 44 aarch64) | q90w2, kernel `7.3.0-next-20261020-iceland-00554` (the patch queue on linux-next `next-20261020`) | [iceland-linux q90w2](https://github.com/mzakamin-hub/iceland-linux/releases/tag/q90w2) | RPM, source RPM, `SHA256SUMS` |
| U-Boot, install build | v7 (2026-10-17) | [iceland-u-boot v7-2026-10-17](https://github.com/mzakamin-hub/iceland-u-boot/releases/tag/v7-2026-10-17) | plain image (RAM test), footered image (`boot_b`), `SHA256SUMS` |
| `iceland-device` (the tablet's settings, with `iceland-device-kde` / `-gnome`), `iceland-coexist` (kernel-install for a shared `/boot`) | iceland-device 0.28-40, iceland-coexist 1.0-7 | [iceland-device-0.28-40](https://github.com/mzakamin-hub/iceland-mainline/releases/tag/iceland-device-0.28-40) | noarch RPMs, source RPMs, `SHA256SUMS` |
| `upower` (time to full to the charge limit) | 1.91.5-1.fc44.iceland1 | [iceland-device-0.28-33](https://github.com/mzakamin-hub/iceland-mainline/releases/tag/iceland-device-0.28-33) | aarch64 RPMs, source RPM, `SHA256SUMS` |
| `iris-vaapi` (VA-API hardware video decode; `iris-vaapi-chromium` for Fedora's chromium) | 0.2.0^20261023git9852479-1.iceland1 | [iris-vaapi-0.2.0-1.iceland1](https://github.com/mzakamin-hub/iceland-mainline/releases/tag/iris-vaapi-0.2.0-1.iceland1) | aarch64 RPMs, source RPM, `SHA256SUMS` |
| `iceland-firmware` (generic firmware) | 11.A.38-6 | [iceland-firmware 11.A.38-6](https://github.com/mzakamin-hub/iceland-firmware/releases/tag/11.A.38-6) | noarch RPM, source RPM, `SHA256SUMS` |
| Windows installer (blocked for writes) | in iceland-device 0.28-16 | [iceland-device-0.28-16](https://github.com/mzakamin-hub/iceland-mainline/releases/tag/iceland-device-0.28-16) | `Install-Pad4Linux.ps1`, `README-INSTALLER.md`, `SHA256SUMS` |

The current kernel is q90w2 (`7.3.0-next-20261020-iceland-00554`, iceland-linux tag `q90w2`). The virtual machine packages are released as
[iceland-gvm 0.3-59](https://github.com/mzakamin-hub/iceland-gvm/releases/tag/0.3-59) (with virglrenderer 1.3.0-1.iceland1) and [iceland-vms 0.2-23](https://github.com/mzakamin-hub/iceland-vms/releases/tag/0.2-23) (with iceland-vms-guest-mesa 26.2.5-1.iceland1) (with iceland-qemu-gunyah 10.0.2-1 from [0.2-20](https://github.com/mzakamin-hub/iceland-vms/releases/tag/0.2-20); RPMs and `SHA256SUMS`;
sources and build steps in each repository).

The Fedora disk image and the install image are **not** published. [Guide 04](docs/guide/04-BUILD-YOUR-OWN.md) covers
building the kernel, U-Boot and the packages, and [INSTALL-GUIDE section 2](docs/INSTALL-GUIDE.md#2-what-you-need) says
what the disk image must contain. The guides give no complete recipe for the disk image. Older releases are on each
repository's releases page.

## Repositories

All repositories are public under the GitHub user `mzakamin-hub`. The guide set is indexed in
[docs/guide/INDEX.md](docs/guide/INDEX.md).

| Repository | Default branch | What it holds |
|---|---|---|
| [iceland-mainline](https://github.com/mzakamin-hub/iceland-mainline) (this one) | `main` | The guides, the feature list, the device package (`packaging/iceland-device`), the dual-boot tools (`tools/dualboot`) and the installer (`tools/installer`). |
| [iceland-linux](https://github.com/mzakamin-hub/iceland-linux) | `main`; current work on `iceland-7.3-rc7-next` | The kernel: a patch queue on linux-next `next-20261020` (the 7.4 base), the build scripts and the `kernel-iceland` package. |
| [iceland-gvm](https://github.com/mzakamin-hub/iceland-gvm) | `main` | The virtual machine stack: crosvm patches for Gunyah, the guest kernel config and patches, `gvm.sh`, the guest tools and the `iceland-gvm` package. |
| [iceland-vms](https://github.com/mzakamin-hub/iceland-vms) | `main` | The Virtual Machines app (GTK4 / libadwaita, Python) and the `iceland-vms` package; the sources of `iceland-qemu-gunyah` (QEMU with the Gunyah accelerator). |
| [iceland-droidloom](https://github.com/mzakamin-hub/iceland-droidloom) | `main` | DroidLoom (Android apps) packaging: the host patches and spec, the image recipe and the `iceland-droidloom` integration package. |
| [iceland-u-boot](https://github.com/mzakamin-hub/iceland-u-boot) | `main` | U-Boot v2026.10-rc5 for the tablet, with the install build and its boot menu, and the build scripts. |
| [iceland-firmware](https://github.com/mzakamin-hub/iceland-firmware) | `main` | The generic firmware of stock 11.A.38 as one RPM, with its manifest, the exclusion list and the vendor notices. |
| [android_device_oneplus_iceland](https://github.com/mzakamin-hub/android_device_oneplus_iceland) | `lineage-24.0` | The LineageOS 24.0 device tree for the tablet (the Android side). |
| [proprietary_vendor_oneplus_iceland](https://github.com/mzakamin-hub/proprietary_vendor_oneplus_iceland) | `lineage-24.0` | The LineageOS 24.0 vendor tree: the proprietary files and the radio images (Git LFS). |

## Glossary

| Term | Meaning |
|---|---|
| **ABL** | Android Boot Loader: the tablet's own boot loader, from OnePlus and Qualcomm. It is closed and the project never writes it. Its fastboot is the rescue path. |
| **fastboot** | The PC tool and the boot loader's USB mode for writing and booting images. `fastboot boot` runs an image from RAM. `fastboot flash` writes a partition. |
| **slot (A/B)** | Each boot partition exists twice, `_a` and `_b`. The boot loader starts the active slot and keeps a successful flag, an unbootable flag and a retry count for each. |
| **boot_b** | The boot partition of slot b. The install writes U-Boot there. |
| **U-Boot** | The open-source boot loader. The project's build in `boot_b` shows the menu and starts Fedora or BlissROM. |
| **sparse image** | An Android image format that stores only the used blocks. `fastboot flash` takes it directly and sends it in pieces. |
| **super** | Android's container for its dynamic system partitions (`system`, `vendor`, `product` and others). The dual boot writes BlissROM's seven of them into it. |
| **LUN** | One of the tablet's six UFS storage units, `sda` to `sdf`. Each uses 4096-byte blocks. LUN 0 holds the split of Part C. |
| **GPT** | The GUID partition table at the start and end of a LUN. The dual boot changes LUN 0's table. |
| **RAM boot** | Starting an image with `fastboot boot`. Nothing is written, and a reboot returns the tablet to its installed boot. |

## Getting help

Open an issue in the repository the problem concerns: `iceland-mainline` for the install and the guides, `iceland-linux`
for the kernel, `iceland-u-boot` and `iceland-firmware`. Never post serial numbers, MAC or Bluetooth addresses, Wi-Fi
network names, backups or other files from your tablet.
